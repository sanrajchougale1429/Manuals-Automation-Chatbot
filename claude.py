import streamlit as st
import os, fitz
from pathlib import Path
from dotenv import load_dotenv

# LangChain & OpenAI Imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
import weaviate

# --- 1. CONFIGURATION ---
load_dotenv()
BASE_DIR = Path(r"C:\Users\HORIZON\Claude\enterprise_sop_system")
SOP_DIR = BASE_DIR / "manuals"
DB_DIR = BASE_DIR / "weaviate_store"

SOP_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    MODEL = "gpt-4o"  # High precision for SOPs
    EMBED_MODEL = "text-embedding-ada-002"
    INDEX_NAME = "EnterpriseSops"

# --- 2. THE PERSISTENT STORAGE ENGINE ---
def chunk_text_by_sentences(text, chunk_size=5):
    """Split text into chunks of N sentences"""
    import re
    # Split by sentence endings (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    
    for i in range(0, len(sentences), chunk_size):
        chunk = ' '.join(sentences[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

def sync_manuals(vectorstore, weaviate_client):
    # Get existing indexed files from Weaviate
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
                    if not text.strip(): continue
                    
                    # Chunk by sentences instead of whole page
                    sentence_chunks = chunk_text_by_sentences(text, chunk_size=5)
                    
                    for chunk_idx, chunk in enumerate(sentence_chunks):
                        docs_to_add.append(Document(
                            page_content=chunk,
                            metadata={
                                "filename": pdf_path.name, 
                                "page": page_num + 1,
                                "chunk": chunk_idx
                            }
                        ))
                doc.close()
        if docs_to_add:
            vectorstore.add_documents(docs_to_add)
            st.toast(f"✅ Library synced!")
            st.rerun()

@st.cache_resource
def init_system():
    embeddings = OpenAIEmbeddings(model=Config.EMBED_MODEL)
    
    # Option 1: Connect to Weaviate Cloud (recommended for Windows)
    # Get your free cluster at: https://console.weaviate.cloud/
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")  # or your WCS URL
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")  # Optional for local
    
    if weaviate_api_key:
        weaviate_client = weaviate.connect_to_wcs(
            cluster_url=weaviate_url,
            auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
            headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
        )
    else:
        # For local Docker instance: docker run -d -p 8080:8080 semitechnologies/weaviate:latest
        weaviate_client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
        )
    
    # Initialize Weaviate vector store
    vectorstore = WeaviateVectorStore(
        client=weaviate_client,
        index_name=Config.INDEX_NAME,
        text_key="text",
        embedding=embeddings
    )
    
    llm = ChatOpenAI(model=Config.MODEL, temperature=0)
    return vectorstore, llm, weaviate_client

# --- 3. SYSTEM PROMPT ---
CITATION_PROMPT = """You are a Lead Enterprise Systems Consultant for Waystar. 
Your goal is to provide comprehensive, high-detail technical guidance based ONLY on the provided SOPs.

CORE PRINCIPLES:
- Provide DETAILED, THOROUGH answers with complete information
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

CITATION REQUIREMENT:
- At the END of your complete answer, add a blank line and then list all sources used
- Format: **Source:** filename.pdf, Page X
- If multiple pages from same file: **Source:** filename.pdf, Pages X, Y, Z
- List each unique source document on a new line

Your answers should feel natural and conversational while being technically precise and comprehensive."""

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

    vectorstore, llm, weaviate_client = init_system()
    sync_manuals(vectorstore, weaviate_client)

    with st.sidebar:
        st.title("📂 Library")
        try:
            # Get unique filenames from Weaviate
            collection = weaviate_client.collections.get(Config.INDEX_NAME)
            response = collection.query.fetch_objects(limit=10000)
            files = []
            for obj in response.objects:
                if hasattr(obj, 'properties') and obj.properties:
                    filename = obj.properties.get('filename')
                    if filename and filename not in files:
                        files.append(filename)
            files = sorted(files)
            
            if files:
                st.write(f"**Manuals Indexed:** {len(files)}")
                for f in files: st.caption(f"• {f}")
        except:
            st.write("No manuals indexed yet.")
        
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
            results = vectorstore.similarity_search(query, k=6)
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
        
        # JavaScript auto-scroll fix
        st.markdown("""
            <script>
                window.scrollTo(0, document.body.scrollHeight);
            </script>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()