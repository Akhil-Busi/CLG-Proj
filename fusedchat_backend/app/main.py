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
from app.services.professional_brain import answer_question as prof_answer
from app.services.admin_brain import answer_admin_query_direct as admin_answer
from app.services.document_brain import (
    register_document, 
    get_document_store, 
    answer_document_question
)
from app.database import save_chat, get_history


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    session_id: str
    query: str
    mode: str = "fast"  # fast or deep for professional brain


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
    Main chat endpoint - routes query to appropriate brain.
    
    Query -> Query Router -> Brain Selection -> Brain Processing -> Response
    """
    print(f"\n💬 Incoming Query: '{request.query}'")
    print(f"   Session: {request.session_id}")
    print(f"   Mode: {request.mode}")
    
    try:
        # Step 1: Route query to appropriate brain
        print("   🔀 Routing query...")
        routing_info = await route_query(request.query)
        
        brain_type = routing_info.get("brain", "professional")
        confidence = routing_info.get("confidence", 0.5)
        
        print(f"   📂 Routed to: {brain_type} (confidence: {confidence})")
        
        # Step 2: Process with appropriate brain
        if brain_type == "professional":
            print("   🧠 Professional Brain: Education Q&A")
            result = await prof_answer(
                question=request.query,
                mode=request.mode,
                use_constraints=True
            )
        
        elif brain_type == "administrator":
            print("   🤖 Admin Brain: Institute Info")
            result = await admin_answer(request.query)
        
        elif brain_type == "document":
            # For document brain, we need document_id - this should come from frontend
            print("   📄 Document Brain: PDF Analysis")
            result = {
                "answer": "Please upload a document first or specify document_id",
                "brain": "document",
                "error": "No document_id provided"
            }
        
        else:
            result = {
                "answer": "I'm not sure how to help with that. Try asking about courses, institute info, or upload a document.",
                "brain": "general"
            }
        
        # Step 3: Save to database
        print(f"   💾 Saving to database...")
        try:
            await save_chat(
                session_id=request.session_id,
                query=request.query,
                response=result.get("answer", ""),
                mode=brain_type
            )
        except Exception as db_err:
            print(f"   ⚠️ Database Error (Ignored): {db_err}")
        
        print(f"   ✅ Response generated")
        
        # Step 4: Return response
        return {
            "status": "success",
            "response": result.get("answer", ""),
            "brain": brain_type,
            "mode": result.get("mode", request.mode),
            "confidence": result.get("confidence", 0.5),
            "sources": result.get("sources", []),
            "citations": result.get("citations", [])
        }
    
    except Exception as exc:
        print(f"❌ Chat Error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


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
