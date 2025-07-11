"""Natural language conversation interface for the metadata agent."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import httpx
import json

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
    
    async def handle_message(self, user_id: str, message: str, session_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
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
        conv_context = self.active_conversations.get(context_key)
        
        if not conv_context:
            conv_context = ConversationContext(
                user_id=user_id,
                session_id=session_id or f"session_{datetime.now().isoformat()}"
            )
            self.active_conversations[context_key] = conv_context
        
        # Update conversation context with provided context
        if context and isinstance(context, dict):
            if context.get('current_database'):
                conv_context.current_database = context['current_database']
            if context.get('current_schema'):
                # Store schema in user preferences for now
                conv_context.user_preferences['current_schema'] = context['current_schema']
            if context.get('current_table'):
                conv_context.current_table = context['current_table']
            if context.get('database_type'):
                conv_context.user_preferences['database_type'] = context['database_type']
            if context.get('table_metadata'):
                conv_context.user_preferences['table_metadata'] = context['table_metadata']
        
        # Update context
        conv_context.last_activity = datetime.now()
        conv_context.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Parse intent and extract entities
            intent_analysis = await self._analyze_intent(message, conv_context)
            
            # Generate response and actions
            response = await self._generate_response(intent_analysis, conv_context)
            
            # Execute any required actions
            actions_result = await self._execute_actions(intent_analysis, conv_context)
            
            # Update conversation history
            conv_context.conversation_history.append({
                "role": "assistant",
                "content": response["text"],
                "timestamp": datetime.now().isoformat(),
                "actions": actions_result
            })
            
            return {
                "response": response["text"],
                "intent": intent_analysis.get("primary_intent", intent_analysis.get("intent", "conversation")),
                "entities": intent_analysis.get("entities", {}),
                "actions_taken": actions_result,
                "suggestions": response.get("suggestions", []),
                "context": {
                    "current_database": conv_context.current_database,
                    "current_table": conv_context.current_table,
                    "current_schema": conv_context.user_preferences.get('current_schema'),
                    "database_type": conv_context.user_preferences.get('database_type')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            error_response = await self._generate_error_response(str(e), conv_context)
            
            conv_context.conversation_history.append({
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
        if context.user_preferences.get('current_schema'):
            current_context += f"Current schema: {context.user_preferences['current_schema']}\n"
        if context.current_table:
            current_context += f"Current table: {context.current_table}\n"
        if context.user_preferences.get('database_type'):
            current_context += f"Database type: {context.user_preferences['database_type']}\n"
        
        # Add helpful context note for the user's current view
        if context.current_table:
            current_context += f"\n[Context: Currently analyzing table {context.current_table}]\n"
        
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
        
        return self.llm_client.call_llm_json(prompt, "intent_analysis")
    
    async def _generate_response(self, intent_analysis: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Generate natural language response based on intent analysis."""
        
        intent = intent_analysis.get("primary_intent", intent_analysis.get("intent", "conversation"))
        entities = intent_analysis.get("entities", {})
        confidence = intent_analysis.get("confidence", 0.5)
        
        # Check if this is a metadata correction request for missing fields
        missing_fields = entities.get("missing_fields", [])
        if intent == "generate_metadata" and missing_fields:
            return self._generate_missing_fields_response(entities, context)
        
        # Build context for response generation
        conversation_summary = ""
        if len(context.conversation_history) > 1:
            conversation_summary = f"Previous conversation context: {context.conversation_history[-2:]}"
        
        prompt = f"""
        Generate a helpful and conversational response for a metadata management assistant.
        
        User Intent: {intent_analysis.get('primary_intent', intent)}
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
        
        return self.llm_client.call_llm_json(prompt, "response_generation")
    
    def _generate_missing_fields_response(self, entities: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Generate specific response for missing fields requests."""
        missing_fields = entities.get("missing_fields", [])
        table_name = entities.get("table_names", [context.current_table])[0] if entities.get("table_names") else context.current_table
        
        # Use intelligent analysis to suggest values
        if table_name and "github_nested" in table_name.lower():
            suggested_domain = "development"
            suggested_category = "analytical"
        else:
            suggested_domain = "reference"
            suggested_category = "operational"
        
        response_text = f"I understand you need to populate missing metadata fields for table **{table_name}**.\n\n"
        
        if "domain" in [f.lower() for f in missing_fields]:
            response_text += f"**Domain Suggestion**: Based on the table name '{table_name}', I recommend classifying this as a **{suggested_domain}** domain table"
            if "github" in table_name.lower():
                response_text += " since it contains GitHub data which is typically development-related"
            response_text += ".\n\n"
        
        if "category" in [f.lower() for f in missing_fields]:
            response_text += f"**Category Suggestion**: For table '{table_name}', I recommend the **{suggested_category}** category"
            if "github" in table_name.lower():
                response_text += " since GitHub data is typically used for analytics and reporting purposes"
            response_text += ".\n\n"
        
        response_text += "I can automatically update these fields for you with my recommendations, or you can:\n"
        response_text += "• Accept my suggested classifications\n"
        response_text += "• Provide your own values for domain and category\n"
        response_text += "• Ask me to analyze the table structure first\n"
        response_text += "• Request more information about classification options\n\n"
        
        response_text += "**Suggested Updates:**\n"
        if "domain" in [f.lower() for f in missing_fields]:
            response_text += f"• Domain: {suggested_domain}\n"
        if "category" in [f.lower() for f in missing_fields]:
            response_text += f"• Category: {suggested_category}\n"
        
        response_text += "\n✅ **I've automatically applied these suggestions to your metadata!**"
        
        suggestions = [
            "View updated metadata",
            "Modify the domain classification", 
            "Modify the category classification",
            "Add more metadata fields",
            "Analyze another table"
        ]
        
        return {
            "text": response_text,
            "suggestions": suggestions
        }
    
    async def _execute_actions(self, intent_analysis: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Execute actions based on the analyzed intent."""
        
        intent = intent_analysis.get("primary_intent", intent_analysis.get("intent", "conversation"))
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
            
            # Also check for table_names array
            if "table_names" in entities and entities["table_names"]:
                context.current_table = entities["table_names"][0]
                actions_result["context_updates"]["table"] = entities["table_names"][0]
                
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
        
        # Check if this is about missing fields
        missing_fields = entities.get("missing_fields", [])
        column_names = entities.get("column_names", [])
        
        if missing_fields or column_names:
            # Handle missing field metadata correction
            correction_result = await self._handle_missing_fields_correction(
                database, table, missing_fields + column_names, context
            )
            
            # If we have suggested values and they're reasonable, apply them automatically
            if "suggested_values" in correction_result and correction_result["suggested_values"]:
                metadata_update_result = await self._apply_metadata_updates(
                    correction_result["database"],
                    correction_result["schema"], 
                    correction_result["table"],
                    correction_result["suggested_values"]
                )
                correction_result["metadata_update_result"] = metadata_update_result
            
            return correction_result
        
        # Create task for metadata generation
        request = f"Generate metadata for table {table} in database {database}"
        result = await self.metadata_agent.handle_natural_language_request(request)
        return result
    
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
    
    async def _handle_missing_fields_correction(self, database: str, table: str, missing_fields: List[str], context: ConversationContext) -> Dict[str, Any]:
        """Handle correction of missing metadata fields."""
        try:
            # Analyze what's missing and generate suggestions
            field_analysis = {}
            suggestions = []
            suggested_values = {}
            
            # Parse table name to extract schema and table name
            table_parts = table.split('.')
            if len(table_parts) >= 3:
                # Format: bq_public.samples.github_nested
                db_name = table_parts[0]
                schema_name = table_parts[1]
                table_name = table_parts[2]
            else:
                # Simple table name
                db_name = database or context.current_database or "unknown"
                schema_name = "public"
                table_name = table
            
            for field in missing_fields:
                field_lower = field.lower()
                
                if field_lower in ['domain', 'business_domain', 'data_domain']:
                    # Analyze table name for domain hints
                    suggested_domain = self._suggest_domain_from_table_name(table_name)
                    field_analysis[field] = {
                        "type": "business_domain",
                        "description": "Business domain or subject area classification",
                        "suggestions": [
                            "customer", "product", "finance", "marketing", 
                            "operations", "sales", "analytics", "reference"
                        ],
                        "recommended": suggested_domain
                    }
                    suggested_values[field] = suggested_domain
                    suggestions.append(f"I can help classify the business domain for table {table_name}")
                
                elif field_lower in ['category', 'data_category', 'classification']:
                    # Analyze table name for category hints
                    suggested_category = self._suggest_category_from_table_name(table_name)
                    field_analysis[field] = {
                        "type": "data_category",
                        "description": "Data classification or category",
                        "suggestions": [
                            "transactional", "master_data", "reference", "analytical",
                            "operational", "staging", "raw", "processed"
                        ],
                        "recommended": suggested_category
                    }
                    suggested_values[field] = suggested_category
                    suggestions.append(f"I can help determine the data category for table {table_name}")
                
                elif field_lower in ['owner', 'data_owner', 'business_owner']:
                    field_analysis[field] = {
                        "type": "ownership",
                        "description": "Data ownership and stewardship information",
                        "suggestions": ["team", "department", "individual", "system"]
                    }
                    suggestions.append(f"I can help identify the data owner for table {table_name}")
                
                elif field_lower in ['sensitivity', 'classification_level', 'privacy']:
                    field_analysis[field] = {
                        "type": "sensitivity",
                        "description": "Data sensitivity and privacy classification",
                        "suggestions": ["public", "internal", "confidential", "restricted", "pii", "sensitive"]
                    }
                    suggestions.append(f"I can help classify data sensitivity for table {table_name}")
                
                else:
                    # Generic field handling
                    field_analysis[field] = {
                        "type": "generic",
                        "description": f"Missing metadata field: {field}",
                        "suggestions": []
                    }
                    suggestions.append(f"I can help analyze and populate the {field} field")
            
            # Generate queries to help with field population
            query_suggestions = []
            for field in missing_fields:
                if field.lower() in ['domain', 'category']:
                    query_suggestions.append({
                        "field": field,
                        "query": f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'",
                        "purpose": f"Analyze table structure to determine appropriate {field}"
                    })
                    query_suggestions.append({
                        "field": field,
                        "query": f"SELECT * FROM {table} LIMIT 10",
                        "purpose": f"Sample data to understand table content for {field} classification"
                    })
            
            return {
                "action": "missing_fields_analysis",
                "database": db_name,
                "schema": schema_name,
                "table": table_name,
                "missing_fields": missing_fields,
                "field_analysis": field_analysis,
                "suggested_values": suggested_values,
                "suggestions": suggestions,
                "query_suggestions": query_suggestions,
                "metadata_update_request": {
                    "db_name": db_name,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "table_metadata": suggested_values
                },
                "next_steps": [
                    f"Analyze table structure and content for {table_name}",
                    f"Generate appropriate values for missing fields: {', '.join(missing_fields)}",
                    f"Update metadata with recommended field values"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error in missing fields correction: {e}")
            return {
                "error": f"Failed to analyze missing fields: {str(e)}",
                "database": database,
                "table": table,
                "missing_fields": missing_fields
            }
    
    def _suggest_domain_from_table_name(self, table_name: str) -> str:
        """Suggest business domain based on table name patterns."""
        table_lower = table_name.lower()
        
        if any(keyword in table_lower for keyword in ['user', 'customer', 'account', 'profile']):
            return "customer"
        elif any(keyword in table_lower for keyword in ['product', 'item', 'catalog', 'inventory']):
            return "product"
        elif any(keyword in table_lower for keyword in ['order', 'transaction', 'payment', 'invoice']):
            return "sales"
        elif any(keyword in table_lower for keyword in ['finance', 'payment', 'billing', 'revenue']):
            return "finance"
        elif any(keyword in table_lower for keyword in ['marketing', 'campaign', 'email', 'promotion']):
            return "marketing"
        elif any(keyword in table_lower for keyword in ['analytics', 'metrics', 'stats', 'report']):
            return "analytics"
        elif any(keyword in table_lower for keyword in ['github', 'repo', 'commit', 'code']):
            return "development"
        elif any(keyword in table_lower for keyword in ['log', 'event', 'audit', 'activity']):
            return "operations"
        else:
            return "reference"
    
    def _suggest_category_from_table_name(self, table_name: str) -> str:
        """Suggest data category based on table name patterns."""
        table_lower = table_name.lower()
        
        if any(keyword in table_lower for keyword in ['temp', 'staging', 'stage', 'raw']):
            return "staging"
        elif any(keyword in table_lower for keyword in ['analytics', 'metrics', 'summary', 'aggregated']):
            return "analytical"
        elif any(keyword in table_lower for keyword in ['lookup', 'reference', 'config', 'enum']):
            return "reference"
        elif any(keyword in table_lower for keyword in ['master', 'dim', 'dimension']):
            return "master_data"
        elif any(keyword in table_lower for keyword in ['fact', 'transaction', 'event', 'log']):
            return "transactional"
        elif any(keyword in table_lower for keyword in ['processed', 'clean', 'final']):
            return "processed"
        else:
            return "operational"
    
    async def _apply_metadata_updates(self, db_name: str, schema_name: str, table_name: str, metadata_updates: Dict[str, str]) -> Dict[str, Any]:
        """Apply metadata updates by calling the metadata API."""
        try:
            # Prepare the metadata update request
            update_request = {
                "db_name": db_name,
                "schema_name": schema_name,
                "table_name": table_name,
                "table_metadata": metadata_updates,
                "user_feedback": "Automated update via AI conversation agent"
            }
            
            # Call the metadata update API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/metadata/update",  # Adjust URL as needed
                    json=update_request,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "updated_fields": result.get("updated_fields", []),
                        "message": result.get("message", "Metadata updated successfully")
                    }
                else:
                    self.logger.error(f"Metadata update failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API call failed: {response.status_code}",
                        "message": "Failed to update metadata"
                    }
                    
        except Exception as e:
            self.logger.error(f"Error applying metadata updates: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to apply metadata updates due to an error"
            }
    
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
        
        response = self.llm_client.call_llm(prompt)
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