# **Nexus Platform - Implementation Guide & Project Structure**

**Version:** 1.0  
**Date:** August 18, 2025  
**Status:** Implementation Ready  

---

## **1. Project Structure**

```
nexus-platform/
├── README.md
├── .gitignore
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── package.json
│
├── frontend/                          # Next.js Frontend
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── globals.css
│   │   │   └── api/
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── RequestForm.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   ├── ErrorHandler.tsx
│   │   │   └── APITester.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── types.ts
│   │   │   └── utils.ts
│   │   └── hooks/
│   │       ├── useScrapingJob.ts
│   │       └── useAPI.ts
│   └── public/
│       └── assets/
│
├── backend/                           # FastAPI Backend
│   ├── main.py
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                       # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── logging.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── job.py
│   │   │   ├── scraper.py
│   │   │   └── endpoint.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── job.py
│   │   │   └── request.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── scraping.py
│   │   │   │   └── generated.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── sandbox.py
│   │   │   └── processor.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py
│   │   │   ├── web_service.py
│   │   │   └── validation_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py
│   │       ├── helpers.py
│   │       └── exceptions.py
│   └── tests/
│       ├── __init__.py
│       ├── test_agent.py
│       ├── test_sandbox.py
│       ├── test_api.py
│       └── test_integration.py
│
├── storage/                           # File-based storage
│   ├── jobs/
│   ├── endpoints/
│   ├── cache/
│   └── logs/
│
├── scripts/                           # Utility scripts
│   ├── setup.sh
│   ├── test.sh
│   └── deploy.sh
│
└── docs/                             # Documentation
    ├── Documentations.txt
    ├── MVP_Requirements.md
    ├── Technical_Requirements.md
    ├── API_Documentation.md
    ├── User_Guide.md
    └── Deployment_Guide.md
```

## **2. Step-by-Step Implementation Guide**

### **Phase 1: Environment Setup (Days 1-2)**

#### **2.1 Initialize Project Structure**

```bash
# Create main project directory
mkdir nexus-platform
cd nexus-platform

# Initialize git repository
git init
echo "node_modules/\n__pycache__/\n.env\nstorage/\n*.log" > .gitignore

# Create directory structure
mkdir -p frontend/src/{app,components,lib,hooks}
mkdir -p backend/{app/{models,api/endpoints,core,services,utils},config,tests}
mkdir -p storage/{jobs,endpoints,cache,logs}
mkdir -p scripts docs
```

#### **2.2 Backend Setup**

```bash
# Create Python virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install fastapi uvicorn python-multipart
pip install requests beautifulsoup4 lxml aiohttp
pip install openai anthropic langchain
pip install pydantic python-dotenv
pip install sqlalchemy asyncpg alembic
pip install pytest httpx pytest-asyncio

# Create requirements.txt
pip freeze > requirements.txt
```

#### **2.3 Frontend Setup**

```bash
# Initialize Next.js project
cd ../frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir

# Install additional dependencies
npm install @radix-ui/react-slot class-variance-authority clsx tailwind-merge
npm install lucide-react @hookform/resolvers react-hook-form zod
npm install axios swr

# Install shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input label textarea card progress alert
```

### **Phase 2: Core Backend Implementation (Days 3-8)**

#### **2.4 Configuration and Settings**

```python
# backend/config/settings.py
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Nexus Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # Anthropic Configuration  
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Security
    SANDBOX_TIMEOUT: int = 30
    SANDBOX_MEMORY_LIMIT: int = 512
    MAX_CONCURRENT_JOBS: int = 5
    
    # Storage
    STORAGE_PATH: str = "storage"
    MAX_STORAGE_SIZE: int = 100  # MB
    
    # Development
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### **2.5 Data Models**

```python
# backend/app/models/job.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    READY = "ready"
    FAILED = "failed"

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    description: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    api_endpoint: Optional[str] = None
    sample_data: Optional[List[Dict[Any, Any]]] = None
    error: Optional[str] = None
    scraper_code: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None

class ScrapingRequest(BaseModel):
    url: HttpUrl
    description: str
    user_id: Optional[str] = None

