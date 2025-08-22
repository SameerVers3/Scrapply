import asyncio
from app.core.sandbox import SecureSandbox

refined_code = '''import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_data(url: str) -> Dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    data = []
    metadata = {"pages_scraped": 0, "total_items": 0, "errors": []}
    try:
        for page in range(1, 4):  # Handle pagination (max 3 pages)
            time.sleep(1)  # Add rate limiting (1 second between requests)
            response = requests.get(url, headers=headers, params={"page": page}, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select("li.col-md-3")
            for item in items:
                try:
                    student_id, student_name = item.text.split(" ", 1)
                    data.append({"student_id": student_id, "student_name": student_name})
                except ValueError:
                    metadata["errors"].append(f"Failed to parse item: {item}")
            metadata["pages_scraped"] += 1
            metadata["total_items"] += len(items)
    except requests.RequestException as e:
        metadata["errors"].append(str(e))
    except Exception as e:
        metadata["errors"].append("Unknown error: " + str(e))
    return {"data": data, "metadata": metadata}
'''


async def main():
    sb = SecureSandbox()
    res = await sb.execute_scraper(refined_code, 'https://nu.edu.pk/Campus/Karachi/DeanLists/')
    print('RESULT:')
    print(res)

asyncio.run(main())
