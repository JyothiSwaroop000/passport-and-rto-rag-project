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
VERSION 3: RAG WITH CHROMADB (PERSISTENT VECTOR DB & RICH METADATA)
================================================================================
Workflow:
    Documents (citizendoc_rules.txt / .pdf)
      ↓
    Chunking (RecursiveCharacterTextSplitter)
      ↓
    Embeddings (FastEmbed / Gemini Embeddings)
      ↓
    ChromaDB (Persistent SQLite Disk Vector Database)
      ↓
    Retriever (with Metadata Filter: Source, Page, Document Type, Authority)
      ↓
    Prompt + Context
      ↓
    LLM (ChatGoogleGenerativeAI / ChatGroq)
      ↓
    Answer

Key Concepts to Explain to Lecturers:
1. FAISS vs. ChromaDB Difference:
   ┌─────────────────────┬──────────────────────────┬─────────────────────────────┐
   │ Feature             │ FAISS (Version 2)        │ ChromaDB (Version 3)        │
   ├─────────────────────┼──────────────────────────┼─────────────────────────────┤
   │ Type                │ Vector library (C++)     │ Full Vector Database        │
   │ Storage             │ In-Memory by default     │ Persistent on Disk (SQLite) │
   │ Metadata Filtering  │ Limited / external       │ Native SQL-like filters     │
   │ Collection Mgmt     │ Manual index files       │ Built-in CRUD collections   │
   │ Production Use      │ Raw vector similarity    │ Production document retrieval│
   └─────────────────────┴──────────────────────────┴─────────────────────────────┘

2. Metadata Attached to Chunks:
   - Source: "citizendoc_rules.pdf"
   - Page: 1 to 7 (1-indexed)
   - Document Type: "Official Statutory Guidelines"
   - Authority: Ministry of External Affairs (MEA) / Ministry of Road Transport (MoRTH)
   - Service Category: E.g., "Passport Address Proof", "Driving License Renewal"
   - Rejection Risk: High / Critical counter rejection traps
================================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma

from src.document_loader import load_and_chunk_documents
from src.embeddings import get_embedding_model
from src.llm_helper import get_llm, generate_extractive_answer

load_dotenv()

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")


class ChromaRAGSystem:
    """
    Version 3: Persistent RAG Pipeline using ChromaDB with Rich Metadata.
    """

    def __init__(
        self,
        api_key: str = None,
        k: int = 3,
        force_rebuild: bool = False,
        provider: str = "auto"
    ):
        self.api_key = api_key
        self.provider = provider
        self.k = k

        # 1. Embeddings Model
        self.embeddings = get_embedding_model(api_key=self.api_key)

        # 2. ChromaDB Vector Store
        self.vector_store = self._load_or_build_collection(force_rebuild)

    def _load_or_build_collection(self, force_rebuild: bool) -> Chroma:
        """Loads persistent ChromaDB or creates and populates it from chunks."""
        if not force_rebuild and os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
            try:
                store = Chroma(
                    collection_name="citizendoc_rules",
                    embedding_function=self.embeddings,
                    persist_directory=CHROMA_DIR
                )
                if store._collection.count() > 0:
                    return store
            except Exception:
                pass

        # Load fresh chunks with rich metadata
        chunks = load_and_chunk_documents()
        store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name="citizendoc_rules",
            persist_directory=CHROMA_DIR
        )
        return store

    def retrieve(self, query: str, filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Finds top-k documents matching the query, with optional metadata filtering.
        Example filter: {"document_type": "Official Statutory Guidelines"} or {"authority": "..."}
        """
        if filter_dict:
            return self.vector_store.similarity_search(query, k=self.k, filter=filter_dict)
        return self.vector_store.similarity_search(query, k=self.k)

    def run(self, question: str, filter_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Full V3 RAG Pipeline Execution with Metadata Tracking.
        """
        retrieved_docs = self.retrieve(question, filter_dict=filter_dict)

        # Build context citing metadata fields (Source, Page, Document Type, Authority)
        context = "\n\n---\n\n".join(
            f"[Source: {doc.metadata.get('source')} | Page: {doc.metadata.get('page')} | "
            f"Type: {doc.metadata.get('document_type')} | Authority: {doc.metadata.get('authority')}]\n"
            f"{doc.page_content}"
            for doc in retrieved_docs
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an assistant for Indian citizen documents (Passport Seva & Parivahan RTO).\n"
                "Answer using ONLY the provided verified context below.\n"
                "Cite the source, page number, and issuing authority for each rule stated.\n"
                "If not mentioned in the context, say that you do not have verified official guidelines."
            ),
            (
                "human",
                "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
            )
        ])

        try:
            llm = get_llm(api_key=self.api_key, provider=self.provider)
            chain = prompt | llm | StrOutputParser()
            answer = chain.invoke({"context": context, "question": question})
        except Exception:
            answer = generate_extractive_answer(question, retrieved_docs)

        return {
            "answer": answer,
            "version": "Version 3 - RAG with ChromaDB (Persistent DB & Metadata)",
            "retrieved_docs": retrieved_docs,
            "context": context
        }


def run_v3(question: str, api_key: str = None, provider: str = "auto", filter_dict: dict = None) -> Dict[str, Any]:
    """Convenience helper to run Version 3."""
    system = ChromaRAGSystem(api_key=api_key, provider=provider)
    return system.run(question, filter_dict=filter_dict)


if __name__ == "__main__":
    v3 = ChromaRAGSystem(force_rebuild=True)
    res = v3.run("Can I use a DigiLocker driving license?")
    print("V3 Result:\n", res["answer"][:350])
    print("\nMetadata on retrieved chunk 0:", res["retrieved_docs"][0].metadata if res["retrieved_docs"] else "None")
