import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Paths
INDEX_PATH = "vector_store/syllabus_index"
OUTPUT_FILE = "debug_syllabus_dump.txt"

def export_vector_db_to_text():
    # 1. Check if index exists
    if not os.path.exists(INDEX_PATH):
        print(f"❌ Error: Index folder not found at {INDEX_PATH}")
        return

    print("Loading Vector Store... (this might take a moment)")
    
    # 2. Load the Index
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.load_local(
            INDEX_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"❌ Failed to load index: {e}")
        return

    # 3. Extract all documents from the internal store
    # Note: .docstore._dict is an internal LangChain attribute, but it works for this purpose.
    all_docs = list(vector_store.docstore._dict.values())
    
    print(f"✅ Found {len(all_docs)} text chunks in the database.")
    print(f"📝 Writing content to '{OUTPUT_FILE}'...")

    # 4. Write to a text file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== FUSEDCHAT DATABASE DUMP ===\n")
        f.write(f"Total Chunks: {len(all_docs)}\n")
        f.write("=================================\n\n")

        for i, doc in enumerate(all_docs):
            f.write(f"--- [CHUNK {i+1}] ---\n")
            f.write(f"Source: {doc.metadata.get('source', 'Unknown')} | Page: {doc.metadata.get('page', 'Unknown')}\n")
            f.write("Content:\n")
            f.write(doc.page_content)
            f.write("\n\n" + "="*50 + "\n\n")

    print(f"🎉 Done! Open '{OUTPUT_FILE}' to see exactly what the AI sees.")

if __name__ == "__main__":
    export_vector_db_to_text()