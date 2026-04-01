import os
import chromadb
from groq import Groq
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

# Load environment variables
load_dotenv()

class LegalAI:
    def __init__(self):
        # 1. Connect to our Local Vector Brain
        self.client = chromadb.PersistentClient(path="./legal_db")
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_collection(
            name="indian_law_kb", 
            embedding_function=self.embedding_fn
        )
        
        # 2. Setup Groq
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def analyze_clause(self, user_clause):
        print(f"\n[➔] Analyzing Clause: '{user_clause[:50]}...'")

        # 3. RETRIEVAL: Find relevant laws in our local DB
        results = self.collection.query(
            query_texts=[user_clause],
            n_results=2
        )
        relevant_law = results['documents'][0]

        # 4. AUGMENTATION & GENERATION: Ask Groq to compare
        prompt = f"""
        You are an expert Indian Legal AI. Compare the 'User Clause' against the 'Reference Law'.
        Determine if the clause is adversarial (unfair) or illegal under Indian Law.
        
        USER CLAUSE: {user_clause}
        REFERENCE LAW: {relevant_law}
        
        Provide a concise verdict (Legal/Illegal/Unfair) and a brief reason.
        """

        chat_completion = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )

        return chat_completion.choices[0].message.content

if __name__ == "__main__":
    ai = LegalAI()
    
    # Example: A common unfair employment clause
    test_clause = "The employee is strictly prohibited from joining any competitor in India for 3 years after leaving this company."
    
    verdict = ai.analyze_clause(test_clause)
    print("\n--- AI LEGAL VERDICT ---")
    print(verdict)