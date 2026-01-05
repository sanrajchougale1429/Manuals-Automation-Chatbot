import streamlit as st
import os, fitz
from pathlib import Path
from dotenv import load_dotenv

# LangChain & Anthropic Imports
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document

# --- 1. CONFIGURATION ---
load_dotenv()
BASE_DIR = Path(r"C:\Users\HORIZON\Claude\enterprise_sop_system")
SOP_DIR = BASE_DIR / "manuals"
DB_DIR = BASE_DIR / "vector_store"

SOP_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    MODEL = "claude-sonnet-4-20250514" 
    EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# --- 2. THE PERSISTENT STORAGE ENGINE ---
def sync_manuals(vectorstore):
    existing_data = vectorstore.get()
    indexed_files = set(m.get('filename') for m in existing_data['metadatas']) if existing_data['metadatas'] else set()
    new_files = [f for f in SOP_DIR.glob("*.pdf") if f.name not in indexed_files]
    
    if new_files:
        docs_to_add = []
        for pdf_path in new_files:
            with st.spinner(f"Reading: {pdf_path.name}..."):
                doc = fitz.open(pdf_path)
                for page_num, page in enumerate(doc):
                    text = page.get_text("text")
                    if not text.strip(): continue
                    docs_to_add.append(Document(
                        page_content=text,
                        metadata={"filename": pdf_path.name, "page": page_num + 1}
                    ))
                doc.close()
        if docs_to_add:
            vectorstore.add_documents(docs_to_add)
            st.toast(f"✅ Library synced!")
            st.rerun()

@st.cache_resource
def init_system():
    embeddings = HuggingFaceEmbeddings(model_name=Config.EMBED_MODEL)
    vectorstore = Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings,
        collection_name="enterprise_sops"
    )
    llm = ChatAnthropic(model=Config.MODEL, temperature=0)
    return vectorstore, llm

# --- 3. SYSTEM PROMPT (Updated for smaller Markdown) ---
CITATION_PROMPT = """You are a professional Enterprise Assistant. 
Answer questions using ONLY the provided context.

FORMATTING RULES:
1. Use '###' for your main headings to keep them a standard size.
2. Use bold text for key steps.
3. If the answer is not in the text, say you cannot find it.
"""

# --- 4. STREAMLIT UI ---
def main():
    st.set_page_config(page_title="SOP Intelligence", layout="wide")
    
    # CSS FIX: This forces headings to look like normal, professional text
    st.markdown("""
        <style>
        /* Make H1, H2, and H3 look like normal balanced headers */
        h1 { font-size: 1.5rem !important; color: #1E293B; margin-bottom: 0.5rem; }
        h2 { font-size: 1.3rem !important; color: #334155; }
        h3 { font-size: 1.1rem !important; font-weight: 700; color: #475569; }
        
        /* Clean up chat message bubbles */
        .stChatMessage { border-radius: 8px; border: 1px solid #E2E8F0; }
        </style>
    """, unsafe_allow_html=True)

    vectorstore, llm = init_system()
    sync_manuals(vectorstore)

    with st.sidebar:
        st.title("📂 Library")
        db_info = vectorstore.get()
        if db_info['metadatas']:
            files = sorted(list(set(m['filename'] for m in db_info['metadatas'])))
            st.write(f"**Manuals Indexed:** {len(files)}")
            for f in files: st.caption(f"• {f}")
        
        if st.button("🗑️ Reset Database"):
            import shutil
            if DB_DIR.exists(): shutil.rmtree(DB_DIR)
            st.cache_resource.clear()
            st.rerun()

    st.title("🏢 Enterprise Manuals Intelligence")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if query := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)

        with st.chat_message("assistant"):
            results = vectorstore.similarity_search(query, k=4)
            context_text = ""
            for d in results:
                context_text += f"\nSOURCE: {d.metadata['filename']} | PAGE: {d.metadata['page']}\n{d.page_content}\n"
            
            messages = [
                SystemMessage(content=CITATION_PROMPT),
                HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {query}")
            ]
            
            response_container = st.empty()
            full_response = ""
            
            for chunk in llm.stream(messages):
                full_response += (chunk.content or "")
                response_container.markdown(full_response + "▌")
            
            response_container.markdown(full_response)
            
            with st.expander("📍 Verified Sources"):
                for d in results:
                    st.info(f"📄 {d.metadata['filename']} (Page {d.metadata['page']})")

        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()