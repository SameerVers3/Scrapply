# **Nexus Platform - Detailed Technical Requirements & Architecture**

**Version:** 1.0  
**Date:** August 18, 2025  
**Status:** Draft  

---

## **1. System Architecture Overview**

### **1.1 High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Engine     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (LLM + Tools) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Execution     │    │   Storage       │
                       │   Sandbox       │    │   (File-based)  │
                       └─────────────────┘    └─────────────────┘
```

### **1.2 Component Breakdown**

#### **Frontend Layer (Next.js)**
- **Purpose:** User interface and experience
- **Responsibilities:**
  - Request form and validation
  - Progress tracking and status updates
  - Results display and API documentation
  - Error handling and user feedback

#### **Backend API Layer (FastAPI)**
- **Purpose:** Business logic orchestration
- **Responsibilities:**
  - Request validation and processing
  - Agent coordination and workflow management
  - Dynamic API endpoint creation
  - Response formatting and error handling

#### **AI Engine Layer (LLM Integration)**
- **Purpose:** Intelligent code generation
- **Responsibilities:**
  - Website analysis and planning
  - Python scraper code generation
  - API structure design
  - Error diagnosis and refinement

#### **Execution Sandbox**
- **Purpose:** Secure code execution
- **Responsibilities:**
  - Generated code execution
  - Resource limitation and security
  - Result capture and validation

#### **Storage Layer (PostgreSQL)**
- **Purpose:** Data persistence with ACID compliance
- **Responsibilities:**
  - Job state management with JSONB support
  - Generated code versioning and storage
  - API endpoint lifecycle management
  - Real-time status updates and querying

## **2. Detailed Technical Specifications**

### **2.1 Frontend Technical Requirements**

#### **Technology Stack:**
- **Framework:** Next.js 14+ with App Router
- **Styling:** Tailwind CSS + shadcn/ui components
- **State Management:** React useState/useEffect + Context API
- **HTTP Client:** Fetch API with custom hooks
- **Type Safety:** TypeScript for all components

#### **Component Architecture:**

```typescript
// Core Types
interface ScrapingRequest {
  url: string;
  description: string;
  userId?: string;
}

interface JobStatus {
  id: string;
  status: 'pending' | 'analyzing' | 'generating' | 'testing' | 'ready' | 'failed';
  progress: number;
  message: string;
  apiEndpoint?: string;
  sampleData?: any;
  error?: string;
}

// Main Components
- RequestForm: Input collection and validation
- ProgressTracker: Real-time status updates
- ResultsDisplay: API endpoint and documentation
- ErrorHandler: User-friendly error messages
- APITester: Simple endpoint testing interface
```

#### **User Experience Requirements:**

| Feature | Requirement | Implementation |
|---------|-------------|----------------|
| Form Validation | Real-time URL and description validation | Zod schema validation |
| Progress Feedback | Live updates during processing | Server-sent events or WebSocket |
| Error Handling | Clear, actionable error messages | Structured error responses |
| Responsive Design | Works on desktop and mobile | Tailwind responsive utilities |
| Accessibility | WCAG 2.1 AA compliance | Semantic HTML + ARIA labels |

### **2.2 Backend Technical Requirements**

#### **Technology Stack:**
- **Framework:** FastAPI 0.100+
- **Database:** PostgreSQL with asyncpg driver
- **ORM:** SQLAlchemy 2.0+ with async support
- **Async Processing:** asyncio + Background Tasks
- **HTTP Client:** aiohttp for web requests
- **HTML Parsing:** BeautifulSoup4 + lxml parser
- **Code Generation:** LangChain + OpenAI/Anthropic API
- **Validation:** Pydantic models
- **Environment:** Python 3.11+

#### **API Design:**

```python
# Core Endpoints
POST /api/v1/scraping/requests
GET  /api/v1/scraping/jobs/{job_id}
GET  /api/v1/scraping/jobs/{job_id}/status
POST /api/v1/scraping/jobs/{job_id}/test

# Dynamic Endpoints (Generated)
GET  /api/v1/generated/{job_id}
```

#### **Data Models:**

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    READY = "ready"
    FAILED = "failed"

class ScrapingRequest(BaseModel):
    url: HttpUrl
    description: str
    user_id: Optional[str] = None

class Job(BaseModel):
    id: str
    url: HttpUrl
    description: str
    status: JobStatus
    progress: int = 0
    message: str = ""
    created_at: datetime
    updated_at: datetime
    api_endpoint: Optional[str] = None
    sample_data: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None
    scraper_code: Optional[str] = None
    
class APIResponse(BaseModel):
    request_timestamp: datetime
    source_url: HttpUrl
    data: List[Dict[Any, Any]]
    metadata: Optional[Dict[str, Any]] = None
```

### **2.3 AI Engine Technical Requirements**

#### **Agent Architecture (Simplified for MVP):**

