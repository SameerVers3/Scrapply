from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Scraper(Base):
    __tablename__ = "scrapers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scraper code versioning
    code_version = Column(Integer, default=1)
    scraper_code = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Execution metadata
    execution_count = Column(Integer, default=0)
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    average_execution_time = Column(Integer, nullable=True)  # in milliseconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Scraper(id={self.id}, job_id={self.job_id}, version={self.code_version})>"
