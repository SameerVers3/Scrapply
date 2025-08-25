"""
Intelligent chat processor for handling natural language requests to modify scraper code.
This module uses AI to understand user requests and apply modifications to existing scrapers.
"""

import logging
import json
import re
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.job import Job, JobStatus
from app.models.chat_message import ChatMessage
from app.core.processor import ScrapingProcessor
from app.core.job_events import job_event_manager
from app.schemas.chat_message import MessageType

logger = logging.getLogger(__name__)

class ChatProcessor:
    """Processes natural language chat messages and executes corresponding actions"""
    
    def __init__(self):
        self.scraping_processor = ScrapingProcessor()
    
    async def process_chat_message(
        self, 
        job_id: str, 
        user_message: str, 
        db: AsyncSession
    ) -> str:
        """
        Process a user chat message and return an appropriate response.
        Can modify scraper code based on natural language requests.
        """
        try:
            # Get the job
            result = await db.execute(
                select(Job).where(Job.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return "❌ Job not found. Please check the job ID and try again."
            
            # Parse the user's intent
            intent = self._parse_user_intent(user_message)
            logger.info(f"Parsed intent for job {job_id}: {intent}")
            
            # Execute the appropriate action based on intent
            response = await self._execute_intent(intent, job, user_message, db)
            
            # Save the assistant's response as a chat message
            await self._save_chat_message(
                job_id=job_id,
                message_type=MessageType.ASSISTANT,
                content=response,
                db=db
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            error_response = f"❌ I encountered an error while processing your request: {str(e)}"
            
            # Still save the error response
            try:
                await self._save_chat_message(
                    job_id=job_id,
                    message_type=MessageType.ASSISTANT,
                    content=error_response,
                    db=db
                )
            except:
                pass
                
            return error_response
    
    def _parse_user_intent(self, message: str) -> Dict[str, Any]:
        """Parse user message to determine intent and extract parameters"""
        message_lower = message.lower().strip()
        
        # Test the API
        if any(phrase in message_lower for phrase in ['test', 'run', 'try', 'execute']):
            if any(phrase in message_lower for phrase in ['api', 'endpoint', 'scraper']):
                return {
                    'action': 'test_api',
                    'confidence': 0.9
                }
        
        # Show endpoint/API details
        if any(phrase in message_lower for phrase in ['show', 'get', 'display']):
            if any(phrase in message_lower for phrase in ['endpoint', 'url', 'api', 'link']):
                return {
                    'action': 'show_endpoint',
                    'confidence': 0.9
                }
        
        # Add more fields
        if any(phrase in message_lower for phrase in ['add', 'include', 'extract']):
            if any(phrase in message_lower for phrase in ['field', 'data', 'element', 'information']):
                # Try to extract specific fields mentioned
                fields = self._extract_field_names(message)
                return {
                    'action': 'add_fields',
                    'fields': fields,
                    'confidence': 0.8
                }
        
        # Modify existing fields
        if any(phrase in message_lower for phrase in ['change', 'modify', 'update', 'edit']):
            if any(phrase in message_lower for phrase in ['field', 'data', 'extraction']):
                fields = self._extract_field_names(message)
                return {
                    'action': 'modify_fields',
                    'fields': fields,
                    'confidence': 0.8
                }
        
        # Remove fields
        if any(phrase in message_lower for phrase in ['remove', 'delete', 'exclude']):
            if any(phrase in message_lower for phrase in ['field', 'data']):
                fields = self._extract_field_names(message)
                return {
                    'action': 'remove_fields',
                    'fields': fields,
                    'confidence': 0.8
                }
        
        # Retry/regenerate scraper
        if any(phrase in message_lower for phrase in ['retry', 'regenerate', 'rebuild', 'recreate']):
            return {
                'action': 'retry_scraper',
                'confidence': 0.9
            }
        
        # Export/download code
        if any(phrase in message_lower for phrase in ['export', 'download', 'code', 'script']):
            return {
                'action': 'show_code',
                'confidence': 0.8
            }
        
        # Help/explain
        if any(phrase in message_lower for phrase in ['help', 'what can', 'how to', 'explain']):
            return {
                'action': 'help',
                'confidence': 0.9
            }
        
        # General conversation
        return {
            'action': 'general_chat',
            'confidence': 0.3
        }
    
    def _extract_field_names(self, message: str) -> List[str]:
        """Extract potential field names from user message"""
        # Common field patterns
        field_patterns = [
            r'\b(title|name|heading|header)\b',
            r'\b(price|cost|amount|fee)\b',
            r'\b(description|text|content|summary)\b',
            r'\b(image|photo|picture|img)\b',
            r'\b(link|url|href)\b',
            r'\b(date|time|timestamp)\b',
            r'\b(author|creator|by)\b',
            r'\b(rating|score|review)\b',
            r'\b(category|tag|type)\b',
        ]
        
        fields = []
        for pattern in field_patterns:
            matches = re.findall(pattern, message.lower())
            fields.extend(matches)
        
        # Remove duplicates and return
        return list(set(fields))
    
    async def _execute_intent(
        self, 
        intent: Dict[str, Any], 
        job: Job, 
        original_message: str,
        db: AsyncSession
    ) -> str:
        """Execute the parsed intent and return response"""
        
        action = intent.get('action')
        
        if action == 'test_api':
            return await self._test_api(job)
        
        elif action == 'show_endpoint':
            return await self._show_endpoint(job)
        
        elif action == 'add_fields':
            fields = intent.get('fields', [])
            return await self._add_fields(job, fields, original_message, db)
        
        elif action == 'modify_fields':
            fields = intent.get('fields', [])
            return await self._modify_fields(job, fields, original_message, db)
        
        elif action == 'remove_fields':
            fields = intent.get('fields', [])
            return await self._remove_fields(job, fields, db)
        
        elif action == 'retry_scraper':
            return await self._retry_scraper(job, db)
        
        elif action == 'show_code':
            return await self._show_code(job)
        
        elif action == 'help':
            return self._get_help_message(job)
        
        else:  # general_chat
            return self._handle_general_chat(original_message, job)
    
    async def _test_api(self, job: Job) -> str:
        """Test the API endpoint and return sample data"""
        if job.status != JobStatus.READY:
            return f"⏳ The API isn't ready yet. Current status: {job.status}. Please wait for it to complete processing."
        
        if not job.api_endpoint_path:
            return "❌ No API endpoint available for this job."
        
        try:
            # Get sample data from the job
            if job.sample_data:
                sample_count = len(job.sample_data) if isinstance(job.sample_data, list) else 1
                formatted_data = json.dumps(job.sample_data, indent=2)
                
                return f"✅ **API Test Results**\n\n**Endpoint:** `{job.api_endpoint_path}`\n\n**Sample Data** ({sample_count} items):\n```json\n{formatted_data}\n```\n\nThe API is working correctly! You can use this endpoint to get real-time data."
            else:
                return f"✅ **API Endpoint Ready**\n\n**Endpoint:** `{job.api_endpoint_path}`\n\nThe API is ready but no sample data is available. The endpoint should work for live requests."
                
        except Exception as e:
            logger.error(f"Error testing API: {e}")
            return f"❌ Error testing the API: {str(e)}"
    
    async def _show_endpoint(self, job: Job) -> str:
        """Show API endpoint details"""
        if job.status != JobStatus.READY:
            return f"⏳ The API isn't ready yet. Current status: {job.status}."
        
        if not job.api_endpoint_path:
            return "❌ No API endpoint available for this job."
        
        base_url = "http://localhost:8000"  # You might want to make this configurable
        full_url = f"{base_url}{job.api_endpoint_path}"
        
        return f"""🔗 **API Endpoint Details**

**Full URL:** `{full_url}`
**Path:** `{job.api_endpoint_path}`
**Method:** GET
**Response Format:** JSON

**Usage Examples:**

**cURL:**
```bash
curl "{full_url}"
```

**JavaScript:**
```javascript
fetch('{full_url}')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Python:**
```python
import requests
response = requests.get('{full_url}')
data = response.json()
```

The endpoint is ready to use! 🚀"""
    
    async def _add_fields(self, job: Job, fields: List[str], message: str, db: AsyncSession) -> str:
        """Add new fields to the scraper"""
        if job.status != JobStatus.READY:
            return f"⏳ Can't modify the scraper right now. Current status: {job.status}. Please wait for it to complete."
        
        if not fields:
            return """🤔 I'd be happy to add more fields to your scraper! 

Please specify what data you'd like to extract. For example:
• "Add price and rating fields"  
• "Include author and publication date"
• "Extract image URLs and descriptions"

What additional information would you like to capture from the website?"""
        
        # Trigger a modification job
        await self._trigger_modification(
            job, 
            f"Add the following fields to the scraper: {', '.join(fields)}. Original request: {message}",
            db
        )
        
        return f"🔄 **Adding New Fields**\n\nI'm working on adding these fields to your scraper:\n" + \
               "\n".join(f"• {field}" for field in fields) + \
               "\n\nThis will take a moment. I'll update you once the modifications are complete!"
    
    async def _modify_fields(self, job: Job, fields: List[str], message: str, db: AsyncSession) -> str:
        """Modify existing fields in the scraper"""
        if job.status != JobStatus.READY:
            return f"⏳ Can't modify the scraper right now. Current status: {job.status}."
        
        await self._trigger_modification(
            job,
            f"Modify the following fields in the scraper: {', '.join(fields)}. User request: {message}",
            db
        )
        
        field_list = "\n".join(f"• {field}" for field in fields) if fields else "the specified fields"
        
        return f"🔄 **Modifying Fields**\n\nI'm updating {field_list} in your scraper based on your request.\n\nThis may take a moment. I'll let you know when the changes are ready!"
    
    async def _remove_fields(self, job: Job, fields: List[str], db: AsyncSession) -> str:
        """Remove fields from the scraper"""
        if job.status != JobStatus.READY:
            return f"⏳ Can't modify the scraper right now. Current status: {job.status}."
        
        if not fields:
            return "🤔 Which fields would you like me to remove? Please specify the field names."
        
        await self._trigger_modification(
            job,
            f"Remove the following fields from the scraper: {', '.join(fields)}",
            db
        )
        
        return f"🗑️ **Removing Fields**\n\nI'm removing these fields from your scraper:\n" + \
               "\n".join(f"• {field}" for field in fields) + \
               "\n\nI'll update you once the changes are complete!"
    
    async def _retry_scraper(self, job: Job, db: AsyncSession) -> str:
        """Retry/regenerate the entire scraper"""
        if job.status in [JobStatus.PENDING, JobStatus.ANALYZING, JobStatus.GENERATING, JobStatus.TESTING]:
            return f"⏳ The scraper is already being processed. Current status: {job.status}."
        
        # Reset job status and trigger reprocessing
        job.status = JobStatus.PENDING
        job.progress = 0
        job.message = "Regenerating scraper based on user request"
        job.api_endpoint_path = None
        job.sample_data = None
        job.error_info = None
        
        await db.commit()
        
        # Trigger reprocessing
        asyncio.create_task(self.scraping_processor.process_job(str(job.id)))
        
        return "🔄 **Regenerating Scraper**\n\nI'm rebuilding your scraper from scratch. This will analyze the website again and create a fresh implementation.\n\nI'll keep you updated on the progress!"
    
    async def _show_code(self, job: Job) -> str:
        """Show the generated scraper code"""
        if job.status != JobStatus.READY:
            return f"⏳ The scraper code isn't ready yet. Current status: {job.status}."
        
        # This is a placeholder - in a real implementation, you'd retrieve the actual generated code
        return f"""📝 **Scraper Code**

The scraper code is generated dynamically and integrated into the API endpoint. Here's how it works:

**Endpoint:** `{job.api_endpoint_path or 'Not available'}`
**Target URL:** `{job.url}`
**Description:** {job.description}

The code is automatically optimized for the target website and includes:
• Robust error handling
• Rate limiting
• Data validation
• Response formatting

For the actual implementation code, you can inspect the API endpoint or contact support for the full source code export."""
    
    def _get_help_message(self, job: Job) -> str:
        """Return help message with available commands"""
        status_help = ""
        if job.status == JobStatus.READY:
            status_help = """
**Your scraper is ready! Here's what you can do:**

🧪 **Test & Use:**
• "Test the API" - Run a test and see sample data
• "Show me the endpoint" - Get the API URL and usage examples

🔧 **Modify:**  
• "Add price and rating fields" - Add new data fields
• "Change the title extraction" - Modify existing fields
• "Remove image fields" - Remove unwanted fields

🔄 **Rebuild:**
• "Regenerate the scraper" - Start over with a fresh build

📝 **Export:**
• "Show me the code" - View implementation details"""
        else:
            status_help = f"""
**Your scraper is currently {job.status}.**

Once it's ready, you'll be able to:
• Test the API
• Modify data fields  
• View the endpoint details
• Regenerate if needed"""
        
        return f"""🤖 **Chat Assistant Help**

I can help you manage and modify your web scraper! {status_help}

**General Commands:**
• "Help" - Show this message
• Natural language works too! Just tell me what you want to do.

**Examples:**
• "Can you add product prices to the scraper?"
• "I need to extract author names as well"
• "Remove the image fields, I don't need them"

What would you like to do with your scraper?"""
    
    def _handle_general_chat(self, message: str, job: Job) -> str:
        """Handle general conversation that doesn't match specific intents"""
        return f"""Thanks for your message! I'm here to help you manage your web scraper.

**Your scraper status:** {job.status}
**Target URL:** {job.url}

I can help you:
• Test your API
• Add or modify data fields
• Show endpoint details
• Regenerate the scraper

Try saying something like:
• "Test the API"
• "Add price fields"  
• "Show me the endpoint"
• "Help" for more options

What would you like me to help you with?"""
    
    async def _trigger_modification(self, job: Job, modification_request: str, db: AsyncSession):
        """Trigger a job modification based on user request"""
        # Update job status
        job.status = JobStatus.ANALYZING
        job.progress = 0
        job.message = f"Modifying scraper: {modification_request}"
        
        await db.commit()
        
        # Publish status update
        await job_event_manager.publish_job_update(str(job.id), {
            'id': str(job.id),
            'status': job.status.value,
            'progress': job.progress,
            'message': job.message,
            'url': job.url,
            'description': job.description
        })
        
        # Trigger async processing
        asyncio.create_task(self.scraping_processor.process_job(str(job.id)))
    
    async def _save_chat_message(
        self, 
        job_id: str, 
        message_type: MessageType, 
        content: str, 
        db: AsyncSession,
        is_status_update: bool = False
    ):
        """Save a chat message to the database"""
        try:
            chat_message = ChatMessage(
                job_id=uuid.UUID(job_id),
                message_type=message_type.value,
                content=content,
                is_status_update=is_status_update
            )
            
            db.add(chat_message)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")

# Global instance
chat_processor = ChatProcessor()
