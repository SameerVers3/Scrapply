import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobStatus
from app.models.scraper import Scraper
from app.models.endpoint import Endpoint
from app.schemas.job import JobCreate, JobUpdate
from app.core.agent import UnifiedAgent
from app.core.sandbox import SecureSandbox
from app.database import AsyncSessionLocal
from config.settings import settings

logger = logging.getLogger(__name__)

class ScrapingProcessor:
    """
    Main processor that coordinates the entire scraping workflow
    """
    
    def __init__(self, db_session: AsyncSession = None):
        self.db = db_session
        self.agent = None
        self.sandbox = SecureSandbox()
    
    async def _get_db_session(self) -> AsyncSession:
        """Get a database session - either the injected one or create a new one"""
        if self.db is not None:
            return self.db
        else:
            # For background tasks, create a new session
            return AsyncSessionLocal()
    
    async def _ensure_db_session(self, session: AsyncSession = None) -> AsyncSession:
        """Ensure we have a valid database session"""
        if session is not None:
            return session
        return await self._get_db_session()
    
    async def create_job(self, job_request: JobCreate) -> str:
        """Create a new scraping job"""
        try:
            session = self.db if self.db else await self._ensure_db_session()
            
            # Create job record
            job = Job(
                url=str(job_request.url),
                description=job_request.description,
                user_id=job_request.user_id,
                status=JobStatus.PENDING,
                progress=0,
                message="Job created, waiting to start processing"
            )
            
            session.add(job)
            await session.commit()
            await session.refresh(job)
            
            logger.info(f"Created job {job.id} for URL: {job.url}")
            return str(job.id)
            
        except Exception as e:
            if session:
                await session.rollback()
            logger.error(f"Failed to create job: {e}")
            raise Exception(f"Failed to create job: {str(e)}")
    
    async def process_job(self, job_id: str) -> None:
        """Process a scraping job through the complete workflow"""
        # Create a new database session for background processing
        async with AsyncSessionLocal() as session:
            try:
                logger.info(f"Starting to process job {job_id}")
                
                # Get job
                job = await self._get_job_by_id(job_id, session)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                # Initialize AI agent
                if not settings.OPENAI_API_KEY:
                    await self._update_job_status(
                        job_id, JobStatus.FAILED, 0,
                        "OpenAI API key not configured",
                        error_info={"error": "Missing OPENAI_API_KEY in configuration"},
                        session=session
                    )
                    return
                
                async with UnifiedAgent(settings.OPENAI_API_KEY, settings.OPENAI_MODEL) as agent:
                    self.agent = agent
                    
                    # Step 1: Analyze website
                    analysis = await self._analyze_website(job, session)
                    if not analysis:
                        return
                    
                    # Step 2: Generate scraper
                    scraper_code = await self._generate_scraper(job, analysis, session)
                    if not scraper_code:
                        return
                    
                    # Step 3: Test scraper
                    test_result = await self._test_scraper(job, scraper_code, session)
                    if not test_result.get('success'):
                        # Try refinement once
                        refined_code = await self._refine_scraper(job, scraper_code, test_result, analysis, session)
                        if refined_code:
                            test_result = await self._test_scraper(job, refined_code, session)
                            scraper_code = refined_code
                    
                    # Step 4: Finalize job
                    await self._finalize_job(job, scraper_code, test_result, analysis, session)
                    
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                await self._update_job_status(
                    job_id, JobStatus.FAILED, 100,
                    f"Processing failed: {str(e)}",
                    error_info={"error": str(e), "error_type": type(e).__name__},
                    session=session
                )
    
    async def _analyze_website(self, job: Job, session: AsyncSession) -> Optional[Dict[str, Any]]:
        """Step 1: Analyze website"""
        try:
            await self._update_job_status(
                str(job.id), JobStatus.ANALYZING, 20,
                "Analyzing website structure and content",
                session=session
            )
            
            analysis = await self.agent.analyze_website(job.url, job.description)
            
            # Save analysis to job
            await self._update_job_analysis(str(job.id), analysis, session)
            
            logger.info(f"Website analysis completed for job {job.id} with confidence {analysis.get('confidence', 0)}")
            return analysis
            
        except Exception as e:
            logger.error(f"Website analysis failed for job {job.id}: {e}")
            await self._update_job_status(
                str(job.id), JobStatus.FAILED, 20,
                f"Website analysis failed: {str(e)}",
                error_info={"step": "analysis", "error": str(e)},
                session=session
            )
            return None
    
    async def _generate_scraper(self, job: Job, analysis: Dict[str, Any], session: AsyncSession) -> Optional[str]:
        """Step 2: Generate scraper code"""
        try:
            await self._update_job_status(
                str(job.id), JobStatus.GENERATING, 50,
                "Generating scraper code",
                session=session
            )
            
            scraper_code = await self.agent.generate_scraper(analysis, job.url, job.description)
            
            # Save scraper code
            scraper = Scraper(
                job_id=job.id,
                scraper_code=scraper_code,
                code_version=1,
                is_active=True
            )
            session.add(scraper)
            await session.commit()
            
            logger.info(f"Scraper code generated for job {job.id}")
            return scraper_code
            
        except Exception as e:
            logger.error(f"Scraper generation failed for job {job.id}: {e}")
            await self._update_job_status(
                str(job.id), JobStatus.FAILED, 50,
                f"Scraper generation failed: {str(e)}",
                error_info={"step": "generation", "error": str(e)},
                session=session
            )
            return None
    
    async def _test_scraper(self, job: Job, scraper_code: str, session: AsyncSession) -> Dict[str, Any]:
        """Step 3: Test scraper code"""
        try:
            await self._update_job_status(
                str(job.id), JobStatus.TESTING, 80,
                "Testing generated scraper",
                session=session
            )
            
            test_result = await self.sandbox.execute_scraper(scraper_code, job.url)
            
            logger.info(f"Scraper test completed for job {job.id}, success: {test_result.get('success', False)}")
            return test_result
            
        except Exception as e:
            logger.error(f"Scraper testing failed for job {job.id}: {e}")
            return {
                "error": f"Testing failed: {str(e)}",
                "success": False,
                "step": "testing"
            }
    
    async def _refine_scraper(self, job: Job, original_code: str, test_result: Dict[str, Any], analysis: Dict[str, Any], session: AsyncSession) -> Optional[str]:
        """Step 4: Refine scraper if needed"""
        try:
            await self._update_job_status(
                str(job.id), JobStatus.GENERATING, 60,
                "Refining scraper based on test results",
                session=session
            )
            
            refined_code = await self.agent.refine_scraper(original_code, test_result, analysis)
            
            # Save refined scraper
            scraper = Scraper(
                job_id=job.id,
                scraper_code=refined_code,
                code_version=2,
                is_active=True
            )
            session.add(scraper)
            await session.commit()
            
            logger.info(f"Scraper code refined for job {job.id}")
            return refined_code
            
        except Exception as e:
            logger.error(f"Scraper refinement failed for job {job.id}: {e}")
            return None
    
    async def _finalize_job(self, job: Job, scraper_code: str, test_result: Dict[str, Any], analysis: Dict[str, Any], session: AsyncSession) -> None:
        """Step 5: Finalize job based on test results"""
        try:
            if test_result.get('success'):
                # Create API endpoint
                endpoint_path = f"/generated/{job.id}"
                endpoint = Endpoint(
                    job_id=job.id,
                    endpoint_path=endpoint_path,
                    is_active=True
                )
                session.add(endpoint)
                
                # Update job as successful
                sample_data = test_result.get('data', [])[:3]  # First 3 items as sample
                
                await self._update_job_status(
                    str(job.id), JobStatus.READY, 100,
                    "API endpoint ready for use",
                    api_endpoint_path=endpoint_path,
                    sample_data=sample_data,
                    completed_at=datetime.utcnow(),
                    session=session
                )
                
                logger.info(f"Job {job.id} completed successfully")
                
            else:
                # Job failed
                await self._update_job_status(
                    str(job.id), JobStatus.FAILED, 100,
                    "Failed to create working scraper",
                    error_info=test_result,
                    completed_at=datetime.utcnow(),
                    session=session
                )
                
                logger.warning(f"Job {job.id} failed after all attempts")
                
        except Exception as e:
            logger.error(f"Failed to finalize job {job.id}: {e}")
            await self._update_job_status(
                str(job.id), JobStatus.FAILED, 100,
                f"Failed to finalize job: {str(e)}",
                error_info={"step": "finalization", "error": str(e)},
                completed_at=datetime.utcnow(),
                session=session
            )
    
    async def _get_job_by_id(self, job_id: str, session: AsyncSession = None) -> Optional[Job]:
        """Get job by ID"""
        try:
            if session is None:
                session = await self._ensure_db_session()
            
            result = await session.execute(
                select(Job).where(Job.id == uuid.UUID(job_id))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    async def _update_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        progress: int, 
        message: str,
        api_endpoint_path: Optional[str] = None,
        sample_data: Optional[list] = None,
        error_info: Optional[Dict[str, Any]] = None,
        completed_at: Optional[datetime] = None,
        session: AsyncSession = None
    ) -> None:
        """Update job status and progress"""
        try:
            if session is None:
                session = await self._ensure_db_session()
            
            update_data = {
                "status": status,
                "progress": progress,
                "message": message,
                "updated_at": datetime.utcnow()
            }
            
            if api_endpoint_path:
                update_data["api_endpoint_path"] = api_endpoint_path
            if sample_data is not None:
                update_data["sample_data"] = sample_data
            if error_info is not None:
                update_data["error_info"] = error_info
            if completed_at is not None:
                update_data["completed_at"] = completed_at
            
            await session.execute(
                update(Job)
                .where(Job.id == uuid.UUID(job_id))
                .values(**update_data)
            )
            await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            await session.rollback()
    
    async def _update_job_analysis(self, job_id: str, analysis: Dict[str, Any], session: AsyncSession = None) -> None:
        """Update job with analysis results"""
        try:
            if session is None:
                session = await self._ensure_db_session()
                
            await session.execute(
                update(Job)
                .where(Job.id == uuid.UUID(job_id))
                .values(analysis=analysis, updated_at=datetime.utcnow())
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to update job analysis for {job_id}: {e}")
            await session.rollback()
    
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get current job status"""
        return await self._get_job_by_id(job_id, self.db)
    
    async def list_jobs(self, limit: int = 10, offset: int = 0) -> list:
        """List recent jobs"""
        try:
            session = self.db if self.db else await self._ensure_db_session()
            result = await session.execute(
                select(Job)
                .order_by(Job.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
