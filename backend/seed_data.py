#!/usr/bin/env python3
"""
Seed data script for Nexus Platform
Creates sample jobs, scrapers, and endpoints for testing
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
import uuid

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.job import Job
from app.models.scraper import Scraper
from app.models.endpoint import Endpoint
from config.settings import settings

# Sample data
SAMPLE_JOBS = [
    {
        "url": "https://quotes.toscrape.com/",
        "description": "Extract inspirational quotes with authors and tags",
        "user_id": "user_001",
        "status": "ready",
        "progress": 100,
        "message": "API endpoint created successfully",
        "api_endpoint_path": "/quotes_toscrape_com",
        "analysis": {
            "content_type": "quotes",
            "structure": "list_of_quotes",
            "elements_found": 10
        },
        "sample_data": {
            "total_quotes": 10,
            "sample_quote": "The world as we have created it is a process of our thinking.",
            "authors": ["Albert Einstein", "J.K. Rowling", "Jane Austen"],
            "status": "success"
        }
    },
    {
        "url": "https://news.ycombinator.com/",
        "description": "Scrape top stories from Hacker News",
        "user_id": "user_002",
        "status": "ready",
        "progress": 100,
        "message": "API endpoint created successfully",
        "api_endpoint_path": "/news_ycombinator_com",
        "analysis": {
            "content_type": "news_stories",
            "structure": "list_of_stories",
            "elements_found": 30
        },
        "sample_data": {
            "total_stories": 30,
            "sample_story": "AI advances in automated testing frameworks",
            "categories": ["Technology", "Startups", "Programming"],
            "status": "success"
        }
    },
    {
        "url": "https://httpbin.org/json",
        "description": "Extract JSON data from httpbin test endpoint",
        "user_id": "user_001",
        "status": "ready",
        "progress": 100,
        "message": "API endpoint created successfully",
        "api_endpoint_path": "/httpbin_org",
        "analysis": {
            "content_type": "json_data",
            "structure": "single_object",
            "elements_found": 1
        },
        "sample_data": {
            "slideshow": {
                "title": "Sample Slide Show",
                "slides": 3
            },
            "status": "success"
        }
    },
    {
        "url": "https://jsonplaceholder.typicode.com/posts",
        "description": "Extract posts from JSONPlaceholder API",
        "user_id": "user_003",
        "status": "analyzing",
        "progress": 35,
        "message": "Analyzing website structure and content patterns"
    },
    {
        "url": "https://invalid-url.example.com/data",
        "description": "Test invalid URL handling",
        "user_id": "user_002",
        "status": "failed",
        "progress": 0,
        "message": "Failed to connect to the URL",
        "error_info": {
            "error_type": "ConnectionError",
            "error_message": "Failed to connect to the URL. Connection timeout after 10 seconds.",
            "timestamp": "2025-08-18T14:00:00Z"
        }
    }
]

SAMPLE_SCRAPERS = [
    {
        "code": '''
import requests
from bs4 import BeautifulSoup
import json

def scrape_quotes():
    """Scrape quotes from quotes.toscrape.com"""
    response = requests.get("https://quotes.toscrape.com/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    quotes = []
    for quote in soup.find_all('div', class_='quote'):
        text = quote.find('span', class_='text').get_text()
        author = quote.find('small', class_='author').get_text()
        tags = [tag.get_text() for tag in quote.find_all('a', class_='tag')]
        
        quotes.append({
            'text': text,
            'author': author,
            'tags': tags
        })
    
    return quotes

# API endpoint handler
def handle_request(params=None):
    limit = params.get('limit', 10) if params else 10
    quotes = scrape_quotes()
    return {"quotes": quotes[:limit]}
''',
        "code_version": 1,
        "execution_count": 15,
        "average_execution_time": 1500
    },
    {
        "code": '''
import requests
from bs4 import BeautifulSoup
import json

def scrape_hackernews():
    """Scrape top stories from Hacker News"""
    response = requests.get("https://news.ycombinator.com/")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    stories = []
    for item in soup.find_all('tr', class_='athing'):
        title_elem = item.find('span', class_='titleline')
        if title_elem:
            link = title_elem.find('a')
            title = link.get_text() if link else ""
            url = link.get('href') if link else ""
            
            stories.append({
                'title': title,
                'url': url,
                'id': item.get('id')
            })
    
    return stories[:10]  # Top 10 stories

# API endpoint handler
def handle_request(params=None):
    limit = params.get('limit', 10) if params else 10
    stories = scrape_hackernews()
    return {"stories": stories[:limit]}
''',
        "code_version": 1,
        "execution_count": 8,
        "average_execution_time": 2100
    },
    {
        "code": '''
import requests
import json

def scrape_httpbin():
    """Scrape JSON data from httpbin.org"""
    response = requests.get("https://httpbin.org/json")
    return response.json()

# API endpoint handler
def handle_request(params=None):
    return {"data": scrape_httpbin()}
''',
        "code_version": 1,
        "execution_count": 23,
        "average_execution_time": 800
    }
]


async def create_seed_data():
    """Create seed data for testing"""
    print("🌱 Creating seed data for Nexus Platform...")
    
    # Create async engine and session
    engine = create_async_engine(str(settings.DATABASE_URL))
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as db:
        try:
            # Create jobs
            jobs = []
            for i, job_data in enumerate(SAMPLE_JOBS):
                job_id = uuid.uuid4()  # Use UUID object, not string
                # Set created_at based on job index for variety
                created_at = datetime.now(timezone.utc) - timedelta(hours=i+1)
                
                job = Job(
                    id=job_id,
                    created_at=created_at,
                    completed_at=created_at + timedelta(minutes=3) if job_data["status"] == "ready" else None,
                    **job_data
                )
                db.add(job)
                jobs.append(job)
                print(f"  ✅ Created job: {job.url} (Status: {job.status})")
            
            await db.flush()  # Flush to get IDs
            
            # Create scrapers for ready jobs
            scrapers = []
            scraper_index = 0
            for job in jobs:
                if job.status == "ready" and scraper_index < len(SAMPLE_SCRAPERS):
                    scraper_data = SAMPLE_SCRAPERS[scraper_index]
                    scraper = Scraper(
                        id=uuid.uuid4(),  # Use UUID object
                        job_id=job.id,
                        scraper_code=scraper_data["code"],
                        code_version=scraper_data["code_version"],
                        execution_count=scraper_data["execution_count"],
                        average_execution_time=scraper_data["average_execution_time"],
                        last_execution_at=job.completed_at,
                        is_active=True,
                        created_at=job.completed_at
                    )
                    db.add(scraper)
                    scrapers.append(scraper)
                    scraper_index += 1
                    print(f"  🔧 Created scraper for job: {job.url}")
            
            await db.flush()
            
            # Create endpoints for ready jobs
            endpoints = []
            for job in jobs:
                if job.status == "ready":
                    endpoint = Endpoint(
                        id=uuid.uuid4(),  # Use UUID object
                        job_id=job.id,
                        endpoint_path=job.api_endpoint_path,
                        is_active=True,
                        access_count=10 + (len(endpoints) * 5),
                        last_accessed_at=job.completed_at + timedelta(minutes=30),
                        average_response_time=1200 + (len(endpoints) * 200),
                        success_rate=98 + len(endpoints),
                        created_at=job.completed_at + timedelta(seconds=30)
                    )
                    db.add(endpoint)
                    endpoints.append(endpoint)
                    print(f"  🌐 Created endpoint: {endpoint.endpoint_path}")
            
            # Commit all changes
            await db.commit()
            
            print(f"\n🎉 Seed data created successfully!")
            print(f"   📊 Jobs: {len(jobs)}")
            print(f"   🔧 Scrapers: {len(scrapers)}")
            print(f"   🌐 Endpoints: {len(endpoints)}")
            print(f"\n🔗 Ready API endpoints:")
            for endpoint in endpoints:
                print(f"   POST http://localhost:8000/generated{endpoint.endpoint_path}")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error creating seed data: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_seed_data())
