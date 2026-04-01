import requests
from bs4 import BeautifulSoup
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

class LegalDataIngestor:
    def __init__(self):
        self.base_url = "https://www.indiacode.nic.in"
        self.search_endpoint = f"{self.base_url}/handle/123456789/1/simple-search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Project: AdversarialClauseDetection/1.0; Contact: dev@firm.com)"
        }
        self.storage = []

    def fetch_act_metadata(self, query: str = "Contract Act") -> List[Dict]:
        """Fetch a list of Acts matching the query to get their unique handles."""
        print(f"[INFO] Searching for: {query}...")
        params = {"query": query, "itemsperpage": 10}
        
        try:
            response = requests.get(self.search_endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            acts = []
            # Selector for the search result table
            table = soup.find('table', {'class': 'table'})
            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) > 2:
                    link = cols[1].find('a')['href']
                    acts.append({
                        "title": cols[1].text.strip(),
                        "handle": link,
                        "date": cols[0].text.strip()
                    })
            return acts
        except Exception as e:
            print(f"[ERROR] Metadata fetch failed: {e}")
            return []

    def scrape_full_text(self, act_meta: Dict):
        """Navigates to the Act page and extracts raw text."""
        url = f"{self.base_url}{act_meta['handle']}"
        print(f"[PROCESS] Ingesting: {act_meta['title']}")
        
        try:
            res = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # Target the main body where the Act content resides
            # Note: Many Indian sites use specific IDs for the viewer container
            content = soup.find('div', {'id': 'view_section'}) 
            raw_text = content.get_text(separator="\n") if content else "Content Not Found"

            self.storage.append({
                "metadata": act_meta,
                "raw_content": raw_text,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            print(f"[ERROR] Failed to scrape {act_meta['title']}: {e}")

    def save_to_staging(self, filename="raw_legal_dump.json"):
        """Saves ingested data to a local JSON file for the cleaning phase."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.storage, f, ensure_ascii=False, indent=4)
        print(f"[SUCCESS] Stored {len(self.storage)} documents in {filename}")

# --- Execution ---
if __name__ == "__main__":
    ingestor = LegalDataIngestor()
    
    # Target high-impact laws for employment contracts
    target_queries = ["Contract Act", "Constitution of India", "Industrial Disputes"]
    
    all_acts = []
    for q in target_queries:
        all_acts.extend(ingestor.fetch_act_metadata(q))

    # Parallel processing for efficiency
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(ingestor.scrape_full_text, all_acts)

    ingestor.save_to_staging()