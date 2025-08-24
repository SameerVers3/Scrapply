from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import asyncio
import logging
import uuid
import json

from app.schemas.job import ScrapingRequest, JobResponse, JobCreate, JobList
from app.models.job import Job, JobStatus
from app.core.processor import ScrapingProcessor
from app.api.dependencies import get_processor
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/requests", response_model=JobResponse, status_code=201)
async def create_scraping_request(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """
    Create a new scraping job
    
    This endpoint creates a new scraping job and starts processing it in the background.
    The job will analyze the website, generate scraper code, test it, and create an API endpoint.
    """
    try:
        logger.info(f"Creating scraping request for URL: {request.url}")
        
        # Create job
        job_create = JobCreate(
            url=request.url,
            description=request.description,
            user_id=request.user_id
        )
        job_id = await processor.create_job(job_create)
        
        # Start processing in background
        background_tasks.add_task(processor.process_job, job_id)
        
        # Return initial job status
        job = await processor.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=500, detail="Failed to retrieve created job")
        
        logger.info(f"Created job {job_id} and started background processing")
        return JobResponse.from_orm(job)
        
    except Exception as e:
        logger.error(f"Failed to create scraping request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """
    Get job status and details
    
    Returns the current status of a scraping job including progress, 
    generated API endpoint (if ready), and any error information.
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        job = await processor.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs", response_model=JobList)
async def list_jobs(
    limit: int = Query(10, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    processor: ScrapingProcessor = Depends(get_processor)
):
    """
    List recent jobs
    
    Returns a paginated list of recent scraping jobs with optional status filtering.
    """
    try:
        jobs = await processor.list_jobs(limit=limit, offset=offset)
        
        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        job_responses = [JobResponse.from_orm(job) for job in jobs]
        
        return JobList(
            jobs=job_responses,
            total=len(job_responses),
            page=offset // limit + 1,
            size=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """
    Retry a failed job
    
    Restarts processing for a failed job. Only jobs with 'failed' status can be retried.
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        job = await processor.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.FAILED:
            raise HTTPException(
                status_code=400, 
                detail=f"Only failed jobs can be retried. Current status: {job.status}"
            )
        
        # Reset job status and restart processing
        await processor._update_job_status(
            job_id, JobStatus.PENDING, 0,
            "Job retry initiated",
            error_info=None,
            session=processor.db
        )
        
        # Start processing in background
        background_tasks.add_task(processor.process_job, job_id)
        
        # Return updated job status
        updated_job = await processor.get_job_status(job_id)
        logger.info(f"Retrying job {job_id}")
        
        return JobResponse.from_orm(updated_job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """
    Delete a job and its associated data
    
    Permanently deletes a job, its scraper code, and API endpoint.
    Active endpoints will be deactivated.
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        job = await processor.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # TODO: Implement job deletion logic
        # This would involve deleting from jobs, scrapers, and endpoints tables
        
        return {"message": f"Job {job_id} deletion initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs/stream/{job_id}")
async def stream_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Stream real-time job status updates using Server-Sent Events"""
    
    logger.info(f"Starting SSE stream for job {job_id}")
    
    async def event_stream():
        try:
            # Get job data
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                return
            
            # Send initial data
            update_data = {
                'id': str(job.id),  # Convert UUID to string
                'status': job.status,
                'progress': job.progress,
                'message': job.message,
                'api_endpoint_path': job.api_endpoint_path,
                'updated_at': job.updated_at.isoformat() if job.updated_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            }
            yield f"data: {json.dumps(update_data)}\n\n"
            
            # If job is already completed, close stream
            if job.status in ['ready', 'failed']:
                yield f"data: {json.dumps({'message': 'Job completed', 'status': job.status})}\n\n"
                return
            
            # For ongoing jobs, we could continue streaming, but for now just close
            yield f"data: {json.dumps({'message': 'Stream ended'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in SSE stream for job {job_id}: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/jobs/test/{job_id}")
async def test_job_retrieval(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Test endpoint to verify job retrieval"""
    try:
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {"error": "Job not found", "job_id": job_id}
        
        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "api_endpoint_path": job.api_endpoint_path,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {e}")
        return {"error": str(e), "job_id": job_id}

@router.get("/jobs/stream-test/{job_id}")
async def stream_test(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Simple SSE test endpoint"""
    
    async def event_stream():
        try:
            # Send a simple test message
            yield f"data: {json.dumps({'message': 'SSE test', 'job_id': job_id})}\n\n"
            
            # Get job data
            result = await db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                yield f"data: {json.dumps({'status': job.status, 'progress': job.progress})}\n\n"
            else:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            
            # Close stream
            yield f"data: {json.dumps({'message': 'Stream complete'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/jobs/simple-test/{job_id}")
async def simple_test(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Simple test endpoint without streaming"""
    try:
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {"error": "Job not found", "job_id": job_id}
        
        return {
            "message": "Simple test successful",
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress
        }
    except Exception as e:
        return {"error": str(e), "job_id": job_id}

@router.get("/jobs/stream-simple/{job_id}")
async def stream_simple(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Simple text response for testing"""
    try:
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return f"data: {json.dumps({'error': 'Job not found'})}\n\n"
        
        update_data = {
            'id': str(job.id),  # Convert UUID to string
            'status': job.status,
            'progress': job.progress,
            'message': job.message,
            'api_endpoint_path': job.api_endpoint_path,
            'updated_at': job.updated_at.isoformat() if job.updated_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        }
        
        return f"data: {json.dumps(update_data)}\n\n"
        
    except Exception as e:
        return f"data: {json.dumps({'error': str(e)})}\n\n"
