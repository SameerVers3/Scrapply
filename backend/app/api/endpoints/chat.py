from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid
import logging

from app.schemas.chat_message import ChatMessageCreate, ChatMessageResponse, ChatHistoryResponse, MessageType
from app.models.chat_message import ChatMessage
from app.models.job import Job
from app.database import get_db
from app.core.chat_processor import chat_processor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/jobs/{job_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    job_id: str,
    message: ChatMessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message for a specific job and get an intelligent response"""
    try:
        # Validate job exists
        result = await db.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Save the user's message first
        user_chat_message = ChatMessage(
            job_id=uuid.UUID(job_id),
            message_type=message.message_type,
            content=message.content,
            is_status_update=message.is_status_update,
            message_metadata=message.message_metadata
        )
        
        db.add(user_chat_message)
        await db.commit()
        await db.refresh(user_chat_message)
        
        # If this is a user message, process it intelligently
        if message.message_type == MessageType.USER:
            try:
                # Process the message and get AI response
                ai_response = await chat_processor.process_chat_message(
                    job_id=job_id,
                    user_message=message.content,
                    db=db
                )
                
                logger.info(f"Processed chat message for job {job_id}, got response: {ai_response[:100]}...")
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                # Still return the user message even if processing fails
                pass
        
        logger.info(f"Chat message created for job {job_id}")
        return ChatMessageResponse.from_orm(user_chat_message)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Failed to create chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/jobs/{job_id}/chat/message", response_model=dict)
async def send_intelligent_chat_message(
    job_id: str,
    message_content: dict,
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message and get an intelligent AI response immediately"""
    try:
        user_message = message_content.get("message", "").strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Validate job exists
        result = await db.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Save the user's message
        user_chat_message = ChatMessage(
            job_id=uuid.UUID(job_id),
            message_type=MessageType.USER.value,
            content=user_message,
            is_status_update=False
        )
        
        db.add(user_chat_message)
        await db.commit()
        await db.refresh(user_chat_message)
        
        # Process the message and get AI response
        ai_response = await chat_processor.process_chat_message(
            job_id=job_id,
            user_message=user_message,
            db=db
        )
        
        logger.info(f"Intelligent chat processing for job {job_id} completed")
        
        return {
            "user_message": {
                "id": str(user_chat_message.id),
                "content": user_message,
                "timestamp": user_chat_message.timestamp.isoformat()
            },
            "ai_response": ai_response,
            "status": "success"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Failed to process intelligent chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/jobs/{job_id}/chat", response_model=ChatHistoryResponse)
async def get_chat_history(
    job_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_status_updates: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a specific job"""
    try:
        # Validate job exists
        result = await db.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Build query
        query = select(ChatMessage).where(ChatMessage.job_id == uuid.UUID(job_id))
        
        # Filter out status updates if requested
        if not include_status_updates:
            query = query.where(ChatMessage.is_status_update == False)
        
        # Order by timestamp (newest first) and apply pagination
        query = query.order_by(desc(ChatMessage.timestamp)).offset(offset).limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        # Reverse to get chronological order (oldest first)
        messages = list(reversed(messages))
        
        # Get total count
        count_query = select(ChatMessage).where(ChatMessage.job_id == uuid.UUID(job_id))
        if not include_status_updates:
            count_query = count_query.where(ChatMessage.is_status_update == False)
        
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        message_responses = [ChatMessageResponse.from_orm(msg) for msg in messages]
        
        return ChatHistoryResponse(
            messages=message_responses,
            total=total
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/jobs/{job_id}/chat/{message_id}")
async def delete_chat_message(
    job_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific chat message"""
    try:
        # Validate job exists
        result = await db.execute(
            select(Job).where(Job.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Find and delete the message
        result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.id == uuid.UUID(message_id),
                ChatMessage.job_id == uuid.UUID(job_id)
            )
        )
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        await db.delete(message)
        await db.commit()
        
        return {"message": "Chat message deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Failed to delete chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
