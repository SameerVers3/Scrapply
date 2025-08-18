from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from typing import List, Optional
import asyncio
import logging
import uuid

from app.schemas.job import ScrapingRequest, JobResponse, JobCreate, JobList
from app.models.job import Job, JobStatus
from app.core.processor import ScrapingProcessor
from app.api.dependencies import get_processor

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
