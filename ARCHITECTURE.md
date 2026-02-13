# FusedChat Three-Brain Architecture

## Project Overview

**FusedChat** is an AI-powered educational platform for SASI Institute of Technology & Engineering with three specialized "brains":

1. **Professional Brain** - Syllabus-based educational Q&A
2. **Administrator Brain** - Institute information lookup
3. **Document Analyst Brain** - PDF analysis and RAG

---

## Brain #1: Professional Brain (Education Chatbot)

### Purpose
Students ask concept questions within the college curriculum.

### Example
**Input:** "Explain Linked Lists"  
**Process:**
1. Query Router identifies this is an educational query
2. Checks JSON Syllabus Map (CSE Branch, Semester 3, etc.)
3. Verifies topic is in curriculum
4. LLM generates personalized explanation

### Two Modes
- **Mode 1 (Fast):** Brief answer from LLM only
- **Mode 2 (Deep):** Search YouTube/websites + vector search for relevant materials + comprehensive answer

### Tech Stack
- **LLM:** Groq API (fast), Ollama (backup)
- **Vector Store:** FAISS (syllabus embeddings)
- **Data Source:** college_syllabus.json (extracted from PDFs)

### MongoDB Schema
```json
{
  "type": "educational_query",
  "session_id": "abc123",
  "user_id": "student_001",
  "query": "Explain Linked Lists",
  "mode": "deep",  // or "fast"
  "branch": "CSE",
  "semester": 3,
  "timestamp": "2026-02-13T10:30:00Z",
  "response": "...",
  "sources": ["Lecture 5", "Textbook Ch 3"],
  "rating": 4.5
}
```

---

## Brain #2: Administrator Brain (Institute Brain)

### Purpose
Answer questions about institute policies, facilities, and administration.

### Example
**Input:** "Who is the HOD of CSE?"  
**Process:**
1. Query Router identifies this is an admin query
2. Checks appropriate data source (JSON hardcoded or RAG PDF)
3. Retrieves from MongoDB cached data
4. Returns answer

### Data Sources & Strategy

| Feature | Data Source | Strategy | Storage |
|---------|------------|----------|---------|
| Bus Routes | sasi.ac.in/transport | Hardcode (static) | bus_routes.json |
| Exam Fees | sasi.ac.in/autonomous | RAG (PDF upload) | Vector Store + MongoDB |
| Tuition Fees | sasi.ac.in/fee-structure | Hardcode (fixed per batch) | fees_structure.json |
| Placements | sasi.ac.in/placements | RAG (Placement Analysis PDF) | Vector Store |
| Faculty Directory | sasi.ac.in/faculty | Hardcode or API | faculty.json |
| Hostel Info | sasi.ac.in/hostel | RAG or Hardcode | hostel_info.json |

### MongoDB Schema
```json
{
  "type": "admin_query",
  "session_id": "abc123",
  "user_id": "student_001",
  "query": "Who is the HOD of CSE?",
  "query_category": "faculty",  // [faculty, fees, buses, placements, hostel, etc]
  "timestamp": "2026-02-13T10:30:00Z",
  "response": "Dr. Rajesh Kumar",
  "data_source": "faculty.json",
  "confidence": 0.95
}
```

---

## Brain #3: Document Analyst (NotebookLM Mode)

### Purpose
Students upload PDFs and get RAG-based answers with citations.

### Example
**Input:** Upload "Unit_1_Notes.pdf" + "What is Array initialization?"  
**Process:**
1. PDF chunked and vectorized → ChromaDB
2. Summary generated: "Covers array basics, allocation, multi-dimensional arrays"
3. Summary stored in MongoDB (NOT full PDF)
4. User question queries ChromaDB for relevant chunks
5. LLM answers with exact citations

### Split Brain Memory Strategy

**MongoDB (Conversation Log):**
- Only stores: User messages + summaries + metadata
- Never stores: Full PDF text

**ChromaDB/FAISS (Knowledge Base):**
- Stores: PDF chunks (vectors) with metadata
- Enables: Fast semantic search

### MongoDB Schema

**Upload Event:**
```json
{
  "type": "document_upload",
  "session_id": "abc123",
  "user_id": "student_001",
  "document": {
    "filename": "Unit_1_Notes.pdf",
    "upload_timestamp": "2026-02-13T10:20:00Z",
    "size_mb": 2.5,
    "summary": "Covers array initialization, memory allocation, and dynamically sized arrays.",
    "topics": ["Array Basics", "Memory Management", "Dynamic Arrays"],
    "chunk_count": 45,
    "vector_store_location": "chroma_doc_uploads/unit_1_notes"
  },
  "status": "processed"
}
```

