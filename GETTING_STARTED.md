# 🚀 FusedChat - Getting Started Guide

**Welcome to FusedChat!** A fully-functional, three-brain AI educational platform for SASI Institute of Technology & Engineering.

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** February 13, 2026

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites
- Python 3.9+
- Node.js 16+
- Groq API Key (free at https://console.groq.com)

### 1️⃣ Clone & Setup Environment

```bash
# Navigate to backend directory
cd fusedchat_backend

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here
MONGO_URL=mongodb://localhost:27017
UPLOAD_DIR=data/uploads/
SYLLABUS_PATH=data/syllabus/syllabus.pdf
SYLLABUS_INDEX_PATH=vector_store/syllabus_index
EOF
```

### 2️⃣ Install Dependencies

```bash
# Backend
cd fusedchat_backend
pip install -r requirements.txt

# Frontend
cd ../fusedchat_frontend
npm install
```

### 3️⃣ Start Backend

```bash
cd fusedchat_backend
uvicorn app.main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### 4️⃣ Start Frontend (New Terminal)

```bash
cd fusedchat_frontend
npm start
# or: PORT=3001 npm start
```

Automatically opens in browser at `http://localhost:3001`

### 5️⃣ Test the System

Choose a brain from the sidebar and start chatting! 🎉

---

## 🧠 Understanding the Three Brains

### Professional Brain 🎓
**Purpose:** Educational Q&A with curriculum constraints

**Features:**
- ⚡ **Fast Mode**: Quick, concise answers
- 🔬 **Deep Mode**: Comprehensive research with web search
- 📚 **Syllabus-constrained**: Stays within curriculum
- 📊 **Confidence scoring**: Shows answer reliability

**Example Queries:**
- "What is a linked list?"
- "Explain binary trees in detail"
- "How do hash tables work?"

### Administrator Brain 🤖
**Purpose:** Campus & administrative information

**Features:**
- 📋 **Faculty directory**: HOD and department info
- 🚌 **Bus routes**: Transportation schedules
- 💰 **Fee structure**: Tuition and exam fees
- 📅 **Academic calendar**: Dates and schedules

**Example Queries:**
- "Who is the CSE HOD?"
- "What are bus timings to Chennai?"
- "How much are the tuition fees?"

### Document Brain 📄
**Purpose:** PDF analysis with Retrieval-Augmented Generation (RAG)

**Features:**
- 📤 **Easy upload**: Drag-and-drop PDF support
- 🔍 **Semantic search**: Find relevant sections
- 📍 **Citations**: Shows exact page references
- ✅ **Zero hallucination**: Only uses document content

**Workflow:**
1. Upload a PDF document
2. Ask questions about it
3. Get answers with exact citations

**Example Documents:**
- Lecture notes
- Textbook chapters
- Research papers
- Exam models

---

## 📁 Project Structure

```
final_cahtbot/
├── fusedchat_backend/
│   ├── app/
│   │   ├── main.py              ✅ FastAPI entry point
│   │   ├── config.py            ✅ Configuration
│   │   ├── database.py          ✅ MongoDB schemas
│   │   ├── services/
│   │   │   ├── professional_brain.py    ✅ Education chatbot
│   │   │   ├── admin_brain.py           ✅ Institute info
│   │   │   ├── document_brain.py        ✅ PDF analysis
│   │   │   ├── query_router.py          ✅ Brain selector
│   │   │   └── ingestion.py      ✅ PDF processing
│   │   └── models/
│   │       └── schemas.py        ✅ Data models
│   ├── data/
│   │   ├── syllabus/            📂 Syllabus PDFs
│   │   ├── uploads/             📂 User-uploaded PDFs
│   │   ├── faculty.json         ✅ Faculty data
│   │   ├── bus_routes.json      ✅ Bus schedule
│   │   └── fees_structure.json  ✅ Fee data
│   ├── vector_store/
│   │   └── syllabus_index/      📂 FAISS vectors
│   ├── requirements.txt         ✅ Dependencies
│   └── .env                     📝 Configuration
│
├── fusedchat_frontend/
│   ├── src/
│   │   ├── App.js              ✅ Main component
│   │   ├── App.css             ✅ Styling
│   │   └── index.js            ✅ Entry point
│   ├── package.json            ✅ Dependencies
│   └── public/                 📂 Static assets
│
├── FusedChat_Testing_Guide.ipynb  ✅ Interactive testing
├── INDEX.md                       ✅ Documentation index
├── SUMMARY.md                     ✅ Project summary
├── ARCHITECTURE.md                ✅ Technical design
├── IMPLEMENTATION_GUIDE.md        ✅ Setup steps
├── COMPLETE_GUIDE.md              ✅ Full reference
└── SETUP_CHECKLIST.md             ✅ Verification
```

---

## 🔌 API Endpoints

### Chat Endpoints

**POST `/chat`** - Main chat endpoint
```json
{
  "session_id": "unique-session-id",
  "query": "What is a linked list?",
  "mode": "fast"  // or "deep" for Professional Brain
}
```

**POST `/chat/document`** - Document-specific chat
```json
{
  "session_id": "unique-session-id",
  "document_id": "doc-id-from-upload",
  "query": "What is the main topic?"
}
```

### Document Endpoints

**POST `/upload`** - Upload PDF
```
multipart/form-data:
- file: <PDF file>
- session_id: <optional>
```

### Utility Endpoints

**GET `/history/{session_id}`** - Get conversation history

**GET `/health`** - Health check

**GET `/docs`** - Interactive API documentation (Swagger)

---

## 🎯 API Testing Guide

### Using Python Requests

```python
import requests
from uuid import uuid4

API_URL = "http://127.0.0.1:8000"
session_id = str(uuid4())

# Test 1: Professional Brain (Fast Mode)
response = requests.post(f"{API_URL}/chat", json={
    "session_id": session_id,
    "query": "What is a linked list?",
    "mode": "fast"
})
print(response.json())

# Test 2: Admin Brain
response = requests.post(f"{API_URL}/chat", json={
    "session_id": session_id,
    "query": "Who is the CSE HOD?"
})
print(response.json())

# Test 3: Upload Document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{API_URL}/upload", files=files, 
                           data={"session_id": session_id})
    doc_id = response.json()["document_id"]

# Test 4: Chat about Document
response = requests.post(f"{API_URL}/chat/document", json={
    "session_id": session_id,
    "document_id": doc_id,
    "query": "What is the main topic?"
})
print(response.json())
```

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "query": "What is machine learning?",
    "mode": "fast"
  }'

