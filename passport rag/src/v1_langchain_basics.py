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
VERSION 1: LANGCHAIN BASICS (NO VECTOR DATABASE / NO RAG)
================================================================================
Workflow:
    Input
      ↓
    Prompt (ChatPromptTemplate)
      ↓
    LLM (ChatGoogleGenerativeAI / ChatGroq)
      ↓
    Output Parser (StrOutputParser)
      ↓
    Chain / Runnable (chain = prompt | llm | output_parser)
      ↓
    Output

Key Concepts to Explain to Lecturers:
1. Pure LangChain Workflow: Demonstrates the foundational LangChain Expression Language (LCEL).
2. Components Used:
   - Prompt Template: Formats the raw user input into a structured prompt.
   - LLM: Generates responses purely from pre-trained parametric weights.
   - Output Parser: Converts the raw AIMessage object into a clean Python string.
   - Runnable / Chain: Composes the components using the pipe operator (`|`).
3. Core Limitation (Why we need RAG):
   Because V1 has NO vector database or document retrieval, the LLM relies solely on
   its pre-trained training data. When asked about specific Indian administrative rules
   (like Section 17 registered rent agreements or Section 15 DL renewal cutoffs),
   it frequently gives generic, outdated, or hallucinated advice.
   This limitation motivates Version 2: RAG with FAISS!
================================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.llm_helper import get_llm

load_dotenv()


class SimpleLangChainBasics:
    """
    Version 1: Basic LangChain Workflow (Baseline without RAG).
    
    Implements: Input -> Prompt -> LLM -> Output Parser -> Chain/Runnable -> Output.
    Strictly NO vector store and NO document retrieval.
    """

    def __init__(self, api_key: str = None, provider: str = "auto", temperature: float = 0.0):
        self.api_key = api_key
        self.provider = provider
        self.temperature = temperature

        # 1. Prompt Template
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a general AI assistant answering questions about Indian citizen procedures.\n"
                "Answer the user's question using your general knowledge."
            ),
            ("human", "{question}")
        ])

        # 2. Output Parser
        self.output_parser = StrOutputParser()

    def run(self, question: str) -> Dict[str, Any]:
        """
        Executes the LangChain runnable chain:
        Input -> Prompt -> LLM -> Output Parser -> Output
        """
        try:
            # 3. LLM
            llm = get_llm(api_key=self.api_key, provider=self.provider, temperature=self.temperature)

            # 4. Chain / Runnable (LCEL Composition)
            chain = self.prompt | llm | self.output_parser

            # 5. Output
            answer = chain.invoke({"question": question})

        except Exception as e:
            # Fallback for offline demonstration if no API key is provided
            answer = (
                f"[V1 Baseline - Parametric LLM Response (No Retrieval)]\n\n"
                f"Question: '{question}'\n\n"
                f"Notice: Version 1 operates with NO vector database and NO document retrieval. "
                f"Without grounded MEA/MoRTH circulars, the LLM cannot verify statutory counter rules "
                f"(such as Sub-Registrar registration under Section 17, or the 1-year driving test cutoff). "
                f"To eliminate hallucinations and ground answers in official gazette circulars, proceed to Version 2 (FAISS RAG)!\n\n"
                f"(Error / Offline Details: {str(e)})"
            )

        return {
            "answer": answer,
            "version": "Version 1 - LangChain Basics (No Vector DB / No RAG)",
            "retrieved_docs": [],
            "context": "No retrieval performed in V1 (Pure Prompt -> LLM -> OutputParser chain)"
        }


def run_v1(question: str, api_key: str = None, provider: str = "auto") -> Dict[str, Any]:
    """Convenience helper to run Version 1."""
    system = SimpleLangChainBasics(api_key=api_key, provider=provider)
    return system.run(question)


if __name__ == "__main__":
    v1 = SimpleLangChainBasics()
    test_q = "Can I submit a notarized rent agreement for passport address proof?"
    print(f"Running V1 Baseline Query: '{test_q}'\n")
    res = v1.run(test_q)
    print("V1 Result:")
    print(res["answer"])
