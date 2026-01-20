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

queries = [
    "I need access to the HR Analyst role in the Workday application"
    #"I need access to the Payroll Admin role in the Salesforce application",
    #"I'm Kevin.Liu and I need access for IT Admin role for Azure AD"
]

for q in queries:
    print(f"\nQuery: {q}")
    results = vectordb.similarity_search(q, k=2)
    for i in range(len(results)):
        if not results:
            print("No results found for query: {}".format(q))
        else:
            print("Content:", results[i].page_content)
            print("Metadata:", results[i].metadata)
