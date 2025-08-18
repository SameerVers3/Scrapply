from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job by ID"""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse.from_orm(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")


@router.get("/{job_id}/result")
async def get_job_result(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job result"""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status == "pending":
            return {"status": "pending", "message": "Job is still processing"}
        elif job.status == "failed":
            return {"status": "failed", "error": job.error_message}
        elif job.status == "completed":
            return {
                "status": "completed",
                "result": job.result,
                "generated_code": job.generated_code,
                "endpoint_path": f"/generated/{job_id}"
            }
        
        return {"status": job.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job result: {str(e)}")


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0, 
    limit: int = 100, 
    user_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List jobs with pagination"""
    try:
        query = select(Job)
        if user_id:
            query = query.where(Job.user_id == user_id)
        
        query = query.offset(skip).limit(limit).order_by(Job.created_at.desc())
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return [JobResponse.from_orm(job) for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a job"""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        await db.delete(job)
        await db.commit()
        
        return {"message": "Job deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
