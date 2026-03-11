#app/services/professional_brain.py
"""
Professional Brain Service
==========================
Specialized education chatbot that answers academic questions.

Features:
- Fast Mode: Direct answers using internal knowledge
- Deep Mode: Comprehensive answers with web search
- Syllabus-constrained: Ensures answers stay within academic scope
- Topic extraction: Identifies subject and concept being asked
- Citation generation: Returns sources from syllabus
"""

import os
import asyncio
import json
import re
from typing import Dict, List, Optional, Tuple
from app.config import settings
from app.services.llm_factory import get_ollama_llm
from app.services.live_researcher import SasiLiveResearcher
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun


# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # 1024 dimensions
OLLAMA_MODEL_FAST = settings.OLLAMA_MODEL_FAST
OLLAMA_MODEL_ANSWER = settings.OLLAMA_MODEL_ANSWER

print("🧠 Initializing Professional Brain...")

# Initialize LLM
llm_answer = get_ollama_llm(
    model_name=OLLAMA_MODEL_ANSWER,
    temperature=0.7,
    max_tokens=1024,
)

llm_fast = get_ollama_llm(
    model_name=OLLAMA_MODEL_FAST,
    temperature=0.5,
    max_tokens=512,
)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# Initialize search (for Deep Mode)
search_tool = DuckDuckGoSearchRun()

# Live researcher (Tavily)
live_researcher = SasiLiveResearcher()

# Load syllabus index if available
SYLLABUS_INDEX_PATH = "vector_store/syllabus_index"
syllabus_vectorstore = None

def load_syllabus_index():
    """Load pre-built syllabus FAISS index."""
    global syllabus_vectorstore
    
    if os.path.exists(SYLLABUS_INDEX_PATH):
        try:
            syllabus_vectorstore = FAISS.load_local(
                SYLLABUS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("✅ Syllabus index loaded successfully.")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load syllabus index: {e}")
            return False
    else:
        print(f"⚠️ Syllabus index not found at {SYLLABUS_INDEX_PATH}")
        return False

# Load on startup
load_syllabus_index()


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

TOPIC_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert academic question analyzer.
Extract the main topic/concept from the student's question.
Return ONLY a JSON object with this structure:
{
    "topic": "Topic Name",
    "subject": "Subject Code (e.g., 23CMMAT1010)",
    "level": "conceptual|computational|practical",
    "keywords": ["key1", "key2", "key3"]
}

Be concise. Topic should be <20 characters."""),
    ("human", "Question: {question}")
])

FAST_MODE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional tutor for {subject}.
Answer the following question CONCISELY but ACCURATELY.
Stay within the official curriculum scope. Do NOT go beyond the course syllabus.

If you don't know the answer or it's outside the course scope, say so directly.
Keep response under 150 words."""),
    ("human", """Question: {question}
Syllabus Reference: {context}""")
])

DEEP_MODE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a comprehensive academic researcher for {subject}.
The student wants an in-depth, well-researched answer.

Use BOTH the internal syllabus knowledge AND the external research provided.
Structure your answer as:
1. **Definition/Concept**
2. **Detailed Explanation** (with examples)
3. **Real-World Applications**
4. **Key Takeaways**

Cite your sources clearly. Maximum response: 500 words."""),
    ("human", """Question: {question}
Syllabus Material: {syllabus_context}
External Research: {web_context}""")
])

CONSTRAINT_CHECK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a curriculum compliance checker.
The student asked a question. Check if it's within the official course scope.

Answer ONLY "YES" or "NO":
- YES: The question is about topics covered in this course
- NO: The question is outside the curriculum scope

Syllabus Topics: {topics}
Question: {question}"""),
    ("human", "Is this question within scope?")
])


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_topic_metadata(question: str) -> Dict:
    """
    Extract topic, subject, and keywords from user's question.
    
    Args:
        question: User's academic question
        
    Returns:
        Dict with topic, subject, level, and keywords
    """
    try:
        chain = TOPIC_EXTRACTION_PROMPT | llm_fast
        response = chain.invoke({"question": question})
        
        # Parse JSON from response
        json_str = response.content
        # Remove markdown code blocks if present
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        metadata = json.loads(json_str)
        return metadata
    except Exception as e:
        print(f"⚠️ Topic extraction error: {e}")
        return {
            "topic": "General",
            "subject": "Unknown",
            "level": "conceptual",
            "keywords": []
        }


