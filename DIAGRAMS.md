# 🎨 FusedChat Architecture Diagrams

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    FusedChat Three-Brain                      │
│                   AI Educational Platform                    │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   React Frontend (Port 3001)                 │
│                                                              │
│    ┌─────────────┐   ┌─────────────┐   ┌──────────────┐    │
│    │   Chat UI   │   │   Sidebar   │   │   Upload     │    │
│    │             │   │  Brain Sel. │   │   Widget     │    │
│    └─────────────┘   └─────────────┘   └──────────────┘    │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/JSON
                       │
┌──────────────────────┴───────────────────────────────────────┐
│          FastAPI Backend (Port 8000)                         │
│          ┌────────────────────────────────────┐             │
│          │    POST /chat    (Main Endpoint)   │             │
│          └────────────────────┬────────────────┘             │
│                               │                             │
│          ┌────────────────────┴────────────────┐             │
│          │     Query Router (Brain Selector)  │             │
│          │     └─ Small Fast LLM              │             │
│          │     └─ Classifies Query            │             │
│          └────────────────┬────────────────────┘             │
│                           │                                 │
│        ┌──────────────────┼──────────────────┐              │
│        │                  │                  │              │
│        ↓                  ↓                  ↓              │
│    ┌────────┐         ┌────────┐       ┌────────┐          │
│    │ PROF   │         │ ADMIN  │       │ DOCUMENT           │
│    │ BRAIN  │         │ BRAIN  │       │ BRAIN             │
│    └────┬───┘         └────┬───┘       └────┬───┘          │
│         │                  │                │              │
│    Groq LLM           JSON Lookup      ChromaDB RAG        │
│    + FAISS             + Groq           + Groq LLM         │
│                                                             │
└─────────┬──────────────────┬──────────────────┬─────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
      ┌──────────┐     ┌──────────┐     ┌──────────────┐
      │  Groq    │     │ MongoDB  │     │ ChromaDB     │
      │  API     │     │ Database │     │ Vector Store │
      │          │     │          │     │              │
      │ llama3   │     │ convo    │     │ Embeddings   │
      │ 70b      │     │ sessions │     │ (Vectors)    │
      └──────────┘     │ users    │     └──────────────┘
                       │ admin    │
                       └──────────┘
```

---

## Query Flow Diagram

### Example 1: Educational Query

```
User Input: "Explain linked lists"
│
├─→ Query Router (LLM Classifier)
│   └─→ Classification: EDUCATIONAL
│
├─→ Professional Brain Activated
│   │
│   ├─→ Extract Topic: "Linked Lists"
│   │
│   ├─→ Check Mode
│   │   ├─ Fast Mode: Direct LLM answer
│   │   └─ Deep Mode: Vector search + Web search
│   │
│   ├─→ FAISS Vector Store
│   │   └─→ Retrieve: "Top 5 chunks about Linked Lists"
│   │       └─→ "Linked lists are data structures..."
│   │
│   ├─→ Generate Answer
│   │   └─→ Groq LLM
│   │       └─→ "Linked lists are data structures where each..."
│   │
│   └─→ Format Response
│       └─→ Add sources, confidence, timing
│
├─→ Save to MongoDB
│   └─→ conversations collection
│       {type: "educational_query", response: "...", rating: null}
│
└─→ Send Response to Frontend
    └─→ "Linked lists are..." [4.6s] [Sources: Lecture 5]
```

### Example 2: Admin Query

```
User Input: "Who is the HOD of CSE?"
│
├─→ Query Router (LLM Classifier)
│   └─→ Classification: ADMIN
│
├─→ Admin Brain Activated
│   │
│   ├─→ Extract Category: "faculty"
│   │
│   ├─→ Load Data Source
│   │   └─→ faculty.json (hardcoded)
│   │       {
│   │         "department": "CSE",
│   │         "hod": "Dr. Rajesh Kumar",
│   │         "email": "rajesh.kumar@sasi.ac.in"
│   │       }
│   │
│   ├─→ Extract Relevant Info
│   │   └─→ Use Groq to format answer
│   │
│   └─→ Generate Response
│       └─→ "Dr. Rajesh Kumar is the HOD of CSE..."
│
├─→ Save to MongoDB
│   └─→ conversations collection
│       {type: "admin_query", response: "...", category: "faculty"}
│
└─→ Send Response to Frontend
    └─→ "Dr. Rajesh Kumar is..." [0.5s]
