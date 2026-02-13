import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
	OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
	OLLAMA_MODEL_ROUTER = os.getenv("OLLAMA_MODEL_ROUTER", "llama3.1:8b")
	OLLAMA_MODEL_FAST = os.getenv("OLLAMA_MODEL_FAST", "llama3.1:8b")
	OLLAMA_MODEL_ANSWER = os.getenv("OLLAMA_MODEL_ANSWER", "llama3.1:8b")
	OLLAMA_MODEL_ADMIN = os.getenv("OLLAMA_MODEL_ADMIN", "llama3.1:8b")
	OLLAMA_MODEL_DOC = os.getenv("OLLAMA_MODEL_DOC", "llama3.1:8b")
	MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
	DB_NAME = "fusedchat_db"

	SYLLABUS_PATH = "C:\\Users\\busia\\OneDrive\\Desktop\\final_cahtbot\\fusedchat_backend\\data\\syllabus\\syllabus.pdf"
	SYLLABUS_INDEX_PATH = "C:\\Users\\busia\\OneDrive\\Desktop\\final_cahtbot\\fusedchat_backend\\vector_store\\syllabus_index"
	UPLOAD_DIR = "data/uploads"
	TEMP_INDEX_PATH = "vector_store/temp_doc_index"


settings = Settings()
