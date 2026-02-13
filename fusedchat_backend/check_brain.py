import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 1. Setup Paths
INDEX_PATH = "vector_store/syllabus_index"

# 2. Check if index exists
if not os.path.exists(INDEX_PATH):
    print(f"❌ Error: No index found at {INDEX_PATH}")
    print("   Did you run 'ingestion.py' successfully?")
    exit()

print("Loading the Brain... (this takes 2 seconds)")

# 3. Load the Brain
try:
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    vector_store = FAISS.load_local(
        INDEX_PATH, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    print("✅ Brain Loaded Successfully!")
except Exception as e:
    print(f"❌ Failed to load index: {e}")
    exit()

# 4. The Test: Search for common syllabus words
query = "Unit metrix"  # Most syllabi have "Unit I", "Unit II", etc.
print(f"\n🔍 Searching for: '{query}'...")

results = vector_store.similarity_search(query, k=3)

print(f"\n--- 📄 FOUND {len(results)} RELEVANT CHUNKS ---")
for i, doc in enumerate(results):
    print(f"\n[Chunk {i+1}]:")
    print("-" * 50)
    # Print the first 300 characters of the content
    print(doc.page_content[:500]) 
    print("-" * 50)

print("\nAnalyze the text above:")
print("1. Can you read English sentences? -> ✅ It works.")
print("2. Is it random symbols like 'x$#@'? -> ❌ OCR failed (quality too low).")
print("3. Is it empty? -> ❌ PDF processing failed.")