```

### Example 3: Document Query

```
Step 1: UPLOAD
User: Upload "Unit_1_Notes.pdf"
│
├─→ Document Brain (Upload Handler)
│   │
│   ├─→ Extract Text from PDF
│   │   └─→ fitz (PyMuPDF) → raw text
│   │
│   ├─→ Chunk & Vectorize
│   │   ├─→ Split into 50 chunks (512 tokens each)
│   │   ├─→ Generate embeddings (BAAI/bge-large-en-v1.5)
│   │   └─→ Store in ChromaDB
│   │
│   ├─→ Generate Summary
│   │   └─→ LLM reads all chunks
│   │       └─→ Output: "This document covers arrays, linked lists..."
│   │
│   ├─→ Save Metadata to MongoDB
│   │   └─→ document_uploads collection
│   │       {
│   │         filename: "Unit_1_Notes.pdf",
│   │         summary: "Covers arrays and linked lists",
│   │         chunk_count: 50,
│   │         topics: ["Arrays", "Linked Lists"],
│   │         vector_store_location: "chroma_uploads/unit_1_notes"
│   │       }
│   │
│   └─→ Return: "Document processed! 50 chunks indexed"
│
└─→ Frontend: "✅ Document indexed successfully!"


Step 2: QUERY
User: "What is array initialization?"
│
├─→ Query Router (LLM Classifier)
│   └─→ Classification: DOCUMENT
│
├─→ Document Brain (Query Handler)
│   │
│   ├─→ Semantic Search in ChromaDB
│   │   └─→ Convert query to embedding
│   │       └─→ Find top-3 similar chunks
│   │           [0.92 similarity] "Array initialization assignments..."
│   │           [0.87 similarity] "Memory allocation for arrays..."
│   │           [0.84 similarity] "Array indexing begins at zero..."
│   │
│   ├─→ Retrieve Full Chunks + Metadata
│   │   └─→ Page numbers, positions, content
│   │
│   ├─→ Generate Answer with Citations
│   │   └─→ Groq LLM receives:
│   │       Context: [3 retrieved chunks]
│   │       Query: "What is array initialization?"
│   │       
│   │       └─→ Output: "Array initialization is the process..."
│   │           Citations: 
│   │           - "[Page 2, Para 1]"
│   │           - "[Page 3, Para 2]"
│   │
│   └─→ Format Response
│       └─→ {response: "...", citations: [...], chunks: 3}
│
├─→ Save to MongoDB
│   └─→ conversations collection
│       {
│         type: "document_query",
│         query: "What is array initialization?",
│         response: "...",
│         citations: ["[Page 2, Para 1]"],
│         chunks_retrieved: 3
│       }
│
└─→ Send Response to Frontend
    └─→ Answer text + citations display
