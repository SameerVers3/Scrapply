import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import time

def scrape_data(url: str) -> Dict[str, Any]:
    data = []
    metadata = {"source": url}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        listings = soup.find_all('div', class_='listing')

        for listing in listings:
            title = listing.find('h2').get_text(strip=True) if listing.find('h2') else 'N/A'
            description = listing.find('p').get_text(strip=True) if listing.find('p') else 'N/A'
            data.append({
                "title": title,
                "description": description
            })

        metadata["total_listings"] = len(data)

    except requests.exceptions.RequestException as e:
        metadata["error"] = str(e)
    finally:
        time.sleep(1)

    return {"data": data, "metadata": metadata}

result = scrape_data("https://www.scrapethissite.com/pages/")
print(result)
