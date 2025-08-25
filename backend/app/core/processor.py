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
from app.models.chat_message import ChatMessage
from app.schemas.job import JobCreate, JobUpdate
from app.core.agent import UnifiedAgent
from app.core.sandbox import SecureSandbox
from app.core.strategy_selector import ScrapingStrategySelector
from app.core.job_events import job_event_manager
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
        self.sandbox = None  # Will be initialized based on scraper type
        self.strategy_selector = ScrapingStrategySelector()
    
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
                
                async with UnifiedAgent(
                    settings.OPENAI_API_KEY, 
                    settings.OPENAI_MODEL,
                    settings.OPENAI_BASE_URL
                ) as agent:
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
                    test_result, final_scraper_code = await self._test_scraper(job, scraper_code, session)
                    if not test_result.get('success'):
                        # Try refinement once
                        refined_code = await self._refine_scraper(job, final_scraper_code, test_result, analysis, session)
                        if refined_code:
                            test_result, final_scraper_code = await self._test_scraper(job, refined_code, session)
                    
                    # Step 4: Finalize job
                    await self._finalize_job(job, final_scraper_code, test_result, analysis, session)
                    
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
            
            # Check if dynamic scraping was already used successfully
            scraping_metadata = analysis.get('scraping_metadata', {})
            used_dynamic_scraping = scraping_metadata.get('used_dynamic_scraping', False)
            
            # Determine scraping strategy
            strategy = self.strategy_selector.select_strategy(analysis, force_dynamic=used_dynamic_scraping)
            config = self.strategy_selector.get_strategy_config(strategy, analysis)
            
            logger.info(f"Selected strategy '{strategy}' for job {job.id} (dynamic scraping used: {used_dynamic_scraping})")
            
            # Generate appropriate scraper code
            if strategy == "dynamic":
                scraper_code = await self.agent.generate_dynamic_scraper(analysis, job.url, job.description)
                scraper_type = "dynamic"
            elif strategy == "hybrid":
                # For hybrid, start with static but be prepared to fallback
                scraper_code = await self.agent.generate_scraper(analysis, job.url, job.description)
                scraper_type = "static"
            else:  # static
                scraper_code = await self.agent.generate_scraper(analysis, job.url, job.description)
                scraper_type = "static"
            
            # Save scraper code with strategy info
            scraper = Scraper(
                job_id=job.id,
                scraper_code=scraper_code,
                code_version=1,
                is_active=True
            )
            session.add(scraper)
            await session.commit()
            
            # Store strategy info in job for later use
            analysis['selected_strategy'] = strategy
            analysis['scraper_type'] = scraper_type
            analysis['strategy_config'] = config
            await self._update_job_analysis(str(job.id), analysis, session)
            
            logger.info(f"Scraper code generated for job {job.id} using {strategy} strategy")
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
            
            # Get job analysis to determine scraper type
            job_with_analysis = await self._get_job_by_id(str(job.id), session)
            analysis = job_with_analysis.analysis or {}
            scraper_type = analysis.get('scraper_type', 'static')
            strategy = analysis.get('selected_strategy', 'static')
            
            # Initialize appropriate sandbox
            if scraper_type == "dynamic":
                self.sandbox = SecureSandbox(scraper_type="dynamic", timeout=60)
            else:
                self.sandbox = SecureSandbox(scraper_type="static", timeout=30)
            
            logger.info(f"Testing {scraper_type} scraper for job {job.id}")
            test_result = await self.sandbox.execute_scraper(scraper_code, job.url)
            
            # Handle hybrid strategy fallback
            if (strategy == "hybrid" and 
                scraper_type == "static" and 
                self.strategy_selector.should_fallback_to_dynamic(test_result, analysis)):
                
                logger.info(f"Hybrid strategy fallback: generating dynamic scraper for job {job.id}")
                
                # Generate dynamic scraper as fallback
                await self._update_job_status(
                    str(job.id), JobStatus.GENERATING, 60,
                    "Falling back to dynamic scraping",
                    session=session
                )
                
                dynamic_code = await self.agent.generate_dynamic_scraper(analysis, job.url, job.description)
                
                # Test dynamic scraper
                await self._update_job_status(
                    str(job.id), JobStatus.TESTING, 85,
                    "Testing dynamic scraper",
                    session=session
                )
                
                dynamic_sandbox = SecureSandbox(scraper_type="dynamic", timeout=60)
                test_result = await dynamic_sandbox.execute_scraper(dynamic_code, job.url)
                
                if test_result.get('success'):
                    # Save the successful dynamic scraper
                    scraper = Scraper(
                        job_id=job.id,
                        scraper_code=dynamic_code,
                        code_version=2,
                        is_active=True
                    )
                    session.add(scraper)
                    await session.commit()
                    
                    # Update analysis to reflect the fallback
                    analysis['scraper_type'] = 'dynamic'
                    analysis['fallback_used'] = True
                    await self._update_job_analysis(str(job.id), analysis, session)
                    
                    # Return the dynamic scraper code for finalization
                    return test_result, dynamic_code
            
            logger.info(f"Scraper test completed for job {job.id}, success: {test_result.get('success', False)}")
            return test_result, scraper_code
            
        except Exception as e:
            logger.error(f"Scraper testing failed for job {job.id}: {e}")
            return {
                "error": f"Testing failed: {str(e)}",
                "success": False,
                "step": "testing"
            }, scraper_code
    
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
                code_version=3,  # Increment version for refined code
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
            
            logger.info(f"✅ Job {job_id} status updated: {status.value} ({progress}%) - {message}")
            
            # Emit real-time event for SSE subscribers
            # First get the job to include URL and description in the event
            try:
                result = await session.execute(
                    select(Job).where(Job.id == uuid.UUID(job_id))
                )
                job = result.scalar_one_or_none()
                
                event_data = {
                    'id': job_id,
                    'status': status.value,
                    'progress': progress,
                    'message': message,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Include job basic info if available
                if job:
                    event_data['url'] = job.url
                    event_data['description'] = job.description
                
                if api_endpoint_path:
                    event_data['api_endpoint_path'] = api_endpoint_path
                if completed_at:
                    event_data['completed_at'] = completed_at.isoformat()
                if error_info:
                    event_data['error_info'] = error_info
                
                # Publish the event asynchronously (don't wait for it)
                logger.info(f"📡 Publishing SSE event for job {job_id}: {status.value} ({progress}%)")
                logger.debug(f"📡 Publishing event with job_id type: {type(job_id)}, value: {repr(job_id)}")
                # Ensure job_id is clean string to prevent corruption
                clean_job_id = str(job_id).strip()
                asyncio.create_task(job_event_manager.publish_job_update(clean_job_id, event_data))
                
            except Exception as e:
                logger.warning(f"Failed to fetch job data for event: {e}")
                # Fallback to basic event data without URL/description
                event_data = {
                    'id': job_id,
                    'status': status.value,
                    'progress': progress,
                    'message': message,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if api_endpoint_path:
                    event_data['api_endpoint_path'] = api_endpoint_path
                if completed_at:
                    event_data['completed_at'] = completed_at.isoformat()
                if error_info:
                    event_data['error_info'] = error_info
                
                # Publish the event asynchronously (don't wait for it)
                logger.info(f"📡 Publishing basic SSE event for job {job_id}: {status.value} ({progress}%)")
                logger.debug(f"📡 Publishing basic event with job_id type: {type(job_id)}, value: {repr(job_id)}")
                # Ensure job_id is clean string to prevent corruption
                clean_job_id = str(job_id).strip()
                asyncio.create_task(job_event_manager.publish_job_update(clean_job_id, event_data))
            
            logger.debug(f"Job {job_id} status updated: {status.value} ({progress}%) - {message}")
            
            # Save status update as chat message
            await self._save_status_as_chat_message(job_id, status, progress, message, session)
            
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            if session:
                await session.rollback()
    
    async def _save_status_as_chat_message(
        self, 
        job_id: str, 
        status: JobStatus, 
        progress: int, 
        message: str,
        session: AsyncSession
    ) -> None:
        """Save job status update as a chat message"""
        try:
            # Create conversational status messages
            status_messages = {
                JobStatus.PENDING: {
                    "emoji": "�",
                    "title": "Getting Started", 
                    "content": "I'm preparing to analyze your website. This should just take a moment!"
                },
                JobStatus.ANALYZING: {
                    "emoji": "🔍", 
                    "title": "Analyzing Website",
                    "content": "I'm examining the website structure and figuring out the best way to extract your data..."
                },
                JobStatus.GENERATING: {
                    "emoji": "⚡",
                    "title": "Creating Your Scraper", 
                    "content": "Now I'm writing custom code tailored specifically for this website. Almost there!"
                },
                JobStatus.TESTING: {
                    "emoji": "🧪",
                    "title": "Testing & Validation",
                    "content": "Testing the scraper to make sure it works perfectly and extracts the data you need."
                },
                JobStatus.READY: {
                    "emoji": "🎉",
                    "title": "Ready to Use!",
                    "content": "Your scraper is ready! I've successfully created an API endpoint that can extract the data whenever you need it."
                },
                JobStatus.FAILED: {
                    "emoji": "😔",
                    "title": "Something Went Wrong",
                    "content": "I encountered an issue while creating your scraper. Let me try a different approach or you can try with a different website."
                }
            }
            
            status_info = status_messages.get(status, {
                "emoji": "📋",
                "title": status.value.title(),
                "content": message
            })
            
            # Create animated, conversational content
            content = f"{status_info['emoji']} **{status_info['title']}**\n\n{status_info['content']}"
            
            # Create chat message
            chat_message = ChatMessage(
                job_id=uuid.UUID(job_id),
                message_type="system",
                content=content,
                is_status_update=True,
                message_metadata=f'{{"status": "{status.value}", "progress": {progress}}}'
            )
            
            session.add(chat_message)
            await session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to save status as chat message for {job_id}: {e}")
    
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