class APIResponse(BaseModel):
    request_timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_url: HttpUrl
    data: List[Dict[Any, Any]]
    metadata: Optional[Dict[str, Any]] = None
    job_id: str
```

#### **2.6 Core Agent Implementation**

```python
# backend/app/core/agent.py
import json
import re
from typing import Dict, Any, Optional
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import requests
from bs4 import BeautifulSoup

class UnifiedAgent:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model,
            temperature=0.1
        )
        
    async def analyze_website(self, url: str, description: str) -> Dict[str, Any]:
        """Analyze website structure and plan extraction strategy"""
        try:
            # Fetch website content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            html_sample = str(soup)[:2000]  # First 2000 characters
            
            # Analysis prompt
            analysis_prompt = f"""
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
{{
  "site_type": "static|dynamic",
  "selectors": {{"field_name": "css_selector"}},
  "pagination": {{"present": true/false, "strategy": "description"}},
  "schema": {{"field": "type"}},
  "challenges": ["list", "of", "challenges"],
  "confidence": 0.8
}}
"""
            
            messages = [HumanMessage(content=analysis_prompt)]
            result = await self.llm.agenerate([messages])
            analysis_text = result.generations[0][0].text
            
            # Parse JSON response
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                analysis = {
                    "site_type": "static",
                    "selectors": {},
                    "pagination": {"present": False, "strategy": "none"},
                    "schema": {},
                    "challenges": ["JSON parsing failed"],
                    "confidence": 0.3
                }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Website analysis failed: {str(e)}")
    
    async def generate_scraper(self, analysis: Dict[str, Any], url: str, description: str) -> str:
        """Generate Python scraper code"""
        
        scraper_prompt = f"""
Generate Python scraper code based on this analysis:

URL: {url}
Description: {description}
Analysis: {json.dumps(analysis, indent=2)}

Requirements:
- Use requests and BeautifulSoup4
- Include comprehensive error handling
- Return data as JSON-serializable dict
- Handle pagination if needed
- Include rate limiting (1 second delay between requests)
- Add realistic user-agent header
- Follow robots.txt respectfully

Function signature must be:
def scrape_data(url: str) -> Dict[str, Any]:
    # Your implementation here
    return {{"data": [...], "metadata": {{...}}}}

Generate only the Python code, no explanations.
"""
        
        messages = [HumanMessage(content=scraper_prompt)]
        result = await self.llm.agenerate([messages])
        code = result.generations[0][0].text
        
        # Clean up the code
        code = self._clean_generated_code(code)
        return code
    
    async def refine_scraper(self, original_code: str, error_info: Dict[str, Any]) -> str:
        """Refine scraper based on test failures"""
        
        refinement_prompt = f"""
The following scraper code failed during testing:

Original Code:
{original_code}

Error Information:
{json.dumps(error_info, indent=2)}

Please fix the issues and return the improved code. Common issues:
1. CSS selectors that don't match elements
2. Missing error handling for network requests  
3. Incorrect data extraction logic
4. Missing pagination handling

Return only the corrected Python code with the same function signature.
"""
        
        messages = [HumanMessage(content=refinement_prompt)]
        result = await self.llm.agenerate([messages])
        refined_code = result.generations[0][0].text
        
        return self._clean_generated_code(refined_code)
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean and validate generated code"""
        # Remove markdown code blocks
        code = re.sub(r'^```python\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\n?$', '', code, flags=re.MULTILINE)
        
        # Basic security validation
        dangerous_patterns = [
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'subprocess',
            r'os\.system',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                raise Exception(f"Generated code contains dangerous pattern: {pattern}")
        
        return code.strip()
```

#### **2.7 Sandbox Implementation**

```python
# backend/app/core/sandbox.py
import subprocess
import tempfile
import os
import json
import signal
import asyncio
from typing import Dict, Any
from pathlib import Path

class SecureSandbox:
    def __init__(self, timeout: int = 30, memory_limit: int = 512):
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.allowed_modules = [
            'requests', 'bs4', 'beautifulsoup4', 'json', 'time', 'urllib',
            'datetime', 're', 'math', 'string', 'html', 'xml'
        ]
    
    async def execute_scraper(self, code: str, url: str) -> Dict[str, Any]:
        """Execute scraper code in sandboxed environment"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            wrapped_code = self._wrap_code(code)
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            # Execute with restrictions
            result = await self._run_with_limits(temp_file, url)
            return result
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def _wrap_code(self, code: str) -> str:
        """Wrap user code with safety checks and timeout"""
        wrapper = f'''
import sys
import json
import signal
import time

# Import restrictions
original_import = __builtins__['__import__']

def restricted_import(name, *args, **kwargs):
    allowed = {self.allowed_modules}
    if name.split('.')[0] not in allowed:
        raise ImportError(f"Module {{name}} not allowed in sandbox")
    return original_import(name, *args, **kwargs)

__builtins__['__import__'] = restricted_import

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout exceeded")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.timeout})

try:
    # User code injection
{self._indent_code(code)}
    
    # Execute main function
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = scrape_data(url)
        print(json.dumps(result, default=str))
    else:
        print(json.dumps({{"error": "No URL provided"}}))
    
except Exception as e:
    error_result = {{
        "error": str(e),
        "type": type(e).__name__,
        "success": False
    }}
    print(json.dumps(error_result))
finally:
    signal.alarm(0)
'''
        return wrapper
    
    def _indent_code(self, code: str) -> str:
        """Indent user code for proper wrapping"""
        lines = code.split('\n')
        indented_lines = ['    ' + line for line in lines]
        return '\n'.join(indented_lines)
    
    async def _run_with_limits(self, script_path: str, url: str) -> Dict[str, Any]:
        """Run script with resource limits"""
        try:
            # Create process with limits
            process = await asyncio.create_subprocess_exec(
                'python', script_path, url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_limits
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {"error": "Execution timeout", "success": False}
            
            # Parse result
            if process.returncode == 0:
                try:
                    result = json.loads(stdout.decode())
                    if 'error' not in result:
                        result['success'] = True
                    return result
                except json.JSONDecodeError:
                    return {
                        "error": f"Invalid JSON output: {stdout.decode()[:200]}",
                        "success": False
                    }
            else:
                return {
                    "error": f"Script failed: {stderr.decode()[:200]}",
                    "success": False
                }
                
        except Exception as e:
            return {"error": f"Sandbox execution failed: {str(e)}", "success": False}
    
    def _set_limits(self):
        """Set resource limits for subprocess"""
        import resource
        # Set memory limit (in bytes)
        memory_limit_bytes = self.memory_limit * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
        # Set CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
```

### **Phase 3: API Endpoints (Days 9-12)**

#### **2.8 Main FastAPI Application**

```python
# backend/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from app.api.endpoints import scraping, generated
from app.utils.exceptions import NexusException

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Autonomous Web-to-API Conversion Platform"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    scraping.router, 
    prefix=f"{settings.API_PREFIX}/scraping",
    tags=["scraping"]
)
app.include_router(
    generated.router,
    prefix=f"{settings.API_PREFIX}/generated", 
    tags=["generated"]
)

