# app/services/llm_factory.py
from langchain_ollama import ChatOllama
from app.config import settings


def get_ollama_llm(
    model_name: str,
    temperature: float,
    max_tokens: int,
) -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=model_name,
        temperature=temperature,
        timeout=120,
        model_kwargs={
            "num_predict": max_tokens,
            "num_ctx": 4096,  # Smaller context window = faster response
            "repeat_penalty": 1.2,  # Prevents the AI from looping
        },
    )