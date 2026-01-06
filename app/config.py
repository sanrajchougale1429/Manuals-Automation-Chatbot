"""
Configuration for Enterprise Manuals Intelligence System
Supports both Ollama (local) and OpenAI (cloud) backends
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# ============================================
# DIRECTORY CONFIGURATION
# ============================================
BASE_DIR = Path(__file__).parent.parent.resolve()
SOP_DIR = BASE_DIR / "manuals"
DB_DIR = BASE_DIR / "chroma_store"

SOP_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# MODEL BACKEND SELECTION
# ============================================
class ModelBackend(Enum):
    OPENAI = "openai"
    CLAUDE = "claude"

# Set your preferred backend here (OPENAI or CLAUDE)
ACTIVE_BACKEND = ModelBackend.CLAUDE  # Using Claude Sonnet 4 (latest)

# ============================================
# OPENAI CONFIGURATION
# ============================================
class OpenAIConfig:
    API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = "gpt-4o"  # Upgraded to GPT-4o for better quality
    EMBED_MODEL = "text-embedding-3-large"  # Upgraded for better embeddings
    
    # Alternative models:
    # LLM_MODEL = "gpt-4o-mini"  # Cheaper option
    # EMBED_MODEL = "text-embedding-3-small"  # Cheaper embeddings

# ============================================
# CLAUDE CONFIGURATION
# ============================================
class ClaudeConfig:
    API_KEY = os.getenv("ANTHROPIC_API_KEY")
    LLM_MODEL = "claude-sonnet-4-20250514"  # Latest Claude Sonnet 4
    # Note: Claude doesn't provide embeddings, uses custom embedding model
    EMBED_MODEL = "all-MiniLM-L6-v2"  # Lightweight, fast embeddings
    
    # Alternative models:
    # LLM_MODEL = "claude-3-5-sonnet-20241022"  # Previous version

# ============================================
# CHUNKING CONFIGURATION
# ============================================
class ChunkConfig:
    CHUNK_SIZE = 1500  # Characters per chunk (increased for better context)
    CHUNK_OVERLAP = 400  # Overlap between chunks (increased for continuity)
    MIN_CHUNK_SIZE = 100  # Minimum chunk size to keep

# ============================================
# RETRIEVAL CONFIGURATION  
# ============================================
class RetrievalConfig:
    TOP_K = 20  # Initial retrieval count (increased for better coverage)
    RERANK_TOP_K = 8  # After re-ranking (increased for more context)
    SIMILARITY_THRESHOLD = 0.2  # Minimum similarity score (lowered for more inclusive search)
    ENABLE_RERANKING = True  # Use cross-encoder re-ranking
    ENABLE_DOMAIN_FILTER = False  # Disabled - allow cross-domain search for better answers

# ============================================
# DOMAIN CLASSIFICATION
# Maps filename patterns to domains for filtered search
# ============================================
DOMAIN_MAPPINGS = {
    "claims": ["claim", "claims"],
    "remits": ["remit", "remits", "deposit"],
    "analytics": ["analytics", "peak"],
    "patient": ["patient", "estimation", "lockbox"],
    "user_management": ["user management", "user guide"],
    "rules": ["rule", "altitude", "assist"],
    "print": ["print", "services"],
}

# Domain keywords for query classification
DOMAIN_KEYWORDS = {
    "claims": ["claim", "claims", "billing", "denial", "denials", "appeal", "payer"],
    "remits": ["remit", "remittance", "deposit", "era", "835", "payment"],
    "analytics": ["analytics", "report", "dashboard", "peak", "metrics", "kpi"],
    "patient": ["patient", "estimation", "estimate", "lockbox", "responsibility"],
    "user_management": ["user", "permission", "role", "access", "login", "password"],
    "rules": ["rule", "wizard", "altitude", "assist", "automation", "workflow"],
    "print": ["print", "statement", "batch", "paper"],
}

# ============================================
# VECTOR STORE CONFIGURATION
# ============================================
class VectorStoreConfig:
    COLLECTION_NAME = "enterprise_manuals"
    DISTANCE_METRIC = "cosine"