# API Docs
open http://localhost:8000/docs
```

---

## 🔧 Configuration

### Backend (.env file)

```env
# Groq API (Required)
GROQ_API_KEY=gsk_your_key_here

# MongoDB (Optional - defaults to local)
MONGO_URL=mongodb://localhost:27017
# OR for Atlas
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/dbname

# File paths
UPLOAD_DIR=data/uploads/
SYLLABUS_PATH=data/syllabus/syllabus.pdf
SYLLABUS_INDEX_PATH=vector_store/syllabus_index

# Optional
DEBUG=true
LOG_LEVEL=INFO
```

### Frontend Configuration

Edit `src/App.js` to change:
```javascript
const API_URL = "http://127.0.0.1:8000";  // Backend URL
```

---

## 🐛 Troubleshooting

### Backend Issues

❌ **"ModuleNotFoundError: No module named 'app'"**
```bash
# Solution: Run from correct directory
cd fusedchat_backend
python -m app.services.professional_brain
```

❌ **"FAISS Index Not Found"**
```bash
# Solution: Place syllabus PDF in correct location
mkdir -p data/syllabus/
# Then add your syllabus.pdf file
# Index builds automatically on first run
```

❌ **"Groq API Error"**
```bash
# Solution: Check your API key
export GROQ_API_KEY=gsk_your_key_here
# (Windows) set GROQ_API_KEY=gsk_your_key_here
```

❌ **"MongoDB Connection Error"**
```bash
# Solution A: Start local MongoDB
mongod

