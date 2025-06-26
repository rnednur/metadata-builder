"""Natural language conversation interface for the metadata agent."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.llm_service import LLMClient


@dataclass
class ConversationContext:
    """Context for ongoing conversations with the agent."""
    user_id: str
    session_id: str
    current_database: Optional[str] = None
    current_table: Optional[str] = None
    conversation_history: List[Dict[str, str]] = None
    user_preferences: Dict[str, Any] = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.last_activity is None:
            self.last_activity = datetime.now()


class ConversationAgent:
    """Natural language interface for metadata operations."""
    
    def __init__(self, metadata_agent):
        """Initialize conversation agent.
        
        Args:
            metadata_agent: Reference to the main MetadataAgent instance
        """
        self.metadata_agent = metadata_agent
        self.llm_client = LLMClient()
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.logger = logging.getLogger(__name__)
        
        # Conversation patterns and intents
        self.intent_patterns = {
            "generate_metadata": [
                "generate metadata", "create documentation", "document table",
                "analyze table", "describe columns", "metadata for"
            ],
            "search_data": [
                "find table", "search for", "look for", "which table",
                "where is", "show me tables", "list tables"
            ],
            "quality_analysis": [
                "data quality", "check quality", "quality issues", "problems",
                "validation", "quality metrics", "data problems"
            ],
            "schema_analysis": [
                "schema changes", "structure changes", "new columns",
                "dropped tables", "schema diff", "what changed"
            ],
            "business_context": [
                "business meaning", "what does", "explain table",
                "business definition", "purpose of", "used for"
            ],
            "export_data": [
                "export", "download", "save to", "generate file",
                "create report", "output to"
            ]
        }
    
    async def handle_message(self, user_id: str, message: str, session_id: str = None) -> Dict[str, Any]:
        """Handle a natural language message from a user.
        
        Args:
            user_id: Unique identifier for the user
            message: Natural language message from the user
            session_id: Optional session identifier
            
        Returns:
            Response containing agent reply and any actions taken
        """
        # Get or create conversation context
        context_key = f"{user_id}_{session_id}" if session_id else user_id
        context = self.active_conversations.get(context_key)
        
        if not context:
            context = ConversationContext(
                user_id=user_id,
                session_id=session_id or f"session_{datetime.now().isoformat()}"
            )
            self.active_conversations[context_key] = context
        
        # Update context
        context.last_activity = datetime.now()
        context.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Parse intent and extract entities
            intent_analysis = await self._analyze_intent(message, context)
            
            # Generate response and actions
            response = await self._generate_response(intent_analysis, context)
            
            # Execute any required actions
            actions_result = await self._execute_actions(intent_analysis, context)
            
            # Update conversation history
            context.conversation_history.append({
                "role": "assistant",
                "content": response["text"],
                "timestamp": datetime.now().isoformat(),
                "actions": actions_result
            })
            
            return {
                "response": response["text"],
                "intent": intent_analysis["intent"],
                "entities": intent_analysis.get("entities", {}),
                "actions_taken": actions_result,
                "suggestions": response.get("suggestions", []),
                "context": {
                    "current_database": context.current_database,
                    "current_table": context.current_table
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            error_response = await self._generate_error_response(str(e), context)
            
            context.conversation_history.append({
                "role": "assistant",
                "content": error_response,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            
            return {
                "response": error_response,
                "error": str(e),
                "suggestions": ["Try rephrasing your request", "Ask for help with available commands"]
            }
    
    async def _analyze_intent(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user intent from natural language message."""
        
        # Build context for LLM
        conversation_context = ""
        if context.conversation_history:
            recent_history = context.conversation_history[-5:]  # Last 5 messages
            conversation_context = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in recent_history
            ])
        
        current_context = ""
        if context.current_database:
            current_context += f"Current database: {context.current_database}\n"
        if context.current_table:
            current_context += f"Current table: {context.current_table}\n"
        
        prompt = f"""
        Analyze this natural language request in the context of a metadata management system:
        
        Current Context:
        {current_context}
        
        Recent Conversation:
        {conversation_context}
        
        User Message: "{message}"
        
        Available Operations:
        1. generate_metadata - Generate or update table/column metadata
        2. search_data - Find tables, columns, or data assets
        3. quality_analysis - Analyze data quality and identify issues
        4. schema_analysis - Analyze schema changes and structure
        5. business_context - Explain business meaning and context
        6. export_data - Export metadata or generate reports
        7. help - Provide help and guidance
        8. conversation - General conversation or clarification
        
        Extract:
        1. Primary intent (from operations above)
        2. Entities (database names, table names, column names, file formats)
        3. Parameters (specific requirements, filters, formats)
        4. Context updates (if user is switching database/table focus)
        5. Confidence level (0.0-1.0)
        
        Return a JSON response with the analysis.
        """
        
        return await self.llm_client.call_llm_json(prompt, "intent_analysis")
    
    async def _generate_response(self, intent_analysis: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Generate natural language response based on intent analysis."""
        
        intent = intent_analysis.get("intent", "conversation")
        entities = intent_analysis.get("entities", {})
        confidence = intent_analysis.get("confidence", 0.5)
        
        # Build context for response generation
        conversation_summary = ""
        if len(context.conversation_history) > 1:
            conversation_summary = f"Previous conversation context: {context.conversation_history[-2:]}"
        
        prompt = f"""
        Generate a helpful and conversational response for a metadata management assistant.
        
        User Intent: {intent}
        Extracted Entities: {entities}
        Confidence Level: {confidence}
        Current Database: {context.current_database}
        Current Table: {context.current_table}
        {conversation_summary}
        
        Guidelines:
        1. Be conversational and helpful
        2. Acknowledge what the user is asking for
        3. If confidence is low (<0.7), ask for clarification
        4. Provide specific next steps or actions
        5. Suggest related operations that might be useful
        6. Use technical terms appropriately based on user expertise
        
        Generate a response that includes:
        1. Main response text
        2. Suggested follow-up actions (if applicable)
        3. Any clarifying questions needed
        
        Return as JSON with "text" and "suggestions" fields.
        """
        
        return await self.llm_client.call_llm_json(prompt, "response_generation")
    
    async def _execute_actions(self, intent_analysis: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Execute actions based on the analyzed intent."""
        
        intent = intent_analysis.get("intent", "conversation")
        entities = intent_analysis.get("entities", {})
        
        actions_result = {
            "actions_performed": [],
            "data_generated": {},
            "context_updates": {}
        }
        
        try:
            if intent == "generate_metadata":
                result = await self._handle_metadata_generation(entities, context)
                actions_result["actions_performed"].append("metadata_generation")
                actions_result["data_generated"]["metadata"] = result
                
            elif intent == "search_data":
                result = await self._handle_data_search(entities, context)
                actions_result["actions_performed"].append("data_search")
                actions_result["data_generated"]["search_results"] = result
                
            elif intent == "quality_analysis":
                result = await self._handle_quality_analysis(entities, context)
                actions_result["actions_performed"].append("quality_analysis")
                actions_result["data_generated"]["quality_metrics"] = result
                
            elif intent == "schema_analysis":
                result = await self._handle_schema_analysis(entities, context)
                actions_result["actions_performed"].append("schema_analysis")
                actions_result["data_generated"]["schema_changes"] = result
            
            # Update context based on entities
            if "database" in entities:
                context.current_database = entities["database"]
                actions_result["context_updates"]["database"] = entities["database"]
                
            if "table" in entities:
                context.current_table = entities["table"]
                actions_result["context_updates"]["table"] = entities["table"]
                
        except Exception as e:
            self.logger.error(f"Error executing actions: {e}")
            actions_result["error"] = str(e)
        
        return actions_result
    
    async def _handle_metadata_generation(self, entities: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Handle metadata generation requests."""
        database = entities.get("database", context.current_database)
        table = entities.get("table", context.current_table)
        
        if not database or not table:
            return {"error": "Database and table must be specified"}
        
        # Create task for metadata generation
        request = f"Generate metadata for table {table} in database {database}"
        return await self.metadata_agent.handle_natural_language_request(request)
    
    async def _handle_data_search(self, entities: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Handle data search requests."""
        # Implementation for data search
        return {"search_type": "table_search", "query": entities.get("search_term", "")}
    
    async def _handle_quality_analysis(self, entities: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Handle quality analysis requests."""
        # Implementation for quality analysis
        return {"analysis_type": "data_quality", "scope": entities.get("scope", "table")}
    
    async def _handle_schema_analysis(self, entities: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Handle schema analysis requests."""
        # Implementation for schema analysis
        return {"analysis_type": "schema_changes", "timeframe": entities.get("timeframe", "recent")}
    
    async def _generate_error_response(self, error: str, context: ConversationContext) -> str:
        """Generate user-friendly error response."""
        prompt = f"""
        Generate a helpful error response for a metadata management assistant.
        
        Error: {error}
        Context: User was trying to interact with metadata system
        
        Create a friendly, helpful response that:
        1. Acknowledges the issue without technical jargon
        2. Suggests what the user can try instead
        3. Offers to help in a different way
        
        Keep it conversational and supportive.
        """
        
        response = await self.llm_client.call_llm(prompt)
        return response.strip()
    
    def get_conversation_summary(self, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """Get summary of conversation context."""
        context_key = f"{user_id}_{session_id}" if session_id else user_id
        context = self.active_conversations.get(context_key)
        
        if not context:
            return {"error": "No active conversation found"}
        
        return {
            "session_id": context.session_id,
            "current_database": context.current_database,
            "current_table": context.current_table,
            "message_count": len(context.conversation_history),
            "last_activity": context.last_activity.isoformat(),
            "user_preferences": context.user_preferences
        } 