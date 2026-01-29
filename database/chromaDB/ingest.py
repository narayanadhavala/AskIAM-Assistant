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
cursor.execute('SELECT * FROM roles')
for row in cursor.fetchall():
    documents.append(
        Document(
            page_content=(
                f"Role {row['role_name']} belongs to the {row['app_name']} application. "
                f"Role ID is {row['role_id']}. "
                f"The role owner is {row['owner']}."
            ),
            metadata={
                "EntityType": "Role",
                "RoleName": row['role_name'],
                "AppName": row['app_name'],
                "RoleID": row['role_id'],
                "Owner": row['owner']
            }
        )
    )

# Users
cursor.execute('SELECT * FROM users')
for row in cursor.fetchall():
    documents.append(
        Document(
            page_content=(
                f"User {row['user_name']} has user ID {row['user_id']}. "
                f"Email address is {row['email']}. "
                f"The manager of this user is {row['manager']}."
            ),
            metadata={
                "EntityType": "User",
                "UserName": row['user_name'],
                "UserID": row['user_id'],
                "Email": row['email'],
                "Manager": row['manager']
            }
        )
    )

# Applications
cursor.execute('SELECT * FROM applications')
for row in cursor.fetchall():
    documents.append(
        Document(
            page_content=(
                f"Application {row['app_name']} has application ID {row['app_id']}. "
                f"The application owner is {row['app_owner']}."
            ),
            metadata={
                "EntityType": "Application",
                "AppName": row['app_name'],
                "AppID": row['app_id'],
                "AppOwner": row['app_owner']
            }
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
