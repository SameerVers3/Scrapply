from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessageCreate(BaseModel):
    job_id: str
    message_type: MessageType
    content: str
    is_status_update: bool = False
    message_metadata: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: str
    job_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    is_status_update: bool
    message_metadata: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            job_id=str(obj.job_id),
            message_type=obj.message_type,
            content=obj.content,
            timestamp=obj.timestamp,
            is_status_update=obj.is_status_update,
            message_metadata=obj.message_metadata
        )

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int
