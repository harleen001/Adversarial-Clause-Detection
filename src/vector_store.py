import json
import chromadb
from chromadb.utils import embedding_functions

class LegalVectorBrain:
    def __init__(self):
        # 1. Initialize the local database (This creates a folder named 'legal_db')
        self.client = chromadb.PersistentClient(path="./legal_db")
        
        # 2. Use a FREE HuggingFace embedding model (runs on your CPU)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # 3. Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name="indian_law_kb",
            embedding_function=self.embedding_fn
        )

    def upload_to_db(self):
        with open("data/processed/cleaned_chunks.json", "r", encoding='utf-8') as f:
            chunks = json.load(f)

        print(f"[➔] Vectorizing {len(chunks)} chunks... this might take a minute.")
        
        self.collection.add(
            ids=[c['id'] for c in chunks],
            documents=[c['text'] for c in chunks],
            metadatas=[{"source": c['source']} for c in chunks]
        )
        print("[✔] Success! Your Local Legal Brain is ready.")

if __name__ == "__main__":
    brain = LegalVectorBrain()
    brain.upload_to_db()    