# Global exception handler
@app.exception_handler(NexusException)
async def nexus_exception_handler(request, exc: NexusException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "suggestion": exc.get_suggestion() if hasattr(exc, 'get_suggestion') else None
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG
    )
```

#### **2.9 Scraping Endpoints**

```python
# backend/app/api/endpoints/scraping.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
import asyncio

from app.models.job import Job, ScrapingRequest, JobStatus
from app.core.processor import ScrapingProcessor
from app.core.storage import FileStorage
from app.core.agent import UnifiedAgent  
from app.core.sandbox import SecureSandbox
from config.settings import settings

router = APIRouter()

# Dependency injection
def get_processor():
    storage = FileStorage(settings.STORAGE_PATH)
    agent = UnifiedAgent(settings.OPENAI_API_KEY)
    sandbox = SecureSandbox(settings.SANDBOX_TIMEOUT, settings.SANDBOX_MEMORY_LIMIT)
    return ScrapingProcessor(storage, agent, sandbox)

@router.post("/requests", response_model=Job)
async def create_scraping_request(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """Create a new scraping job"""
    try:
        job_id = await processor.create_job(request)
        
        # Start processing in background
        background_tasks.add_task(processor.process_job, job_id)
        
        # Return initial job status
        job = await processor.storage.load_job(job_id)
        return job
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/jobs/{job_id}", response_model=Job)
async def get_job_status(
    job_id: str,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """Get job status and details"""
    job = await processor.storage.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs", response_model=List[Job])
async def list_jobs(
    limit: int = 10,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """List recent jobs"""
    jobs = await processor.storage.list_jobs(limit)
    return jobs

@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    processor: ScrapingProcessor = Depends(get_processor)
):
    """Retry a failed job"""
    job = await processor.storage.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    # Reset job status
    job.status = JobStatus.PENDING
    job.progress = 0
    job.error = None
    await processor.storage.save_job(job)
    
    # Restart processing
    background_tasks.add_task(processor.process_job, job_id)
    
    return {"message": "Job retry initiated"}
```

### **Phase 4: Frontend Implementation (Days 13-18)**

#### **2.10 Main Page Component**

```typescript
// frontend/src/app/page.tsx
'use client';

import { useState } from 'react';
import { RequestForm } from '@/components/RequestForm';
import { ProgressTracker } from '@/components/ProgressTracker';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { ErrorHandler } from '@/components/ErrorHandler';
import { useScrapingJob } from '@/hooks/useScrapingJob';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const { job, error, createJob, refetchJob } = useScrapingJob(currentJobId);

  const handleSubmitRequest = async (url: string, description: string) => {
    try {
      const jobId = await createJob({ url, description });
      setCurrentJobId(jobId);
    } catch (err) {
      console.error('Failed to create job:', err);
    }
  };

  const handleRetry = () => {
    if (currentJobId) {
      refetchJob();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Nexus Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Transform any website into a structured API with natural language descriptions.
            No coding required.
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-6">
          {/* Request Form */}
          <Card>
            <CardHeader>
              <CardTitle>Create New API</CardTitle>
            </CardHeader>
            <CardContent>
              <RequestForm onSubmit={handleSubmitRequest} disabled={!!currentJobId && job?.status !== 'ready' && job?.status !== 'failed'} />
            </CardContent>
          </Card>

          {/* Progress Tracker */}
          {currentJobId && job && (
            <Card>
              <CardHeader>
                <CardTitle>Processing Status</CardTitle>
              </CardHeader>
              <CardContent>
                <ProgressTracker job={job} />
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {error && (
            <ErrorHandler error={error} onRetry={handleRetry} />
          )}

          {/* Results Display */}
          {job?.status === 'ready' && (
            <Card>
              <CardHeader>
                <CardTitle>Your API is Ready!</CardTitle>
              </CardHeader>
              <CardContent>
                <ResultsDisplay job={job} />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
```

#### **2.11 Request Form Component**

```typescript
// frontend/src/components/RequestForm.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, Send } from 'lucide-react';

interface RequestFormProps {
  onSubmit: (url: string, description: string) => Promise<void>;
  disabled?: boolean;
}

export function RequestForm({ onSubmit, disabled = false }: RequestFormProps) {
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ url?: string; description?: string }>({});

  const validateForm = (): boolean => {
    const newErrors: { url?: string; description?: string } = {};

    // URL validation
    try {
      new URL(url);
    } catch {
      newErrors.url = 'Please enter a valid URL';
    }

    // Description validation
    if (description.length < 10) {
      newErrors.description = 'Please provide a more detailed description (at least 10 characters)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await onSubmit(url, description);
      // Reset form on success
      setUrl('');
      setDescription('');
    } catch (error) {
      console.error('Submission failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="url">Website URL</Label>
        <Input
          id="url"
          type="url"
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={disabled || isSubmitting}
          className={errors.url ? 'border-red-500' : ''}
        />
        {errors.url && (
          <p className="text-sm text-red-600">{errors.url}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Data Requirements</Label>
        <Textarea
          id="description"
          placeholder="Describe what data you want to extract. For example: 'Extract product names, prices, and descriptions from all items on this page'"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={disabled || isSubmitting}
          rows={4}
          className={errors.description ? 'border-red-500' : ''}
        />
        {errors.description && (
          <p className="text-sm text-red-600">{errors.description}</p>
        )}
        <p className="text-sm text-gray-500">
          Be specific about what information you need. The more detail you provide, the better the results.
        </p>
      </div>

      <Button
        type="submit"
        disabled={disabled || isSubmitting || !url || !description}
        className="w-full"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating API...
          </>
        ) : (
          <>
            <Send className="mr-2 h-4 w-4" />
            Create API
          </>
        )}
      </Button>
    </form>
  );
}
```

## **3. Testing Strategy**

### **3.1 Backend Testing**

```python
# backend/tests/test_integration.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_scraping_request():
    request_data = {
        "url": "https://example.com",
        "description": "Extract all paragraph text"
    }
    response = client.post("/api/v1/scraping/requests", json=request_data)
    assert response.status_code == 200
    job = response.json()
    assert job["url"] == request_data["url"]
    assert job["status"] == "pending"

@pytest.mark.asyncio
async def test_sandbox_security():
    from app.core.sandbox import SecureSandbox
    
    sandbox = SecureSandbox()
    
    # Test dangerous code rejection
    dangerous_code = """
import os
os.system("rm -rf /")
"""
    
    with pytest.raises(Exception):
        await sandbox.execute_scraper(dangerous_code, "https://example.com")
```

### **3.2 Frontend Testing**

```typescript
// frontend/src/__tests__/RequestForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RequestForm } from '@/components/RequestForm';

describe('RequestForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('renders form elements', () => {
    render(<RequestForm onSubmit={mockOnSubmit} />);
    
    expect(screen.getByLabelText(/website url/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/data requirements/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create api/i })).toBeInTheDocument();
  });

  test('validates URL format', async () => {
    render(<RequestForm onSubmit={mockOnSubmit} />);
    
    const urlInput = screen.getByLabelText(/website url/i);
    const submitButton = screen.getByRole('button', { name: /create api/i });
    
    fireEvent.change(urlInput, { target: { value: 'invalid-url' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/please enter a valid url/i)).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });
});
```

## **4. Deployment Instructions**

### **4.1 Local Development**

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend  
cd frontend
npm run dev
```

### **4.2 Production Docker Setup**

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: 
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
    volumes:
      - ./storage:/app/storage

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
```

### **4.3 Environment Configuration**

```bash
# .env.example
# Copy to .env and fill in your values

# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Anthropic API (Alternative)
# ANTHROPIC_API_KEY=your-anthropic-key-here

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=5

# Security Settings
SANDBOX_TIMEOUT=30
SANDBOX_MEMORY_LIMIT=512

# Storage Settings
STORAGE_PATH=storage
MAX_STORAGE_SIZE=100
```

## **5. Monitoring and Maintenance**

### **5.1 Health Monitoring**

```python
# backend/app/api/endpoints/health.py
from fastapi import APIRouter
from typing import Dict, Any
import psutil
import os
from pathlib import Path

router = APIRouter()

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Comprehensive health check"""
    storage_path = Path("storage")
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('.').percent
        },
        "storage": {
            "total_jobs": len(list(storage_path.glob("jobs/*"))),
            "storage_size_mb": sum(f.stat().st_size for f in storage_path.rglob('*') if f.is_file()) / (1024*1024)
        },
        "config": {
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
            "sandbox_timeout": settings.SANDBOX_TIMEOUT
        }
    }
```

### **5.2 Cleanup Scripts**

```bash
#!/bin/bash
# scripts/cleanup.sh

# Clean up old job data (older than 7 days)
find storage/jobs -type d -mtime +7 -exec rm -rf {} +

# Clean up cache (older than 24 hours)  
find storage/cache -type f -mtime +1 -delete

# Clean up logs (older than 30 days)
find storage/logs -name "*.log" -mtime +30 -delete

echo "Cleanup completed at $(date)"
```

---

**This completes the comprehensive implementation guide for the Nexus Platform MVP. The guide provides a complete roadmap from setup to deployment, with detailed code examples and best practices for building a production-ready web-to-API conversion platform.**
