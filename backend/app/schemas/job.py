from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    READY = "ready"
    FAILED = "failed"

class ScrapingRequest(BaseModel):
    url: HttpUrl = Field(..., description="The website URL to scrape")
    description: str = Field(..., min_length=10, max_length=1000, description="Natural language description of data requirements")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    
    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

class JobResponse(BaseModel):
    id: str
    url: str
    description: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    message: str = ""
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    api_endpoint_path: Optional[str] = None
    sample_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None  # accept dict or list
    error_info: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        
    @validator('id', pre=True)
    def convert_uuid_to_string(cls, v):
        if hasattr(v, 'hex'):  # UUID object
            return str(v)
        return v

    @validator('sample_data', pre=True)
    def validate_sample_data(cls, v):
        # Accept both list and dict coming from JSONB column
        if v is None:
            return None
        if isinstance(v, (dict, list)):
            return v
        # If it's a stringified JSON, try to parse it
        try:
            import json
            return json.loads(v)
        except Exception:
            raise ValueError('sample_data must be a dict or list')

class JobCreate(BaseModel):
    url: HttpUrl
    description: str
    user_id: Optional[str] = None

class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    api_endpoint_path: Optional[str] = None
    sample_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    error_info: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None

class JobList(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    size: int

class APIResponse(BaseModel):
    request_timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_url: str
    data: List[Dict[Any, Any]]
    metadata: Optional[Dict[str, Any]] = None
    job_id: str
    execution_time_ms: Optional[int] = None