def retrieve_syllabus_context(question: str, k: int = 3):
    if not syllabus_vectorstore:
        return "No syllabus available.", []
    
    try:
        # We try the most common method first
        try:
            results = syllabus_vectorstore.similarity_search_with_score(question, k=k)
        except AttributeError:
            # Fallback for older/newer versions
            results = syllabus_vectorstore.similarity_search_with_relevance_scores(question, k=k)
        
        context_parts = []
        sources = []
        for doc, score in results:
            context_parts.append(doc.page_content)
            sources.append({"page": doc.metadata.get("page"), "relevance": float(score)})
        
        return "\n---\n".join(context_parts), sources
    except Exception as e:
        print(f"⚠️ Retrieval error: {e}")
        return "Context not found.", []


def has_meaningful_syllabus_context(question: str, syllabus_context: str) -> bool:
    """
    Determine if retrieved syllabus text is actually useful for this question.

    This avoids treating generic/placeholder retrieval output as valid local data,
    which would incorrectly block web fallback.
    """
    if not syllabus_context or not syllabus_context.strip():
        return False

    context_lower = syllabus_context.strip().lower()
    placeholder_markers = {
        "no syllabus available.",
        "context not found.",
        "no syllabus available",
        "context not found",
    }
    if context_lower in placeholder_markers:
        return False

    # Basic lexical overlap check to avoid unrelated vector hits.
    stop_words = {
        "what", "which", "when", "where", "who", "whom", "whose", "why", "how",
        "is", "are", "was", "were", "be", "been", "being",
        "the", "a", "an", "of", "to", "for", "in", "on", "at", "by", "with",
        "and", "or", "if", "about", "tell", "me", "please", "can", "could", "you",
        "this", "that", "these", "those", "from", "into", "than", "then", "also",
        "explain", "give", "show", "write", "describe",
    }

    question_terms = [
        token for token in re.findall(r"[a-zA-Z0-9]+", question.lower())
        if len(token) > 3 and token not in stop_words
    ]

    # If query has no strong keywords, any non-placeholder context is acceptable.
    if not question_terms:
        return True

    overlap_count = sum(1 for token in set(question_terms) if token in context_lower)

    # Require at least one meaningful term overlap for local-context confidence.
    return overlap_count >= 1


def web_search_for_topic(topic: str, keywords: List[str]) -> str:
    """
    Perform web search for comprehensive information.
    
    Args:
        topic: Main topic
        keywords: Search keywords
        
    Returns:
        Formatted search results
    """
    try:
        # Construct search query
        query = f"{topic} {' '.join(keywords)}"
        print(f"🔍 Searching: {query}")
        
        # Use DuckDuckGo for search
        results = search_tool.run(query)
        
        if results:
            # Limit result length
            return results[:1500]  # Max 1500 chars
        else:
            return "No additional resources found."
    except Exception as e:
        print(f"⚠️ Web search error: {e}")
        return "Web search unavailable."


def check_syllabus_scope(question: str, topics: str) -> bool:
    """
    Verify if question is within curriculum scope.
    
    Args:
        question: User's question
        topics: Available topics in syllabus
        
    Returns:
        True if in scope, False otherwise
    """
    try:
        chain = CONSTRAINT_CHECK_PROMPT | llm_fast
        response = chain.invoke({
            "question": question,
            "topics": topics
        })
        
        answer = response.content.strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"⚠️ Scope check error: {e}")
        return True  # Default to allowing the question


# =============================================================================
# CORE BRAIN FUNCTIONS
# =============================================================================

async def fast_mode(question: str, topic_metadata: Optional[Dict] = None) -> Dict:
    """
    Fast Mode: Quick, concise answer based on internal knowledge only.
    
    Args:
        question: User's question
        topic_metadata: Optional pre-extracted metadata
        
    Returns:
        Response dict with answer, sources, and metadata
    """
    print(f"\n⚡ FAST MODE: {question}")
    
    # Extract metadata if not provided
    if not topic_metadata:
        topic_metadata = extract_topic_metadata(question)
    
    # Retrieve syllabus context
    syllabus_context, sources = retrieve_syllabus_context(
        question,
        k=2  # Only 2 chunks for fast mode
    )
    
    # Generate answer
    chain = FAST_MODE_PROMPT | llm_fast
    response = chain.invoke({
        "question": question,
        "subject": topic_metadata.get("subject", "Unknown"),
        "context": syllabus_context
    })
    
    answer = response.content.strip()
    
    return {
        "answer": answer,
        "mode": "fast",
        "topic": topic_metadata.get("topic"),
        "subject": topic_metadata.get("subject"),
        "sources": sources,
        "source_count": len(sources),
        "confidence": 0.85 if sources else 0.60
    }


