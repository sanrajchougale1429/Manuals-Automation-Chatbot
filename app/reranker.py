"""
Re-ranking Module
Uses cross-encoder models to re-rank retrieved documents for better relevance
"""

from typing import List, Tuple
from dataclasses import dataclass
from langchain_core.documents import Document
from config import RetrievalConfig

# Global reranker instance (loaded lazily)
_reranker = None


@dataclass
class RankedDocument:
    """Document with relevance score"""
    document: Document
    score: float


def load_reranker():
    """
    Load the cross-encoder model for re-ranking.
    Uses sentence-transformers with a pre-trained model.
    """
    global _reranker
    
    if _reranker is not None:
        return _reranker
    
    try:
        from sentence_transformers import CrossEncoder
        
        # MS MARCO model - trained for passage re-ranking
        _reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512  # Limit input length
        )
        print("✅ Re-ranker loaded successfully")
        return _reranker
    
    except ImportError:
        print("⚠️ sentence-transformers not installed. Re-ranking disabled.")
        return None
    except Exception as e:
        print(f"⚠️ Could not load re-ranker: {e}")
        return None


def rerank_documents(
    query: str,
    documents: List[Document],
    top_k: int = RetrievalConfig.RERANK_TOP_K
) -> List[Document]:
    """
    Re-rank documents using a cross-encoder model.
    
    Cross-encoders are more accurate than bi-encoders for relevance
    because they see query and document together, but are slower.
    We use them to re-rank a small set of initially retrieved docs.
    
    Args:
        query: The user's question
        documents: List of retrieved documents
        top_k: Number of top documents to return after re-ranking
    
    Returns:
        List of top_k most relevant documents
    """
    if not documents:
        return []
    
    if not RetrievalConfig.ENABLE_RERANKING:
        return documents[:top_k]
    
    reranker = load_reranker()
    
    if reranker is None:
        # Fallback: return original order
        return documents[:top_k]
    
    try:
        # Prepare query-document pairs
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Get relevance scores
        scores = reranker.predict(pairs)
        
        # Combine documents with scores
        ranked = [
            RankedDocument(doc, score)
            for doc, score in zip(documents, scores)
        ]
        
        # Sort by score (higher is better)
        ranked.sort(key=lambda x: x.score, reverse=True)
        
        # Return top_k documents
        return [r.document for r in ranked[:top_k]]
    
    except Exception as e:
        print(f"Re-ranking failed: {e}")
        return documents[:top_k]


def get_reranker_status() -> str:
    """Check if re-ranker is available and loaded"""
    if not RetrievalConfig.ENABLE_RERANKING:
        return "Disabled in config"
    
    reranker = load_reranker()
    if reranker is None:
        return "Not available (install sentence-transformers)"
    return "Active"
