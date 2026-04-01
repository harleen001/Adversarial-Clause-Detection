import json
import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

class LegalDataCleaner:
    def __init__(self):
        self.input_file = "data/raw/legal_knowledge_base.json"
        self.output_dir = "data/processed"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # This is the industry standard for RAG chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " "]
        )

    def clean_text(self, text):
        """Removes common Indian Kanoon/Legal website noise."""
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        # Remove 'Cites X docs' or 'Cited by Y docs' noise
        text = re.sub(r'Cites \d+ docs.*?\n', '', text)
        text = re.sub(r'Cited by \d+ docs.*?\n', '', text)
        # Remove 'Full Context' or 'Download PDF' links
        text = re.sub(r'Get this document in PDF.*?\n', '', text)
        return text.strip()

    def process_kb(self):
        with open(self.input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        processed_chunks = []
        # We use enumerate(raw_data) to get a unique doc_idx for each entry
        for doc_idx, doc in enumerate(raw_data):
            clean_body = self.clean_text(doc['content'])
            chunks = self.text_splitter.split_text(clean_body)
            
            for i, chunk in enumerate(chunks):
                # We add doc_idx to the ID to ensure "Entire Act_1" from file A 
                # is different from "Entire Act_1" from file B
                processed_chunks.append({
                    "id": f"doc_{doc_idx}_chunk_{i}", 
                    "source": doc['metadata']['title'],
                    "text": chunk,
                    "timestamp": doc['timestamp']
                })

        output_path = os.path.join(self.output_dir, "cleaned_chunks.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_chunks, f, indent=4)
        
        print(f"[✔] Cleaning Complete! Generated {len(processed_chunks)} unique AI-ready chunks.")

if __name__ == "__main__":
    cleaner = LegalDataCleaner()
    cleaner.process_kb()