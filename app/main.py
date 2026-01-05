import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage

from vectorstore import init_system
from ingestion import sync_manuals
from prompts import CITATION_PROMPT
from config import Config


def main():
    st.set_page_config(page_title="SOP Intelligence", layout="wide")

    # ---- INIT SYSTEM ----
    vectorstore, llm, weaviate_client = init_system()
    sync_manuals(vectorstore, weaviate_client)

    # =========================
    # ✅ SIDEBAR (RESTORED)
    # =========================
    with st.sidebar:
        st.title("📂 Library")

        try:
            collection = weaviate_client.collections.get(Config.INDEX_NAME)
            response = collection.query.fetch_objects(limit=10000)

            files = []
            for obj in response.objects:
                if hasattr(obj, "properties") and obj.properties:
                    filename = obj.properties.get("filename")
                    if filename and filename not in files:
                        files.append(filename)

            files = sorted(files)

            if files:
                st.write(f"**Manuals Indexed:** {len(files)}")
                for f in files:
                    st.caption(f"• {f}")
            else:
                st.write("No manuals indexed yet.")

        except Exception:
            st.write("No manuals indexed yet.")

        if st.button("🗑️ Reset Database"):
            import shutil
            from config import DB_DIR

            if DB_DIR.exists():
                shutil.rmtree(DB_DIR)

            st.cache_resource.clear()
            st.rerun()

    # =========================
    # MAIN UI
    # =========================
    st.title("🏢 Enterprise Manuals Intelligence")

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
            results = vectorstore.similarity_search(query, k=6)

            context_text = ""
            for d in results:
                context_text += (
                    f"\nSOURCE: {d.metadata['filename']} | PAGE: {d.metadata['page']}\n"
                    f"{d.page_content}\n"
                )

            messages = [
                SystemMessage(content=CITATION_PROMPT),
                HumanMessage(
                    content=f"Context:\n{context_text}\n\nQuestion: {query}"
                ),
            ]

            response_container = st.empty()
            full_response = ""

            for chunk in llm.stream(messages):
                full_response += chunk.content or ""
                response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


if __name__ == "__main__":
    main()