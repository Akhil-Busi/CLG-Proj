#app/services/admin_brain.py
"""
Administrator Brain Service
============================
Specialized brain for handling administrative and logistical queries.

Features:
- Hardcoded data: Bus routes, faculty info, fees, etc.
- RAG-based: Placements, exam procedures, hostel rules
- Category routing: Automatically identifies query type
- Fuzzy matching: Finds answers even with typos/variations
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from app.config import settings
from app.services.llm_factory import get_ollama_llm
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_MODEL = settings.OLLAMA_MODEL_ADMIN
DATA_DIR = "data/"

print("🤖 Initializing Administrator Brain...")

llm = get_ollama_llm(
    model_name=OLLAMA_MODEL,
    temperature=0.5,
    max_tokens=1024,
)


# =============================================================================
# DATA LOADING
# =============================================================================

def load_json_data(filename: str) -> Dict:
    """Load JSON data file."""
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️ Data file not found: {filepath}")
        return {}
    
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return {}


# Load all admin data
FACULTY_DATA = load_json_data("faculty.json")
BUS_ROUTES_DATA = load_json_data("bus_routes.json")
FEES_DATA = load_json_data("fees_structure.json")

print(f"✅ Loaded {len(FACULTY_DATA.get('departments', []))} departments")
print(f"✅ Loaded {len(BUS_ROUTES_DATA.get('routes', []))} bus routes")
print(f"✅ Loaded fee structures for {len(FEES_DATA.get('batches', []))} batches")


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

CATEGORY_DETECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an admin query classifier.
Categorize this query into ONE of: faculty, fees, buses, placements, hostel, academic_calendar, general

Return ONLY the category name in lowercase. Examples:
"Who is the CSE HOD?" -> faculty
"What are the bus timings?" -> buses
"How much do I pay?" -> fees
"Tell me about placements" -> placements
"Hostel rules?" -> hostel

Query: {query}"""),
    ("human", "What is the category of this query?")
])

RESPONSE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful SASI Institute administrator.
Answer the student's query clearly and accurately using the provided data.

If the data answers the question, use it directly.
If not, say "I don't have this information, please contact the administration office."

Keep response under 200 words. Be friendly and professional."""),
    ("human", """Student Query: {query}
Available Data: {data}""")
])


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def detect_category(query: str) -> str:
    """
    Detect query category using LLM.
    
    Args:
        query: Admin query
        
    Returns:
        Category: faculty|fees|buses|placements|hostel|academic_calendar|general
    """
    try:
        chain = CATEGORY_DETECTION_PROMPT | llm
        response = chain.invoke({"query": query})
        category = response.content.strip().lower()
        
        valid_categories = ["faculty", "fees", "buses", "placements", "hostel", "academic_calendar", "general"]
        return category if category in valid_categories else "general"
    except Exception as e:
        print(f"⚠️ Category detection error: {e}")
        return "general"


def search_faculty(query: str) -> str:
    """
    Search faculty directory for HOD or department info using fuzzy matching.
    
    Args:
        query: Faculty-related query
        
    Returns:
        Formatted faculty information
    """
    query_lower = query.lower()
    
    # Get faculty info from bus_routes.json
    faculty_info = BUS_ROUTES_DATA.get("faculty_info", {})
    
    results = []
    
    for dept_code, dept_data in faculty_info.items():
        dept_name = dept_code.upper()
        hod_name = dept_data.get("hod", "N/A")
        
        # Fuzzy match: Check if department code or name appears in query
        if fuzzy_match(query_lower, dept_code, threshold=0.5) or \
           fuzzy_match(query_lower, dept_name, threshold=0.5) or \
           fuzzy_match(query_lower, hod_name, threshold=0.6):
            
            results.append(f"""