async def deep_mode(question: str, topic_metadata: Optional[Dict] = None) -> Dict:
    """
    Deep Mode: Comprehensive answer with web research.
    
    Args:
        question: User's question
        topic_metadata: Optional pre-extracted metadata
        
    Returns:
        Response dict with detailed answer, citations, and research
    """
    print(f"\n🔬 DEEP MODE: {question}")
    
    # Extract metadata if not provided
    if not topic_metadata:
        topic_metadata = extract_topic_metadata(question)
    
    # Parallel retrieval: syllabus + web search
    print("📚 Retrieving syllabus material...")
    syllabus_context, sources = retrieve_syllabus_context(
        question,
        k=5  # More chunks for deep mode
    )
    
    print("🌐 Searching the web...")
    web_context = web_search_for_topic(
        topic_metadata.get("topic", ""),
        topic_metadata.get("keywords", [])
    )
    
    # Generate comprehensive answer
    chain = DEEP_MODE_PROMPT | llm_answer
    response = chain.invoke({
        "question": question,
        "subject": topic_metadata.get("subject", "Unknown"),
        "syllabus_context": syllabus_context,
        "web_context": web_context
    })
    
    answer = response.content.strip()
    
    return {
        "answer": answer,
        "mode": "deep",
        "topic": topic_metadata.get("topic"),
        "subject": topic_metadata.get("subject"),
        "sources": sources,
        "source_count": len(sources),
        "web_search_performed": True,
        "confidence": 0.95 if sources else 0.88
    }


async def answer_question(
    question: str,
    mode: str = "fast",
    use_constraints: bool = True
) -> Dict:
    """
    Main entry point for Professional Brain.
    
    Args:
        question: User's academic question
        mode: "fast" or "deep"
        use_constraints: Whether to check syllabus scope
        
    Returns:
        Complete response dict with answer and metadata
    """
    # Try extracting topic
    topic_metadata = extract_topic_metadata(question)
    
    # Optional: Check scope (can disable for testing)
    if use_constraints:
        # Get sample topics from index
        sample_topics = "Linked Lists, Arrays, Trees, Graphs, Sorting, Searching"
        in_scope = check_syllabus_scope(question, sample_topics)
        
        if not in_scope:
            return {
                "answer": "I'm trained specifically for SASI Institute curriculum. Your question seems outside the syllabus scope. Please ask about: Linked Lists, Arrays, Trees, Graphs, Sorting, Searching, and related data structures.",
                "mode": "blocked",
                "topic": topic_metadata.get("topic"),
                "in_scope": False,
                "confidence": 1.0
            }
    
    # Route to appropriate mode
    if mode.lower() == "deep":
        result = await deep_mode(question, topic_metadata)
    else:
        result = await fast_mode(question, topic_metadata)
    
    return result


# =============================================================================
# STUDIO ORCHESTRATOR - Multi-Source Intelligence
# =============================================================================

