import chromadb
from langchain_chroma import Chroma
from core.model_factory import create_embeddings
from core.config_loader import load_config

def load_vectordb():
    cfg = load_config()
    client = chromadb.HttpClient(
        host=cfg["chroma"]["host"],
        port=cfg["chroma"]["port"],
    )

    return Chroma(
        client=client,
        collection_name=cfg["chroma"]["collection"],
        embedding_function=create_embeddings(),
    )
