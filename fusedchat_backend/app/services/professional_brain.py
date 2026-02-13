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
from typing import Dict, List, Optional, Tuple
from app.config import settings
from app.services.llm_factory import get_ollama_llm
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


def retrieve_syllabus_context(question: str, k: int = 3) -> Tuple[str, List[Dict]]:
    """
    Retrieve relevant syllabus chunks using semantic search.
    
    Args:
        question: User's question
        k: Number of chunks to retrieve
        
    Returns:
        Tuple of (context_text, source_metadata)
    """
    if not syllabus_vectorstore:
        return "No syllabus available.", []
    
    try:
        # Semantic search
        results = syllabus_vectorstore.similarity_search_with_scores(
            question,
            k=k
        )
        
        context_parts = []
        sources = []
        
        for doc, score in results:
            context_parts.append(doc.page_content)
            sources.append({
                "page": doc.metadata.get("page", "Unknown"),
                "unit": doc.metadata.get("unit", "General"),
                "subject": doc.metadata.get("subject_code", "Unknown"),
                "relevance_score": float(score)
            })
        
        context = "\n---\n".join(context_parts)
        return context, sources
    except Exception as e:
        print(f"⚠️ Syllabus retrieval error: {e}")
        return "Error retrieving syllabus context.", []


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
