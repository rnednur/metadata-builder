"""
Metadata router for generating table metadata and semantic models.
"""

import logging
import asyncio
import uuid
import numpy as np
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from ..models import (
    MetadataGenerationRequest,
    MetadataResponse,
    LookMLGenerationRequest,
    LookMLResponse,
    ProcessingStats,
    BackgroundJobResponse,
    JobStatusRequest,
    OutputFormat,
    MetadataUpdateRequest,
    MetadataUpdateResponse,
    AIMetadataUpdateRequest,
    AIMetadataUpdateResponse
)
from ..dependencies import get_connection_manager, get_job_manager, ConnectionManager, JobManager, get_database_session
from sqlalchemy.orm import Session
from ...core.generate_table_metadata import generate_complete_table_metadata, get_table_info_with_better_sampling
from ...core.semantic_models import generate_lookml_model
from ...utils.storage_utils import (
    get_metadata_storage_path,
    get_metadata_directory_path,
    list_stored_metadata,
    get_fully_qualified_table_name
)
import json
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metadata", tags=["metadata"])


def create_processing_stats(start_time: datetime, end_time: datetime, 
                          total_tokens: int = None, estimated_cost: float = None) -> ProcessingStats:
    """Helper function to create processing stats."""
    duration = (end_time - start_time).total_seconds()
    return ProcessingStats(
        total_duration_seconds=duration,
        start_time=start_time,
        end_time=end_time,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost
    )


