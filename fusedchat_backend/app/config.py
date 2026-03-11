# app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

class Settings:
    # --- OLLAMA Models ---
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://dissociative-subcardinally-ranae.ngrok-free.dev")
    OLLAMA_MODEL_ROUTER = "llama3.2:3b" # Faster for routing
    OLLAMA_MODEL_FAST = "llama3.1:8b"
    OLLAMA_MODEL_ANSWER = "llama3.1:8b"
    OLLAMA_MODEL_ADMIN = "llama3.1:8b"
    OLLAMA_MODEL_DOC = "llama3.1:8b"
    
    # NEW: Specific model for heavy research/extraction tasks
    OLLAMA_MODEL_RESEARCHER = "qwen2.5:7b" 
    
    # NEW: Increased timeout specifically for the Live Researcher (in seconds)
    OLLAMA_TIMEOUT = 180 

    # --- Database ---
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = "fusedchat_db"

    # --- Live Search ---
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # --- File Paths ---
    SYLLABUS_PATH = str(BASE_DIR / "data" / "syllabus" / "syllabus.pdf")
    SYLLABUS_INDEX_PATH = str(BASE_DIR / "vector_store" / "syllabus_index")
    UPLOAD_DIR = str(BASE_DIR / "data" / "uploads")
    TEMP_INDEX_PATH = str(BASE_DIR / "vector_store" / "temp_doc_index")

settings = Settings()