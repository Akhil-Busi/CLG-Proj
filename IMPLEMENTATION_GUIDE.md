# FusedChat Three-Brain Implementation Guide

## Quick Start: Installation & Setup

### Step 1: Install Dependencies

```bash
cd fusedchat_backend

# Core dependencies
pip install motor pymongo          # MongoDB async driver
pip install chromadb               # Vector store (local)
pip install langchain-community    # LangChain
pip install langchain-groq         # Groq API
pip install langchain-ollama       # Ollama (optional)
pip install fastapi uvicorn        # Web framework
pip install python-dotenv          # Environment variables
pip install pydantic               # Data validation

# For document processing
pip install python-multipart       # File uploads
pip install fitz pymupdf           # PDF extraction
```

### Step 2: Environment Configuration

Create `.env` file in `fusedchat_backend/`:

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=fusedchat

# Groq API (Get from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here

# Paths
UPLOAD_DIR=data/uploads
SYLLABUS_INDEX_PATH=vector_store/syllabus_index
TEMP_INDEX_PATH=vector_store/temp_doc_index

# Optional: Ollama Setup
OLLAMA_BASE_URL=http://localhost:11434
USE_OLLAMA_FALLBACK=false
```

### Step 3: Start MongoDB Locally

#### Option A: Docker (Recommended)
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

#### Option B: Local Installation
- Download from https://www.mongodb.com/try/download/community
- Start MongoDB service

#### Option C: MongoDB Atlas (Cloud)
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

### Step 4: Install Ollama (Optional)

For local LLM fallback:
1. Download from https://ollama.ai
2. Run: `ollama pull mistral`
3. Ollama will run on http://localhost:11434

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│               (http://localhost:3001)                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓ API Calls
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (8000)                  │
│                                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │    Query Router (Small LLM Classifier)       │   │
│  │    ↓         ↓           ↓                   │   │
│  │  PROF      ADMIN       DOCUMENT              │   │
│  │ BRAIN      BRAIN        BRAIN                │   │
│  └──────────────────────────────────────────────┘   │
│         ↓          ↓           ↓                    │
│      (Groq)   (JSON/RAG)  (ChromaDB)               │
│         ↓          ↓           ↓                    │
└─────────────────────────────────────────────────────┘
         ↓          ↓           ↓
    ┌────────┐  ┌────────┐  ┌──────────┐
    │ Groq   │  │MongoDB │  │ChromaDB  │
    │ API    │  │        │  │ /FAISS   │
    └────────┘  └────────┘  └──────────┘
```

---

## Database Schema Structure

### MongoDB Collections

```
fusedchat/
├── conversations          # All chat messages
├── document_uploads       # PDF metadata
├── sessions              # User sessions
├── users                 # User profiles
├── admin_data            # Hardcoded institute info (faculty, fees, etc)
├── feedback              # User ratings
└── analytics             # Usage stats
```

---

## Implementation Steps

### Phase 1: Backend Setup

#### 1.1 Update `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "fusedchat"
    
    # API Keys
    GROQ_API_KEY: str
    
    # Paths
    UPLOAD_DIR: str = "data/uploads"
    SYLLABUS_INDEX_PATH: str = "vector_store/syllabus_index"
    TEMP_INDEX_PATH: str = "vector_store/temp_doc_index"
    SYLLABUS_PATH: str = "data/syllabus"
    
    # Ollama (Optional)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    USE_OLLAMA_FALLBACK: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 1.2 Update `app/main.py`

Add MongoDB connection lifecycle:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo

app = FastAPI(title="FusedChat API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifecycle Events
@app.on_event("startup")
async def startup():
    await connect_to_mongo()
    print("✅ Application started")

@app.on_event("shutdown")
async def shutdown():
    await close_mongo()
    print("❌ Application shutting down")
```

#### 1.3 Create Brain Handlers

Create three separate modules:

**`app/services/professional_brain.py`**
```python
from langchain_groq import ChatGroq
from app.services.ingestion import load_index

async def answer_educational_query(query: str, mode: str, topic: str):
    """
    mode: "fast" (LLM only) or "deep" (RAG + Web search)
    """
    vector_store = load_index("vector_store/syllabus_index")
    
    if mode == "fast":
        # Direct LLM response
        response = llm.invoke(query)
    else:
        # Deep search: retrieve from vector store + web
        docs = vector_store.similarity_search(query, k=5)
        context = "\n".join([d.page_content for d in docs])
        # Add web search results...
        response = llm.invoke(f"Using context: {context}\n\nQuery: {query}")
    
    return response.content
```

**`app/services/admin_brain.py`**
```python
import json
from pathlib import Path

async def answer_admin_query(category: str, query: str):
    """
    Fetch from JSON files or vector store
    """
    data_map = {
        "faculty": "data/faculty.json",
        "fees": "data/fees_structure.json",
        "buses": "data/bus_routes.json",
        "placements": "vector_store/placement_pdfs"  # RAG
    }
    
    if category in ["faculty", "fees", "buses"]:
        with open(data_map[category]) as f:
            data = json.load(f)
        # Prompt LLM to extract answer from data
    else:
        # Query vector store for category
        pass
    
    return formatted_answer
```

**`app/services/document_brain.py`**
```python
from app.services.ingestion import build_index, load_index

async def answer_document_query(document_id: str, query: str):
    """
    Query uploaded PDF using RAG
    """
    vector_store = load_index(f"vector_store/temp_doc_index/{document_id}")
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    
    # Generate answer with citations
    response = llm.invoke(...)
    citations = [doc.metadata["source"] for doc in docs]
    
    return {
        "response": response.content,
        "citations": citations,
        "chunks_retrieved": len(docs)
    }
```

---

### Phase 2: Update Main Endpoints

Update `app/main.py` with new endpoints:

```python
from app.services.query_router import route_query
from app.services.professional_brain import answer_educational_query
from app.services.admin_brain import answer_admin_query
from app.services.document_brain import answer_document_query

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Unified chat endpoint that routes to appropriate brain
    """
    # Step 1: Route the query
    routing_info = await route_query(request.query, request.mode)
    brain = routing_info["brain"]
    
    if brain == "educational":
        response = await answer_educational_query(
            request.query,
            mode=routing_info["mode"],
            topic=routing_info["topic"]
        )
    elif brain == "admin":
        response = await answer_admin_query(
            routing_info["category"],
            request.query
        )
    else:  # document
        response = await answer_document_query(
            request.document_id,
            request.query
        )
    
    # Save to MongoDB
    await save_conversation(
        session_id=request.session_id,
        query=request.query,
        response=response,
        brain_type=brain
    )
    
    return {"response": response, "brain": brain}
```

---

### Phase 3: Frontend Updates

Update React to send document_id when in document mode:

```jsx
// In App.js

const handleSend = async () => {
  const payload = {
    session_id: sessionId.current,
    query: input,
    brain: isDocMode ? "document" : "professional",
    document_id: currentDocumentId,  // New
    mode: selectedMode  // "fast" or "deep"
  };
  
  const res = await axios.post(`${API_URL}/chat`, payload);
  // ...
};
```

---

## Testing the Three Brains

Run tests to verify each brain:

```bash
cd fusedchat_backend

# Test Query Router
python -m app.services.query_router

# Expected output:
# Query: Explain linked lists
# Brain: EDUCATIONAL
# Topic: Linked Lists
```

```bash
# Test with real API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_123",
    "query": "Who is the HOD of CSE?",
    "mode": "admin"
  }'
```

---

## Performance Optimization

### 1. Caching Responses
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_answer(query_hash: str):
    # Returns cached answer for similar queries
    pass
```

### 2. Batch Processing for Vector Embeddings
```python
# Process uploads in background
from celery import Celery

@app.post("/upload")
async def upload_document(file: UploadFile):
    # Save file
    # Queue embedding job
    task = process_pdf.delay(file_path)
    # Return immediately
    return {"status": "processing", "task_id": task.id}
```

### 3. MongoDB Indexing
Already handled in `database.py` - indexes created automatically.

---

## Monitoring & Analytics

Track:
- Which brain is used most?
- Average response time per brain
- User satisfaction ratings
- Document upload patterns

```python
"""In MongoDB queries collection"""

# Get usage stats
db.conversations.aggregate([
    {"$group": {
        "_id": "$type",
        "count": {"$sum": 1},
        "avg_rating": {"$avg": "$rating"}
    }}
])
```

---

## Troubleshooting

### MongoDB Connection Error
```
Error: Cannot connect to MongoDB
Solution: Ensure MongoDB is running (docker ps or check service)
```

### Query Router Always Returns "Educational"
```
Error: All queries routed to same brain
Solution: Check Groq API key in .env, verify classifier_llm initialization
```

### ChromaDB Permission Error
```
Error: Permission denied on vector_store directory
Solution: chmod 755 vector_store/ (Linux/Mac) or run as admin (Windows)
```

---

## Next: Frontend Integration

With the backend ready, update React frontend to:
1. ✅ Show which brain answered
2. ✅ Display confidence scores
3. ✅ Show citations for document mode
4. ✅ Add Knowledge Graph visualization
5. ✅ Implement user dashboard

---

## Summary

You now have:
- ✅ Query Router (intelligent brain selector)
- ✅ Professional Brain (educational Q&A)
- ✅ Admin Brain (institute information)
- ✅ Document Brain (PDF analysis)
- ✅ MongoDB integration (conversation logging)
- ✅ ChromaDB integration (vector search)

**Ready to deploy! 🚀**