```

---

## Database Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MongoDB (fusedchat)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Collections:                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ conversations                                    │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ _id          │ ObjectId                          │  │
│  │ type         │ "educational_query"              │  │
│  │ session_id   │ "user_abc123"                    │  │
│  │ user_id      │ "student_001"                    │  │
│  │ query        │ "Explain linked lists"           │  │
│  │ response     │ "Linked lists are..."            │  │
│  │ timestamp    │ 2026-02-13T10:30:00Z            │  │
│  │ metadata     │ {brain, confidence, ...}         │  │
│  │ rating       │ null (user rates later)          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ document_uploads                                 │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ _id                  │ ObjectId                  │  │
│  │ session_id           │ "user_abc123"            │  │
│  │ filename             │ "Unit_1_Notes.pdf"       │  │
│  │ upload_timestamp     │ 2026-02-13T10:20:00Z    │  │
│  │ summary              │ "Covers arrays..."       │  │
│  │ chunk_count          │ 50                       │  │
│  │ vector_store_loc     │ "chroma_uploads/unit1"   │  │
│  │ topics               │ ["Arrays", "Lists"]      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ sessions                                         │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ _id          │ ObjectId                          │  │
│  │ session_id   │ "user_abc123"                    │  │
│  │ user_id      │ "student_001"                    │  │
│  │ created_at   │ 2026-02-13T10:00:00Z            │  │
│  │ total_queries│ 25                               │  │
│  │ query_by_brain│ {prof: 15, admin: 7, doc: 3}   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ users                                            │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ _id          │ ObjectId                          │  │
│  │ user_id      │ "student_001"                    │  │
│  │ email        │ "student@sasi.ac.in"             │  │
│  │ name         │ "Akhil Busi"                     │  │
│  │ branch       │ "CSE"                            │  │
│  │ semester     │ 5                                │  │
│  │ created_at   │ 2025-01-01T00:00:00Z            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               ChromaDB (Vector Store)                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Collection: professional_brain                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ id: "cse_dsa_unit2_chunk_001"                   │  │
│  │ embedding: [1.23, -0.45, ..., 0.89] (1536D)    │  │
│  │ document: "Linked lists are data structures..." │  │
│  │ metadata: {                                      │  │
│  │   branch: "CSE",                                │  │
│  │   semester: 3,                                  │  │
│  │   unit: "Unit 2",                               │  │
│  │   topic: "Linked Lists",                        │  │
│  │   page: 15                                      │  │
│  │ }                                               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Collection: document_uploads                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ id: "unit_1_notes_chunk_001"                    │  │
│  │ embedding: [0.12, 0.34, ..., 0.56]             │  │
│  │ document: "Array initialization assigns mem..."  │  │
│  │ metadata: {                                      │  │
│  │   session_id: "user_abc123",                    │  │
│  │   file: "Unit_1_Notes.pdf",                     │  │
│  │   source: "page_2_para_1",                      │  │
│  │   page_num: 2                                   │  │
│  │ }                                               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│           Data Files (JSON - Hardcoded)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  bus_routes.json         →  Bus transport info         │
│  faculty.json            →  Faculty directory + HODs   │
│  fees_structure.json     →  Fee structure by batch     │
│  placement_data.json     →  Placement stats            │
│  hostel_info.json        →  Hostel information         │
│  academic_calendar.json  →  Important dates            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Component Interaction

```
┌────────────────────────────────────────────────────────────┐
│                  React Frontend                            │
│                                                            │
│  ┌─────────────────┐         ┌──────────────────┐        │
│  │  Sidebar        │         │  ChatDisplay     │        │
│  │  ┌────────────┐ │         │  ┌────────────┐ │        │
│  │  │ Brain Sel  │ │         │  │ Messages   │ │        │
│  │  │ - Prof     │ │         │  │ User: "..." │ │        │
│  │  │ - Admin    │ │         │  │ Bot: "..." │ │        │
│  │  │ - Document │ │         │  │            │ │        │
│  │  └────────────┘ │         │  └────────────┘ │        │
│  │  ┌────────────┐ │         │  ┌────────────┐ │        │
│  │  │ Upload Box │ │         │  │ InputBar   │ │        │
│  │  │ (Doc mode) │ │         │  │ + SendBtn  │ │        │
│  │  └────────────┘ │         │  └────────────┘ │        │
│  └─────────────────┘         └──────────────────┘        │
│           │                           │                  │
│           └───────────────┬───────────┘                  │
│                           │                              │
│       setIsDocMode()    dispatch                         │
│       setInput()        handleSend()                      │
│                           │                              │
└───────────────────────────┼──────────────────────────────┘
                            │ API Calls
                            ↓
                  ┌─────────────────┐
                  │ FastAPI Backend │
                  └────────┬────────┘
                           │
                  POST /chat (data)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Route Classify      Process         Save to DB
        │              Response             │
        ↓              (LLM)                ↓
   Query Router      Answer Gen       MongoDB
        │                │            (conversations)
   Brain Select          │            (document_uploads)
        │                │            (sessions)
        ↓                ↓
   ┌─────────────────────────┐
   │   Brain Engine          │
   ├─────────────────────────┤
   │ • Professional Brain    │
   │ • Admin Brain           │
   │ • Document Brain        │
   └─────────────────────────┘
        │
        └──→ Vector Store
             (ChromaDB/FAISS)
             
             JSON Files
             (hardcoded data)
             
             Groq API
             (LLM inference)
```

---

## Data Flow During Chat

```
User Types Message
        │
        ↓
React Component
  setInput(msg)
  handleSend()
        │
        ↓ Payload
