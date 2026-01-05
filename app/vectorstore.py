import os
import weaviate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from config import Config
import streamlit as st


@st.cache_resource
def init_system():
    embeddings = OpenAIEmbeddings(model=Config.EMBED_MODEL)

    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

    if weaviate_api_key:
        client = weaviate.connect_to_wcs(
            cluster_url=weaviate_url,
            auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
            headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")},
        )
    else:
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")},
        )

    vectorstore = WeaviateVectorStore(
        client=client,
        index_name=Config.INDEX_NAME,
        text_key="text",
        embedding=embeddings,
    )

    llm = ChatOpenAI(model=Config.MODEL, temperature=0)
    return vectorstore, llm, client