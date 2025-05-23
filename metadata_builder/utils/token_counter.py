"""Token counting utility for LLM requests."""

import logging
import time
from typing import Dict, Any, Optional
import tiktoken

logger = logging.getLogger(__name__)

class TokenCounter:
    """Counts tokens in LLM requests and responses."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize token counter.
        
        Args:
            model: The model name to use for token counting
        """
        self.model = model or "gpt-4-turbo-preview"
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        self.request_count = 0
        self.start_time = time.time()
        
        # Maps model names to tiktoken encodings
        self.model_encodings = {
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-3.5-turbo-16k": "cl100k_base",
            "gpt-4": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4-turbo-preview": "cl100k_base",
            "gpt-4-32k": "cl100k_base"
        }
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Token count
        """
        try:
            encoding_name = self.model_encodings.get(self.model, "cl100k_base")
            encoding = tiktoken.get_encoding(encoding_name)
            token_count = len(encoding.encode(text))
            return token_count
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}")
            # Approximate token count as fallback (rough estimate: 4 chars per token)
            return len(text) // 4
    
    def update_stats(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Update token usage statistics.
        
        Args:
            prompt_tokens: Tokens used in the prompt
            completion_tokens: Tokens used in the completion
        """
        self.token_usage["prompt_tokens"] += prompt_tokens
        self.token_usage["completion_tokens"] += completion_tokens
        self.token_usage["total_tokens"] += prompt_tokens + completion_tokens
        self.request_count += 1
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics.
        
        Returns:
            Dictionary with token usage statistics
        """
        elapsed_time = time.time() - self.start_time
        stats = {
            **self.token_usage,
            "request_count": self.request_count,
            "elapsed_time_seconds": elapsed_time,
            "tokens_per_second": self.token_usage["total_tokens"] / max(1, elapsed_time),
            "average_tokens_per_request": self.token_usage["total_tokens"] / max(1, self.request_count)
        }
        return stats
    
    def log_usage(self) -> None:
        """Log current token usage statistics."""
        stats = self.get_usage_stats()
        logger.info(f"Token usage: {stats['prompt_tokens']} prompt, "
                   f"{stats['completion_tokens']} completion, "
                   f"{stats['total_tokens']} total across {stats['request_count']} requests")
        logger.debug(f"Detailed token stats: {stats}")
    
    def reset_stats(self) -> None:
        """Reset token usage statistics."""
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        self.request_count = 0
        self.start_time = time.time() 