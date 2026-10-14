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
VERSION 2: RAG WITH FAISS (BASIC IN-MEMORY VECTOR RETRIEVAL)
================================================================================
Workflow:
    Documents (citizendoc_rules.txt / .pdf)
      ↓
    Document Loader (load_documents)
      ↓
    Text Splitter (RecursiveCharacterTextSplitter)
      ↓
    Embeddings (FastEmbed / Gemini Embeddings)
      ↓
    FAISS (In-Memory Vector Store)
      ↓
    Retriever (similarity_search / as_retriever)
      ↓
    Prompt + Context (ChatPromptTemplate with {context} & {question})
      ↓
    LLM (ChatGoogleGenerativeAI / ChatGroq)
      ↓
    Answer

Key Concepts to Explain to Lecturers:
1. What is FAISS? Facebook AI Similarity Search. An in-memory C++ library for
   high-speed dense vector similarity calculations (using inner product or L2 distance).
2. How V2 Solves V1's Flaws:
   Instead of guessing, the system retrieves the top-k chunks from the official manual
   and feeds them into the prompt. The LLM is instructed to answer ONLY from this context.
3. Limitation of FAISS (Why we upgrade to V3 ChromaDB):
   FAISS is strictly an in-memory index; it lacks native database features, persistent
   storage out-of-the-box, and cannot easily perform SQL-style metadata filtering
   (such as filtering strictly by Authority or Document Type).
================================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

from src.document_loader import load_and_chunk_documents
from src.embeddings import get_embedding_model
from src.llm_helper import get_llm, generate_extractive_answer

load_dotenv()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index")


class FaissRAGSystem:
    """
    Version 2: Basic RAG Pipeline using FAISS.
    """

    def __init__(
        self,
        api_key: str = None,
        force_rebuild: bool = False,
        k: int = 3,
        provider: str = "auto"
    ):
        self.api_key = api_key
        self.provider = provider
        self.k = k

        # 1. Embeddings Model
        self.embeddings = get_embedding_model(api_key=self.api_key)

        # 2. Vector Store (FAISS)
        self.vector_store = self._load_or_build_index(force_rebuild)

        # 3. Retriever
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": self.k})

    def _load_or_build_index(self, force_rebuild: bool) -> FAISS:
        """Loads FAISS index from disk if cached, or builds fresh from document chunks."""
        index_file = os.path.join(INDEX_DIR, "index.faiss")
        if not force_rebuild and os.path.exists(index_file):
            try:
                return FAISS.load_local(INDEX_DIR, self.embeddings, allow_dangerous_deserialization=True)
            except Exception:
                pass

        # Step: Load and chunk documents
        chunks = load_and_chunk_documents()
        # Step: Build FAISS vector store
        store = FAISS.from_documents(chunks, self.embeddings)
        os.makedirs(INDEX_DIR, exist_ok=True)
        store.save_local(INDEX_DIR)
        return store

    def retrieve(self, query: str) -> List[Document]:
        """Finds top-k documents matching the query using vector similarity."""
        return self.vector_store.similarity_search(query, k=self.k)

    def run(self, question: str) -> Dict[str, Any]:
        """
        Full V2 RAG Pipeline Execution:
        Retrieve Context -> Format Prompt -> LLM -> Parse Answer
        """
        retrieved_docs = self.retrieve(question)

        # Build context string with citations
        context = "\n\n---\n\n".join(
            f"[Source: {doc.metadata.get('source')} | Page: {doc.metadata.get('page')} | Authority: {doc.metadata.get('authority')}]\n"
            f"{doc.page_content}"
            for doc in retrieved_docs
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an assistant for Indian citizen documents (Passport Seva & Parivahan RTO).\n"
                "Answer using ONLY the provided verified context below.\n"
                "Explicitly cite the source, authority, and page number for your statements.\n"
                "If the information is not present in the context, state that you do not have official guidance."
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
            # Fallback to extractive citations if API key is not present
            answer = generate_extractive_answer(question, retrieved_docs)

        return {
            "answer": answer,
            "version": "Version 2 - RAG with FAISS (In-Memory Similarity Search)",
            "retrieved_docs": retrieved_docs,
            "context": context
        }


def run_v2(question: str, api_key: str = None, provider: str = "auto") -> Dict[str, Any]:
    """Convenience helper to run Version 2."""
    system = FaissRAGSystem(api_key=api_key, provider=provider)
    return system.run(question)


if __name__ == "__main__":
    v2 = FaissRAGSystem(force_rebuild=True)
    res = v2.run("Is a notarized rent agreement accepted for passport?")
    print("V2 Result:\n", res["answer"][:350])
    print("\nRetrieved Chunks:", len(res["retrieved_docs"]))
