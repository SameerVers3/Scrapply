from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.processor import ScrapingProcessor

async def get_processor(db: AsyncSession = Depends(get_db)) -> ScrapingProcessor:
    """Dependency to get scraping processor with database session"""
    return ScrapingProcessor(db)
