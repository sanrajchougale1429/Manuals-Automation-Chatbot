import streamlit as st
import os, fitz
import openai
from pathlib import Path
from dotenv import load_dotenv

# LangChain & OpenAI Imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# Replaced langchain_chroma with langchain_qdrant
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document

# --- 1. CONFIGURATION ---
load_dotenv() 
api_key = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(r"C:\Users\HORIZON\Manuals Automation Chatbot")
SOP_DIR = BASE_DIR / "manuals"
DB_DIR = BASE_DIR / "vector_store"

SOP_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    MODEL = "gpt-4"  
    EMBED_MODEL = "text-embedding-ada-002"
    COLLECTION_NAME = "enterprise_sops"

# --- 2. THE PERSISTENT STORAGE ENGINE ---
def sync_manuals(vectorstore):
    # Qdrant search to get indexed filenames (logic remains the same)
    existing_data = vectorstore.client.scroll(
        collection_name=Config.COLLECTION_NAME,
        limit=10000,
        with_payload=True
    )[0]
    
    indexed_files = set(point.payload.get('metadata', {}).get('filename') for point in existing_data if point.payload)
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
    embeddings = OpenAIEmbeddings(model=Config.EMBED_MODEL)
    
    # Initialize Qdrant Client in local path mode for persistence
    client = QdrantClient(path=str(DB_DIR))
    
    # Ensure collection exists
    collections = client.get_collections().collections
    exists = any(c.name == Config.COLLECTION_NAME for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=Config.COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )

    # Wrap in LangChain VectorStore
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=Config.COLLECTION_NAME,
        embedding=embeddings,
    )
    
    llm = ChatOpenAI(model=Config.MODEL, temperature=0)
    return vectorstore, llm

# --- 3. SYSTEM PROMPT ---
CITATION_PROMPT = """You are a Lead Enterprise Systems Consultant for Waystar. 
Your goal is to provide comprehensive, high-detail technical guidance based ONLY on the provided SOPs.

CORE PRINCIPLES:
- Provide detailed answers appropriate to the question type and user intent
- Adapt your response structure to match the query type naturally
- Extract ALL relevant details from the context
- Use exact terminology from the manual

RESPONSE GUIDELINES BY QUERY TYPE:

**For "How to access/navigate" questions:**
- Brief explanation of what the feature is
- Complete navigation path with exact menu items
- Required permissions or access requirements
- What users will see when they arrive

**For "What is" or "Definition" questions:**
- Clear definition in 2-3 sentences
- Purpose and use cases
- Key characteristics or capabilities
- Related features or dependencies

**For "How to do/perform" questions:**
- Brief context of what the task accomplishes
- Step-by-step instructions with exact field/button names
- Any prerequisites or required settings
- Expected outcomes or results

**For "What does X do" or feature explanation:**
- Purpose and function overview
- Detailed breakdown of components/options
- How users interact with it
- Impact or results of using it

**For troubleshooting or "Why" questions:**
- Identify the issue/scenario
- Explain the cause if documented
- Provide solution steps
- Preventive measures if available

**For comparison questions:**
- Clear distinctions between options
- When to use each
- Advantages/limitations of each
- Relevant use cases

FORMATTING RULES:
- Use **bold** for ALL button names, field names, menu items, and key technical terms
- Use ### for major section headers only when needed
- Use bullet points (•) for lists of features/options
- Use numbered lists (1, 2, 3) for sequential steps
- Keep paragraphs focused and scannable
- Add line breaks between distinct sections
- give the answers in detaile as possible

DETAIL REQUIREMENTS:
- If the manual lists 8 options, include ALL 8 options
- If there are 6 steps, provide ALL 6 steps with complete details
- Describe what each button/field does, not just its name
- Include warnings, notes, or restrictions mentioned in the manual
- Never use vague phrases like "and more", "etc.", or "various options"

STRICT RULES:
- Use exact terminology from the manual (e.g., 'Rule Wizard', 'AltitudeAssist')
- If information is missing, state: "The manual does not cover [specific detail]"
- NEVER add information not found in the provided context
- NEVER give generic or superficial answers
- Do NOT add inline source citations (they're added automatically)

CITATION REQUIREMENT:
- At the END of your complete answer, add a blank line and then list all sources used
- Format: **Source:** filename.pdf, Page X
- List each source only once, even if used multiple times
- Do not repeat citations within the answer body


Your answers should feel natural and conversational while being technically precise and comprehensive."""


# --- 4. STREAMLIT UI ---
def main():
    st.set_page_config(page_title="SOP Intelligence", layout="wide")
    
    st.markdown("""
        <style>
        h1 { font-size: 1.5rem !important; color: #1E293B; margin-bottom: 0.5rem; }
        h2 { font-size: 1.3rem !important; color: #334155; }
        h3 { font-size: 1.1rem !important; font-weight: 700; color: #475569; }
        .stChatMessage { border-radius: 8px; border: 1px solid #E2E8F0; }
        </style>
    """, unsafe_allow_html=True)

    vectorstore, llm = init_system()
    sync_manuals(vectorstore)

    with st.sidebar:
        st.title("📂 Library")
        # Updated logic for Qdrant to list files
        points = vectorstore.client.scroll(
            collection_name=Config.COLLECTION_NAME,
            limit=10000,
            with_payload=True
        )[0]
        indexed_files = sorted(list(set(p.payload.get('metadata', {}).get('filename') for p in points if p.payload)))
        
        if indexed_files:
            st.write(f"**Manuals Indexed:** {len(indexed_files)}")
            for f in indexed_files: st.caption(f"• {f}")
        
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
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()