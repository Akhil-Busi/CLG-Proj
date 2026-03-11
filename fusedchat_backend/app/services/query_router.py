# app/services/query_router.py
from app.config import settings
from app.services.llm_factory import get_ollama_llm
import json
import re

classifier_llm = get_ollama_llm(
    model_name=settings.OLLAMA_MODEL_ROUTER,
    temperature=0,
    max_tokens=256,
)

async def route_query(query: str) -> dict:
    """Simplified, robust router."""
    
    # 1. Classification
    classify_prompt = f"""Classify this query into ONE category: EDUCATIONAL, ADMIN, or DOCUMENT.
    Query: {query}
    Respond with ONLY the word."""
    
    try:
        raw_class = classifier_llm.invoke(classify_prompt).content.strip().upper()
        brain_type = "educational"
        if "ADMIN" in raw_class:
            brain_type = "admin"
        elif "DOCUMENT" in raw_class:
            brain_type = "document"
    except:
        brain_type = "educational"

    # 2. Context Extraction (using simple string formatting to avoid Braces errors)
    context_prompt = f"""Extract metadata for this query. 
    Query: {query}
    Respond ONLY with a JSON object like this:
    {{"has_file_reference": false, "academic_keywords": [], "admin_keywords": [], "mode_preference": "fast"}}"""

    try:
        resp = classifier_llm.invoke(context_prompt).content
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        context = json.loads(match.group()) if match else {}
    except:
        context = {"mode_preference": "fast"}

    return {
        "brain": brain_type,
        "query": query,
        "confidence": 0.9,
        "mode": context.get("mode_preference", "fast")
    }
