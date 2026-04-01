import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class LegalDataIngestor:
    def __init__(self):
        # Switching to Indian Kanoon - much more stable for dev projects
        self.base_url = "https://indiankanoon.org"
        self.output_dir = os.path.join("data", "raw")
        os.makedirs(self.output_dir, exist_ok=True)

    async def scrape_kanoon(self, query: str):
        async with async_playwright() as p:
            # Headless=True for speed, but you can set to False to watch
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            print(f"[➔] Querying Indian Kanoon: {query}")
            search_url = f"{self.base_url}/search/?formInput={query.replace(' ', '+')}"
            
            await page.goto(search_url, wait_until="networkidle")

            # Extract result links
            # Indian Kanoon search results are usually in div.result_title
            acts_data = await page.evaluate("""() => {
                const results = [];
                const items = document.querySelectorAll('.result_title a');
                items.forEach(item => {
                    results.push({
                        title: item.innerText.trim(),
                        link: item.getAttribute('href')
                    });
                });
                return results;
            }""")

            print(f"   [+] Found {len(acts_data)} results. Ingesting top matches...")
            
            final_results = []
            # We take the top 3 relevant results
            for act in acts_data[:3]:
                doc_url = f"{self.base_url}{act['link']}"
                print(f"      [✓] Downloading: {act['title']}")
                
                await page.goto(doc_url, wait_until="domcontentloaded")
                
                # Indian Kanoon puts the main text in a div called 'judgement' or 'doc_body'
                content = await page.evaluate("""() => {
                    const doc = document.querySelector('.judgement') || document.querySelector('.doc_body') || document.body;
                    return doc.innerText;
                }""")
                
                final_results.append({
                    "metadata": act,
                    "content": content,
                    "source": "Indian Kanoon",
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(1) # Be polite to their servers

            await browser.close()
            return final_results

    def save_data(self, data, filename):
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n[✔] Project Ingestion Complete!")
        print(f"[✔] Total legal docs stored: {len(data)}")
        print(f"[✔] File Location: {path}")

async def main():
    ingestor = LegalDataIngestor()
    # High-value targets for your 'Adversarial Clause' AI
    queries = ["Indian Contract Act 1872", "Section 27 Contract Act", "Constitution of India"]
    
    all_results = []
    for q in queries:
        batch = await ingestor.scrape_kanoon(q)
        all_results.extend(batch)
    
    ingestor.save_data(all_results, "legal_knowledge_base.json")

if __name__ == "__main__":
    asyncio.run(main())