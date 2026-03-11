#app/main.py

import os
import shutil
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.services.ingestion import build_index
from app.services.query_router import route_query
from app.services.professional_brain import answer_question as prof_answer, studio_orchestrator
from app.services.admin_brain import answer_admin_query_direct as admin_answer
from app.services.document_brain import (
    register_document, 
    get_document_store, 
    answer_document_question
)
from app.database import save_chat, get_history


# =============================================================================
# SIMPLE CONVERSATION FILTER
# =============================================================================

GREETINGS = {"hello", "hi", "hey", "good morning", "good evening", "greetings"}
THANKS_FAREWELLS = {"thank you", "thanks", "bye", "goodbye", "appreciate it"}


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    session_id: str
    query: str
    mode: str = "fast"  # fast or deep for professional brain
    regulation: str = "SITE 21"  # Academic curriculum version: SITE 18/21/23
    document_id: Optional[str] = None  # Optional document ID for Studio mode


class DocumentMode(BaseModel):
    session_id: str
    document_id: str
    query: str


# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(
    title="FusedChat API",
    description="Three-Brain AI Platform for SASI Institute",
    version="1.0.0"
)

# CORS Middleware - Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("vector_store", exist_ok=True)


# =============================================================================
# STARTUP & SHUTDOWN EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    print("\n" + "="*60)
    print("🚀 FusedChat Backend Starting...")
    print("="*60)
    
    # Build syllabus index if missing
    if not os.path.exists(settings.SYLLABUS_INDEX_PATH):
        print("\n📚 Building Syllabus Index...")
        if os.path.exists(settings.SYLLABUS_PATH):
            build_index(settings.SYLLABUS_PATH, settings.SYLLABUS_INDEX_PATH)
            print("✅ Syllabus Index Ready.")
        else:
            print(f"⚠️ Warning: Syllabus PDF not found at {settings.SYLLABUS_PATH}")
    else:
        print("✅ Syllabus index already built")
    
    print("\n" + "="*60)
    print("✅ Backend Ready!")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("\n🛑 Shutting down FusedChat...")