```python
class UnifiedAgent:
    """Single agent handling all processing steps"""
    
    async def analyze_website(self, url: str, description: str) -> AnalysisResult:
        """Analyze website structure and plan extraction strategy"""
        
    async def generate_scraper(self, analysis: AnalysisResult) -> str:
        """Generate Python scraper code"""
        
    async def create_api_endpoint(self, job_id: str, scraper_code: str) -> str:
        """Create FastAPI endpoint dynamically"""
        
    async def test_endpoint(self, endpoint_url: str) -> TestResult:
        """Test generated endpoint and validate results"""
        
    async def refine_scraper(self, test_result: TestResult, original_code: str) -> str:
        """Refine scraper based on test failures"""
```

#### **Prompt Engineering:**

```python
ANALYSIS_PROMPT = """
Analyze the following website and extraction requirements:

URL: {url}
Requirements: {description}

Website HTML (first 2000 chars):
{html_sample}

Tasks:
1. Determine if this is a static or dynamic website
2. Identify the best CSS selectors for the required data
3. Check for pagination or infinite scroll
4. Suggest a JSON schema for the output
5. Identify potential challenges or obstacles

Return your analysis in this JSON format:
{
  "site_type": "static|dynamic",
  "selectors": {"field_name": "css_selector"},
  "pagination": {"present": true/false, "strategy": "description"},
  "schema": {"field": "type"},
  "challenges": ["list", "of", "challenges"]
}
"""

SCRAPER_GENERATION_PROMPT = """
Generate Python scraper code based on this analysis:

Analysis: {analysis}
Requirements: {description}

Requirements:
- Use requests and BeautifulSoup4
- Include error handling
- Return data as JSON-serializable dict
- Handle pagination if needed
- Include rate limiting (1 second delay between requests)
- Add user-agent header

Function signature:
def scrape_data(url: str) -> Dict[str, Any]:
    # Your code here
    return {"data": [...], "metadata": {...}}
"""
```

### **2.4 Execution Sandbox Technical Requirements**

#### **Security Implementation:**

```python
import subprocess
import tempfile
import os
import signal
from typing import Dict, Any

class SecureSandbox:
    def __init__(self):
        self.timeout = 30  # seconds
        self.memory_limit = 512  # MB
        self.allowed_modules = [
            'requests', 'bs4', 'json', 'time', 'urllib',
            'datetime', 're', 'math', 'string'
        ]
    
    async def execute_scraper(self, code: str, url: str) -> Dict[str, Any]:
        """Execute scraper code in sandboxed environment"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.wrap_code(code))
            temp_file = f.name
        
        try:
            # Execute with restrictions
            result = await self.run_with_limits(temp_file, url)
            return result
        finally:
            os.unlink(temp_file)
    
    def wrap_code(self, code: str) -> str:
        """Wrap user code with safety checks"""
        wrapper = f"""
import sys
import json
import signal

# Import restrictions
original_import = __builtins__['__import__']

def restricted_import(name, *args, **kwargs):
    allowed = {self.allowed_modules}
    if name not in allowed:
        raise ImportError(f"Module {{name}} not allowed")
    return original_import(name, *args, **kwargs)

__builtins__['__import__'] = restricted_import

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.timeout})

try:
    # User code here
{code}
    
    # Execute main function
    result = scrape_data(sys.argv[1])
    print(json.dumps(result))
    
except Exception as e:
    print(json.dumps({{"error": str(e), "type": type(e).__name__}}))
finally:
    signal.alarm(0)
"""
        return wrapper
```

### **2.5 Storage Technical Requirements**

#### **File-Based Storage Structure:**

```
storage/
├── jobs/
│   ├── {job_id}/
│   │   ├── metadata.json
│   │   ├── scraper.py
│   │   ├── analysis.json
│   │   └── results.json
├── endpoints/
│   └── {job_id}_endpoint.py
└── cache/
    └── {url_hash}/
        ├── html.txt
        └── analysis.json
```

#### **Data Persistence Models:**

```python
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

class FileStorage:
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    async def save_job(self, job: Job) -> None:
        job_dir = self.base_path / "jobs" / job.id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "id": job.id,
            "url": str(job.url),
            "description": job.description,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "api_endpoint": job.api_endpoint,
            "error": job.error
        }
        
        with open(job_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
    
    async def load_job(self, job_id: str) -> Optional[Job]:
        job_dir = self.base_path / "jobs" / job_id
        metadata_file = job_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None
            
        with open(metadata_file, "r") as f:
            data = json.load(f)
            
        return Job(**data)
```

## **3. Integration Patterns**

### **3.1 Frontend-Backend Communication**

