from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class ChatMessage(Base):
    """Chat message model for storing chat history"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_status_update = Column(Boolean, default=False)  # True for automatic status updates
    message_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Relationships
    job = relationship("Job", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, job_id={self.job_id}, type={self.message_type})>"
