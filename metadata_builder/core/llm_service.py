"""LLM client for metadata generation."""

import json
import logging
import re
import time
from typing import Dict, Any, Optional

from openai import OpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config.config import get_llm_api_config
from ..utils.token_counter import TokenCounter
from ..metadata.exceptions import LLMEmptyResponseError

logger = logging.getLogger(__name__)

class LLMClient:
    """Handles interactions with the LLM API."""
    
    def __init__(self, model: str = None, client: Optional[OpenAI] = None):
        """Initialize LLM client.
        
        Args:
            model: Optional model name to use
            client: Optional OpenAI client instance
        """
        if client is None:
            api_key, base_url, model = get_llm_api_config()
            self.client = OpenAI(base_url=base_url, api_key=api_key)
        else:
            self.client = client
        self.model = model
        self.token_counter = TokenCounter(model)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((LLMEmptyResponseError, OpenAIError))
    )
    def call_llm(self, prompt: str) -> str:
        """Call LLM and get raw response.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response as a string
            
        Raises:
            LLMEmptyResponseError: If LLM returns empty response
            OpenAIError: If there's an API error
        """
        start_time = time.time()
        try:
            if not isinstance(prompt, str):
                logger.error(f"Invalid prompt type: {type(prompt)}")
                raise ValueError(f"Prompt must be a string, got {type(prompt)}")
                
            logger.info(f"LLM REQUEST: {prompt}")
            
            try:
                prompt_tokens = self.token_counter.count_tokens(prompt)
                logger.info(f"Prompt tokens: {prompt_tokens}")
            except Exception as e:
                logger.error(f"Error counting tokens: {e}")
                prompt_tokens = 0
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=8192,
            )

            if not response or not response.choices or len(response.choices) == 0:
                logger.error("Empty response received from LLM")
                raise LLMEmptyResponseError("Empty response from LLM")

            content = response.choices[0].message.content
            if not content or not content.strip():
                logger.error("Empty content received from LLM")
                raise LLMEmptyResponseError("Response content is empty")

            try:
                completion_tokens = self.token_counter.count_tokens(content)
                self.token_counter.update_stats(prompt_tokens, completion_tokens)
                logger.info(f"Completion tokens: {completion_tokens}")
            except Exception as e:
                logger.error(f"Error counting completion tokens: {e}")

            elapsed_time = time.time() - start_time
            logger.info(f"LLM call completed in {elapsed_time:.2f} seconds")
            logger.info(f"Raw LLM response:\n{content}")
            
            return content.strip()

        except OpenAIError as e:
            elapsed_time = time.time() - start_time
            logger.error(f"OpenAI API error after {elapsed_time:.2f} seconds: {str(e)}")
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error in LLM call after {elapsed_time:.2f} seconds: {e}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((LLMEmptyResponseError, OpenAIError, json.JSONDecodeError))
    )
    def call_llm_json(
        self,
        prompt: str,
        operation_type: str = 'default',
        structure: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call LLM and parse response as JSON.
        
        Args:
            prompt: The prompt to send to the LLM
            operation_type: Type of operation being performed
            structure: Optional JSON structure to expect
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            LLMEmptyResponseError: If LLM returns empty response
            json.JSONDecodeError: If response is not valid JSON
        """
        try:
            content = self.call_llm(prompt)
            cleaned_content = self._clean_json_string(content.strip())
            if not cleaned_content:
                raise json.JSONDecodeError("No JSON content found", content, 0)
                
            return json.loads(cleaned_content)
            
        except Exception as e:
            logger.error(f"Error in LLM JSON call for {operation_type}: {str(e)}")
            raise

    @staticmethod
    def _clean_json_string(json_string: str) -> str:
        """Clean and validate JSON string.
        
        Args:
            json_string: Raw JSON string to clean
            
        Returns:
            Cleaned JSON string
        """
        json_string = json_string.strip()
        json_string = re.sub(r'[^\x00-\x7F]+', '', json_string)
        json_string = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', json_string)
        json_string = re.sub(r',\s*([\]}])', r'\1', json_string)
        
        json_start = json_string.find('{')
        json_end = json_string.rfind('}') + 1
        
        if json_start != -1 and json_end != 0:
            json_string = json_string[json_start:json_end]
            
            # Fix unbalanced braces
            open_braces = json_string.count('{')
            close_braces = json_string.count('}')
            if open_braces > close_braces:
                json_string += '}' * (open_braces - close_braces)
                
            open_brackets = json_string.count('[')
            close_brackets = json_string.count(']')
            if open_brackets > close_brackets:
                json_string += ']' * (open_brackets - close_brackets)
                
            # Fix truncated strings
            if json_string.count('"') % 2 != 0:
                json_string += '"'
        
        return json_string 