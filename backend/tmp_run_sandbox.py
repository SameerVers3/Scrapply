import asyncio
from app.core.sandbox import SecureSandbox

refined_code = '''import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import time

class TimeoutException(Exception): pass

def scrape_data(url: str) -> Dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    data = []
    metadata = {"pages_scraped": 0, "total_items": 0, "errors": []}
    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        product_elements = soup.select('a.footer-category-link')
        for product_element in product_elements:
            try:
                product_name = product_element.text.strip()
                data.append({"product_name": product_name})
            except Exception as e:
                metadata["errors"].append(str(e))
        metadata["pages_scraped"] += 1
        metadata["total_items"] = len(data)
    except requests.exceptions.RequestException as e:
        metadata["errors"].append(str(e))
    except TimeoutException as e:
        metadata["errors"].append("Execution timeout")
    return {"data": data, "metadata": metadata}
'''

async def main():
    sb = SecureSandbox()
    res = await sb.execute_scraper(refined_code, 'https://codewithsadee.github.io/anon-ecommerce-website/')
    print('RESULT:')
    print(res)

asyncio.run(main())
