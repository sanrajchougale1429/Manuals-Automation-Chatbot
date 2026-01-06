"""
Document Ingestion Module
Processes PDFs with smart chunking and domain classification
"""

import streamlit as st
import fitz  # PyMuPDF
from pathlib import Path
from typing import List
from langchain_core.documents import Document

from config import SOP_DIR
from chunking import recursive_text_splitter
from domain_classifier import classify_document_domain
from vectorstore import get_indexed_files, add_documents


def extract_pdf_text(pdf_path: Path) -> List[dict]:
    """
    Extract text from a PDF file with page-level metadata.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of dicts with 'text', 'page', 'filename' keys
    """
    pages = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            
            if text.strip():
                pages.append({
                    "text": text,
                    "page": page_num + 1,
                    "filename": pdf_path.name
                })
        
        doc.close()
    
    except Exception as e:
        st.error(f"Error reading {pdf_path.name}: {e}")
    
    return pages


def process_pdf(pdf_path: Path) -> List[Document]:
    """
    Process a single PDF file into chunked documents.
    
    Pipeline:
    1. Extract text from each page
    2. Classify document domain
    3. Chunk text with overlap
    4. Create LangChain Documents with metadata
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of LangChain Document objects
    """
    documents = []
    
    # Extract pages
    pages = extract_pdf_text(pdf_path)
    
    if not pages:
        return documents
    
    # Get content sample for domain classification (first 2000 chars)
    content_sample = " ".join([p["text"][:500] for p in pages[:4]])
    domain = classify_document_domain(pdf_path.name, content_sample)
    
    # Process each page
    for page_data in pages:
        # Chunk the page text
        chunks = recursive_text_splitter(page_data["text"])
        
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk.content,
                metadata={
                    "filename": page_data["filename"],
                    "page": page_data["page"],
                    "chunk_index": i,
                    "domain": domain,
                    "section": chunk.section_header,
                    "char_start": chunk.start_char,
                    "char_end": chunk.end_char,
                }
            )
            documents.append(doc)
    
    return documents


def sync_manuals() -> dict:
    """
    Sync all manuals in the SOP directory with the vector store.
    Only processes new files that haven't been indexed yet.
    
    Returns:
        Dict with sync statistics
    """
    # Get already indexed files
    indexed_files = set(get_indexed_files())
    
    # Find new PDFs
    all_pdfs = list(SOP_DIR.glob("*.pdf"))
    new_files = [f for f in all_pdfs if f.name not in indexed_files]
    
    stats = {
        "total_files": len(all_pdfs),
        "already_indexed": len(indexed_files),
        "new_files": len(new_files),
        "chunks_added": 0,
        "errors": []
    }
    
    if not new_files:
        return stats
    
    # Process new files
    all_docs = []
    
    for pdf_path in new_files:
        with st.spinner(f"📄 Processing: {pdf_path.name}..."):
            try:
                docs = process_pdf(pdf_path)
                all_docs.extend(docs)
                st.success(f"✅ {pdf_path.name}: {len(docs)} chunks")
            except Exception as e:
                stats["errors"].append(f"{pdf_path.name}: {e}")
                st.error(f"❌ {pdf_path.name}: {e}")
    
    # Add all documents to vector store
    if all_docs:
        with st.spinner("🔄 Adding to vector store..."):
            count = add_documents(all_docs)
            stats["chunks_added"] = count
        
        st.toast(f"✅ Indexed {len(new_files)} new manuals ({count} chunks)")
    
    return stats


def get_manual_info() -> List[dict]:
    """
    Get information about all manuals in the directory.
    
    Returns:
        List of dicts with filename, size, indexed status
    """
    indexed = set(get_indexed_files())
    
    manuals = []
    for pdf_path in SOP_DIR.glob("*.pdf"):
        manuals.append({
            "filename": pdf_path.name,
            "size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
            "indexed": pdf_path.name in indexed,
        })
    
    return sorted(manuals, key=lambda x: x["filename"])