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
MODULE: LLM Helper
Purpose: Initializes chat language models across providers (Gemini, Groq, or
grounded extractive fallback for offline testing).
================================================================================
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()


def get_llm(
    api_key: Optional[str] = None,
    provider: str = "auto",
    temperature: float = 0.0,
    model_name: Optional[str] = None
):
    """
    Returns an initialized LangChain Chat LLM.
    
    Supported Providers:
    1. Google Gemini (ChatGoogleGenerativeAI - gemini-1.5-flash)
    2. Groq (ChatGroq - llama-3.1-8b-instant [Ultra-fast ~1s] or llama-3.3-70b-versatile)
    """
    # Clean and auto-detect API key
    clean_key = (api_key or "").strip()
    if clean_key.startswith("gsk_"):
        provider = "groq"
        groq_key = clean_key
    elif provider == "groq":
        groq_key = clean_key or os.getenv("GROQ_API_KEY", "").strip()
    else:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()

    gemini_key = clean_key if provider == "gemini" else os.getenv("GOOGLE_API_KEY", "").strip()

    # 1. Use Google Gemini if selected or available
    if provider == "gemini" or (provider == "auto" and gemini_key and gemini_key != "your-gemini-api-key-here"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name or "gemini-1.5-flash",
            temperature=temperature,
            google_api_key=gemini_key,
            request_timeout=25.0
        )

    # 2. Use Groq if selected or available
    if (provider == "groq" or provider == "auto") and groq_key and groq_key != "your-groq-api-key-here":
        from langchain_groq import ChatGroq
        selected_model = model_name or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        return ChatGroq(
            model=selected_model,
            temperature=temperature,
            groq_api_key=groq_key,
            max_tokens=350,
            request_timeout=10.0,
            max_retries=1
        )

    raise ValueError(
        "No active API Key found for online LLM synthesis. "
        "Please provide GOOGLE_API_KEY or GROQ_API_KEY in .env or via the web interface."
    )


def generate_extractive_answer(query: str, documents: List[Document]) -> str:
    """
    Offline Grounded Advisory Fallback:
    Synthesizes a structured, cited answer directly from retrieved passages
    when running without external API keys or during network outages.
    Ensures 100% adherence to verified text with explicit citations.
    """
    if not documents:
        return "No relevant information found in the official regulatory documents."

    parts = []
    for doc in documents[:3]:
        page = doc.metadata.get("page", 1)
        auth = doc.metadata.get("authority", "Government of India")
        category = doc.metadata.get("service_category", "Citizen Services")
        risk = doc.metadata.get("rejection_risk", "HIGH")
        
        parts.append(
            f"🏛️ **[{auth} | {category} | Page {page} | Risk Level: {risk}]**\n\n"
            f"{doc.page_content.strip()}"
        )

    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    print("LLM Helper module loaded successfully.")