# =============================================================================
# UPLOAD ENDPOINT
# =============================================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = ""
):
    """
    Upload and process a PDF document.
    
    Returns:
        document_id, filename, status, chunk count
    """
    try:
        # Validate file
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"\n📄 Processing document: {file.filename}")
        
        # Register document
        doc_info = register_document(
            file_path,
            file.filename,
            session_id or "anonymous"
        )
        
        if "error" in doc_info:
            raise HTTPException(status_code=500, detail=doc_info["error"])
        
        print(f"✅ Document registered: {doc_info['document_id']}")
        
        return {
            "status": "success",
            "document_id": doc_info["document_id"],
            "filename": file.filename,
            "chunks_created": doc_info.get("chunks_created", 0),
            "message": "Document processed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN CHAT ENDPOINT
# =============================================================================

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint - Uses Studio Orchestrator for multi-source intelligence.
    
    The Studio approach combines all available sources:
    - Course Syllabus (Educational Brain)
    - User Documents (Document Brain)
    - Institute Data (Admin Brain)
    """
    
    # 1. Quick system responses
    q = request.query.lower().strip()
    if q in ["hi", "hello", "hey", "greetings", "good morning", "good evening"]:
        return {
            "status": "success",
            "response": "Hello! I am FusedChat Studio, your intelligent academic workspace. I can help you with coursework, uploaded documents, and campus information - all at once! How can I assist you today?",
            "brain": "system",
            "suggestions": [
                "Create a study plan from my syllabus",
                "Analyze my uploaded document",
                "Show me the fee structure",
                "Generate practice questions"
            ]
        }
    
    if q in ["how are you?", "how are you", "how r u"]:
        return {
            "status": "success",
            "response": "I'm functioning perfectly and ready to help! I have access to your syllabus, documents, and all campus information.",
            "brain": "system",
            "suggestions": [
                "What can you do?",
                "Help me study for exams",
                "Upload a document"
            ]
        }
    
    if "what can you do" in q or "your features" in q or "capabilities" in q:
        return {
            "status": "success",
            "response": """I'm FusedChat Studio - your AI Research Lab! Here's what I can do:

📚 **Academic Intelligence**: Answer questions using your course syllabus
📄 **Document Analysis**: Analyze PDFs you upload (notes, assignments, research papers)
🏫 **Campus Assistant**: Provide info about fees, buses, faculty, and more
🎯 **Smart Tasks**: Create study plans, generate quizzes, explain code
🔗 **Multi-Source Fusion**: Combine syllabus + your documents for comprehensive answers

Just ask me anything or upload a document to get started!""",
            "brain": "system",
            "suggestions": [
                "Show me bus routes",
                "Create a study guide for Data Structures",
                "What are the fee payment options?"
            ]
        }
    
    print(f"\n💬 Studio Processing: '{request.query}'")
    print(f"   Session: {request.session_id}")
    print(f"   Mode: {request.mode}")
    print(f"   Document: {request.document_id or 'None'}")
    
    try:
        # Use Studio Orchestrator for intelligent multi-source response
        print("   🎯 Activating Studio Orchestrator...")
        
        result = await studio_orchestrator(
            question=request.query,
            session_id=request.session_id,
            document_id=request.document_id,
            mode=request.mode
        )
        
        # Save to database
        print(f"   💾 Saving to database...")
        try:
            await save_chat(
                session_id=request.session_id,
                query=request.query,
                response=result.get("answer", ""),
                mode="studio"
            )
        except Exception as db_err:
            print(f"   ⚠️ Database Error (Ignored): {db_err}")
        
        print(f"   ✅ Studio response generated")
        
        # Return enriched response with suggestions
        return {
            "status": "success",
            "response": result.get("answer", ""),
            "brain": result.get("brain", "studio_core"),
            "mode": result.get("mode", request.mode),
            "sources_used": result.get("sources_used", []),
            "suggestions": result.get("suggestions", []),
            "source_count": result.get("source_count", 0)
        }
    
    except Exception as exc:
        print(f"❌ Studio Error: {exc}")
        import traceback
        traceback.print_exc()
        
        # Fallback response
        return {
            "status": "error",
            "response": "I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support.",
            "brain": "error",
            "error": str(exc)
        }


# =============================================================================
# DOCUMENT CHAT ENDPOINT
# =============================================================================

@app.post("/chat/document")
async def chat_document(request: DocumentMode):
    """
    Chat about a specific uploaded document.
    
    Requires: document_id from previous upload
    """
    print(f"\n📄 Document Chat: {request.query}")
    print(f"   Document: {request.document_id}")
    
    try:
        # Get vector store for document
        vector_store = get_document_store(request.document_id)
        
        if not vector_store:
            raise HTTPException(
                status_code=404,
                detail=f"Document {request.document_id} not found"
            )
        
        # Answer question about document
        result = await answer_document_question(
            query=request.query,
            vector_store=vector_store,
            document_id=request.document_id
        )
        
        # Save to database
        try:
            await save_chat(
                session_id=request.session_id,
                query=request.query,
                response=result.get("answer", ""),
                mode="document"
            )
        except Exception as db_err:
            print(f"⚠️ Database Error (Ignored): {db_err}")
        
        print(f"✅ Document chat response generated")
        
        return {
            "status": "success",
            "response": result.get("answer", ""),
            "brain": "document",
            "document_id": request.document_id,
            "citations": result.get("citations", []),
            "pages_referenced": result.get("pages_referenced", []),
            "confidence": result.get("confidence", 0.8)
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Document Chat Error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# =============================================================================
# CONVERSATION HISTORY ENDPOINT
# =============================================================================

@app.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = 50
):
    """
    Retrieve conversation history for a session.
    
    Args:
        session_id: User session ID
        limit: Maximum number of messages to return
        
    Returns:
        List of messages in conversation
    """
    try:
        print(f"\n📜 Fetching history for session: {session_id}")
        
        history = await get_history(session_id, limit=limit)
        
        return {
            "status": "success",
            "session_id": session_id,
            "message_count": len(history),
            "messages": history
        }
    except Exception as e:
        print(f"❌ History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "FusedChat Backend",
        "version": "1.0.0"
    }


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/")
async def root():
    """Welcome message and API info."""
    return {
        "welcome": "FusedChat - Three-Brain AI Platform",
        "institute": "SASI Institute of Technology & Engineering",
        "endpoints": {
            "chat": "POST /chat - Main chat interface",
            "upload": "POST /upload - Upload PDF document",
            "document_chat": "POST /chat/document - Chat about uploaded document",
            "history": "GET /history/{session_id} - Get conversation history",
            "health": "GET /health - Health check",
            "docs": "GET /docs - Interactive API documentation"
        },
        "brains": ["professional", "administrator", "document"]
    }
