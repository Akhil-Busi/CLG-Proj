import os
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.services.llm_factory import get_ollama_llm
from langchain.prompts import ChatPromptTemplate

# Fix path for standalone run
if __name__ == "__main__":
    sys.path.append(os.getcwd()) 

from app.config import settings

# --- 1. SETUP EMBEDDINGS & LLM (Keep these as they are) ---
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

llm = get_ollama_llm(
    model_name=settings.OLLAMA_MODEL_ANSWER,
    temperature=0,
    max_tokens=1024,
)

# --- 2. ADDED: INTENT DETECTION KEYWORDS ---
GREETINGS = ["hello", "hi", "hey", "good morning", "good evening", "greetings"]
THANKS_FAREWELLS = ["thank you", "thanks", "bye", "goodbye", "appreciate it"]

RAG_PROMPT = """
You are an academic AI assistant. Answer the question strictly based on the provided context. 
If the answer is not in the context, say "I cannot find the answer in the provided document."

Context:
{context}

Question: 
{question}
"""
prompt_template = ChatPromptTemplate.from_template(RAG_PROMPT)

def get_answer(query: str, mode: str):
    # --- 3. ADDED: INTENT DETECTION LOGIC ---
    normalized_query = query.lower().strip()

    if normalized_query in GREETINGS:
        return "Hello! I am FusedChat, your academic assistant. How can I help you with the syllabus or a document today?"
    
    if normalized_query in THANKS_FAREWELLS:
        return "You're welcome! Feel free to ask another question if you need help."
    # ----------------------------------------
    
    # If it's not a greeting, proceed with the RAG pipeline...
    if mode == "document":
        path = settings.TEMP_INDEX_PATH
    else:
        path = settings.SYLLABUS_INDEX_PATH

    if not os.path.exists(path):
        return "Error: Brain not found. Please run ingestion or upload a document first."

    vector_store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    docs = retriever.invoke(query)
    
    print(f"\n🔍 Retrieved {len(docs)} chunks for query: '{query}'")
    if docs:
        print(f"1st Chunk Preview: {docs[0].page_content[:100]}...\n")

    context_text = "\n\n".join([d.page_content for d in docs])

    chain = prompt_template | llm
    response = chain.invoke({"context": context_text, "question": query})

    return response.content

# Standalone Test
if __name__ == "__main__":
    print("--- Testing RAG ---")
    print(get_answer("What are the course objectives for Linear Algebra?", "professional"))
    print("\n--- Testing Greeting ---")
    print(get_answer("hello", "professional"))