┌─────────────────────────┐
│ {                       │
│   session_id: "...",    │
│   query: "...",         │
│   mode: "fast/deep",    │
│   brain: "auto"         │
│ }                       │
└──────────┬──────────────┘
           │
           ↓ axios.post(API)
           │
    ┌──────────────────────────────────┐
    │  FastAPI /chat endpoint          │
    └────────────┬─────────────────────┘
                 │
                 ↓ Classify
        ┌────────────────────┐
        │ Query Router       │
        │ (Small LLM)        │
        │ ↓  (0.3s)          │
        │ → EDUCATIONAL      │
        │ → ADMIN            │
        │ → DOCUMENT         │
        └────────────┬───────┘
                     │ Brain Type
                     ↓
             ┌───────────────┐
             │ Select Brain  │
             │               │
             ├─ Professional │ → FAISS + Groq
             ├─ Admin        │ → JSON + Groq  
             └─ Document     │ → ChromaDB + Groq
                     │
                     ↓ Execute Brain Logic (1-3s)
                     
             ┌───────────────────────────┐
             │ Generate Answer           │
             │                           │
             │ LLM (Groq) processes      │
             │ ↓ (with context if RAG)   │
             │ Returns formatted text    │
             └───────┬───────────────────┘
                     │
                     ↓ Save to MongoDB
            ┌────────────────────┐
            │ conversations      │
            │ + metadata         │
            │ + timestamps       │
            └────────┬───────────┘
                     │
         ↓ Response JSON Back to Frontend
┌──────────────────────────────────┐
│ {                                │
│   response: "Linked lists are..",│
│   brain: "professional",         │
│   metadata: {                    │
│     confident: 0.92,             │
│     response_time: 2350ms        │
│   }                              │
│ }                                │
└──────────────────────────────────┘
           │
           ↓ React receives
    
Message appears in chat
Load state disappears
Response displays with brain icon
```

---

## Memory Management Strategy

```
┌─────────────────────────────────────────────────────────┐
│        SPLIT BRAIN MEMORY PATTERN                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ⚠️ WRONG APPROACH (Don't do this!)                    │
│ ┌─────────────────────────────────────────────────────┐│
│ │ MongoDB stores:                                    ││
│ │ {                                                  ││
│ │   document: "50MB of full PDF text",             ││
│ │   formatted_text: "Even more text...",           ││
│ │   chunks: [{full_chunk_1}, {full_chunk_2}, ...] ││
│ │ }                                                  ││
│ │                                                   ││
│ │ Problems:                                         ││
│ │ ✗ MongoDB explodes in size                       ││
│ │ ✗ AI gets confused with too much context         ││
│ │ ✗ Slow queries and indexing                      ││
│ │ ✗ High storage costs at scale                    ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ ✅ CORRECT APPROACH (Do this!)                        │
│ ┌─────────────────────────────────────────────────────┐│
│ │ MongoDB stores (Lightweight):                     ││
│ │ {                                                  ││
│ │   filename: "Unit_1_Notes.pdf",                  ││
│ │   summary: "3-4 sentence overview",              ││
│ │   topics: ["Arrays", "Linked Lists"],            ││
│ │   chunks_count: 50,                              ││
│ │   vector_store_ref: "chroma_uploads/unit_1"      ││
│ │ }                                                  ││
│ │ Size: < 1KB ✓                                    ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ ChromaDB stores (Vector Database):                   │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Chunk 1:                                           ││
│ │ ├─ ID: "chunk_001"                               ││
│ │ ├─ Embedding: [1.23, -0.45, ...]  (1536 values) ││
│ │ ├─ Text: "Array initialization assigns..."      ││
│ │ └─ Metadata: {page: 2, para: 1}                  ││
│ │                                                   ││
│ │ Chunk 2:                                           ││
│ │ ├─ ID: "chunk_002"                               ││
│ │ ├─ Embedding: [0.12, 0.34, ...]                 ││
│ │ ├─ Text: "Memory allocation for arrays..."       ││
│ │ └─ Metadata: {page: 3, para: 2}                  ││
│ │ ...                                               ││
│ │                                                   ││
│ │ When query arrives:                              ││
│ │ 1. Convert query to embedding                    ││
│ │ 2. Find top-3 similar chunks                     ││
│ │ 3. Pass ONLY those chunks to LLM                 ││
│ │ 4. LLM generates answer                          ││
│ │ 5. LLM adds citations with page numbers          ││
│ │                                                   ││
│ │ Benefits: ✓ Fast ✓ Accurate ✓ Efficient         ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Visualization

This is architecture for **production-grade RAG system**! 

The split brain approach is used by:
- OpenAI's ChatGPT (GPT-4 knowledge retrieval)
- Google's PaLM RAG
- Enterprise LLM systems

You're implementing enterprise-level architecture! 🚀

---

*Diagrams generated: February 13, 2026*
