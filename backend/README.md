# Nexus Platform Backend

AI-powered web-to-API conversion platform backend built with FastAPI and PostgreSQL.

## Quick Start

1. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

2. **Start the Application**
   ```bash
   ./start.sh
   ```
   
   Or manually:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup database
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   
   # Start server
   uvicorn main:app --reload
   ```

## API Endpoints

- **POST /api/v1/scraping/requests** - Submit scraping job
- **GET /api/v1/jobs/{job_id}** - Get job status
- **GET /api/v1/jobs/{job_id}/result** - Get job result
- **POST /generated/{job_id}** - Use generated API
- **GET /health** - Health check

## Documentation

- **API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Features

- ✅ AI-powered code generation with OpenAI GPT-4
- ✅ Secure sandboxed code execution
- ✅ PostgreSQL database with async SQLAlchemy
- ✅ Multi-agent AI architecture with LangChain
- ✅ RESTful API with FastAPI
- ✅ Request validation with Pydantic
- ✅ Database migrations with Alembic
- ✅ Comprehensive error handling
- ✅ Request logging and monitoring

## Architecture

```
backend/
├── app/
│   ├── api/endpoints/     # API route handlers
│   ├── core/             # Business logic (AI agents, sandbox)
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic validation schemas
│   └── database.py       # Database configuration
├── config/
│   └── settings.py       # Application settings
├── alembic/             # Database migrations
├── requirements.txt     # Python dependencies
└── main.py             # FastAPI application
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# OpenAI
OPENAI_API_KEY=sk-...

# Application
DEBUG=true
LOG_LEVEL=INFO
```

## Testing

The backend is ready for testing! Start with:

1. Submit a scraping job via POST `/api/v1/scraping/requests`
2. Check job status via GET `/api/v1/jobs/{job_id}`
3. Use the generated API via POST `/generated/{job_id}`
