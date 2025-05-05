import os
from chromadb import PersistentClient

import ollama
from PyPDF2 import PdfReader
from docx import Document as DocxDocument

# Initialize ChromaDB client
chroma = PersistentClient(path="./chroma_db")


def chunk_text(text, chunk_size=500, overlap=50):
    """
    Splits text into overlapping chunks.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def get_embeddings(chunks, model="nomic-embed-text", batch_size=50):
    """
    Generate embeddings for a list of text chunks using Ollama.
    """
    if isinstance(chunks, str):
        chunks = [chunks]

    embeddings = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        try:
            resp = ollama.embed(model=model, input=batch)
            batch_embeds = resp.get("embeddings", [])
        except Exception as e:
            print(f"Error embedding batch at {start}: {e}")
            batch_embeds = [None] * len(batch)
        embeddings.extend(batch_embeds)
    return embeddings

def ingest_document_chunks(doc):
    """
    Reads and chunks an approved document, then embeds and stores in Chroma.
    """
    path = doc.file.path
    ext = os.path.splitext(path)[1].lower()

    # Extract text
    if ext == ".docx":
        docx = DocxDocument(path)
        text = "\n".join([para.text for para in docx.paragraphs])
    elif ext == ".pdf":
        reader = PdfReader(path)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()

    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks)

    # Save chunks to Chroma
    collection = chroma.get_or_create_collection(name="documents")

    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        if embedding is None:
            continue  # Skip bad batches
        metadata = {
            "doc_id": str(doc.id),
            "chunk_index": idx,
            "title": doc.title,
        }
        collection.upsert(
            ids=[f"{doc.id}_{idx}"],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[chunk],
        )


def delete_document_chunks(doc_id):
    """
    Removes all vector entries related to the given document ID.
    """
    collection = chroma.get_or_create_collection(name="documents")

    # Get all current IDs to filter only the ones related to this document
    results = collection.get(include=['ids', 'metadatas'])
    ids_to_delete = [
        doc_id for doc_id, meta in zip(results['ids'], results['metadatas'])
        if meta.get('doc_id') == str(doc_id)
    ]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

def get_chroma_collection():
    """
    Returns the documents collection from ChromaDB.
    """
    return chroma.get_or_create_collection(name="documents")

# documents/utils.py

def get_relevant_context(query: str, top_k: int = 5) -> str:
    """
    Retrieves the top_k most relevant document chunks from ChromaDB for the given query.
    """
    # Step 1: Embed the query
    query_embedding = get_embeddings([query])[0]
    if query_embedding is None:
        return ""

    # Step 2: Query the ChromaDB collection
    collection = get_chroma_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Step 3: Extract and concatenate the retrieved documents
    documents = results.get("documents", [[]])[0]
    return "\n\n".join(documents)