```typescript
// Frontend API Client
class NexusAPI {
    private baseURL = '/api/v1';
    
    async createScrapingJob(request: ScrapingRequest): Promise<Job> {
        const response = await fetch(`${this.baseURL}/scraping/requests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return response.json();
    }
    
    async getJobStatus(jobId: string): Promise<Job> {
        const response = await fetch(`${this.baseURL}/scraping/jobs/${jobId}`);
        return response.json();
    }
    
    async testGeneratedAPI(jobId: string): Promise<any> {
        const response = await fetch(`${this.baseURL}/generated/${jobId}`);
        return response.json();
    }
}
```

### **3.2 Backend Processing Flow**

```python
# Main processing workflow
class ScrapingProcessor:
    def __init__(self, storage: FileStorage, agent: UnifiedAgent, sandbox: SecureSandbox):
        self.storage = storage
        self.agent = agent
        self.sandbox = sandbox
    
    async def process_request(self, request: ScrapingRequest) -> str:
        # Create job
        job = Job(
            id=generate_job_id(),
            url=request.url,
            description=request.description,
            status=JobStatus.PENDING
        )
        await self.storage.save_job(job)
        
        # Process in background
        asyncio.create_task(self._process_job(job))
        
        return job.id
    
    async def _process_job(self, job: Job) -> None:
        try:
            # Step 1: Analyze website
            job.status = JobStatus.ANALYZING
            job.progress = 20
            await self.storage.save_job(job)
            
            analysis = await self.agent.analyze_website(str(job.url), job.description)
            
            # Step 2: Generate scraper
            job.status = JobStatus.GENERATING
            job.progress = 50
            await self.storage.save_job(job)
            
            scraper_code = await self.agent.generate_scraper(analysis)
            
            # Step 3: Test scraper
            job.status = JobStatus.TESTING
            job.progress = 80
            await self.storage.save_job(job)
            
            test_result = await self.sandbox.execute_scraper(scraper_code, str(job.url))
            
            if test_result.get('error'):
                # Try refinement once
                refined_code = await self.agent.refine_scraper(test_result, scraper_code)
                test_result = await self.sandbox.execute_scraper(refined_code, str(job.url))
                scraper_code = refined_code
            
            if test_result.get('error'):
                # Final failure
                job.status = JobStatus.FAILED
                job.error = test_result['error']
            else:
                # Success - create endpoint
                endpoint_url = await self.agent.create_api_endpoint(job.id, scraper_code)
                job.status = JobStatus.READY
                job.api_endpoint = endpoint_url
                job.sample_data = test_result.get('data', [])[:3]  # First 3 items
            
            job.progress = 100
            await self.storage.save_job(job)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.progress = 100
            await self.storage.save_job(job)
```

## **4. Performance & Scalability Considerations**

### **4.1 Performance Requirements**

| Metric | Requirement | Implementation Strategy |
|--------|-------------|-------------------------|
| Response Time | < 60s total processing | Async processing + progress updates |
| Concurrent Users | 5 simultaneous requests | Process pool + queue management |
| Memory Usage | < 512MB per job | Sandbox limits + garbage collection |
| Storage | < 100MB total | File cleanup + size limits |

### **4.2 Error Handling Strategy**

```python
class NexusException(Exception):
    """Base exception for Nexus platform"""
    pass

class WebsiteAccessError(NexusException):
    """Failed to access target website"""
    pass

class ScraperGenerationError(NexusException):
    """Failed to generate scraper code"""
    pass

class SandboxExecutionError(NexusException):
    """Failed to execute code in sandbox"""
    pass

class APICreationError(NexusException):
    """Failed to create API endpoint"""
    pass

# Error handling middleware
@app.exception_handler(NexusException)
async def nexus_exception_handler(request: Request, exc: NexusException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "suggestion": get_error_suggestion(exc)
        }
    )
```

## **5. Security Considerations**

### **5.1 Code Execution Security**

- **Restricted Imports:** Only allow safe modules
- **Timeout Limits:** Kill long-running processes
- **Memory Limits:** Prevent memory exhaustion
- **File System Isolation:** Temporary directories only
- **Network Restrictions:** Only allow outbound HTTP/HTTPS

### **5.2 Input Validation**

```python
class SecurityValidator:
    DANGEROUS_PATTERNS = [
        r'__import__\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'subprocess',
        r'os\.system',
        r'file\s*\(',
        r'open\s*\('
    ]
    
    @staticmethod
    def validate_generated_code(code: str) -> bool:
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False
        return True
```

## **6. Testing Strategy**

### **6.1 Unit Testing**

```python
# Test coverage requirements
- Agent functionality: >90%
- API endpoints: >95%
- Security components: >95%
- Data models: >90%

# Key test cases
- Valid scraper generation
- Error handling and recovery
- Sandbox security
- API endpoint creation
- Data validation
```

### **6.2 Integration Testing**

```python
# End-to-end test scenarios
1. Simple static website scraping
2. Website with pagination
3. Error scenarios (404, timeout, etc.)
4. Malformed user inputs
5. Resource exhaustion scenarios
```

## **7. Deployment Architecture**

### **7.1 Development Environment**

```bash
# Local development stack
- Frontend: npm run dev (Next.js)
- Backend: uvicorn main:app --reload
- Storage: Local file system
- AI: OpenAI API (development key)
```

### **7.2 Production Considerations**

```bash
# Production deployment
- Container: Docker with multi-stage builds
- Web Server: Nginx reverse proxy
- Process Manager: Systemd or Docker Compose
- Monitoring: Basic logging and health checks
- Backup: Automated job data backup
```

---

**Document Prepared By:** AI Development Team  
**Technical Review:** Required  
**Next Update:** August 25, 2025
