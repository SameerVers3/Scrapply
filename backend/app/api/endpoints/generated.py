from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import uuid
import logging
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.scraper import Scraper
from app.models.endpoint import Endpoint
from app.schemas.job import APIResponse
from app.core.sandbox import SecureSandbox

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{job_id}")
async def execute_generated_api(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute the generated API endpoint for a job
    
    This endpoint runs the scraper code associated with a job and returns the scraped data.
    The endpoint is only available for jobs with 'ready' status.
    """
    try:
        # Validate UUID format
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Get job details
        result = await db.execute(
            select(Job)
            .where(Job.id == job_uuid)
            .where(Job.status == JobStatus.READY)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=404, 
                detail="Job not found or not ready. The API endpoint may still be processing."
            )
        
        # Get active scraper for this job
        scraper_result = await db.execute(
            select(Scraper)
            .where(Scraper.job_id == job_uuid)
            .where(Scraper.is_active == True)
            .order_by(Scraper.code_version.desc())
        )
        scraper = scraper_result.scalar_one_or_none()
        
        if not scraper:
            raise HTTPException(
                status_code=500,
                detail="No active scraper found for this job"
            )
        
        # Get endpoint record
        endpoint_result = await db.execute(
            select(Endpoint)
            .where(Endpoint.job_id == job_uuid)
            .where(Endpoint.is_active == True)
        )
        endpoint = endpoint_result.scalar_one_or_none()
        
        if not endpoint:
            raise HTTPException(
                status_code=500,
                detail="No active endpoint found for this job"
            )
        
        # Execute scraper
        sandbox = SecureSandbox()
        start_time = time.time()
        
        logger.info(f"Executing scraper for job {job_id}")
        result = await sandbox.execute_scraper(scraper.scraper_code, job.url)
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if not result.get('success'):
            logger.error(f"Scraper execution failed for job {job_id}: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Scraper execution failed: {result.get('error', 'Unknown error')}"
            )
        
        # Update endpoint statistics
        await db.execute(
            update(Endpoint)
            .where(Endpoint.id == endpoint.id)
            .values(
                access_count=Endpoint.access_count + 1,
                last_accessed_at=datetime.utcnow(),
                average_response_time=execution_time_ms
            )
        )
        
        # Update scraper statistics
        await db.execute(
            update(Scraper)
            .where(Scraper.id == scraper.id)
            .values(
                execution_count=Scraper.execution_count + 1,
                last_execution_at=datetime.utcnow(),
                average_execution_time=execution_time_ms
            )
        )
        
        await db.commit()
        
        # Prepare response
        api_response = APIResponse(
            source_url=job.url,
            data=result.get('data', []),
            metadata=result.get('metadata', {}),
            job_id=job_id,
            execution_time_ms=execution_time_ms
        )
        
        logger.info(f"Successfully executed scraper for job {job_id}, returned {len(api_response.data)} items")
        
        return api_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing API for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{job_id}/info")
async def get_api_info(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about the generated API endpoint
    
    Returns metadata about the API including the original job details,
    scraper information, and usage statistics.
    """
    try:
        # Validate UUID format
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Get job details with related data
        result = await db.execute(
            select(Job)
            .where(Job.id == job_uuid)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get scraper info
        scraper_result = await db.execute(
            select(Scraper)
            .where(Scraper.job_id == job_uuid)
            .where(Scraper.is_active == True)
            .order_by(Scraper.code_version.desc())
        )
        scraper = scraper_result.scalar_one_or_none()
        
        # Get endpoint info
        endpoint_result = await db.execute(
            select(Endpoint)
            .where(Endpoint.job_id == job_uuid)
            .where(Endpoint.is_active == True)
        )
        endpoint = endpoint_result.scalar_one_or_none()
        
        # Prepare response
        info = {
            "job": {
                "id": str(job.id),
                "url": job.url,
                "description": job.description,
                "status": job.status,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "sample_data": job.sample_data[:2] if job.sample_data else None  # First 2 items
            },
            "api": {
                "endpoint_path": job.api_endpoint_path,
                "is_active": endpoint.is_active if endpoint else False,
                "created_at": endpoint.created_at if endpoint else None
            },
            "scraper": {
                "version": scraper.code_version if scraper else None,
                "execution_count": scraper.execution_count if scraper else 0,
                "last_execution_at": scraper.last_execution_at if scraper else None,
                "average_execution_time_ms": scraper.average_execution_time if scraper else None
            },
            "usage_stats": {
                "access_count": endpoint.access_count if endpoint else 0,
                "last_accessed_at": endpoint.last_accessed_at if endpoint else None,
                "success_rate": endpoint.success_rate if endpoint else None
            } if endpoint else None
        }
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API info for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{job_id}/test")
async def test_api_endpoint(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Test the generated API endpoint
    
    Executes the scraper and returns a limited result set for testing purposes.
    This is useful for verifying that the API is working correctly.
    """
    try:
        # This is essentially the same as the main endpoint but with limited results
        response = await execute_generated_api(job_id, db)
        
        # Limit the data for testing (first 3 items max)
        if hasattr(response, 'data') and isinstance(response.data, list):
            response.data = response.data[:3]
        
        return {
            "test_result": "success",
            "sample_data": response.data,
            "execution_time_ms": response.execution_time_ms,
            "total_items_available": len(response.data)
        }
        
    except HTTPException as e:
        return {
            "test_result": "failed",
            "error": str(e.detail),
            "status_code": e.status_code
        }
    except Exception as e:
        logger.error(f"Test failed for job {job_id}: {e}")
        return {
            "test_result": "failed",
            "error": "Internal server error",
            "status_code": 500
        }
