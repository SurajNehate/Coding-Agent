import os
from enum import Enum
from typing import Optional, Any
from langchain_core.language_models import BaseChatModel

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"

def get_llm(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs: Any
) -> BaseChatModel:
    """
    Get an LLM instance based on provider.
    
    Args:
        provider: LLM provider name ("google", "anthropic", "openai")
        model: Model name (uses defaults if not specified)
        api_key: API key (uses env vars if not specified)
        temperature: Sampling temperature
        **kwargs: Additional provider-specific arguments
        
    Returns:
        BaseChatModel instance
    """
    provider = provider.lower()
    
    if provider == LLMProvider.GROQ:
        from langchain_groq import ChatGroq
        
        default_model = os.getenv("GROQ_MODEL")
        api_key = api_key or os.getenv("GROQ_API_KEY")
            
        return ChatGroq(
            model=model or default_model,
            temperature=temperature,
            api_key=api_key,
            **kwargs
        )

    elif provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic
        
        default_model = os.getenv("ANTHROPIC_MODEL")
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        return ChatAnthropic(
            model=model or default_model,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )
    
    elif provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI
        
        default_model = os.getenv("OPENAI_MODEL")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        return ChatOpenAI(
            model=model or default_model,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )
    
    elif provider == LLMProvider.OLLAMA:
        from langchain_ollama import ChatOllama
        
        default_model = os.getenv("OLLAMA_MODEL")
        base_url = os.getenv("OLLAMA_BASE_URL")
            
        return ChatOllama(
            model=model or default_model,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )

    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {', '.join([p.value for p in LLMProvider])}"
        )