**{dept_name} Department**
HOD: {hod_name}
Location: {dept_data.get('location', 'N/A')}
Phone: {dept_data.get('office_phone', 'N/A')}
Email: {dept_data.get('email', 'N/A')}
""")
    
    # If no faculty match found, search in loaded faculty data as fallback
    if not results and FACULTY_DATA:
        for dept in FACULTY_DATA.get("departments", []):
            dept_name_lower = dept.get("name", "").lower()
            code_lower = dept.get("code", "").lower()
            
            if fuzzy_match(query_lower, dept_name_lower, threshold=0.6) or \
               fuzzy_match(query_lower, code_lower, threshold=0.6):
                
                hod = dept.get("hod", {})
                results.append(f"""
**{dept.get('name')} Department**
HOD: {hod.get('name', 'N/A')}
Email: {hod.get('email', 'N/A')}
Phone: {hod.get('phone', 'N/A')}
Office: {hod.get('office', 'N/A')}
Specializations: {', '.join(dept.get('specializations', []))}
""")
    
    return "\n".join(results) if results else ""


def fuzzy_match(s1: str, s2: str, threshold: float = 0.6) -> bool:
    """
    Fuzzy string matching using Levenshtein-like logic.
    
    Args:
        s1, s2: Strings to compare
        threshold: Match confidence (0-1)
        
    Returns:
        True if strings are similar enough
    """
    s1_lower = s1.lower().strip()
    s2_lower = s2.lower().strip()
    
    # Exact match
    if s1_lower == s2_lower:
        return True
    
    # Substring match
    if s1_lower in s2_lower or s2_lower in s1_lower:
        return True
    
    # Phonetic/Prefix matching
    # Split into words and check partial matches
    s1_words = set(s1_lower.split())
    s2_words = set(s2_lower.split())
    
    if s1_words & s2_words:  # Any word in common
        return True
    
    # Simple Levenshtein-like distance check
    # Count matching characters
    matches = sum(1 for c in s1_lower if c in s2_lower)
    similarity = matches / max(len(s1_lower), len(s2_lower))
    
    return similarity >= threshold


def search_buses(query: str) -> str:
    """Improved bus search: Checks route names and stop details."""
    query_lower = query.lower()
    found_routes = []
    
    # Get the routes from your JSON
    routes = BUS_ROUTES_DATA.get("transport_routes", [])
    
    for route in routes:
        name = route.get("route_name", "").lower()
        details = route.get("route_details", "").lower()
        
        # Match if the city name is in the route name OR the stop details
        if name in query_lower or any(word.strip() in query_lower for word in details.split("→")):
            found_routes.append(f"Route {route.get('route_no')}: {route.get('route_name')} ({route.get('route_details')})")
            
    return "\n".join(found_routes) if found_routes else ""


def search_fees(query: str) -> str:
    """
    Search fee structure information.
    
    Args:
        query: Fee-related query
        
    Returns:
        Formatted fee information
    """
    query_lower = query.lower()
    
    # Extract batch year if mentioned
    batch = None
    for batch_data in FEES_DATA.get("batches", []):
        batch_year = str(batch_data.get("batch", ""))
        if batch_year in query_lower:
            batch = batch_data
            break
    
    # Default to latest batch if not specified
    if not batch and FEES_DATA.get("batches"):
        batch = FEES_DATA["batches"][0]
    
    if not batch:
        return ""
    
    batch_year = batch.get("batch", "Unknown")
    
    # Format fee info
    fees_breakdown = f"""
**Fee Structure - Batch {batch_year}**

Per Semester Fees:
- Tuition Fee: ₹{batch.get('tuition_fee', 0):,}
- Development Fee: ₹{batch.get('development_fee', 0):,}
- Library Fee: ₹{batch.get('library_fee', 0):,}
- Sports Fee: ₹{batch.get('sports_fee', 0):,}

Total per Semester: ₹{batch.get('total_per_semester', 0):,}
Total per Annum: ₹{batch.get('total_per_annum', 0):,}
4-Year Total: ₹{batch.get('total_4year', 0):,}

