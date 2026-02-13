from langchain_community.chat_models import ChatOllama
from app.config import settings


def get_ollama_llm(model_name: str, temperature: float, max_tokens: int) -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=model_name,
        temperature=temperature,
        model_kwargs={"num_predict": max_tokens},
    )