**Query Event:**
```json
{
  "type": "document_query",
  "session_id": "abc123",
  "user_id": "student_001",
  "document_id": "unit_1_notes_001",
  "query": "What is array initialization?",
  "retrieved_chunks": 3,
  "citations": [
    "Page 2, Para 1: 'Array initialization is the process...'",
    "Page 3, Para 2: 'Static allocation requires...'"
  ],
  "response": "...",
  "confidence": 0.92,
  "timestamp": "2026-02-13T10:32:00Z"
}
```

---

## Query Router (Brain Selector) 🧠

The Query Router is the "smart dispatcher" that reads incoming queries and routes them to the correct brain.

### How It Works

```
User Query
    ↓
Query Router (Small, Fast LLM)
    ├─→ Professional Brain (educational content)
    ├─→ Admin Brain (institute info)
    └─→ Document Brain (uploaded PDFs)
```

### Logic

```python
def route_query(query: str) -> str:
    # Use a small, fast LLM to classify
    classification = fast_llm(f"Classify query as: educational, admin, or document. Query: {query}")
    
    if "document" in classification:
        return "document_brain"
    elif "institute" in classification or "admin" in classification:
        return "admin_brain"
    else:
        return "professional_brain"
```

---

## Database Architecture

### 1. MongoDB (Conversation Memory)

**Connection:** `mongodb+srv://user:pass@cluster.mongodb.net/fusedchat`

**Collections:**
- `conversations` - Chat history
- `users` - Student profiles
- `sessions` - Active sessions
- `admin_data` - Hardcoded institute info
- `feedback` - User ratings and feedback

### 2. ChromaDB (Vector Store - Local)

**Location:** `./vector_stores/chroma/`

**Collections:**
- `professional_brain` - Syllabus embeddings
- `document_uploads` - User-uploaded PDFs (per session)
- `admin_knowledge` - FAQ embeddings

### 3. JSON Data Files

**Location:** `./data/`

```
data/
├── college_syllabus.json       # Syllabus Map
├── faculty.json                # Faculty directory
├── bus_routes.json             # Bus information
├── fees_structure.json         # Tuition fees
├── placement_data.json         # Placement stats
└── hostel_info.json            # Hostel details
```

---

## LLM Configuration

### Groq API (Primary)
- **Model:** `llama3-70b-8192`
- **Use Case:** Professional Brain + Query Router
- **Cost:** Fast and free (1000 requests/day free tier)

### Ollama (Backup/Local)
- **Model:** `mistral` or `llama2` (local)
- **Use Case:** Self-hosted fallback
- **Cost:** Free, privacy-first

### Query Router LLM
- **Model:** Groq's smaller model or `mistral:7b` (Ollama)
- **Purpose:** Fast 2-3 second classification

---

## Frontend Integration

The React frontend will have:

1. **Query Input Bar**
   - Unified input for all three brains
   - Auto-detection of query type

2. **Admin Sidebar**
   - Toggle between brains
   - Document upload
   - Settings

3. **Response Display**
   - Shows which brain answered
   - Citations for document brain
   - Confidence score
   - Related topics

4. **Knowledge Graph**
   - Visual representation of connected concepts
   - Shows topic prerequisites
   - Links to related documents

---

## Implementation Phases

### Phase 1: Core Setup (Week 1)
- [ ] MongoDB schema design
- [ ] ChromaDB integration
- [ ] Groq API + Ollama config
- [ ] Query Router implementation

### Phase 2: Professional Brain (Week 2)
- [ ] Syllabus JSON extraction
- [ ] Fast & Deep modes
- [ ] Vector search implementation
- [ ] YouTube/web search integration

### Phase 3: Admin Brain (Week 3)
- [ ] Data source setup (JSON + RAG PDFs)
- [ ] FAQ embeddings
- [ ] Caching strategy

### Phase 4: Document Brain (Week 4)
- [ ] PDF chunking & summarization
- [ ] Upload workflow
- [ ] Citation generation

### Phase 5: Frontend + Knowledge Graph (Week 5)
- [ ] React components for all brains
- [ ] Knowledge graph visualization
- [ ] Settings & user profiles

---

## Security & Privacy

- MongoDB credentials in `.env`
- API keys encrypted
- Document uploads stored securely
- User data anonymization options
- GDPR compliance ready

---

## Monitoring & Analytics

Track:
- Query distribution (which brain is used most?)
- Response accuracy (user ratings)
- Response time per brain
- Document upload patterns
- User learning progress

---

## Next Steps

1. ✅ Review this architecture
2. ⏳ Start with MongoDB + ChromaDB setup
3. ⏳ Build Query Router
4. ⏳ Implement Professional Brain
5. ⏳ Add Admin Brain
6. ⏳ Complete Document Brain
7. ⏳ Frontend integration
8. ⏳ Knowledge Graph visualization
