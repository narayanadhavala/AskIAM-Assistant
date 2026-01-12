import chromadb
from langchain_chroma.vectorstores import Chroma
from langchain_ollama.embeddings import OllamaEmbeddings

# Embeddings (must match what you used during ingestion)
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Connect to Chroma HTTP server
client = chromadb.HttpClient(
    host="localhost",
    port=8000
)

# Load existing collection
vectordb = Chroma(
    client=client,
    collection_name="iam-metadata",
    embedding_function=embeddings
)

# # Simple similarity search
# results = vectordb.similarity_search(
#     "HR Analyst role in Workday",
#     k=2
# )

# for i, doc in enumerate(results, 1):
#     print(f"\nResult {i}")
#     print("Content:", doc.page_content)
#     print("Metadata:", doc.metadata)

queries = [
    "Who owns the HR Analyst role?",
    "Workday HR role",
    "Give me HR access in Workday",
    "Role for HR team in Workday"
]

for q in queries:
    print(f"\nQuery: {q}")
    results = vectordb.similarity_search(q, k=1)
    print(results[0].page_content)
    print(results[0].metadata)