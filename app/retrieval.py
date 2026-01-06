"""
Retrieval Module
Orchestrates search, re-ranking, and context building
"""

from typing import List, Tuple
from langchain_core.documents import Document

from config import RetrievalConfig
from vectorstore import similarity_search
from reranker import rerank_documents
from domain_classifier import extract_domain_context


def retrieve_context(
    query: str,
    top_k: int = RetrievalConfig.RERANK_TOP_K
) -> Tuple[List[Document], str]:
    """
    Retrieve relevant context for a query.
    
    Pipeline:
    1. Initial retrieval with domain filtering
    2. Re-rank with cross-encoder
    3. Build formatted context string
    
    Args:
        query: User's question
        top_k: Number of final documents to return
    
    Returns:
        Tuple of (documents, formatted_context_string)
    """
    # Step 1: Initial retrieval (fetch more for re-ranking)
    initial_k = RetrievalConfig.TOP_K
    documents = similarity_search(query, k=initial_k)
    
    if not documents:
        return [], ""
    
    # Step 2: Re-rank if enabled
    if RetrievalConfig.ENABLE_RERANKING:
        documents = rerank_documents(query, documents, top_k=top_k)
    else:
        documents = documents[:top_k]
    
    # Step 3: Build context string
    context_parts = []
    
    for doc in documents:
        meta = doc.metadata
        source_info = f"SOURCE: {meta.get('filename', 'Unknown')} | PAGE: {meta.get('page', '?')}"
        
        if meta.get('section'):
            source_info += f" | SECTION: {meta.get('section')}"
        
        context_parts.append(f"\n{source_info}\n{doc.page_content}\n")
    
    context_string = "\n---\n".join(context_parts)
    
    return documents, context_string


def format_sources(documents: List[Document]) -> str:
    """
    Format source citations from documents.
    
    Args:
        documents: List of retrieved documents
    
    Returns:
        Formatted source string
    """
    if not documents:
        return ""
    
    # Deduplicate sources
    sources = {}
    for doc in documents:
        filename = doc.metadata.get("filename", "Unknown")
        page = doc.metadata.get("page", "?")
        key = f"{filename}|{page}"
        
        if key not in sources:
            sources[key] = {"filename": filename, "page": page}
    
    # Format
    source_lines = []
    for source in sources.values():
        source_lines.append(f"**{source['filename']}**, Page {source['page']}")
    
    return "\n".join(source_lines)


def build_retrieval_summary(documents: List[Document], query: str) -> dict:
    """
    Build a summary of the retrieval process for debugging.
    
    Args:
        documents: Retrieved documents
        query: Original query
    
    Returns:
        Dict with retrieval statistics
    """
    if not documents:
        return {
            "documents_found": 0,
            "domains": [],
            "files": [],
            "domain_hint": extract_domain_context(query)
        }
    
    domains = set()
    files = set()
    
    for doc in documents:
        meta = doc.metadata
        if "domain" in meta:
            domains.add(meta["domain"])
        if "filename" in meta:
            files.add(meta["filename"])
    
    return {
        "documents_found": len(documents),
        "domains": list(domains),
        "files": list(files),
        "domain_hint": extract_domain_context(query)
    }
