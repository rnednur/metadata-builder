"""API routes for AI agent functionality."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ...agent.core import MetadataAgent
from ...agent.conversation import ConversationAgent
from ..dependencies import get_metadata_agent, get_conversation_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    user_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str
    intent: str
    entities: Dict[str, Any]
    actions_taken: Dict[str, Any]
    suggestions: list[str]
    context: Dict[str, Any]
    error: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""
    state: str
    active_tasks: int
    completed_tasks: int
    queue_size: int
    uptime: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    conversation_agent: ConversationAgent = Depends(get_conversation_agent)
):
    """
    Send a natural language message to the AI agent.
    
    The agent can understand and respond to various metadata-related requests:
    - Generate metadata for tables
    - Search for data assets
    - Analyze data quality
    - Explain business context
    - Export metadata
    """
    try:
        response = await conversation_agent.handle_message(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(
            response=response.get("response", ""),
            intent=response.get("intent", "unknown"),
            entities=response.get("entities", {}),
            actions_taken=response.get("actions_taken", {}),
            suggestions=response.get("suggestions", []),
            context=response.get("context", {}),
            error=response.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent: MetadataAgent = Depends(get_metadata_agent)
):
    """
    Get the current status of the AI agent.
    
    Returns information about:
    - Current operational state
    - Number of active and completed tasks
    - Queue size
    - Uptime
    """
    try:
        # Calculate uptime (you'd need to track start time in the agent)
        uptime = "0h 0m"  # Placeholder
        
        return AgentStatusResponse(
            state=agent.state.value,
            active_tasks=len(agent.active_tasks),
            completed_tasks=len(agent.completed_tasks),
            queue_size=len(agent.task_queue),
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{user_id}/summary")
async def get_conversation_summary(
    user_id: str,
    session_id: Optional[str] = None,
    conversation_agent: ConversationAgent = Depends(get_conversation_agent)
):
    """
    Get a summary of the current conversation context.
    
    Returns:
    - Current database and table context
    - Conversation statistics
    - User preferences
    """
    try:
        summary = conversation_agent.get_conversation_summary(
            user_id=user_id,
            session_id=session_id
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{user_id}")
async def clear_conversation(
    user_id: str,
    session_id: Optional[str] = None,
    conversation_agent: ConversationAgent = Depends(get_conversation_agent)
):
    """
    Clear conversation history for a user.
    """
    try:
        context_key = f"{user_id}_{session_id}" if session_id else user_id
        
        if context_key in conversation_agent.active_conversations:
            del conversation_agent.active_conversations[context_key]
            return {"message": "Conversation cleared successfully"}
        else:
            return {"message": "No active conversation found"}
            
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/natural-language")
async def create_task_from_natural_language(
    request: dict,
    agent: MetadataAgent = Depends(get_metadata_agent)
):
    """
    Create tasks from natural language descriptions.
    
    This endpoint allows direct task creation without conversation context.
    Useful for API integrations and automated workflows.
    """
    try:
        natural_request = request.get("request", "")
        
        if not natural_request:
            raise HTTPException(status_code=400, detail="Request text is required")
        
        result = await agent.handle_natural_language_request(natural_request)
        
        return {
            "task_creation_result": result,
            "message": "Tasks created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating tasks from natural language: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_task_queue(
    agent: MetadataAgent = Depends(get_metadata_agent)
):
    """
    Get the current task queue status.
    
    Returns information about:
    - Queued tasks
    - Active tasks
    - Recently completed tasks
    """
    try:
        return {
            "queued_tasks": [
                {
                    "id": task.id,
                    "type": task.type,
                    "priority": task.priority,
                    "database": task.database,
                    "table": task.table,
                    "scheduled_time": task.scheduled_time.isoformat(),
                    "dependencies": task.dependencies
                }
                for task in agent.task_queue
            ],
            "active_tasks": [
                {
                    "id": task.id,
                    "type": task.type,
                    "database": task.database,
                    "table": task.table
                }
                for task in agent.active_tasks.values()
            ],
            "completed_tasks_count": len(agent.completed_tasks),
            "total_queue_size": len(agent.task_queue)
        }
        
    except Exception as e:
        logger.error(f"Error getting task queue: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 