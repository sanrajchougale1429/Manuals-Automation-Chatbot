"""
Smart Chunking Module
Implements recursive text splitting with overlap and section awareness
"""

import re
from typing import List, Tuple
from dataclasses import dataclass
from config import ChunkConfig


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    content: str
    start_char: int
    end_char: int
    section_header: str = ""


def extract_section_headers(text: str) -> List[Tuple[int, str]]:
    """
    Extract section headers and their positions from text.
    Looks for patterns like numbered sections, ALL CAPS headers, etc.
    """
    headers = []
    
    # Pattern 1: Numbered sections (1. Header, 1.1 Header, etc.)
    numbered_pattern = r'^(\d+\.?\d*\.?\s+[A-Z][^\n]{3,50})$'
    
    # Pattern 2: ALL CAPS headers
    caps_pattern = r'^([A-Z][A-Z\s]{5,50})$'
    
    # Pattern 3: Headers with colon
    colon_pattern = r'^([A-Z][^:\n]{3,40}:)\s*$'
    
    for pattern in [numbered_pattern, caps_pattern, colon_pattern]:
        for match in re.finditer(pattern, text, re.MULTILINE):
            headers.append((match.start(), match.group(1).strip()))
    
    # Sort by position
    headers.sort(key=lambda x: x[0])
    return headers


def find_current_section(position: int, headers: List[Tuple[int, str]]) -> str:
    """Find the section header that applies to a given position"""
    current_section = ""
    for header_pos, header_text in headers:
        if header_pos <= position:
            current_section = header_text
        else:
            break
    return current_section


def recursive_text_splitter(
    text: str,
    chunk_size: int = ChunkConfig.CHUNK_SIZE,
    chunk_overlap: int = ChunkConfig.CHUNK_OVERLAP,
    min_chunk_size: int = ChunkConfig.MIN_CHUNK_SIZE
) -> List[Chunk]:
    """
    Split text into overlapping chunks while respecting semantic boundaries.
    
    Strategy:
    1. Try to split on paragraph boundaries (\\n\\n)
    2. If chunks too large, split on sentence boundaries (. ! ?)
    3. If still too large, split on word boundaries
    4. Maintain overlap between chunks for context continuity
    """
    
    if not text or len(text.strip()) < min_chunk_size:
        return []
    
    # Extract section headers for metadata
    headers = extract_section_headers(text)
    
    # Separators in order of preference (most semantic to least)
    separators = [
        "\n\n",  # Paragraph breaks
        "\n",    # Line breaks
        ". ",    # Sentence endings
        "! ",
        "? ",
        "; ",    # Clause breaks
        ", ",    # Phrase breaks
        " ",     # Word breaks
    ]
    
    chunks = []
    
    def split_recursive(text_segment: str, start_offset: int, sep_index: int = 0) -> List[Chunk]:
        """Recursively split text using progressively finer separators"""
        
        if len(text_segment) <= chunk_size:
            if len(text_segment.strip()) >= min_chunk_size:
                section = find_current_section(start_offset, headers)
                return [Chunk(
                    content=text_segment.strip(),
                    start_char=start_offset,
                    end_char=start_offset + len(text_segment),
                    section_header=section
                )]
            return []
        
        if sep_index >= len(separators):
            # Force split at chunk_size if no separators work
            section = find_current_section(start_offset, headers)
            result = []
            for i in range(0, len(text_segment), chunk_size - chunk_overlap):
                chunk_text = text_segment[i:i + chunk_size]
                if len(chunk_text.strip()) >= min_chunk_size:
                    result.append(Chunk(
                        content=chunk_text.strip(),
                        start_char=start_offset + i,
                        end_char=start_offset + i + len(chunk_text),
                        section_header=section
                    ))
            return result
        
        separator = separators[sep_index]
        parts = text_segment.split(separator)
        
        if len(parts) == 1:
            # Separator not found, try next one
            return split_recursive(text_segment, start_offset, sep_index + 1)
        
        result = []
        current_chunk = ""
        current_start = start_offset
        
        for i, part in enumerate(parts):
            # Add separator back (except for last part)
            part_with_sep = part + separator if i < len(parts) - 1 else part
            
            if len(current_chunk) + len(part_with_sep) <= chunk_size:
                current_chunk += part_with_sep
            else:
                # Save current chunk
                if len(current_chunk.strip()) >= min_chunk_size:
                    section = find_current_section(current_start, headers)
                    result.append(Chunk(
                        content=current_chunk.strip(),
                        start_char=current_start,
                        end_char=current_start + len(current_chunk),
                        section_header=section
                    ))
                
                # Start new chunk with overlap
                if chunk_overlap > 0 and current_chunk:
                    # Get last chunk_overlap characters for overlap
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + part_with_sep
                    current_start = current_start + len(current_chunk) - len(overlap_text) - len(part_with_sep)
                else:
                    current_chunk = part_with_sep
                    current_start = start_offset + sum(len(p) + len(separator) for p in parts[:i])
                
                # If single part is too large, split it recursively
                if len(current_chunk) > chunk_size:
                    result.extend(split_recursive(current_chunk, current_start, sep_index + 1))
                    current_chunk = ""
        
        # Don't forget the last chunk
        if len(current_chunk.strip()) >= min_chunk_size:
            section = find_current_section(current_start, headers)
            result.append(Chunk(
                content=current_chunk.strip(),
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                section_header=section
            ))
        
        return result
    
    return split_recursive(text, 0)


def chunk_pdf_page(text: str, page_num: int, filename: str) -> List[dict]:
    """
    Chunk a single PDF page and return documents with metadata.
    
    Returns:
        List of dicts with 'content' and 'metadata' keys
    """
    chunks = recursive_text_splitter(text)
    
    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            "content": chunk.content,
            "metadata": {
                "filename": filename,
                "page": page_num,
                "chunk_index": i,
                "section": chunk.section_header,
                "char_start": chunk.start_char,
                "char_end": chunk.end_char,
            }
        })
    
    return documents


# For backward compatibility
def chunk_text_by_sentences(text: str, chunk_size: int = 5) -> List[str]:
    """
    Legacy function - now uses smart chunking internally.
    Kept for backward compatibility.
    """
    chunks = recursive_text_splitter(text)
    return [chunk.content for chunk in chunks]
