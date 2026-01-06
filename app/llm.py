"""
LLM Module
Supports OpenAI and Claude (Anthropic) language models
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from config import ACTIVE_BACKEND, ModelBackend, OpenAIConfig, ClaudeConfig


def get_llm(streaming: bool = True) -> BaseChatModel:
    """
    Get the appropriate LLM based on active backend.
    
    Args:
        streaming: Whether to enable streaming responses
    
    Returns:
        LangChain ChatModel instance
    """
    if ACTIVE_BACKEND == ModelBackend.CLAUDE:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=ClaudeConfig.LLM_MODEL,
                temperature=0,
                max_tokens=4096,
                anthropic_api_key=ClaudeConfig.API_KEY,
            )
        except ImportError:
            print("⚠️ langchain-anthropic not installed. Install with: pip install langchain-anthropic")
            print("Falling back to OpenAI...")
            return ChatOpenAI(
                model=OpenAIConfig.LLM_MODEL,
                temperature=0,
                streaming=streaming,
            )
    else:  # OpenAI (default)
        return ChatOpenAI(
            model=OpenAIConfig.LLM_MODEL,
            temperature=0,
            streaming=streaming,
        )


def get_model_info() -> dict:
    """Get information about the currently configured model"""
    if ACTIVE_BACKEND == ModelBackend.CLAUDE:
        return {
            "backend": "Claude (Anthropic)",
            "llm_model": ClaudeConfig.LLM_MODEL,
            "embed_model": ClaudeConfig.EMBED_MODEL,
            "cost": "Paid",
        }
    else:  # OpenAI
        return {
            "backend": "OpenAI",
            "llm_model": OpenAIConfig.LLM_MODEL,
            "embed_model": OpenAIConfig.EMBED_MODEL,
            "cost": "Paid",
        }
