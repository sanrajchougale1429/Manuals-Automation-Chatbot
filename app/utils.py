def chunk_text_by_sentences(text, chunk_size=5):
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []

    for i in range(0, len(sentences), chunk_size):
        chunk = ' '.join(sentences[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks