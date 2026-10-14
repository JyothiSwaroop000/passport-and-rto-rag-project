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
EVALUATION BENCHMARK DATASET (20 STANDARDIZED CITIZEN INQUIRIES)
Contains 20 realistic citizen inquiries covering Passport Seva (MEA) and
Parivahan RTO (MoRTH) compliance, expected page citations, and key facts.
Used to benchmark V2 (FAISS) vs V3 (ChromaDB) vs V4 (FlashRank Reranking).
================================================================================
"""

from typing import List, Dict, Any

EVALUATION_QUESTIONS: List[Dict[str, Any]] = [
    # --- CHAPTER 1: PASSPORT PROOF OF ADDRESS & REJECTION TRAPS ---
    {
        "id": "Q1",
        "category": "Passport Address Proof",
        "service": "Passport (MEA)",
        "expected_page": 1,
        "question": "Can I submit a notarized rent agreement on Rs 100 stamp paper as proof of address for my passport application?",
        "key_facts": ["registered rent agreement", "sub-registrar", "section 17", "notarized", "rejected"]
    },
    {
        "id": "Q2",
        "category": "Passport Address Proof",
        "service": "Passport (MEA)",
        "expected_page": 1,
        "question": "Which bank passbooks are accepted as address proof for passport and what endorsement is required?",
        "key_facts": ["scheduled public sector", "scheduled private sector", "photograph", "stamped", "branch manager"]
    },
    {
        "id": "Q3",
        "category": "Passport Address Proof",
        "service": "Passport (MEA)",
        "expected_page": 1,
        "question": "What is the maximum validity age for electricity and water bills submitted as passport address proof?",
        "key_facts": ["last 2 months", "2 billing cycles", "utility", "present address"]
    },

    # --- CHAPTER 2: DOB & NON-ECR STATUS ---
    {
        "id": "Q4",
        "category": "Passport DOB Rules",
        "service": "Passport (MEA)",
        "expected_page": 2,
        "question": "Is a birth certificate still mandatory for passport applicants born on or after 26 January 1989?",
        "key_facts": ["relaxed", "december 2016", "pan card", "aadhaar", "matriculation"]
    },
    {
        "id": "Q5",
        "category": "Passport Non-ECR Status",
        "service": "Passport (MEA)",
        "expected_page": 2,
        "question": "What document is required to qualify for Non-ECR status and what restriction does ECR status impose?",
        "key_facts": ["matriculation", "10th standard pass certificate", "18 notified countries", "emigration check"]
    },
    {
        "id": "Q6",
        "category": "Passport Non-ECR Status",
        "service": "Passport (MEA)",
        "expected_page": 2,
        "question": "Can income tax assessment orders be used to qualify for Non-ECR passport status?",
        "key_facts": ["income tax payers", "assessment orders", "last 1 year", "non-ecr"]
    },

    # --- CHAPTER 3: TATKAAL PASSPORT SCHEME ---
    {
        "id": "Q7",
        "category": "Tatkaal Passport Matrix",
        "service": "Passport (MEA)",
        "expected_page": 3,
        "question": "How many documents are mandatory for an adult Tatkaal passport application from the approved list?",
        "key_facts": ["three", "3 documents", "13 documents", "aadhaar", "dispatch"]
    },
    {
        "id": "Q8",
        "category": "Tatkaal Passport Matrix",
        "service": "Passport (MEA)",
        "expected_page": 3,
        "question": "What happens if there is a minor spelling discrepancy between the 3 documents submitted under Tatkaal?",
        "key_facts": ["exact", "consistency", "spelling", "tatkaal to normal", "character-by-character"]
    },
    {
        "id": "Q9",
        "category": "Tatkaal Passport Matrix",
        "service": "Passport (MEA)",
        "expected_page": 3,
        "question": "Is a Verification Certificate from a Joint Secretary (Annexure F) still mandatory for normal citizens applying for Tatkaal?",
        "key_facts": ["annexure e", "standard affidavit", "no longer mandatory", "annexure f"]
    },

    # --- CHAPTER 4: NAME CHANGE & LOST PASSPORT ---
    {
        "id": "Q10",
        "category": "Passport Name Change",
        "service": "Passport (MEA)",
        "expected_page": 4,
        "question": "What is mandatory for a major name change in a passport versus a minor spelling correction?",
        "key_facts": ["two original newspaper", "local vernacular", "national english", "gazette notification"]
    },
    {
        "id": "Q11",
        "category": "Passport Name Change",
        "service": "Passport (MEA)",
        "expected_page": 4,
        "question": "Is a marriage certificate mandatory for a woman to change her surname in passport after marriage?",
        "key_facts": ["no longer mandatory", "annexure d", "self-declaration", "spouse's passport"]
    },
    {
        "id": "Q12",
        "category": "Passport Lost & Damaged",
        "service": "Passport (MEA)",
        "expected_page": 4,
        "question": "What documents are required to reissue a lost passport and can it be processed under Tatkaal?",
        "key_facts": ["police report", "ncr", "fir", "annexure f", "cannot be processed under tatkaal"]
    },

    # --- CHAPTER 5: DRIVING LICENSE RULES ---
    {
        "id": "Q13",
        "category": "Driving License Conversion",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 5,
        "question": "What is the minimum waiting period and maximum validity of a Learner's License before booking a permanent DL driving test?",
        "key_facts": ["minimum of 30 days", "180 days", "6 months", "form 3", "driving test"]
    },
    {
        "id": "Q14",
        "category": "Driving License Renewal",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 5,
        "question": "What is the penalty rule if a driving license is expired for more than 1 year under Section 15 of the MV Act?",
        "key_facts": ["expired for more than one year", "re-test", "practical driving test", "section 15"]
    },
    {
        "id": "Q15",
        "category": "Driving License Renewal",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 5,
        "question": "When is a Form 1A medical certificate mandatory for private non-transport driving license renewal?",
        "key_facts": ["form 1a", "medical certificate", "above 40 years", "registered medical practitioner"]
    },

    # --- CHAPTER 6: DIGILOCKER & CMVR ENFORCEMENT ---
    {
        "id": "Q16",
        "category": "DigiLocker CMVR Rule 139",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 6,
        "question": "Can traffic police legally demand physical original DL and RC if presented on DigiLocker or mParivahan?",
        "key_facts": ["rule 139", "cmvr", "legally valid", "cannot demand physical", "mparivahan"]
    },
    {
        "id": "Q17",
        "category": "DigiLocker CMVR Rule 139",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 6,
        "question": "Are screenshots or WhatsApp PDF images of a driving license legally valid during traffic police checking?",
        "key_facts": ["screenshots", "not accepted", "digilocker", "mparivahan", "digital signature"]
    },
    {
        "id": "Q18",
        "category": "DigiLocker CMVR Rule 139",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 6,
        "question": "How do enforcement officers impound a digital driving license for dangerous driving or red light violations?",
        "key_facts": ["electronic impounding", "e-challan", "sarathi database", "physical confiscation not required"]
    },

    # --- CHAPTER 7: RTO INTERSTATE VEHICLE TRANSFER & NOC ---
    {
        "id": "Q19",
        "category": "RTO Vehicle NOC",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 7,
        "question": "What is the critical chassis number requirement on Form 28 when applying for interstate vehicle NOC?",
        "key_facts": ["form 28 in triplicate", "pencil print", "chassis number", "pencil imprint", "smudged"]
    },
    {
        "id": "Q20",
        "category": "RTO Vehicle Transfer",
        "service": "Driving License & RTO (MoRTH)",
        "expected_page": 7,
        "question": "Which forms are required for ownership transfer upon vehicle sale and what is the submission timeline?",
        "key_facts": ["form 29", "notice of transfer", "form 30", "report of transfer", "14 days"]
    }
]
