"""
Query Router - Brain Selector
Routes incoming queries to the appropriate brain:
1. Professional Brain (educational content)
2. Admin Brain (institute information)
3. Document Brain (uploaded PDF analysis)
"""

from langchain.prompts import ChatPromptTemplate
from app.config import settings
from app.services.llm_factory import get_ollama_llm
from typing import Literal
import json

# Initialize the fast classifier LLM
classifier_llm = get_ollama_llm(
    model_name=settings.OLLAMA_MODEL_ROUTER,
    temperature=0,
    max_tokens=256,
)

CLASSIFICATION_PROMPT = """You are a query classifier for an educational AI system.

Classify the following query into EXACTLY ONE category:

Categories:
1. EDUCATIONAL - Questions about academic concepts, syllabus topics, course content
   Examples: "Explain linked lists", "What is recursion?", "How do I solve this problem?", "What are dynamic arrays?"

2. ADMIN - Questions about institute policies, facilities, administration
   Examples: "Who is the HOD of CSE?", "What are the bus routes?", "What are the fees?", "How many placements last year?", "Where is the hostel?"

3. DOCUMENT - User has uploaded a PDF document and is asking about its contents
   Keywords to look for: "document", "file", "uploaded", "PDF", "notes", "paper"
   Examples: "What's in that PDF I uploaded?", "Summarize the document", "Based on my notes...", "From the file..."

Query: {query}

Respond ONLY with one word: EDUCATIONAL, ADMIN, or DOCUMENT"""

QUERY_CONTEXT_PROMPT = """Extract relevant context from this query for routing:

Query: {query}

Provide JSON output with:
{
    "has_file_reference": boolean,  // Does it mention a document/file?
    "academic_keywords": [list],     // Educational terms found
    "admin_keywords": [list],         // Institute info terms found
    "mode_preference": string         // "fast" or "deep" (if educational)
}"""

async def classify_query(query: str) -> Literal["educational", "admin", "document"]:
    """
    Classify a query to determine which brain should handle it.
    
    Args:
        query: User's input query
        
    Returns:
        One of: "educational", "admin", "document"
    """
    
    try:
        prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        chain = prompt | classifier_llm
        
        response = chain.invoke({"query": query})
        classification = response.content.strip().upper()
        
        # Map to lowercase for consistency
        if "EDUCATIONAL" in classification:
            return "educational"
        elif "ADMIN" in classification:
            return "admin"
        elif "DOCUMENT" in classification:
            return "document"
        else:
            # Default to educational if unclear
            return "educational"
            
    except Exception as e:
        print(f"Error in query classification: {e}")
        return "educational"  # Safe default

async def extract_query_context(query: str) -> dict:
    """
    Extract context and metadata from the query.
    
    Returns:
        Dictionary with query context
    """
    
    try:
        prompt = ChatPromptTemplate.from_template(QUERY_CONTEXT_PROMPT)
        chain = prompt | classifier_llm
        
        response = chain.invoke({"query": query})
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            context = json.loads(json_match.group())
            return context
        
    except Exception as e:
        print(f"Error extracting query context: {e}")
    
    # Default context
    return {
        "has_file_reference": False,
        "academic_keywords": [],
        "admin_keywords": [],
        "mode_preference": "fast"
    }

# ===== TOPIC EXTRACTION FOR EDUCATIONAL QUERIES =====

TOPIC_EXTRACTION_PROMPT = """Extract the academic topic from this educational query.

Query: {query}

Return ONLY the main topic/concept this question is about.
Examples:
- "Explain linked lists" -> "Linked Lists"
- "How do I implement binary search?" -> "Binary Search"
- "What's the difference between recursion and iteration?" -> "Recursion vs Iteration"

Topic: """

async def extract_academic_topic(query: str) -> str:
    """Extract the main academic topic from an educational query"""
    
    try:
        prompt = ChatPromptTemplate.from_template(TOPIC_EXTRACTION_PROMPT)
        chain = prompt | classifier_llm
        
        response = chain.invoke({"query": query})
        return response.content.strip()
        
    except Exception as e:
        print(f"Error extracting topic: {e}")
        return "General Topic"

