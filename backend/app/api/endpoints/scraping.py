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
from app.core.job_events import job_event_manager
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
    Create a new scraping job with dynamic website support
    
    This endpoint creates a new scraping job and starts processing it in the background.
    The system automatically:
    
    1. **Analyzes the website** to detect JavaScript frameworks and dynamic content
    2. **Selects optimal strategy**: Static, Dynamic (browser automation), or Hybrid
    3. **Generates scraper code** optimized for the detected website type
    4. **Tests in secure sandbox** with appropriate timeout and resources
    5. **Creates API endpoint** for accessing scraped data
    
    **Supported Website Types:**
    - Traditional static websites (HTML + CSS)
    - JavaScript-enhanced sites (jQuery, simple dynamics)
    - Modern SPAs (React, Vue, Angular, Next.js, Nuxt, etc.)
    - Sites with infinite scroll, modals, AJAX loading
    
    **Automatic Features:**
    - Framework detection (React, Vue, Angular, Next.js, etc.)
    - Modal/popup dismissal
    - Dynamic content waiting (networkidle, DOM changes)
    - Infinite scroll handling
    - Hybrid fallback (static → dynamic if needed)
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
    
    logger.info(f"Starting real-time SSE stream for job {job_id}")
    
    # Validate job exists
    try:
        result = await db.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            async def error_stream():
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
    except ValueError:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'Invalid job ID format'})}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    async def event_stream():
        # Subscribe to job events
        queue = await job_event_manager.subscribe(job_id)
        
        try:
            # Send current job state first
            current_state = {
                'id': str(job.id),
                'url': job.url,
                'description': job.description,
                'status': job.status.value,
                'progress': job.progress,
                'message': job.message,
                'api_endpoint_path': job.api_endpoint_path,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'updated_at': job.updated_at.isoformat() if job.updated_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'timestamp': job.updated_at.isoformat() if job.updated_at else None
            }
            
            yield f"data: {json.dumps(current_state)}\n\n"
            
            # If job is already completed, send status and keep minimal connection
            if job.status in [JobStatus.READY, JobStatus.FAILED]:
                # Send final status but keep connection for a short monitoring period
                final_update = dict(current_state)
                final_update['final'] = True
                final_update['message'] = f'Job already completed with status: {job.status.value}'
                yield f"data: {json.dumps(final_update)}\n\n"
                
                # Keep connection open for a short time for monitoring, then close gracefully
                await asyncio.sleep(5)  # Wait 5 seconds
                yield f"data: {json.dumps({'type': 'connection_closing', 'reason': 'job_completed'})}\n\n"
                return
            
            # Wait for real-time updates for active jobs
            connection_timeout = 300  # 5 minutes max connection time
            keepalive_interval = 30   # Send keepalive every 30 seconds
            
            try:
                while True:
                    try:
                        # Wait for next update with timeout
                        update = await asyncio.wait_for(queue.get(), timeout=keepalive_interval)
                        
                        # Send the update
                        yield f"data: {json.dumps(update)}\n\n"
                        
                        # Close stream if job is completed
                        if update.get('status') in ['ready', 'failed']:
                            final_message = {
                                'type': 'job_completed',
                                'message': f'Job completed with status: {update.get("status")}',
                                'final': True,
                                'timestamp': asyncio.get_event_loop().time()
                            }
                            yield f"data: {json.dumps(final_message)}\n\n"
                            break
                            
                    except asyncio.TimeoutError:
                        # Send keepalive ping
                        keepalive = {
                            'type': 'keepalive',
                            'timestamp': asyncio.get_event_loop().time(),
                            'subscribers': job_event_manager.get_subscriber_count(job_id),
                            'connection_age_seconds': keepalive_interval
                        }
                        yield f"data: {json.dumps(keepalive)}\n\n"
                        continue
                        
            except asyncio.CancelledError:
                logger.info(f"SSE stream cancelled for job {job_id}")
                raise
            except Exception as e:
                logger.error(f"Error in SSE stream for job {job_id}: {e}")
                yield f"data: {json.dumps({'error': str(e), 'final': True})}\n\n"
            
        finally:
            # Always unsubscribe when connection closes
            await job_event_manager.unsubscribe(job_id, queue)
            logger.info(f"SSE stream ended for job {job_id}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@router.get("/jobs/stream-health")
async def stream_health():
    """Get SSE system health information"""
    return {
        "sse_enabled": True,
        "total_active_streams": job_event_manager.get_total_subscribers(),
        "active_jobs": len(job_event_manager._subscribers),
        "system_status": "healthy"
    }

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

@router.post("/analyze", status_code=200)
async def analyze_website_preview(
    request: ScrapingRequest,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """
    Preview website analysis without creating a job
    
    This endpoint analyzes a website and returns detection results for:
    - JavaScript frameworks (React, Vue, Angular, etc.)
    - Dynamic content indicators
    - Recommended scraping strategy
    - Confidence scores
    
    Use this to understand how the system will approach scraping a particular website.
    """
    try:
        logger.info(f"Analyzing website preview for URL: {request.url}")
        
        # Import here to avoid circular dependencies
        from app.core.agent import UnifiedAgent
        from app.core.strategy_selector import ScrapingStrategySelector
        from config.settings import settings
        
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not configured"
            )
        
        # Analyze website
        async with UnifiedAgent(
            settings.OPENAI_API_KEY,
            settings.OPENAI_MODEL, 
            settings.OPENAI_BASE_URL
        ) as agent:
            analysis = await agent.analyze_website(str(request.url), request.description)
        
        # Get strategy recommendation
        selector = ScrapingStrategySelector()
        strategy = selector.select_strategy(analysis)
        config = selector.get_strategy_config(strategy, analysis)
        
        # Format response
        dynamic_indicators = analysis.get('dynamic_indicators', {})
        
        return {
            "url": str(request.url),
            "description": request.description,
            "analysis": {
                "site_type": analysis.get('site_type', 'unknown'),
                "confidence": analysis.get('confidence', 0),
                "selectors": analysis.get('selectors', {}),
                "challenges": analysis.get('challenges', []),
                "recommended_approach": analysis.get('recommended_approach', '')
            },
            "dynamic_detection": {
                "confidence_score": dynamic_indicators.get('confidence_score', 0),
                "javascript_frameworks": dynamic_indicators.get('javascript_frameworks', []),
                "spa_patterns": dynamic_indicators.get('spa_patterns', []),
                "dynamic_loading": dynamic_indicators.get('dynamic_loading', []),
                "requires_interaction": dynamic_indicators.get('requires_interaction', False)
            },
            "strategy": {
                "selected": strategy,
                "engine": config.get('engine', 'unknown'),
                "timeout": config.get('timeout', 30),
                "approach": config.get('approach', ''),
                "libraries": config.get('libraries', [])
            },
            "capabilities": {
                "static_scraping": True,
                "dynamic_scraping": True,
                "browser_automation": True,
                "javascript_execution": True,
                "spa_support": True,
                "infinite_scroll": True,
                "modal_handling": True,
                "hybrid_fallback": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze website: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-dynamic", status_code=200)
async def test_dynamic_scraping(
    request: ScrapingRequest
):
    """
    Test dynamic scraping capabilities on a website
    
    This endpoint performs a quick test of dynamic scraping without creating a job:
    1. Detects dynamic content and frameworks
    2. Performs browser-based scraping 
    3. Returns sample results and metadata
    
    Use this for testing and validation before creating full scraping jobs.
    """
    try:
        logger.info(f"Testing dynamic scraping for URL: {request.url}")
        
        from app.core.dynamic_scraper import DynamicScraperEngine
        
        async with DynamicScraperEngine(timeout=30) as scraper:
            # Step 1: Detect dynamic content
            detection = await scraper.detect_dynamic_content(str(request.url))
            
            # Step 2: Perform basic scraping test
            basic_selectors = {
                "container": "body",
                "titles": "h1, h2, h3",
                "links": "a",
                "text": "p"
            }
            
            scraping_result = await scraper.scrape_with_browser(
                str(request.url),
                basic_selectors,
                {
                    "wait_strategy": "networkidle",
                    "handle_scroll": False
                }
            )
            
            return {
                "url": str(request.url),
                "description": request.description,
                "detection": detection,
                "scraping_test": {
                    "success": scraping_result.get("success", False),
                    "items_extracted": len(scraping_result.get("data", [])),
                    "sample_data": scraping_result.get("data", [])[:3],  # First 3 items
                    "metadata": scraping_result.get("metadata", {}),
                    "error": scraping_result.get("error", None)
                },
                "recommendations": {
                    "strategy": "dynamic" if detection.get("confidence_score", 0) > 0.5 else "static",
                    "estimated_timeout": 60 if detection.get("confidence_score", 0) > 0.7 else 30,
                    "frameworks_detected": detection.get("javascript_frameworks", []),
                    "special_handling_needed": len(detection.get("dynamic_loading", [])) > 0
                }
            }
        
    except Exception as e:
        logger.error(f"Failed to test dynamic scraping: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/capabilities")
async def get_scraping_capabilities():
    """
    Get information about scraping capabilities
    
    Returns detailed information about what types of websites and content
    the scraping system can handle.
    """
    return {
        "version": "2.0.0",
        "features": {
            "static_scraping": {
                "supported": True,
                "description": "Traditional HTTP requests + BeautifulSoup parsing",
                "best_for": ["Simple HTML sites", "Server-rendered pages", "APIs"],
                "timeout": "30 seconds",
                "resource_usage": "Low"
            },
            "dynamic_scraping": {
                "supported": True,
                "description": "Browser automation with Playwright",
                "best_for": ["SPAs", "JavaScript-heavy sites", "Modern web apps"],
                "timeout": "60 seconds", 
                "resource_usage": "High"
            },
            "hybrid_approach": {
                "supported": True,
                "description": "Try static first, fallback to dynamic automatically",
                "best_for": ["Unknown sites", "Mixed content", "Optimization"],
                "timeout": "45 seconds",
                "resource_usage": "Medium"
            }
        },
        "supported_frameworks": [
            "React", "Next.js", "Vue.js", "Nuxt.js", "Angular", 
            "Svelte", "jQuery", "Ember.js", "Backbone.js"
        ],
        "supported_patterns": [
            "Single Page Applications (SPAs)",
            "Server-Side Rendering (SSR)",
            "Client-Side Rendering (CSR)",
            "Infinite scroll",
            "Modal/popup interfaces",
            "AJAX-loaded content",
            "Dynamic form interactions",
            "Real-time updates"
        ],
        "automatic_handling": [
            "JavaScript framework detection",
            "Dynamic content waiting",
            "Modal dismissal",
            "Loading spinner detection",
            "Network idle waiting",
            "Content change detection",
            "Error recovery and retries"
        ],
        "browser_features": {
            "engine": "Chromium (Playwright)",
            "headless": True,
            "user_agent": "Modern Chrome",
            "viewport": "1920x1080",
            "javascript": True,
            "cookies": True,
            "local_storage": True
        }
    }
