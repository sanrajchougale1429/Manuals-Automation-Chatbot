"""
Embedding Module
Supports OpenAI embeddings and sentence-transformers models
"""

from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from typing import List
from config import ACTIVE_BACKEND, ModelBackend, OpenAIConfig, ClaudeConfig


class SentenceTransformerEmbeddings(Embeddings):
    """Custom embeddings using sentence-transformers library"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()


def get_embeddings() -> Embeddings:
    """
    Get the appropriate embeddings based on active backend.
    
    Returns:
        LangChain Embeddings instance
    """
    if ACTIVE_BACKEND == ModelBackend.CLAUDE:
        # Use sentence-transformers for Claude
        return SentenceTransformerEmbeddings(model_name=ClaudeConfig.EMBED_MODEL)
    else:
        # Use OpenAI embeddings for OpenAI backend
        return OpenAIEmbeddings(model=OpenAIConfig.EMBED_MODEL)


def get_embedding_dimension() -> int:
    """
    Get the dimension of embeddings for vector store configuration.
    """
    if ACTIVE_BACKEND == ModelBackend.CLAUDE:
        # Sentence-transformers dimensions
        model_dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "multi-qa-MiniLM-L6-cos-v1": 384,
        }
        return model_dimensions.get(ClaudeConfig.EMBED_MODEL, 384)
    else:
        # OpenAI dimensions
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dimensions.get(OpenAIConfig.EMBED_MODEL, 1536)
