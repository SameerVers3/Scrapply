from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
import uuid

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    READY = "ready"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    progress = Column(Integer, default=0)
    message = Column(Text, default="")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # JSON fields for flexible data storage
    analysis = Column(JSONB, nullable=True)
    sample_data = Column(JSONB, nullable=True)
    error_info = Column(JSONB, nullable=True)
    
    # Additional metadata
    user_id = Column(String(255), nullable=True, index=True)  # For future user system
    api_endpoint_path = Column(String(500), nullable=True, unique=True)
    
    # Relationships
    chat_messages = relationship("ChatMessage", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, url={self.url[:50]})>"
