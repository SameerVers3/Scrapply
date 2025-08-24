import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class JobEventManager:
    """
    Manages real-time job events and SSE connections
    """
    
    def __init__(self):
        # Store active SSE connections per job
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        # Store latest job state
        self._job_states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to job updates and return a queue for receiving events"""
        async with self._lock:
            if job_id not in self._subscribers:
                self._subscribers[job_id] = set()
            
            # Create a queue for this subscriber
            queue = asyncio.Queue(maxsize=100)  # Limit queue size to prevent memory issues
            self._subscribers[job_id].add(queue)
            
            logger.info(f"New SSE subscriber for job {job_id}. Total subscribers: {len(self._subscribers[job_id])}")
            return queue
    
    async def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        """Unsubscribe from job updates"""
        async with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id].discard(queue)
                if not self._subscribers[job_id]:
                    # Remove job if no more subscribers
                    del self._subscribers[job_id]
                    # Clean up job state if job is completed
                    if job_id in self._job_states:
                        job_state = self._job_states[job_id]
                        if job_state.get('status') in ['ready', 'failed']:
                            del self._job_states[job_id]
                
                logger.info(f"SSE subscriber removed for job {job_id}. Remaining subscribers: {len(self._subscribers.get(job_id, []))}")
    
    async def publish_job_update(self, job_id: str, update_data: Dict[str, Any]):
        """Publish job update to all subscribers"""
        async with self._lock:
            # Update stored job state
            self._job_states[job_id] = update_data
            
            if job_id not in self._subscribers:
                return  # No subscribers for this job
            
            # Create the event data
            event_data = {
                'id': job_id,
                'timestamp': datetime.utcnow().isoformat(),
                **update_data
            }
            
            # Send to all subscribers
            subscribers_to_remove = []
            for queue in self._subscribers[job_id].copy():  # Copy to avoid modification during iteration
                try:
                    # Non-blocking put - if queue is full, remove the subscriber
                    queue.put_nowait(event_data)
                except asyncio.QueueFull:
                    logger.warning(f"SSE queue full for job {job_id}, removing subscriber")
                    subscribers_to_remove.append(queue)
                except Exception as e:
                    logger.error(f"Error sending event to subscriber for job {job_id}: {e}")
                    subscribers_to_remove.append(queue)
            
            # Remove problematic subscribers
            for queue in subscribers_to_remove:
                self._subscribers[job_id].discard(queue)
            
            logger.debug(f"Published update for job {job_id} to {len(self._subscribers[job_id])} subscribers")
    
    async def get_latest_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest known state for a job"""
        async with self._lock:
            return self._job_states.get(job_id)
    
    def get_subscriber_count(self, job_id: str) -> int:
        """Get number of active subscribers for a job"""
        return len(self._subscribers.get(job_id, []))
    
    def get_total_subscribers(self) -> int:
        """Get total number of active SSE connections"""
        return sum(len(subscribers) for subscribers in self._subscribers.values())

# Global instance
job_event_manager = JobEventManager()
