# ⚡ FusedChat Setup Checklist

## 📋 Pre-Installation

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed  
- [ ] Git installed
- [ ] Groq API key obtained (https://console.groq.com)
- [ ] 4GB RAM available
- [ ] 500MB disk space available

---

## 🔧 Step 1: Environment Setup

### 1.1 MongoDB
```bash
# Option A: Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Option B: Local
# Download from https://www.mongodb.com/try/download/community
# Run MongoDB service

# Option C: MongoDB Atlas (Cloud)
# Create account at https://www.mongodb.com/cloud/atlas
# Get connection string
```

- [ ] MongoDB running on port 27017

### 1.2 Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

- [ ] Virtual environment activated

### 1.3 Install Backend Dependencies
```bash
cd fusedchat_backend
pip install -r requirements.txt
```

- [ ] All packages installed successfully
- [ ] No error messages

---

## 🗂️ Step 2: Configuration

### 2.1 Create .env File
```bash
cd fusedchat_backend

# Create .env
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=fusedchat
GROQ_API_KEY=gsk_YOUR_ACTUAL_KEY_HERE
UPLOAD_DIR=data/uploads
SYLLABUS_INDEX_PATH=vector_store/syllabus_index
TEMP_INDEX_PATH=vector_store/temp_doc_index
OLLAMA_BASE_URL=http://localhost:11434
USE_OLLAMA_FALLBACK=false
EOF
```

- [ ] .env file created in fusedchat_backend/
- [ ] GROQ_API_KEY filled in with actual key
- [ ] MongoDB connection string correct

### 2.2 Create Required Directories
```bash
# From fusedchat_backend/
mkdir -p data/uploads data/syllabus
mkdir -p vector_store/syllabus_index vector_store/temp_doc_index
```

- [ ] All directories created

---

## 🚀 Step 3: Backend Launch

### 3.1 Start Backend Server
```bash
cd fusedchat_backend
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
✅ Connected to MongoDB
🔌 Loading Embedding Model: BAAI/bge-large-en-v1.5...
```

- [ ] Backend server running
- [ ] MongoDB connected
- [ ] Embedding model loaded
- [ ] No error messages

### 3.2 Test Backend
```bash
# In a new terminal
curl http://localhost:8000/health

# Expected: {"status": "ok"}
```

- [ ] Backend responds to /health endpoint

---

## 🎨 Step 4: Frontend Setup

### 4.1 Install Frontend Dependencies
```bash
cd ../fusedchat_frontend
npm install
```

- [ ] Dependencies installed (should see "added XXX packages")
- [ ] No major vulnerabilities

### 4.2 Start Frontend
```bash
npm start
```

**Expected Output:**
```
Compiled successfully!
Local: http://localhost:3000
```

- [ ] Frontend starts without errors
- [ ] Browser auto-opens to http://localhost:3000 (or 3001)

---

## ✅ Step 5: Verification Tests

### 5.1 Test Query Router
```bash
# Backend terminal: Run query router test
cd fusedchat_backend
python -m app.services.query_router

# Expected: Multiple test queries classified correctly
```

- [ ] Query router classifies queries as EDUCATIONAL, ADMIN, DOCUMENT

### 5.2 Test API Integration
```bash
# Test educational query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_123",
    "query": "What is a linked list?",
    "mode": "fast"
  }'

# Expected: JSON response with answer
```

- [ ] API returns valid response
- [ ] Response is from appropriate brain

### 5.3 Test Frontend-Backend Communication
```
1. Open http://localhost:3000 in browser
2. Type a question: "Explain arrays"
3. Press Enter or click Send
4. Should see response within 5 seconds
```

- [ ] Message appears in chat
- [ ] "Thinking..." loading state shows
- [ ] Response appears from brain
- [ ] No console errors

### 5.4 Test Document Upload
```
1. Click "Document Brain" toggle
2. Upload a PDF file
3. Wait for "Document indexed successfully!" message
4. Ask a question about the document
5. Should see answer with citations
```

- [ ] PDF uploads without errors
- [ ] Summary generated automatically
- [ ] Queries return relevant chunks
- [ ] Citations display correctly

---

## 📊 Step 6: Check Logs & Monitoring

### 6.1 Backend Logs
```bash
# Check MongoDB operations
tail -f backend.log

# Check for:
✅ Successful API calls
✅ Vector search operations
✅ MongoDB transactions
❌ No error messages
```

- [ ] Backend logs show normal operation

### 6.2 Database Check
```bash
# Connect to MongoDB
mongo

# List databases
show dbs

# Switch to fusedchat
use fusedchat

# Check collections
show collections

# Count documents
db.conversations.countDocuments()
```

- [ ] fusedchat database exists
- [ ] Collections created: conversations, document_uploads, sessions, users
- [ ] At least 1 document in conversations (from testing)

---

## 🎯 Step 7: Final Checklist

### System Status
- [ ] MongoDB running
- [ ] Backend API running on :8000
- [ ] Frontend running on :3000 or :3001
- [ ] No error messages in any terminal

### Feature Tests
- [ ] Professional Brain responds to educational queries
- [ ] Admin Brain responds to institute queries
- [ ] Document Brain processes PDF uploads
- [ ] Query Router correctly classifies queries
- [ ] Responses appear in real-time
- [ ] MongoDB stores conversation history
- [ ] Citations display for document queries

### Performance
- [ ] Fast mode response: < 5 seconds
- [ ] Deep mode response: < 12 seconds
- [ ] Document search: < 3 seconds
- [ ] No lag in UI

---

## 🚨 Troubleshooting

### Backend Won't Start
```
Error: Cannot connect to MongoDB
Fix: Ensure MongoDB is running (docker ps)

Error: GROQ_API_KEY not found
Fix: Check .env file has correct key

Error: Port 8000 already in use
Fix: Change port: uvicorn app.main:app --reload --port 8001
```

### Frontend Won't Start
```
Error: Port 3000 already in use
Fix: Set PORT=3001 npm start

Error: Cannot reach backend
Fix: Check backend is running on :8000
Check CORS is enabled in app/main.py
```

### Queries Not Working
```
Error: Query timeout
Fix: Ensure vector embeddings are loaded
Check Groq API key is valid

Error: No response from brain
Fix: Check MongoDB connection
Check vector store files exist
Review browser console for errors
```

---

## 📱 Access Points

Once everything is running:

| Component | URL | Purpose |
|-----------|-----|---------|
| Frontend | http://localhost:3000 | Chat interface |
| Backend API | http://localhost:8000 | API endpoints |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MongoDB | localhost:27017 | Database |

---

## 🔄 Daily Usage

### Start Everything
```bash
# Terminal 1: MongoDB (if using Docker)
docker start mongodb

# Terminal 2: Backend
cd fusedchat_backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Frontend
cd fusedchat_frontend
npm start
```

### Stop Everything
```bash
# Ctrl+C in each terminal
# Then:
docker stop mongodb  # if using Docker
```

---

## 📚 Documentation Files

- **README.md** - Project overview
- **ARCHITECTURE.md** - Detailed architecture explanation
- **IMPLEMENTATION_GUIDE.md** - Step-by-step implementation
- **This file** - Setup checklist

---

## 🎓 Next Steps After Setup

1. **Syllabus Upload**: Add your college syllabus PDFs to `data/syllabus/`
2. **Fine-tune Prompts**: Edit prompts in brain services for better responses
3. **Add More Data**: Upload faculty info, fee structures, placement data
4. **Frontend Customization**: Add your college colors and logo
5. **Knowledge Graph**: Implement topic relationship visualization
6. **User Authentication**: Add login system for students
7. **Analytics Dashboard**: Build monitoring and usage statistics
8. **Mobile App**: Convert to React Native for mobile

---

## ✨ You're Ready!

If all checks pass, you have a fully functional three-brain AI system! 🎉

**Questions?** Check the documentation or test files for examples.

**Status:** Ready for Development ✅

---

*Last Updated: February 13, 2026*
*FusedChat v1.0.0*
