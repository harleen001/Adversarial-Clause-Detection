import os
from langchain_community.document_loaders import CSVLoader
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_pinecone import PineconeVectorStore # type: ignore
from dotenv import load_dotenv

load_dotenv()

def ingest_kaggle_data(file_path):
    # 1. Load your Kaggle CSV
    loader = CSVLoader(file_path=file_path, encoding="utf-8")
    data = loader.load()

    # 2. Use a FREE local embedding model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 3. Push to Pinecone
    index_name = "indian-legal-index"
    vectorstore = PineconeVectorStore.from_documents(
        data, embeddings, index_name=index_name
    )
    print("Kaggle Data Successfully Indexed!")

# Usage: ingest_kaggle_data("data/raw/indian_legal_clauses.csv")