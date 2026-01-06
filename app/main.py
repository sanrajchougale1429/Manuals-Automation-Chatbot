"""
Enterprise Manuals Intelligence - Main Application
A RAG-powered chatbot for enterprise documentation
"""

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage

from config import ACTIVE_BACKEND, ModelBackend, RetrievalConfig
from llm import get_llm, get_model_info
from ingestion import sync_manuals, get_manual_info
from retrieval import retrieve_context, build_retrieval_summary
from vectorstore import reset_vectorstore, get_collection_stats
from reranker import get_reranker_status
from prompts import get_prompt


def init_page():
    """Initialize Streamlit page configuration"""
    st.set_page_config(
        page_title="Waystar Manuals Intelligence",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Clean, modern CSS without overlap issues
    st.markdown("""
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Global Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        
        /* Main Background */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Main Content Area */
        .main .block-container {
            padding: 2rem !important;
            max-width: 1200px !important;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            margin: 1.5rem auto !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #1e293b !important;
            padding: 1.5rem 1rem !important;
        }
        
        [data-testid="stSidebar"] > div {
            background: #1e293b !important;
        }
        
        /* Sidebar Text Colors */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #e2e8f0 !important;
        }
        
        /* Sidebar Title */
        [data-testid="stSidebar"] h1 {
            font-size: 1.3rem !important;
            font-weight: 700 !important;
            margin-bottom: 1.5rem !important;
            padding-bottom: 1rem !important;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Sidebar Info Box */
        [data-testid="stSidebar"] [data-testid="stAlert"] {
            background: rgba(102, 126, 234, 0.15) !important;
            border: 1px solid rgba(102, 126, 234, 0.3) !important;
            border-radius: 8px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stAlert"] p {
            color: #ffffff !important;
            line-height: 1.6 !important;
            margin: 0 !important;
        }
        
        /* Metrics in Sidebar */
        [data-testid="stSidebar"] [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.05) !important;
            padding: 0.75rem !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 0.85rem !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 1.5rem !important;
            font-weight: 700 !important;
        }
        
        /* Sidebar Buttons */
        [data-testid="stSidebar"] button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin: 0.25rem 0 !important;
        }
        
        [data-testid="stSidebar"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Expander in Sidebar */
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            margin: 0.5rem 0 !important;
        }
        
        [data-testid="stSidebar"] .streamlit-expanderHeader {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        [data-testid="stSidebar"] .streamlit-expanderContent {
            color: #cbd5e1 !important;
        }
        
        /* Main Title */
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            text-align: center !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Caption/Subtitle */
        [data-testid="stCaptionContainer"] {
            text-align: center !important;
            color: #64748b !important;
            font-size: 1rem !important;
            margin-bottom: 2rem !important;
        }
        
        /* Chat Messages */
        .stChatMessage {
            border-radius: 12px !important;
            padding: 1.25rem !important;
            margin-bottom: 1rem !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* User Message */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]) {
            background: linear-gradient(135deg, #f0f4ff 0%, #f5f3ff 100%) !important;
            border-left: 4px solid #667eea !important;
        }
        
        /* Chat Input */
        .stChatInput {
            border-radius: 12px !important;
            border: 2px solid #e2e8f0 !important;
        }
        
        .stChatInput:focus-within {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: #f8fafc !important;
            border-radius: 8px !important;
            padding: 0.75rem 1rem !important;
            font-weight: 600 !important;
        }
        
        /* Success/Error/Warning */
        .stSuccess {
            background: #d1fae5 !important;
            color: #065f46 !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }
        
        .stError {
            background: #fee2e2 !important;
            color: #991b1b !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }
        
        .stWarning {
            background: #fef3c7 !important;
            color: #92400e !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }
        
        /* Code blocks */
        code {
            background: #1e293b !important;
            color: #e2e8f0 !important;
            padding: 0.2rem 0.4rem !important;
            border-radius: 4px !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with system info and controls"""
    with st.sidebar:
        st.title("📚 Manual Library")
        
        model_info = get_model_info()
        
        st.info(f"""
**{model_info['backend']}**  
LLM: {model_info['llm_model']}  
Embed: {model_info['embed_model']}
        """)
        
        stats = get_collection_stats()
        col1, col2 = st.columns(2)
        col1.metric("📄 Files", stats["indexed_files"])
        col2.metric("📦 Chunks", stats["total_chunks"])
        
        with st.expander("📋 Indexed Manuals"):
            for manual in get_manual_info():
                status = "✅" if manual["indexed"] else "⏳"
                st.caption(f"{status} {manual['filename']}")
        
        with st.expander("⚙️ System Status"):
            st.write(f"**Re-ranker:** {get_reranker_status()}")
            st.write(f"**Domain Filter:** {'On' if RetrievalConfig.ENABLE_DOMAIN_FILTER else 'Off'}")
            if stats["domains"]:
                st.write("**Domains:** " + ", ".join(stats["domains"]))
        
        st.divider()
        
        col1, col2 = st.columns(2)
        if col1.button("🔄 Sync"):
            with st.spinner("Syncing..."):
                result = sync_manuals()
                if result["new_files"] > 0:
                    st.success(f"Added {result['new_files']} files")
                    st.rerun()
                else:
                    st.info("Up to date")
        
        if col2.button("🗑️ Reset"):
            reset_vectorstore()
            st.cache_resource.clear()
            st.success("Reset!")
            st.rerun()


def main():
    """Main application"""
    init_page()
    
    if "initialized" not in st.session_state:
        sync_manuals()
        st.session_state.initialized = True
    
    render_sidebar()
    
    st.title("🏢 Waystar Manuals Intelligence")
    st.caption("AI-Powered Documentation Assistant | Powered by Claude Sonnet 4")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if query := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                documents, context = retrieve_context(query)
                
                if not documents:
                    response = "No relevant information found. Try rephrasing or check if manuals are indexed."
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    return
                
                summary = build_retrieval_summary(documents, query)
                with st.expander("🔍 Retrieved from"):
                    st.write(f"Docs: {summary['documents_found']} | Domains: {', '.join(summary['domains'])}")
            
            messages = [
                SystemMessage(content=get_prompt()),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
            ]
            
            llm = get_llm(streaming=True)
            response_container = st.empty()
            full_response = ""
            
            try:
                for chunk in llm.stream(messages):
                    content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    full_response += (content or "")
                    response_container.markdown(full_response + "▌")
                
                response_container.markdown(full_response)
            
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                
                if "API key" in str(e).lower() or "authentication" in str(e).lower():
                    st.warning("💡 **Tip:** Make sure your API key is set in the `.env` file")
                    st.code("OPENAI_API_KEY=sk-your-key-here", language="bash")
                
                full_response = error_msg
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    main()