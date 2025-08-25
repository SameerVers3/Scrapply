#!/usr/bin/env python3
"""
Test script to validate syntax error fixing logic
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.agent import ScrapingAgent

def test_syntax_fix():
    agent = ScrapingAgent()
    
    # Test case 1: Truncated data.append
    broken_code = '''from playwright.async_api import async_playwright
import asyncio
import json
import time
from typing import Dict, Any, List

async def scrape_data(url: str) -> Dict[str, Any]:
    start_time = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            hackathons = await page.query_selector_all('.hackathon-card')
            data = []
            
            for hackathon in hackathons:
                date = await hackathon.query_selector('.date')
                status = await hackathon.query_selector('.status')
                title = await hackathon.query_selector('.title')
                description = await hackathon.query_selector('.description')
                tag = await hackathon.query_selector('.tag')
                
                data.append({
                    "date": await date.inner_text() if date else None,
                    "status": await status'''
    
    print("Testing syntax fix for truncated code...")
    fixed_code = agent._clean_generated_code(broken_code, "dynamic")
    
    # Try to compile the fixed code
    try:
        compile(fixed_code, '<test>', 'exec')
        print("✅ Fixed code compiles successfully!")
        print("Fixed code length:", len(fixed_code))
        print("Last 500 chars:", fixed_code[-500:])
        return True
    except SyntaxError as e:
        print(f"❌ Fixed code still has syntax error: {e}")
        print(f"Error at line {e.lineno}: {e.text}")
        return False

if __name__ == "__main__":
    success = test_syntax_fix()
    sys.exit(0 if success else 1)