async def generate_metadata_task(job_id: str, request: MetadataGenerationRequest, 
                                job_manager: JobManager, conn_manager: ConnectionManager) -> None:
    """Background task for metadata generation."""
    try:
        job_manager.update_job_status(job_id, "running", progress=0.1)
        
        start_time = datetime.now()
        
        # Generate metadata
        metadata = generate_complete_table_metadata(
            db_name=request.db_name,
            table_name=request.table_name,
            schema_name=request.schema_name,
            analysis_sql=request.analysis_sql,
            sample_size=request.sample_size,
            num_samples=request.num_samples,
            connection_manager=conn_manager,
            include_relationships=request.include_relationships,
            include_aggregation_rules=request.include_aggregation_rules,
            include_query_rules=request.include_query_rules,
            include_data_quality=request.include_data_quality,
            include_query_examples=request.include_query_examples,
            include_additional_insights=request.include_additional_insights,
            include_business_rules=request.include_business_rules,
            include_categorical_definitions=request.include_categorical_definitions
        )
        
        end_time = datetime.now()
        
        # Extract processing stats from metadata if available
        processing_stats_data = metadata.get('processing_stats', {})
        total_tokens = processing_stats_data.get('total_tokens')
        estimated_cost = processing_stats_data.get('estimated_cost')
        
        # Create response
        response = MetadataResponse(
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_name=request.table_name,
            metadata=metadata,
            processing_stats=create_processing_stats(start_time, end_time, total_tokens, estimated_cost),
            format=OutputFormat.JSON
        )
        
        # Auto-save the metadata to persistent storage
        try:
            metadata_file = get_metadata_storage_path(request.db_name, request.schema_name, request.table_name)
            storage_data = {
                "db_name": request.db_name,
                "schema_name": request.schema_name,
                "table_name": request.table_name,
                "metadata": metadata,
                "stored_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Ensure directory exists
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(metadata_file, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            logger.info(f"Auto-saved metadata for {request.db_name}.{request.schema_name}.{request.table_name}")
        except Exception as save_error:
            logger.warning(f"Failed to auto-save metadata for job {job_id}: {str(save_error)}")
            # Don't fail the job if storage fails
        
        # Update job with result
        job_manager.update_job_status(job_id, "completed", progress=1.0, result=response.dict())
        
    except Exception as e:
        logger.error(f"Metadata generation failed for job {job_id}: {str(e)}")
        job_manager.update_job_status(job_id, "failed", error=str(e))


async def generate_lookml_task(job_id: str, request: LookMLGenerationRequest,
                              job_manager: JobManager) -> None:
    """Background task for LookML generation."""
    try:
        job_manager.update_job_status(job_id, "running", progress=0.1)
        
        start_time = datetime.now()
        
        # Generate LookML
        lookml_result = generate_lookml_model(
            db_name=request.db_name,
            schema_name=request.schema_name,
            table_names=request.table_names,
            model_name=request.model_name,
            include_derived_tables=request.include_derived_tables,
            include_explores=request.include_explores,
            additional_prompt=request.additional_prompt,
            generation_type=request.generation_type,
            existing_lookml=request.existing_lookml,
            token_threshold=request.token_threshold
        )
        
        end_time = datetime.now()
        
        # Extract processing stats from result if available
        processing_stats_data = lookml_result.get('processing_stats', {})
        total_tokens = processing_stats_data.get('total_tokens')
        estimated_cost = processing_stats_data.get('estimated_cost')
        
        # Create response
        response = LookMLResponse(
            model_name=request.model_name,
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_names=request.table_names,
            lookml_content=lookml_result,
            processing_stats=create_processing_stats(start_time, end_time, total_tokens, estimated_cost)
        )
        
        # Update job with result
        job_manager.update_job_status(job_id, "completed", progress=1.0, result=response.dict())
        
    except Exception as e:
        logger.error(f"LookML generation failed for job {job_id}: {str(e)}")
        job_manager.update_job_status(job_id, "failed", error=str(e))


@router.post("/generate", response_model=MetadataResponse)
async def generate_metadata_sync(
    request: MetadataGenerationRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> MetadataResponse:
    """
    Generate table metadata synchronously.
    
    This endpoint will wait for the metadata generation to complete before returning.
    For long-running operations, consider using the async endpoint.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(request.db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{request.db_name}' not found"
            )
        
        start_time = datetime.now()
        
        # Generate metadata
        metadata = generate_complete_table_metadata(
            db_name=request.db_name,
            table_name=request.table_name,
            schema_name=request.schema_name,
            analysis_sql=request.analysis_sql,
            sample_size=request.sample_size,
            num_samples=request.num_samples,
            connection_manager=conn_manager,
            include_relationships=request.include_relationships,
            include_aggregation_rules=request.include_aggregation_rules,
            include_query_rules=request.include_query_rules,
            include_data_quality=request.include_data_quality,
            include_query_examples=request.include_query_examples,
            include_additional_insights=request.include_additional_insights,
            include_business_rules=request.include_business_rules,
            include_categorical_definitions=request.include_categorical_definitions
        )
        
        end_time = datetime.now()
        
        # Extract processing stats from metadata if available
        processing_stats_data = metadata.get('processing_stats', {})
        total_tokens = processing_stats_data.get('total_tokens')
        estimated_cost = processing_stats_data.get('estimated_cost')
        
        return MetadataResponse(
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_name=request.table_name,
            metadata=metadata,
            processing_stats=create_processing_stats(start_time, end_time, total_tokens, estimated_cost),
            format=OutputFormat.JSON
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/async", response_model=BackgroundJobResponse)
async def generate_metadata_async(
    request: MetadataGenerationRequest,
    background_tasks: BackgroundTasks,
    conn_manager: ConnectionManager = Depends(get_connection_manager),
    job_manager: JobManager = Depends(get_job_manager)
) -> BackgroundJobResponse:
    """
    Generate table metadata asynchronously.
    
    Returns a job ID that can be used to check the status and retrieve results.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(request.db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{request.db_name}' not found"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        job = job_manager.create_job(job_id, "metadata_generation")
        
        # Start background task
        background_tasks.add_task(generate_metadata_task, job_id, request, job_manager, conn_manager)
        
        return BackgroundJobResponse(
            job_id=job_id,
            status="pending",
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start metadata generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lookml/generate", response_model=LookMLResponse)
async def generate_lookml_sync(
    request: LookMLGenerationRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> LookMLResponse:
    """
    Generate LookML semantic model synchronously.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(request.db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{request.db_name}' not found"
            )
        
        start_time = datetime.now()
        
        # Generate LookML
        lookml_result = generate_lookml_model(
            db_name=request.db_name,
            schema_name=request.schema_name,
            table_names=request.table_names,
            model_name=request.model_name,
            include_derived_tables=request.include_derived_tables,
            include_explores=request.include_explores,
            additional_prompt=request.additional_prompt,
            generation_type=request.generation_type,
            existing_lookml=request.existing_lookml,
            token_threshold=request.token_threshold
        )
        
        end_time = datetime.now()
        
        # Extract processing stats from result if available
        processing_stats_data = lookml_result.get('processing_stats', {})
        total_tokens = processing_stats_data.get('total_tokens')
        estimated_cost = processing_stats_data.get('estimated_cost')
        
        return LookMLResponse(
            model_name=request.model_name,
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_names=request.table_names,
            lookml_content=lookml_result,
            processing_stats=create_processing_stats(start_time, end_time, total_tokens, estimated_cost)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LookML generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lookml/generate/async", response_model=BackgroundJobResponse)
async def generate_lookml_async(
    request: LookMLGenerationRequest,
    background_tasks: BackgroundTasks,
    conn_manager: ConnectionManager = Depends(get_connection_manager),
    job_manager: JobManager = Depends(get_job_manager)
) -> BackgroundJobResponse:
    """
    Generate LookML semantic model asynchronously.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(request.db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{request.db_name}' not found"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        job = job_manager.create_job(job_id, "lookml_generation")
        
        # Start background task
        background_tasks.add_task(generate_lookml_task, job_id, request, job_manager)
        
        return BackgroundJobResponse(
            job_id=job_id,
            status="pending",
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start LookML generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=BackgroundJobResponse)
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> BackgroundJobResponse:
    """
    Get the status of a background job.
    """
    try:
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job '{job_id}' not found"
            )
        
        return BackgroundJobResponse(
            job_id=job_id,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            progress=job.progress,
            result=job.result,
            error=job.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for '{job_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-test", response_model=MetadataUpdateResponse)
async def update_metadata_test(
    request: MetadataUpdateRequest
) -> MetadataUpdateResponse:
    """
    Update table metadata manually (test version without authentication).
    """
    try:
        # Use consistent storage path with db.schema.table format
        filepath = get_metadata_storage_path(
            request.db_name, 
            request.schema_name, 
            request.table_name
        )
        
        # Load existing metadata if it exists
        existing_metadata = {}
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    existing_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing metadata: {e}")
        
        updated_fields = []
        
        # Update table-level metadata
        if request.table_metadata:
            if 'table_metadata' not in existing_metadata:
                existing_metadata['table_metadata'] = {}
            
            for field, value in request.table_metadata.items():
                existing_metadata['table_metadata'][field] = value
                updated_fields.append(f"table.{field}")
        
        # Update column-level metadata
        if request.column_metadata:
            if 'column_metadata' not in existing_metadata:
                existing_metadata['column_metadata'] = {}
            
            for column_name, column_updates in request.column_metadata.items():
                if column_name not in existing_metadata['column_metadata']:
                    existing_metadata['column_metadata'][column_name] = {}
                
                for field, value in column_updates.items():
                    existing_metadata['column_metadata'][column_name][field] = value
                    updated_fields.append(f"column.{column_name}.{field}")
        
        # Add metadata about the update
        existing_metadata['last_updated'] = datetime.now().isoformat()
        existing_metadata['update_reason'] = request.user_feedback or 'Manual update'
        
        # Save updated metadata
        try:
            with open(filepath, 'w') as f:
                json.dump(existing_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save metadata: {e}")
        
        qualified_table_name = get_fully_qualified_table_name(
            request.db_name, request.schema_name, request.table_name
        )
        logger.info(f"Updated metadata for {qualified_table_name}")
        
        return MetadataUpdateResponse(
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_name=request.table_name,
            updated_fields=updated_fields,
            success=True,
            message=f"Successfully updated {len(updated_fields)} metadata fields"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=MetadataUpdateResponse)
async def update_metadata(
    request: MetadataUpdateRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> MetadataUpdateResponse:
    """
    Update table metadata manually.
    
    Allows direct updates to table and column metadata without AI generation.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(request.db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{request.db_name}' not found"
            )
        
        # Use consistent storage path with db.schema.table format
        filepath = get_metadata_storage_path(
            request.db_name, 
            request.schema_name, 
            request.table_name
        )
        
        # Load existing metadata if it exists
        existing_metadata = {}
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    existing_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing metadata: {e}")
        
        updated_fields = []
        
        # Update table-level metadata
        if request.table_metadata:
            if 'table_metadata' not in existing_metadata:
                existing_metadata['table_metadata'] = {}
            
            for field, value in request.table_metadata.items():
                existing_metadata['table_metadata'][field] = value
                updated_fields.append(f"table.{field}")
        
        # Update column-level metadata
        if request.column_metadata:
            if 'column_metadata' not in existing_metadata:
                existing_metadata['column_metadata'] = {}
            
            for column_name, column_updates in request.column_metadata.items():
                if column_name not in existing_metadata['column_metadata']:
                    existing_metadata['column_metadata'][column_name] = {}
                
                for field, value in column_updates.items():
                    existing_metadata['column_metadata'][column_name][field] = value
                    updated_fields.append(f"column.{column_name}.{field}")
        
        # Add metadata about the update
        existing_metadata['last_updated'] = datetime.now().isoformat()
        existing_metadata['update_reason'] = request.user_feedback or 'Manual update'
        
        # Save updated metadata
        try:
            with open(filepath, 'w') as f:
                json.dump(existing_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save metadata: {e}")
        
        qualified_table_name = get_fully_qualified_table_name(
            request.db_name, request.schema_name, request.table_name
        )
        logger.info(f"Updated metadata for {qualified_table_name}")
        
        return MetadataUpdateResponse(
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_name=request.table_name,
            updated_fields=updated_fields,
            success=True,
            message=f"Successfully updated {len(updated_fields)} metadata fields"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/ai", response_model=AIMetadataUpdateResponse)
async def update_metadata_with_ai(
    request: AIMetadataUpdateRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> AIMetadataUpdateResponse:
    """
    Update table metadata using AI-powered analysis of user feedback.
    
    Uses LLM to interpret user feedback and suggest appropriate metadata updates.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(request.db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{request.db_name}' not found"
            )
        
        # Use LLM to analyze user feedback and suggest updates
        from ...core.llm_service import get_llm_service
        llm_service = get_llm_service()
        
        # Build prompt for metadata update
        prompt = f"""
        You are a metadata analyst. A user has provided feedback about table metadata that needs to be updated.
        
        Current metadata:
        {request.current_metadata}
        
        User feedback:
        {request.user_feedback}
        
        Update scope: {request.update_scope}
        {f"Target column: {request.target_column}" if request.target_column else ""}
        
        Please analyze the feedback and suggest appropriate metadata updates. Return a JSON response with:
        {{
            "suggested_updates": {{
                // Updated metadata fields and values
            }},
            "explanation": "Clear explanation of what was changed and why",
            "confidence_score": 0.95, // 0-1 confidence score
            "reasoning": "Detailed reasoning for the changes"
        }}
        
        Focus on:
        - Correcting factual errors
        - Improving descriptions and business context
        - Updating categorizations and classifications
        - Ensuring consistency with user feedback
        
        Be conservative - only suggest changes that are clearly supported by the feedback.
        """
        
        # Get LLM response
        response = llm_service.generate_response(prompt, max_tokens=1500)
        
        # Parse JSON response
        import json
        try:
            ai_response = json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            ai_response = {
                "suggested_updates": {},
                "explanation": "Unable to parse AI response properly",
                "confidence_score": 0.1,
                "reasoning": "JSON parsing failed"
            }
        
        return AIMetadataUpdateResponse(
            database_name=request.db_name,
            schema_name=request.schema_name,
            table_name=request.table_name,
            suggested_updates=ai_response.get("suggested_updates", {}),
            explanation=ai_response.get("explanation", ""),
            confidence_score=ai_response.get("confidence_score", 0.5),
            reasoning=ai_response.get("reasoning", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI metadata update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stored-test/{db_name}/{schema_name}/{table_name}")
async def get_stored_metadata_test(
    db_name: str,
    schema_name: str,
    table_name: str
):
    """
    Get stored metadata for a specific table (test version without authentication).
    """
    try:
        # Use consistent storage path with db.schema.table format
        filepath = get_metadata_storage_path(db_name, schema_name, table_name)
        
        # Check if metadata file exists
        if not filepath.exists():
            qualified_table_name = get_fully_qualified_table_name(db_name, schema_name, table_name)
            raise HTTPException(
                status_code=404,
                detail=f"No saved metadata found for table '{qualified_table_name}'"
            )
        
        # Load metadata from file
        try:
            with open(filepath, 'r') as f:
                stored_metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load stored metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load stored metadata: {e}")
        
        # Handle different storage formats
        if "metadata" in stored_metadata:
            # New format: metadata is nested under "metadata" key
            # Check if there's another level of nesting
            if isinstance(stored_metadata["metadata"], dict) and "metadata" in stored_metadata["metadata"]:
                metadata_content = stored_metadata["metadata"]["metadata"]  # Double-nested
            else:
                metadata_content = stored_metadata["metadata"]  # Single-nested
            
            # Extract table-level metadata
            table_metadata = {
                "description": metadata_content.get("description", ""),
                "purpose": metadata_content.get("table_description", {}).get("purpose", ""),
                "business_use_cases": metadata_content.get("table_description", {}).get("business_use_cases", []),
                "domain": metadata_content.get("table_insights", {}).get("domain", ""),
                "category": metadata_content.get("table_insights", {}).get("category", "")
            }
            
            # Extract column-level metadata
            column_metadata = {}
            columns = metadata_content.get("columns", {})
            for col_name, col_info in columns.items():
                column_metadata[col_name] = {
                    "description": col_info.get("description", col_info.get("definition", "")),
                    "business_name": col_info.get("business_name", ""),
                    "purpose": col_info.get("purpose", ""),
                    "format": col_info.get("format", ""),
                    "data_type": col_info.get("data_type", ""),
                    "constraints": col_info.get("constraints", []),
                    "statistics": col_info.get("statistics", {}),
                    "is_categorical": col_info.get("is_categorical", False),
                    "is_numerical": col_info.get("is_numerical", False)
                }
            
            last_updated = stored_metadata.get("stored_at")
            update_reason = "Generated metadata"
        else:
            # Legacy format: direct table_metadata and column_metadata fields
            table_metadata = stored_metadata.get("table_metadata", {})
            column_metadata = stored_metadata.get("column_metadata", {})
            last_updated = stored_metadata.get("last_updated")
            update_reason = stored_metadata.get("update_reason")
        
        # Build response
        response = {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "table_metadata": table_metadata,
            "column_metadata": column_metadata,
            "last_updated": last_updated,
            "update_reason": update_reason,
            "metadata": stored_metadata.get("metadata")  # Include full metadata for frontend
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve stored metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stored/{db_name}/{schema_name}/{table_name}")
async def get_stored_metadata(
    db_name: str,
    schema_name: str,
    table_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    Get stored metadata for a specific table.
    
    Returns previously saved metadata from the database.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{db_name}' not found"
            )
        
        # Use consistent storage path with db.schema.table format
        filepath = get_metadata_storage_path(db_name, schema_name, table_name)
        
        # Check if metadata file exists
        if not filepath.exists():
            qualified_table_name = get_fully_qualified_table_name(db_name, schema_name, table_name)
            raise HTTPException(
                status_code=404,
                detail=f"No saved metadata found for table '{qualified_table_name}'"
            )
        
        # Load metadata from file
        try:
            with open(filepath, 'r') as f:
                stored_metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load stored metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load stored metadata: {e}")
        
        # Handle different storage formats
        if "metadata" in stored_metadata:
            # New format: metadata is nested under "metadata" key
            # Check if there's another level of nesting
            if isinstance(stored_metadata["metadata"], dict) and "metadata" in stored_metadata["metadata"]:
                metadata_content = stored_metadata["metadata"]["metadata"]  # Double-nested
            else:
                metadata_content = stored_metadata["metadata"]  # Single-nested
            
            # Extract table-level metadata
            table_metadata = {
                "description": metadata_content.get("description", ""),
                "purpose": metadata_content.get("table_description", {}).get("purpose", ""),
                "business_use_cases": metadata_content.get("table_description", {}).get("business_use_cases", []),
                "domain": metadata_content.get("table_insights", {}).get("domain", ""),
                "category": metadata_content.get("table_insights", {}).get("category", "")
            }
            
            # Extract column-level metadata
            column_metadata = {}
            columns = metadata_content.get("columns", {})
            for col_name, col_info in columns.items():
                column_metadata[col_name] = {
                    "description": col_info.get("description", col_info.get("definition", "")),
                    "business_name": col_info.get("business_name", ""),
                    "purpose": col_info.get("purpose", ""),
                    "format": col_info.get("format", ""),
                    "data_type": col_info.get("data_type", ""),
                    "constraints": col_info.get("constraints", []),
                    "statistics": col_info.get("statistics", {}),
                    "is_categorical": col_info.get("is_categorical", False),
                    "is_numerical": col_info.get("is_numerical", False)
                }
            
            last_updated = stored_metadata.get("stored_at")
            update_reason = "Generated metadata"
        else:
            # Legacy format: direct table_metadata and column_metadata fields
            table_metadata = stored_metadata.get("table_metadata", {})
            column_metadata = stored_metadata.get("column_metadata", {})
            last_updated = stored_metadata.get("last_updated")
            update_reason = stored_metadata.get("update_reason")
        
        # Build response
        response = {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "table_metadata": table_metadata,
            "column_metadata": column_metadata,
            "last_updated": last_updated,
            "update_reason": update_reason,
            "metadata": stored_metadata.get("metadata")  # Include full metadata for frontend
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve stored metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample-data/{db_name}/{schema_name}/{table_name}")
async def get_sample_data(
    db_name: str,
    schema_name: str,
    table_name: str,
    sample_size: int = 100,
    num_samples: int = 2,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    Get sample data for a specific table independently of metadata generation.
    
    This endpoint allows fetching sample data without needing to generate full metadata.
    """
    try:
        # Validate connection exists
        if not conn_manager.connection_exists(db_name):
            raise HTTPException(
                status_code=404,
                detail=f"Database connection '{db_name}' not found"
            )
        
        # Get table schema and sample data
        start_time = datetime.now()
        
        try:
            schema, sample_data = get_table_info_with_better_sampling(
                table_name=table_name,
                db_name=db_name,
                schema_name=schema_name,
                sample_size=sample_size,
                num_samples=num_samples,
                connection_manager=conn_manager
            )
        except Exception as e:
            logger.error(f"Failed to fetch sample data: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch sample data: {str(e)}"
            )
        
        end_time = datetime.now()
        
        # Convert sample data to dictionary format and sanitize for JSON
        if not sample_data.empty:
            # Replace problematic values before conversion
            sample_data = sample_data.replace([np.inf, -np.inf], None)  # Replace infinity with None
            sample_data = sample_data.where(sample_data.notna(), None)  # Replace NaN with None
            sample_data_dict = sample_data.to_dict('records')
            
            # Additional sanitization for any remaining non-JSON-compliant values
            def sanitize_value(value):
                if isinstance(value, (float, int)) and (value != value or value == float('inf') or value == float('-inf')):
                    return None
                elif isinstance(value, datetime):
                    return value.isoformat()
                return value
            
            sample_data_dict = [
                {k: sanitize_value(v) for k, v in record.items()}
                for record in sample_data_dict
            ]
        else:
            sample_data_dict = []
        
        # Build response
        response = {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "sample_data": sample_data_dict,
            "column_count": len(schema),
            "sample_row_count": len(sample_data_dict),
            "processing_time_seconds": (end_time - start_time).total_seconds(),
            "schema": schema,
            "fetched_at": end_time.isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample-data-test/{db_name}/{schema_name}/{table_name}")
async def get_sample_data_test(
    db_name: str,
    schema_name: str,
    table_name: str,
    sample_size: int = 100,
    num_samples: int = 2
):
    """
    Get sample data for a specific table (test version without authentication).
    
    This endpoint allows testing sample data fetching without authentication.
    """
    try:
        # For testing, create mock sample data
        mock_sample_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": 2, 
                "name": "Jane Smith",
                "email": "jane@example.com",
                "status": "inactive",
                "created_at": "2024-01-16T14:20:00Z"
            }
        ]
        
        mock_schema = {
            "id": "integer",
            "name": "varchar(255)",
            "email": "varchar(255)",
            "status": "varchar(50)",
            "created_at": "timestamp"
        }
        
        # Build response
        response = {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "sample_data": mock_sample_data,
            "column_count": len(mock_schema),
            "sample_row_count": len(mock_sample_data),
            "processing_time_seconds": 0.1,
            "schema": mock_schema,
            "fetched_at": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to fetch test sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{db_name}")
async def list_tables_with_metadata(db_name: str):
    """
    List all tables that have stored metadata for a given database.
    """
    try:
        # Use storage utility to list metadata files
        metadata_files = list_stored_metadata(db_name)
        
        tables_with_metadata = []
        for metadata_info in metadata_files:
            modified_at = datetime.fromtimestamp(metadata_info["modified_timestamp"]).isoformat()
            tables_with_metadata.append({
                "database_name": metadata_info["database_name"],
                "schema_name": metadata_info["schema_name"],
                "table_name": metadata_info["table_name"],
                "modified_at": modified_at,
                "qualified_name": get_fully_qualified_table_name(
                    metadata_info["database_name"],
                    metadata_info["schema_name"],
                    metadata_info["table_name"]
                )
            })
        
        return {
            "status": "success",
            "database": db_name,
            "tables": tables_with_metadata,
            "count": len(tables_with_metadata)
        }
        
    except Exception as e:
        logger.error(f"Failed to list tables with metadata for {db_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tables with metadata: {str(e)}"
        )


@router.post("/store")
async def store_metadata(request: dict):
    """
    Store generated metadata for a table.
    """
    try:
        db_name = request.get("db_name")
        schema_name = request.get("schema_name") 
        table_name = request.get("table_name")
        metadata = request.get("metadata")
        
        if not all([db_name, schema_name, table_name, metadata]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: db_name, schema_name, table_name, metadata"
            )
        
        # Create storage directory structure
        metadata_dir = Path("metadata_storage")
        storage_path = metadata_dir / db_name / schema_name
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Store metadata with timestamp
        metadata_file = storage_path / f"{table_name}.json"
        storage_data = {
            "db_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "metadata": metadata,
            "stored_at": request.get("created_at", datetime.now().isoformat()),
            "version": "1.0"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(storage_data, f, indent=2, default=str)
        
        logger.info(f"Stored metadata for {db_name}.{schema_name}.{table_name}")
        
        return {
            "status": "success",
            "message": f"Metadata stored for {db_name}.{schema_name}.{table_name}",
            "file_path": str(metadata_file)
        }
        
    except Exception as e:
        logger.error(f"Failed to store metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store metadata: {str(e)}"
        )


@router.delete("/stored/{db_name}/{schema_name}/{table_name}")
async def delete_stored_metadata(db_name: str, schema_name: str, table_name: str):
    """
    Delete stored metadata for a table.
    """
    try:
        # Use consistent storage path with db.schema.table format
        metadata_file = get_metadata_storage_path(db_name, schema_name, table_name)
        qualified_table_name = get_fully_qualified_table_name(db_name, schema_name, table_name)
        
        if metadata_file.exists():
            metadata_file.unlink()
            logger.info(f"Deleted stored metadata for {qualified_table_name}")
            return {
                "status": "success",
                "message": f"Metadata deleted for {qualified_table_name}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Stored metadata not found for {qualified_table_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete stored metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete stored metadata: {str(e)}"
        )


 