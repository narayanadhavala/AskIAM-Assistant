import chromadb

client = chromadb.HttpClient(
    host="localhost",
    port=8000
)

collection_name = "iam-metadata"  # change as needed

collection = client.get_collection(collection_name)
data = collection.get(include=["documents", "embeddings", "metadatas"])

print(f"\nCollection: {collection_name}")

if not data["documents"]:
    print("No documents found")
else:
    for i, doc in enumerate(data["documents"]):
        print(f"\nDocument {i+1}")
        print("Content:", doc)
        print("Metadata:", data["metadatas"][i])
        print("Embedding vector length:", len(data["embeddings"][i]))
