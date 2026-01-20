import psycopg2
import psycopg2.extras
import chromadb
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="postgres",
    database="iamdb"
)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

documents = []

# Roles
cursor.execute('SELECT * FROM "Roles"')
for row in cursor.fetchall():
    documents.append(
        Document(
            page_content=(
                f"Role {row['RoleName']} belongs to the {row['AppName']} application. "
                f"Role ID is {row['RoleID']}. "
                f"The role owner is {row['Owner']}."
            ),
            metadata={"type": "role", **row}
        )
    )

# Users
cursor.execute('SELECT * FROM "Users"')
for row in cursor.fetchall():
    documents.append(
        Document(
            page_content=(
                f"User {row['UserName']} has user ID {row['UserID']}. "
                f"Email address is {row['Email']}. "
                f"The manager of this user is {row['Manager']}."
            ),
            metadata={"type": "user", **row}
        )
    )

# Applications
cursor.execute('SELECT * FROM "Applications"')
for row in cursor.fetchall():
    documents.append(
        Document(
            page_content=(
                f"Application {row['AppName']} has application ID {row['AppID']}. "
                f"The application owner is {row['AppOwner']}."
            ),
            metadata={"type": "application", **row}
        )
    )

# Ollama embeddings
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Chroma HTTP client
client = chromadb.HttpClient(
    host="localhost",
    port=8000
)

client.delete_collection("iam-metadata")
print("Collection iam-metadata deleted")

collections = client.list_collections()
print([c.name for c in collections])

# Vector store
vectordb = Chroma(
    client=client,
    collection_name="iam-metadata",
    embedding_function=embeddings
)

vectordb.add_documents(documents)

print("Vectorization completed successfully using Chroma Docker")
