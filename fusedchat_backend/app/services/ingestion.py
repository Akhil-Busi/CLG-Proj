import os
import re
import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --- CONFIGURATION ---
# We use BGE-Large as requested. It is much smarter than MiniLM.
# If this is too slow on your PC, switch back to "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2" # Fallback

print(f"🔌 Loading Embedding Model: {EMBEDDING_MODEL_NAME}...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"}, # Change to "cuda" if you have an NVIDIA GPU
    encode_kwargs={"normalize_embeddings": True}
)

# Initialize OCR
ocr_engine = RapidOCR()

def extract_text_with_ocr(pdf_path: str):
    """
    Extracts text from scanned PDF using RapidOCR.
    Returns a list of raw Page objects (text + page_number).
    """
    print("🕵️‍♂️ Starting OCR extraction...")
    doc = fitz.open(pdf_path)
    raw_pages = []

    for page_num, page in enumerate(doc):
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        result, _ = ocr_engine(img_bytes)
        
        page_text = ""
        if result:
            page_text = "\n".join([line[1] for line in result])
        
        if page_text.strip():
            raw_pages.append({
                "text": page_text,
                "page": page_num + 1
            })
            print(f"   ✅ Page {page_num + 1} processed.")
        else:
            print(f"   ⚠️ Page {page_num + 1} seems empty.")

    return raw_pages

def process_structured_documents(raw_pages):
    """
    1. Detects Subject Code (Context).
    2. Splits content by 'Unit'.
    3. Creates Metadata-rich Documents.
    """
    structured_docs = []
    
    # Regex to find Subject Code (e.g., 23CMMAT1010)
    # Looks for patterns like 23 + letters + numbers
    subject_code_pattern = r"(23[A-Z]{2,}[A-Z0-9/]+)"
    
    # Regex to find Units (e.g., Unit -1, UNIT I, Unit-3)
    unit_pattern = r"(?:UNIT|Unit)\s*[-–]?\s*(?:[0-9]+|[IVX]+)"

    current_subject_code = "Unknown"

    for page_data in raw_pages:
        text = page_data["text"]
        page_num = page_data["page"]

        # 1. Try to find a Subject Code on this page
        # If found, update current_subject_code for subsequent chunks
        code_match = re.search(subject_code_pattern, text)
        if code_match:
            current_subject_code = code_match.group(1)

        # 2. Split by UNIT headings
        # re.split with capturing group () keeps the delimiter (the Unit Name)
        splits = re.split(f"({unit_pattern})", text, flags=re.IGNORECASE)

        # If no units found, treat whole page as one chunk (e.g., Introduction page)
        if len(splits) == 1:
            doc = Document(
                page_content=text,
                metadata={
                    "source": "syllabus",
                    "page": page_num,
                    "subject_code": current_subject_code,
                    "unit": "General/Intro"
                }
            )
            structured_docs.append(doc)
        else:
            # If units found, process them
            # split[0] is text before the first unit (Intro text)
            if splits[0].strip():
                structured_docs.append(Document(
                    page_content=splits[0],
                    metadata={
                        "source": "syllabus", 
                        "page": page_num, 
                        "subject_code": current_subject_code,
                        "unit": "General"
                    }
                ))

            # Iterate through the splits. 
            # Pattern is: [Unit Header], [Unit Content], [Unit Header], [Unit Content]...
            for i in range(1, len(splits), 2):
                unit_name = splits[i].strip()     # e.g., "Unit -1"
                unit_content = splits[i+1].strip() if (i+1) < len(splits) else ""

                if unit_content:
                    # Combine Header + Content for the embedding text
                    final_text = f"Subject: {current_subject_code}\n{unit_name}\n{unit_content}"
                    
                    doc = Document(
                        page_content=final_text,
                        metadata={
                            "source": "syllabus",
                            "page": page_num,
                            "subject_code": current_subject_code,
                            "unit": unit_name
                        }
                    )
                    structured_docs.append(doc)

    return structured_docs

from tqdm import tqdm  # Progress bar library

def build_index(pdf_path: str, save_path: str):
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return None

    # 1. OCR Extraction
    raw_pages = extract_text_with_ocr(pdf_path)
    if not raw_pages:
        print("❌ OCR failed to extract text.")
        return None

    # 2. Structure-Aware Processing
    print("🧩 Organizing text into Units and extracting Metadata...")
    documents = process_structured_documents(raw_pages)
    print(f"   Generated {len(documents)} structured units.")

    # 3. Text Splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    final_chunks = text_splitter.split_documents(documents)
    total_chunks = len(final_chunks)
    print(f"   Final chunks to embed: {total_chunks}")

    # 4. Vector Store Creation with BATCHING
    print(f"🔮 Generating Embeddings with {EMBEDDING_MODEL_NAME}...")
    
    try:
        # We will initialize the vector store with the first batch
        # ensuring the computer only handles 32 items at a time.
        batch_size = 32 
        
        print(f"   Processing in batches of {batch_size} to prevent freezing...")
        
        # --- BATCH 1: Initialize ---
        first_batch = final_chunks[:batch_size]
        vector_store = FAISS.from_documents(first_batch, embeddings)
        
        # --- BATCH 2 to END: Add to index ---
        # tqdm creates the progress bar so you know it's not frozen
        for i in tqdm(range(batch_size, total_chunks, batch_size), desc="  Embedding"):
            end_index = i + batch_size
            batch = final_chunks[i : end_index]
            vector_store.add_documents(batch)

        # Save result
        vector_store.save_local(save_path)
        print(f"✅ Success! Index saved to: {save_path}")
        return vector_store
        
    except Exception as e:
        print(f"❌ Error creating FAISS index: {e}")
        return None
def load_index(index_path: str):
    if os.path.exists(index_path):
        return FAISS.load_local(
            index_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
    return None

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"📂 Running from: {current_dir}")

    # Paths
    if "services" in current_dir:
        pdf_path = "../../data/syllabus/syllabus.pdf"
        index_path = "../../vector_store/syllabus_index"
    else:
        pdf_path = "data/syllabus/syllabus.pdf"
        index_path = "vector_store/syllabus_index"

    if os.path.exists(pdf_path):
        build_index(pdf_path, index_path)
    else:
        print(f"❌ Critical Error: PDF not found at {pdf_path}")