Payment Methods: {', '.join(batch.get('payment_methods', []))}
"""
    
    return fees_breakdown


def get_admin_data(category: str) -> str:
    """
    Retrieve admin data based on category.
    
    Args:
        category: faculty|fees|buses|placements|hostel|academic_calendar|general
        
    Returns:
        Relevant data as formatted string
    """
    if category == "faculty":
        return json.dumps(FACULTY_DATA, indent=2)
    elif category == "buses":
        return json.dumps(BUS_ROUTES_DATA, indent=2)
    elif category == "fees":
        return json.dumps(FEES_DATA, indent=2)
    elif category == "placements":
        return "Placement data retrieved from RAG (Vector DB) - integrate with ChromaDB"
    elif category == "hostel":
        return "Hostel rules retrieved from RAG (Vector DB) - integrate with ChromaDB"
    elif category == "academic_calendar":
        return "Academic calendar retrieved from RAG (Vector DB) - integrate with ChromaDB"
    else:
        return "General administration information"


# =============================================================================
# CORE BRAIN FUNCTIONS
# =============================================================================

async def answer_admin_query(query: str, use_rag: bool = False) -> Dict:
    """
    Main entry point for Administrator Brain.
    
    Args:
        query: Administrative question
        use_rag: Whether to use RAG for vector search (future feature)
        
    Returns:
        Response dict with answer and metadata
    """
    print(f"\n👨‍💼 ADMIN BRAIN: {query}")
    
    # Step 1: Detect category
    category = detect_category(query)
    print(f"📂 Category detected: {category}")
    
    # Step 2: Get relevant data
    data = get_admin_data(category)
    
    # Step 3: Generate response using LLM
    chain = RESPONSE_GENERATION_PROMPT | llm
    response = chain.invoke({
        "query": query,
        "data": data
    })
    
    answer = response.content.strip()
    
    return {
        "answer": answer,
        "brain": "administrator",
        "category": category,
        "data_source": "hardcoded_and_rag",
        "confidence": 0.90,
        "used_rag": use_rag
    }


# =============================================================================
# ALTERNATIVE DIRECT SEARCH FUNCTIONS
# =============================================================================

async def answer_admin_query_direct(query: str) -> Dict:
    """
    Alternative: Direct search without LLM categorization (faster).
    
    Args:
        query: Administrative question
        
    Returns:
        Response dict
    """
    query_lower = query.lower()
    
    # Try to match keywords directly
    if any(word in query_lower for word in ["faculty", "hod", "professor", "department", "staff"]):
        data = search_faculty(query)
        category = "faculty"
    elif any(word in query_lower for word in ["bus", "route", "transport", "timing"]):
        data = search_buses(query)
        category = "buses"
    elif any(word in query_lower for word in ["fee", "fees", "cost", "tuition", "payment"]):
        data = search_fees(query)
        category = "fees"
    else:
        data = "I'm not sure which category this belongs to. Please ask about faculty, fees, or buses."
        category = "general"
    
    return {
        "answer": data,
        "brain": "administrator",
        "category": category,
        "data_source": "hardcoded",
        "confidence": 0.85
    }


async def get_admin_context(query: str) -> str:
    """Targeted context retrieval for the orchestrator."""
    q = query.lower()
    
    # 1. Bus/Transport Logic
    if any(k in q for k in ["bus", "route", "timing", "transport", "travel"]):
        return search_buses(query)
    
    # 2. Faculty Logic (Returning empty so Orchestrator triggers Web Search as requested)
    if any(k in q for k in ["hod", "faculty", "professor", "head of"]):
        return "" 
        
    # 3. Fees Logic
    if "fee" in q or "tuition" in q:
        return search_fees(query)

    return ""


# =============================================================================
# TESTING
# =============================================================================

async def test_admin_brain():
    """Test the Administrator Brain."""
    
    test_queries = [
        "Who is the HOD of CSE?",
        "What are the bus timings to Chennai?",
        "How much are the tuition fees?",
        "When does the Tambaram bus leave?",
        "Can I get CSE department contact?",
    ]
    
    print("\n" + "="*60)
    print("ADMINISTRATOR BRAIN TEST")
    print("="*60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        result = await answer_admin_query_direct(query)
        
        print(f"📂 Category: {result['category']}")
        print(f"✅ Answer: {result['answer'][:200]}...")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(test_admin_brain())
