from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Endpoint(Base):
    __tablename__ = "endpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Endpoint configuration
    endpoint_path = Column(String(500), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Usage statistics
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    average_response_time = Column(Integer, nullable=True)  # in milliseconds
    success_rate = Column(Integer, default=100)  # percentage
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Endpoint(id={self.id}, path={self.endpoint_path}, active={self.is_active})>"
