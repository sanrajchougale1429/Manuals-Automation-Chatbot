"""
Vector Store Module
Uses ChromaDB for local persistent vector storage
Supports domain-filtered retrieval
"""

import chromadb
from chromadb.config import Settings
from typing import List, Optional, Set
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import DB_DIR, VectorStoreConfig, RetrievalConfig
from embeddings import get_embeddings
from domain_classifier import classify_query_domain


# Global instances
_chroma_client = None
_vectorstore = None


def get_chroma_client():
    """Get or create ChromaDB persistent client"""
    global _chroma_client
    
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=str(DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
    
    return _chroma_client


def get_vectorstore() -> Chroma:
    """
    Get or create the vector store instance.
    Uses ChromaDB with persistent storage.
    """
    global _vectorstore
    
    if _vectorstore is None:
        embeddings = get_embeddings()
        
        _vectorstore = Chroma(
            collection_name=VectorStoreConfig.COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(DB_DIR),
        )
    
    return _vectorstore


def get_available_domains() -> Set[str]:
    """Get set of domains that exist in the vector store"""
    vectorstore = get_vectorstore()
    
    try:
        # Get all documents' metadata
        collection = vectorstore._collection
        results = collection.get(include=["metadatas"])
        
        domains = set()
        for metadata in results.get("metadatas", []):
            if metadata and "domain" in metadata:
                domains.add(metadata["domain"])
        
        return domains
    except Exception:
        return set()


def get_indexed_files() -> List[str]:
    """Get list of files that have been indexed"""
    vectorstore = get_vectorstore()
    
    try:
        collection = vectorstore._collection
        results = collection.get(include=["metadatas"])
        
        files = set()
        for metadata in results.get("metadatas", []):
            if metadata and "filename" in metadata:
                files.add(metadata["filename"])
        
        return sorted(list(files))
    except Exception:
        return []


def add_documents(documents: List[Document]) -> int:
    """
    Add documents to the vector store.
    
    Args:
        documents: List of LangChain Document objects
    
    Returns:
        Number of documents added
    """
    vectorstore = get_vectorstore()
    vectorstore.add_documents(documents)
    return len(documents)


def similarity_search(
    query: str,
    k: int = RetrievalConfig.TOP_K,
    domain_filter: bool = RetrievalConfig.ENABLE_DOMAIN_FILTER
) -> List[Document]:
    """
    Search for similar documents, optionally filtered by domain.
    
    Args:
        query: Search query
        k: Number of results to return
        domain_filter: Whether to filter by detected domain
    
    Returns:
        List of matching documents
    """
    vectorstore = get_vectorstore()
    
    # Build filter based on query domain
    filter_dict = None
    if domain_filter:
        detected_domains = classify_query_domain(query)
        available_domains = get_available_domains()
        
        # Only filter if we detected domains that exist
        valid_domains = [d for d in detected_domains if d in available_domains]
        
        if valid_domains:
            if len(valid_domains) == 1:
                filter_dict = {"domain": valid_domains[0]}
            else:
                filter_dict = {"domain": {"$in": valid_domains}}
    
    # Perform search
    try:
        if filter_dict:
            results = vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = vectorstore.similarity_search(query, k=k)
        
        return results
    
    except Exception as e:
        print(f"Search error: {e}")
        # Fallback: search without filter
        return vectorstore.similarity_search(query, k=k)


def reset_vectorstore():
    """Delete all data and reset the vector store"""
    global _vectorstore, _chroma_client
    
    import shutil
    
    # Close connections
    _vectorstore = None
    _chroma_client = None
    
    # Delete storage directory
    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)
    
    # Recreate directory
    DB_DIR.mkdir(parents=True, exist_ok=True)


def get_collection_stats() -> dict:
    """Get statistics about the vector store"""
    vectorstore = get_vectorstore()
    
    try:
        collection = vectorstore._collection
        count = collection.count()
        
        return {
            "total_chunks": count,
            "indexed_files": len(get_indexed_files()),
            "domains": list(get_available_domains()),
        }
    except Exception:
        return {
            "total_chunks": 0,
            "indexed_files": 0,
            "domains": [],
        }