# ===== ADMIN CATEGORY EXTRACTION =====

ADMIN_CATEGORY_PROMPT = """Classify this admin query into one of these categories:

Categories:
- faculty: Questions about faculty/HOD/teachers
- fees: Questions about tuition fees, exam fees
- buses: Questions about bus routes and transportation
- placements: Questions about placements and company recruitment
- hostel: Questions about hostel facilities and accommodation
- academic_calendar: Questions about dates, exam schedules
- general: Other institute questions

Query: {query}

Return ONLY the category name."""

async def extract_admin_category(query: str) -> str:
    """Extract the admin query category"""
    
    try:
        prompt = ChatPromptTemplate.from_template(ADMIN_CATEGORY_PROMPT)
        chain = prompt | classifier_llm
        
        response = chain.invoke({"query": query})
        category = response.content.strip().lower()
        
        valid_categories = [
            "faculty", "fees", "buses", "placements", 
            "hostel", "academic_calendar", "general"
        ]
        
        return category if category in valid_categories else "general"
        
    except Exception as e:
        print(f"Error extracting admin category: {e}")
        return "general"

# ===== MAIN ROUTER FUNCTION =====

async def route_query(query: str, user_context: dict = None) -> dict:
    """
    Main query routing function.
    
    Args:
        query: User's input query
        user_context: Optional dict with user info (user_id, session_id, etc)
        
    Returns:
        Router decision dict with routing info and extracted metadata
    """
    
    # Step 1: Classify query
    brain_type = await classify_query(query)
    
    # Step 2: Extract context
    context = await extract_query_context(query)
    
    # Step 3: Extract specific metadata based on brain type
    routing_info = {
        "brain": brain_type,
        "query": query,
        "confidence": 0.90,
        "context": context
    }
    
    if brain_type == "educational":
        topic = await extract_academic_topic(query)
        mode = context.get("mode_preference", "fast")
        
        routing_info.update({
            "topic": topic,
            "mode": mode,  # "fast" or "deep"
            "requires_deep_search": mode == "deep"
        })
        
    elif brain_type == "admin":
        category = await extract_admin_category(query)
        
        routing_info.update({
            "category": category,
            "data_sources": _get_data_sources_for_category(category)
        })
        
    elif brain_type == "document":
        # Document brain needs document_id to be set by frontend
        routing_info.update({
            "requires_document": True,
            "query_type": "database_search"
        })
    
    return routing_info

def _get_data_sources_for_category(category: str) -> list:
    """Map admin category to data sources"""
    
    sources_map = {
        "faculty": ["faculty.json", "admin_vector_store"],
        "fees": ["fees_structure.json", "exam_fees_pdf"],
        "buses": ["bus_routes.json"],
        "placements": ["placement_data.json", "placement_pdfs"],
        "hostel": ["hostel_info.json"],
        "academic_calendar": ["academic_calendar.json"],
        "general": ["admin_faq_vectorstore"]
    }
    
    return sources_map.get(category, ["admin_faq_vectorstore"])

# ===== DEBUG/TEST FUNCTION =====

async def test_router():
    """Test the query router with sample queries"""
    
    test_queries = [
        "Explain linked lists and their applications",
        "Who is the HOD of Computer Science?",
        "What are the bus routes for campus?",
        "Based on the PDF I uploaded, what's the main topic?",
        "How do I calculate time complexity?",
        "What are the placement stats for this year?"
    ]
    
    print("\n🧠 Query Router Test")
    print("=" * 60)
    
    for query in test_queries:
        result = await route_query(query)
        print(f"\nQuery: {query}")
        print(f"Brain: {result['brain'].upper()}")
        if "topic" in result:
            print(f"Topic: {result['topic']}")
        if "category" in result:
            print(f"Category: {result['category']}")
        if "mode" in result:
            print(f"Mode: {result['mode']}")
        print(f"Confidence: {result['confidence']:.0%}")
        print("-" * 60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_router())
