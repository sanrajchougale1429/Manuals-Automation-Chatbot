import streamlit as st
import fitz
from langchain_core.documents import Document
from utils import chunk_text_by_sentences
from config import SOP_DIR, Config


def sync_manuals(vectorstore, weaviate_client):
    try:
        collection = weaviate_client.collections.get(Config.INDEX_NAME)
        response = collection.query.fetch_objects(limit=10000)
        indexed_files = set()

        for obj in response.objects:
            if hasattr(obj, 'properties') and obj.properties:
                filename = obj.properties.get('filename')
                if filename:
                    indexed_files.add(filename)
    except:
        indexed_files = set()

    new_files = [f for f in SOP_DIR.glob("*.pdf") if f.name not in indexed_files]

    if new_files:
        docs_to_add = []
        for pdf_path in new_files:
            with st.spinner(f"Reading: {pdf_path.name}..."):
                doc = fitz.open(pdf_path)
                for page_num, page in enumerate(doc):
                    text = page.get_text("text")
                    if not text.strip():
                        continue

                    chunks = chunk_text_by_sentences(text, chunk_size=5)

                    for idx, chunk in enumerate(chunks):
                        docs_to_add.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "filename": pdf_path.name,
                                    "page": page_num + 1,
                                    "chunk": idx,
                                },
                            )
                        )
                doc.close()

        if docs_to_add:
            vectorstore.add_documents(docs_to_add)
            st.toast("✅ Library synced!")
            st.rerun()