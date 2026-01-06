"""
Domain Classification Module
Auto-detects document domains from filenames and content
Routes queries to relevant document subsets
"""

import re
from typing import List, Optional, Set
from config import DOMAIN_MAPPINGS, DOMAIN_KEYWORDS


def classify_document_domain(filename: str, content_sample: str = "") -> str:
    """
    Classify a document into a domain based on filename and content.
    
    Args:
        filename: The PDF filename
        content_sample: First ~1000 chars of document content (optional)
    
    Returns:
        Domain string (e.g., 'claims', 'remits', 'analytics')
    """
    filename_lower = filename.lower()
    content_lower = content_sample.lower() if content_sample else ""
    
    # Check filename against domain mappings
    for domain, patterns in DOMAIN_MAPPINGS.items():
        for pattern in patterns:
            if pattern in filename_lower:
                return domain
    
    # If no match from filename, check content
    if content_sample:
        domain_scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
    
    # Default domain for unclassified documents
    return "general"


def classify_query_domain(query: str) -> List[str]:
    """
    Detect which domains a query is asking about.
    Can return multiple domains if query spans topics.
    
    Args:
        query: User's question
    
    Returns:
        List of relevant domain strings (can be empty for general queries)
    """
    query_lower = query.lower()
    detected_domains = []
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in query_lower)
        if matches > 0:
            detected_domains.append((domain, matches))
    
    # Sort by match count and return domains
    detected_domains.sort(key=lambda x: x[1], reverse=True)
    
    # Return top domains (max 3)
    return [d[0] for d in detected_domains[:3]]


def get_domain_filter(query: str, available_domains: Set[str]) -> Optional[dict]:
    """
    Generate a metadata filter for vector search based on query domain.
    
    Args:
        query: User's question
        available_domains: Set of domains that exist in the vector store
    
    Returns:
        Filter dict for ChromaDB or None if no filtering needed
    """
    detected = classify_query_domain(query)
    
    if not detected:
        return None  # No domain detected, search all
    
    # Only filter on domains that actually exist
    valid_domains = [d for d in detected if d in available_domains]
    
    if not valid_domains:
        return None
    
    if len(valid_domains) == 1:
        return {"domain": valid_domains[0]}
    else:
        return {"domain": {"$in": valid_domains}}


def extract_domain_context(query: str) -> str:
    """
    Extract domain-specific context hints for the LLM.
    Helps the model understand what type of answer is expected.
    
    Args:
        query: User's question
    
    Returns:
        Context hint string
    """
    domains = classify_query_domain(query)
    
    context_hints = {
        "claims": "This question relates to claims processing, billing, denials, or payer interactions.",
        "remits": "This question relates to remittance advice, ERA processing, deposits, or payment reconciliation.",
        "analytics": "This question relates to reports, dashboards, analytics, or performance metrics.",
        "patient": "This question relates to patient estimation, responsibility, or lockbox processing.",
        "user_management": "This question relates to user accounts, permissions, roles, or access control.",
        "rules": "This question relates to automation rules, Rule Wizard, or AltitudeAssist workflows.",
        "print": "This question relates to print services, statements, or batch printing.",
    }
    
    hints = [context_hints.get(d, "") for d in domains if d in context_hints]
    return " ".join(hints)


def get_all_domains() -> List[str]:
    """Return list of all defined domains"""
    return list(DOMAIN_MAPPINGS.keys()) + ["general"]
