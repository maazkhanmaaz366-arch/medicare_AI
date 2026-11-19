
from pathlib import Path
from fastembed import TextEmbedding
import numpy as np 
from langchain_text_splitters import RecursiveCharacterTextSplitter
embedding_model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5')

DOCUMENT_PATH = Path(__file__).resolve().parent.parent.parent/'clinical_policies.md'

def load_and_chunk_document(file_path:Path) -> list[dict]:
    "Reads an organization policy document and splits it by markdown section (##Header).No hardcord python lists needed"

    if not file_path.exists():
        print(f"Warning: Policy document not found at {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    splitter =RecursiveCharacterTextSplitter(
        chunk_size = 400,
        chunk_overlap = 50,
        separators = ['\n\n','\n','. ',' ']
    )
    chunks = splitter.split_text(text)
    return chunks
    

CLINICAL_CHUNKS = load_and_chunk_document(DOCUMENT_PATH)
DOC_EMBEDDINGS = list(embedding_model.embed(CLINICAL_CHUNKS)) if CLINICAL_CHUNKS else []

def query_clinical_guidlines(query:str) -> str:
    """
    Finds the most relevent policy chunk from the loaded document
    """

    if not CLINICAL_CHUNKS or not DOC_EMBEDDINGS:
        return "clinic policy document are currently being loaded please contact staff directly"

    query_vec = list(embedding_model.embed([query]))[0]

    similarities = [
        np.dot(query_vec,doc_vec)/(np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)) for doc_vec in DOC_EMBEDDINGS

    ]

    best_idx = int(np.argmax(similarities))
    best_score = similarities[best_idx]

    if best_score<0.35:
        return ('i could not find an official clinic preperation rule for the specific question.'
        "please contact the clinic nursing station directly at (555) 019-8800 for medical advice"
        )

    matched = CLINICAL_CHUNKS[best_idx]
    return f"📌 [Official Clinic Guideline]:\n{matched}"