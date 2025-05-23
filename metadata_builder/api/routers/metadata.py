"""
Metadata router for generating table metadata and semantic models.
"""

import logging
import asyncio
import uuid
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
    OutputFormat
)
from ..dependencies import get_connection_manager, get_job_manager, ConnectionManager, JobManager
from ...core.generate_table_metadata import generate_complete_table_metadata
from ...core.semantic_models import generate_lookml_model

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
                                job_manager: JobManager) -> None:
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
        background_tasks.add_task(generate_metadata_task, job_id, request, job_manager)
        
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