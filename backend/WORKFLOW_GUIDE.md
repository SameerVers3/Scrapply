# 🚀 Nexus Platform - Step-by-Step Workflow Guide

## Overview
Nexus Platform transforms any website into a RESTful API using AI-powered web scraping. Here's how to use it effectively.

## 🏃‍♂️ Quick Start

### 1. Start the Backend Server
```bash
cd backend
conda activate myenv
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Add Seed Data (Optional)
```bash
python seed_data.py
```

### 3. Access the API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📋 Complete Workflow

### Step 1: Submit a Scraping Job
Submit a URL to be converted into an API endpoint.

**Endpoint**: `POST /api/v1/scraping/requests`

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraping/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://quotes.toscrape.com/",
    "user_id": "user_123",
    "description": "Extract inspirational quotes with authors and tags"
  }'
```

**Response**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "Job submitted successfully",
  "estimated_time": "2-5 minutes"
}
```

### Step 2: Monitor Job Progress
Check the status of your scraping job.

**Endpoint**: `GET /api/v1/jobs/{job_id}`

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/jobs/abc123-def456-ghi789"
```

**Response Examples**:

**Pending**:
```json
{
  "id": "abc123-def456-ghi789",
  "url": "https://quotes.toscrape.com/",
  "status": "pending",
  "user_id": "user_123",
  "created_at": "2025-08-18T15:00:00Z"
}
```

**Completed**:
```json
{
  "id": "abc123-def456-ghi789",
  "url": "https://quotes.toscrape.com/",
  "status": "completed",
  "user_id": "user_123",
  "processing_time": 3.2,
  "created_at": "2025-08-18T15:00:00Z",
  "updated_at": "2025-08-18T15:03:00Z"
}
```

### Step 3: Get Job Results
Once completed, retrieve the job results and generated code.

**Endpoint**: `GET /api/v1/jobs/{job_id}/result`

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/jobs/abc123-def456-ghi789/result"
```

**Response**:
```json
{
  "status": "completed",
  "result": {
    "total_quotes": 10,
    "sample_quote": "The world as we have created it is a process of our thinking.",
    "authors": ["Albert Einstein", "J.K. Rowling"],
    "status": "success"
  },
  "generated_code": "import requests\nfrom bs4 import BeautifulSoup...",
  "endpoint_path": "/generated/abc123-def456-ghi789"
}
```

### Step 4: Use the Generated API
Your website is now available as a RESTful API endpoint!

**Endpoint**: `POST /generated/{job_id}`

**Example Request**:
```bash
curl -X POST "http://localhost:8000/generated/abc123-def456-ghi789" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

**Response**:
```json
{
  "quotes": [
    {
      "text": "The world as we have created it is a process of our thinking.",
      "author": "Albert Einstein",
      "tags": ["change", "deep-thoughts", "thinking", "world"]
    },
    {
      "text": "It is our choices, Harry, that show what we truly are.",
      "author": "J.K. Rowling",
      "tags": ["abilities", "choices"]
    }
  ]
}
```

---

## 🔧 Advanced Features

### List All Jobs
**Endpoint**: `GET /api/v1/jobs/`

```bash
curl "http://localhost:8000/api/v1/jobs/?skip=0&limit=10&user_id=user_123"
```

### Delete a Job
**Endpoint**: `DELETE /api/v1/jobs/{job_id}`

```bash
curl -X DELETE "http://localhost:8000/api/v1/jobs/abc123-def456-ghi789"
```

---

## 📊 Testing with Seed Data

The seed data creates 5 sample jobs with different statuses:

1. **Quotes Scraper** (Completed) - `quotes_toscrape_com`
2. **Hacker News** (Completed) - `news_ycombinator_com` 
3. **HTTP Bin** (Completed) - `httpbin_org`
4. **JSON Placeholder** (Pending) 
5. **Invalid URL** (Failed)

### Test the Generated APIs:

```bash
# Test quotes scraper
curl -X POST "http://localhost:8000/generated/{quotes_job_id}"

# Test Hacker News scraper  
curl -X POST "http://localhost:8000/generated/{hackernews_job_id}"

# Test HTTP Bin scraper
curl -X POST "http://localhost:8000/generated/{httpbin_job_id}"
```

---

## 🎯 Use Cases

### 1. E-commerce Price Monitoring
```bash
curl -X POST "http://localhost:8000/api/v1/scraping/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example-store.com/products",
    "user_id": "price_monitor_001",
    "description": "Monitor product prices and availability"
  }'
```

### 2. News Aggregation
```bash
curl -X POST "http://localhost:8000/api/v1/scraping/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news-site.com/latest",
    "user_id": "news_bot_001", 
    "description": "Aggregate latest news headlines"
  }'
```

### 3. Job Listings API
```bash
curl -X POST "http://localhost:8000/api/v1/scraping/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://job-board.com/listings",
    "user_id": "job_scraper_001",
    "description": "Extract job listings with details"
  }'
```

---

## ⚡ Performance Tips

1. **Batch Processing**: Submit multiple URLs at once for efficiency
2. **Caching**: Generated APIs cache results for faster responses
3. **Rate Limiting**: Respect website rate limits automatically
4. **Error Handling**: Robust error handling with detailed messages

---

## 🔒 Security Features

- **Sandbox Execution**: All scraping code runs in isolated environment
- **Resource Limits**: Memory and time limits prevent abuse
- **Input Validation**: All inputs validated and sanitized
- **Rate Limiting**: API endpoints have configurable rate limits

---

## 🐛 Troubleshooting

### Common Issues:

1. **Job Stuck in Pending**: Check if OpenAI API key is configured
2. **Connection Errors**: Verify the target website is accessible
3. **Timeout Errors**: Some websites may take longer to scrape
4. **Permission Denied**: Some websites block scraping

### Error Codes:
- `400`: Bad Request - Invalid URL or parameters
- `404`: Job not found
- `429`: Rate limit exceeded
- `500`: Internal server error

---

## 📈 Monitoring

Monitor your API usage:
- Job success/failure rates
- Processing times
- API endpoint usage statistics
- Error logs and debugging info

Access logs at: http://localhost:8000/health