async def studio_orchestrator(
    question: str,
    session_id: str,
    regulation: str = "SITE 21",
    document_id: Optional[str] = None,
    mode: str = "fast"
) -> Dict:
    """
    The 'Google AI Studio' Orchestrator.
    Synthesizes knowledge from Syllabus, Admin JSONs, User PDFs, and Live Web.
    """
    print(f"🧬 Studio: Processing '{question}'")

    mode_normalized = (mode or "fast").strip().lower()

    from app.services.admin_brain import get_admin_context
    
    # 1. FETCH LOCAL CONTEXT
    admin_ctx = (await get_admin_context(question) or "").strip()
    syll_ctx, _ = retrieve_syllabus_context(question, k=2)

    if not has_meaningful_syllabus_context(question, syll_ctx):
        syll_ctx = ""
    
    # 2. FILTER SYLLABUS NOISE
    # If the query is clearly about a Bus or a Person, ignore irrelevant syllabus data
    is_admin_query = any(k in question.lower() for k in ["bus", "route", "fee", "hod", "faculty", "dean"])
    if is_admin_query and "timetable" not in question.lower():
        syll_ctx = "" 

    # 3. SMART WEB TRIGGER
    # If it's a deep search OR we found nothing locally OR it's a faculty query (since JSON is deleted)
    is_faculty_query = any(k in question.lower() for k in ["who is", "hod", "professor", "faculty"])
    
    web_data = None
    if mode_normalized == "deep" or is_faculty_query or (not admin_ctx and not syll_ctx):
        print("🌐 Triggering Web Search...")
        web_data = await live_researcher.execute(question)

    # 4. SILENT SYSTEM PROMPT (Prevents the AI from talking about its logic)
    SYSTEM_PROMPT = """You are FusedChat Studio. Provide direct, helpful answers.
    
    STRICT RULES:
    1. DO NOT explain your reasoning or source names.
    2. If providing a table, you MUST leave a blank line before the table starts so it renders correctly.
    3. Use **bold** for key names and # for headers.
    4. If the answer is not found, offer to help with a different query or suggest the official website.
    5. Be proactive and lively!"""

    USER_CONTENT = f"""
    QUESTION: {question}
    ---
    DATA SOURCES:
    {f"ADMIN DATA: {admin_ctx}" if admin_ctx else ""}
    {f"SYLLABUS DATA: {syll_ctx}" if syll_ctx else ""}
    {f"WEB DATA: {web_data['answer']}" if web_data else ""}
    """

    try:
        selected_llm = llm_answer if mode_normalized == "deep" else llm_fast
        response = await selected_llm.ainvoke([("system", SYSTEM_PROMPT), ("human", USER_CONTENT)])
        
        return {
            "answer": response.content,
            "brain": "studio_core",
            "sources_used": {"admin": bool(admin_ctx), "web": bool(web_data)}
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"answer": "Connection lost. Please check your internet/Ollama.", "brain": "error"}


def generate_suggestions(question: str, sources_available: List[str]) -> List[str]:
    """
    Generate intelligent next-step suggestions based on query and available sources.
    
    Args:
        question: User's current question
        sources_available: List of source types available
        
    Returns:
        List of suggested follow-up queries
    """
    q_lower = question.lower()
    suggestions = []
    
    # Topic-based suggestions
    if any(word in q_lower for word in ["matrix", "linear algebra", "vector"]):
        suggestions = [
            "Show me Python code examples for matrix operations",
            "Generate practice problems on matrices",
            "Is this topic in my exam syllabus?"
        ]
    
    elif any(word in q_lower for word in ["data structure", "linked list", "tree", "graph"]):
        suggestions = [
            "Explain with a visual diagram",
            "Compare this with other data structures",
            "What are the time complexities?"
        ]
    
    elif any(word in q_lower for word in ["fee", "admission", "contact"]):
        suggestions = [
            "What are the payment methods?",
            "Show me the fee structure",
            "Where is the admin office?"
        ]
    
    elif any(word in q_lower for word in ["bus", "route", "transport"]):
        suggestions = [
            "Which bus passes near my location?",
            "Show all available routes",
            "What are the bus timings?"
        ]
    
    elif any(word in q_lower for word in ["study", "exam", "prepare", "learn"]):
        suggestions = [
            "Create a 5-day study plan for this topic",
            "Generate practice questions",
            "Summarize key points from my notes"
        ]
    
    # Source-based suggestions
    if "Your Uploaded Document" in sources_available:
        suggestions.append("Summarize my uploaded document")
        suggestions.append("Compare this with the syllabus")
    
    if "Course Syllabus" in sources_available:
        suggestions.append("What topics should I focus on?")
        suggestions.append("Show me related syllabus sections")
    
    # Default suggestions
    if not suggestions:
        suggestions = [
            "Explain this in simpler terms",
            "Give me a practical example",
            "What should I study next?"
        ]
    
    # Return max 4 suggestions
    return suggestions[:4]


# =============================================================================
# TESTING & EXAMPLES
# =============================================================================

async def test_professional_brain():
    """Test the Professional Brain with sample questions."""
    
    test_questions = [
        ("What is a Linked List?", "fast"),
        ("Explain Binary Search Trees in detail", "deep"),
        ("How do hash tables work?", "fast"),
        ("What is time complexity analysis?", "deep"),
    ]
    
    print("\n" + "="*60)
    print("PROFESSIONAL BRAIN TEST")
    print("="*60)
    
    for question, mode in test_questions:
        print(f"\n📝 Question: {question}")
        print(f"🎯 Mode: {mode}")
        
        result = await answer_question(question, mode=mode, use_constraints=False)
        
        print(f"✅ Answer: {result['answer'][:200]}...")
        print(f"📊 Confidence: {result.get('confidence', 'N/A')}")
        print(f"📚 Sources: {result.get('source_count', 0)}")
        print("-" * 60)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_professional_brain())
