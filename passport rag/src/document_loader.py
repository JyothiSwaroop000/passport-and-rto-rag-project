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
MODULE: Document Loader & Text Splitter
Purpose: Loads regulatory documents and splits them into chunks with metadata
(source, page, document_type, authority, service_category, rejection_risk).
================================================================================
"""

import os
import re
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DEFAULT_TXT = os.path.join(DATA_DIR, "citizendoc_rules.txt")
DEFAULT_PDF = os.path.join(DATA_DIR, "citizendoc_rules.pdf")


def load_documents(file_path: str = None) -> List[Document]:
    """
    Step 1: Document Loading with Rich Regulatory Metadata.
    
    Reads the official 7-page regulatory handbook and creates LangChain Document
    objects with 1-indexed page numbers and explicit metadata:
    - source: filename
    - page: 1 to 7 (1-indexed for accurate citation)
    - document_type: Official Statutory Guidelines
    - authority: Ministry of External Affairs (MEA) or Ministry of Road Transport (MoRTH)
    - service_category: Specific service (e.g., Passport Address Proof, Tatkaal, DL Renewal)
    - rejection_risk: Counter rejection risk level
    """
    path = file_path or (DEFAULT_TXT if os.path.exists(DEFAULT_TXT) else DEFAULT_PDF)
    documents: List[Document] = []

    # If text file exists, parse page markers '--- [PAGE X] ---'
    if os.path.exists(DEFAULT_TXT):
        with open(DEFAULT_TXT, "r", encoding="utf-8") as f:
            full_text = f.read()

        pages_raw = full_text.split("--- [PAGE ")
        for p in pages_raw:
            if not p.strip():
                continue
            match = re.match(r"^(\d+)\]\s*---\n?(.*)", p, re.DOTALL)
            if match:
                page_num = int(match.group(1))
                page_content = match.group(2).strip()

                # Extract regulatory metadata from page header
                auth_match = re.search(r"Authority:\s*([^\n]+)", page_content)
                cat_match = re.search(r"Service Category:\s*([^\n]+)", page_content)
                risk_match = re.search(r"Rejection Risk Tier:\s*([^\n]+)", page_content)

                authority = auth_match.group(1).strip() if auth_match else "Government of India"
                category = cat_match.group(1).strip() if cat_match else "Citizen Services"
                risk = risk_match.group(1).strip() if risk_match else "HIGH / COUNTER REJECTION RISK"

                doc = Document(
                    page_content=page_content,
                    metadata={
                        "source": "citizendoc_rules.pdf",
                        "page": page_num,
                        "document_type": "Official Statutory Guidelines",
                        "authority": authority,
                        "service_category": category,
                        "rejection_risk": risk
                    }
                )
                documents.append(doc)

    elif os.path.exists(path) and path.endswith(".pdf"):
        # Fallback to PyPDFLoader if only PDF is available
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(path)
        pdf_docs = loader.load()
        for idx, p_doc in enumerate(pdf_docs, start=1):
            p_doc.metadata["page"] = idx  # Normalize to 1-indexed
            p_doc.metadata["document_type"] = "Official Statutory Guidelines"
            p_doc.metadata["source"] = "citizendoc_rules.pdf"
            documents.append(p_doc)

    return documents


def load_and_chunk_documents(
    file_path: str = None,
    chunk_size: int = 750,
    chunk_overlap: int = 150
) -> List[Document]:
    """
    Step 2: Text Chunking.
    
    Splits documents into smaller overlapping chunks:
    - chunk_size (750 chars): Balances semantic completeness and retrieval precision.
    - chunk_overlap (150 chars): Preserves context across chunk boundaries so rules
      spanning boundaries are not split and lost.
    """
    raw_docs = load_documents(file_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n### ", "\n\n", "\n", ". ", " "]
    )

    chunks = text_splitter.split_documents(raw_docs)
    return chunks


if __name__ == "__main__":
    chunks = load_and_chunk_documents()
    print(f"Total chunks created: {len(chunks)}")
    if chunks:
        print("\n--- Sample Chunk 1 Metadata ---")
        print(chunks[0].metadata)
        print("\n--- Sample Chunk 1 Content Snippet ---")
        print(chunks[0].page_content[:250])
