from langchain_ollama import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from core.config_loader import load_config

def create_llm():
    cfg = load_config()
    return ChatOllama(
        model=cfg["ollama"]["llm_model"],
        base_url=cfg["ollama"]["base_url"],
        temperature=0,
    )

def create_embeddings():
    cfg = load_config()
    return OllamaEmbeddings(
        model=cfg["ollama"]["embedding_model"],
        base_url=cfg["ollama"]["base_url"],
    )