# Solution B: Use MongoDB Atlas (cloud)
# Get connection string from: https://www.mongodb.com/atlas
# Add to .env: MONGO_URL=mongodb+srv://...
```

### Frontend Issues

❌ **"Cannot GET /chat"**
```bash
# Solution: Ensure backend is running
cd fusedchat_backend
uvicorn app.main:app --reload
```

❌ **"Port 3001 already in use"**
```bash
# Solution: Use different port
PORT=3002 npm start
```

❌ **"axios error: Network Error"**
```bash
# Solution: Check backend URL in src/App.js
# Must match: http://127.0.0.1:8000
```

---

## 📊 Data Preparation

### Add Your Syllabus

1. **Place PDF in correct location:**
   ```bash
   mkdir -p data/syllabus/
   # Copy your syllabus PDF as: data/syllabus/syllabus.pdf
   ```

2. **Index builds automatically on startup** (takes ~30 seconds for large PDFs)

3. **Verify index was built:**
   ```bash
   ls -la vector_store/syllabus_index/
   # Should show: index.faiss, index.pkl
   ```

### Update Faculty Information

Edit `data/faculty.json`:
```json
{
  "departments": [
    {
      "name": "Computer Science & Engineering",
      "code": "CSE",
      "hod": {
        "name": "Dr. Name",
        "email": "hod@sasi.ac.in",
        "phone": "+91-xxx-xxxx"
      }
    }
  ]
}
```

### Update Bus Routes

Edit `data/bus_routes.json`:
```json
{
  "routes": [
    {
      "route_name": "Chennai",
      "departure_time": "08:00 AM",
      "arrival_time": "06:00 PM",
      "stops": ["Campus", "City Center", "Airport"]
    }
  ]
}
```

### Update Fee Structure

Edit `data/fees_structure.json`:
```json
{
  "batches": [
    {
      "batch": 2025,
      "tuition_fee": 150000,
      "total_per_semester": 175000
    }
  ]
}
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build backend image
cd fusedchat_backend
docker build -t fusedchat-backend .

# Build frontend image
cd ../fusedchat_frontend
docker build -t fusedchat-frontend .

# Run containers
docker run -p 8000:8000 fusedchat-backend
docker run -p 3001:3001 fusedchat-frontend
```

### Cloud Deployment

**AWS:**
- Deploy FastAPI to AWS Lambda or EC2
- Deploy React to S3 + CloudFront
- Use MongoDB Atlas

**Google Cloud:**
- Deploy to Cloud Run
- Store static assets in Cloud Storage

**Heroku:**
- Simple push deployment
- Just add `Procfile`

---

## 📈 Performance Tips

1. **Use GPU for embeddings** (in `professional_brain.py`):
   ```python
   model_kwargs={"device": "cuda"}  # Instead of "cpu"
   ```

2. **Enable caching** for frequently asked questions

3. **Batch process** PDFs during off-peak hours

4. **Monitor API usage** on Groq console

5. **Use MongoDB indexing** for faster queries

---

## 🤝 Getting Help

### Resources
- 📖 **Full Guide**: Read `COMPLETE_GUIDE.md`
- 🏗️ **Architecture**: Read `ARCHITECTURE.md`
- 📋 **Setup**: Read `IMPLEMENTATION_GUIDE.md`
- 🎯 **Project Summary**: Read `SUMMARY.md`
- 📑 **Documentation Index**: Read `INDEX.md`

### Common Questions

**Q: Can I use a different LLM instead of Groq?**  
A: Yes! Edit the imports in each brain file and use any LangChain-compatible LLM.

**Q: How do I add more brains?**  
A: Create a new file in `app/services/`, implement the async function, and update routing in `query_router.py`.

**Q: Can I train the model on my own data?**  
A: The system uses RAG (retrieval-based), not training. Just add PDFs and they're searchable immediately.

**Q: What's the maximum document size?**  
A: Depends on your GPU/CPU. Typically 50-100 MB PDFs work fine. Larger ones take longer to index.

---

## ✨ What's Included

✅ **Three specialized brains** - Professional, Admin, Document  
✅ **Professional UI** - Modern React with dark theme  
✅ **RAG System** - Retrieval-Augmented Generation for accuracy  
✅ **PDF Analysis** - With exact citations  
✅ **MongoDB Integration** - Conversation persistence  
✅ **FAISS Indexing** - Fast semantic search  
✅ **Web Search** - Optional for deep research  
✅ **Conversation History** - Full session tracking  
✅ **Error Handling** - Graceful error messages  
✅ **Production Ready** - Deploy to cloud immediately  

---

## 🎉 You're Ready!

Your FusedChat system is **fully functional and ready to use**. Start with the **Quick Start** section above and happy chatting! 🚀

For detailed setup, see `IMPLEMENTATION_GUIDE.md`  
For technical details, see `ARCHITECTURE.md`  
For API reference, open `http://localhost:8000/docs`

---

**Need more help?** Check the troubleshooting section above or read the comprehensive guides in the root directory.

**Last Updated:** February 13, 2026  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
