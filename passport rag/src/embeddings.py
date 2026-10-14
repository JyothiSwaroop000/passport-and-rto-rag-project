"""
================================================================================
PROJECT TITLE: CitizenDoc: AI-Powered Passport Seva & Parivahan RTO Rejection Preventer
PROBLEM STATEMENT:
    Millions of Indian citizens visit Passport Seva Kendras (PSK) and Regional
    Transport Offices (RTO) each year, facing immediate counter rejections due to
    obscure statutory rules (notarized vs registered rent agreements, cooperative
    bank passbooks, Tatkaal name spellings, 1-year DL expiry cutoff, Form 28 chassis imprint).
PROPOSED SOLUTION:
    A 4-stage progressive RAG system (V1 LangChain Basics -> V2 FAISS -> V3 ChromaDB
    -> V4 FlashRank Reranker) grounded in verified MEA & MoRTH official circulars,
    deployed with Streamlit and monitored via LangSmith.
TARGET USERS:
    Passport applicants, vehicle owners, motorists, and Citizen Facilitation Centers (CSC).
DATA / DOCUMENTS TO BE USED:
    CitizenDoc Official Regulatory Compliance Handbook (7 chapters, .txt and .pdf).
EXPECTED OUTPUT:
    Verified compliance advisories citing official authority and page numbers,
    counter rejection risk alerts, interactive pre-screening, and LangSmith tracing.
================================================================================
MODULE: Embeddings Factory
Purpose: Converts text passages into dense numerical vectors for semantic search.
Supports:
1. Google Gemini Embeddings (models/embedding-001) via API key.
2. Local FastEmbed (BAAI/bge-small-en-v1.5) via ONNX Runtime (free, fast, offline).
================================================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_embedding_model(api_key: str = None):
    """
    Returns an embedding model for vector generation:
    - If a valid Google Gemini key is provided (and NOT a Groq gsk_ key): uses GoogleGenerativeAIEmbeddings.
    - Default/Fallback: uses local FastEmbedEmbeddings (BAAI/bge-small-en-v1.5).
      FastEmbed runs entirely on CPU using ONNX Runtime with zero API key requirement,
      making it ideal for free, fast, offline academic demonstrations.
    """
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()
    # Ensure a Groq key (starting with gsk_) is NEVER treated as a Google key
    if api_key and not api_key.startswith("gsk_") and api_key != "your-gemini-api-key-here":
        gemini_key = api_key

    if gemini_key and not gemini_key.startswith("gsk_") and gemini_key != "your-gemini-api-key-here":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=gemini_key
            )
        except Exception:
            pass

    # Free, local ONNX embedding model (runs completely offline on CPU, <10ms)
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


if __name__ == "__main__":
    emb = get_embedding_model()
    test_vec = emb.embed_query("Passport proof of address requirement")
    print(f"Embedding Model Initialized Successfully! Vector Dimensions: {len(test_vec)}")
