# AskIAM Assistant - AI-Powered IAM Access Validation

An intelligent IAM (Identity and Access Management) assistant that validates user access requests using LLM-based decision-making with RAG (Retrieval Augmented Generation) and a multi-tool validation pipeline.

---

## 📋 Project Overview

The AskIAM Assistant provides an intelligent chatbot interface for validating IAM access requests. It combines:
- **RAG Engine**: Vector search on IAM metadata using ChromaDB
- **LLM Processing**: Natural language understanding via Ollama
- **MCP Tools**: SQL generation and validation for entity verification
- **Comprehensive Tracing**: Full execution trace logging for audit purposes

---

## 📁 Directory Structure

```
AskIAM-Assistant/
├── backend/                         # Main application (current active version)
│   ├── app.py                       # Gradio UI entry point
│   ├── orchestrator.py              # Request routing (RAG → MCP)
│   ├── config.yaml                  # Configuration (LLM, ChromaDB, tools)
│   ├── requirements.txt             # Python dependencies
│   ├── core/                        # Core utilities
│   │   ├── config_loader.py         # YAML config loader
│   │   ├── model_factory.py         # LLM & embeddings factory
│   │   └── types.py                 # Type definitions
│   ├── mcp/                         # Model Context Protocol tools
│   │   ├── trace.py                 # Trace handler & session manager
│   │   ├── extract.py               # Request extraction
│   │   ├── validators.py            # Entity validation
│   │   ├── graph.py                 # MCP orchestration
│   │   └── tools/
│   │       ├── entity_validator.py  # Generic entity validator
│   │       ├── sql_generator.py     # SQL generation tool
│   │       └── sql_validator.py     # SQL safety validator
│   └── rag/                         # RAG pipeline
│       ├── rag_engine.py            # RAG similarity search & LLM validation
│       └── vectorstore.py           # ChromaDB vector store initialization
│
├── database/                        # Database setup
│   ├── iam_sample_data.sql         # Sample IAM data (Users, Apps, Roles)
│   └── chromaDB/
│       ├── ingest.py               # Ingest IAM data into ChromaDB
│       └── test-chroma.py          # Test ChromaDB queries
│
├── ReadME.md                        
├── requirements.txt                 # Root-level dependencies
└── tools.yaml                       # MCP toolbox configuration

```

---

## ⚙️ Prerequisites

- **OS**: Linux/macOS/Windows (Linux recommended)
- **Python**: 3.9+
- **Docker**: For MySQL, ChromaDB, Toolbox
- **Ollama**: For running LLMs locally

---

## 🚀 Setup Instructions

### Step 1: Clone/Extract the Project

```bash
cd /path/to/AskIAM-Assistant
cd backend  # Enter the main application directory
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Start Docker Services

#### 3.1 MySQL Database

```bash
docker pull mysql:8.0
docker run -d --name iam-mysql \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -p 3306:3306 \
  mysql:8.0

# Wait 30 seconds for initialization
sleep 30

# Load sample data
mysql -h 127.0.0.1 -u root -proot123 < ../database/iam_sample_data.sql
```

#### 3.2 ChromaDB (Vector Store)

```bash
docker pull chromadb/chroma:latest
docker run -d --name chromadb \
  -p 8000:8000 \
  chromadb/chroma:latest
```

#### 3.3 Toolbox (MCP Server for SQL Execution)

```bash
docker run -d --name iam-toolbox \
  -p 5000:5000 \
  --network host \
  -v "$(pwd)/../tools.yaml:/app/tools.yaml" \
  us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:0.23.0
```

### Step 4: Start Ollama

In a separate terminal:

```bash
ollama serve

# In another terminal, pull required models
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

### Step 5: Ingest IAM Data into ChromaDB

```bash
python ../database/chromaDB/ingest.py
```

### Step 6: Start the Application

```bash
python app.py
```

The app will launch on `http://localhost:7860`

---

## 📊 Request Processing Flow

```
User Query
    ↓
[Orchestrator] (orchestrator.py)
    ├─→ [RAG Validation] (rag_engine.py)
    │   ├─→ Vector similarity search (ChromaDB)
    │   ├─→ LLM decision (Ollama)
    │   └─→ Return (if confident)
    │
    ├─→ [MCP Validation] (graph.py)
    │   ├─→ Extract request parameters (extract.py)
    │   ├─→ Validate entities (validators.py)
    │   │   ├─→ Generate SQL (sql_generator.py)
    │   │   ├─→ Validate SQL (sql_validator.py)
    │   │   └─→ Execute via Toolbox
    │   └─→ Return result
    │
    └─→ [Response to User]
         └─→ [Full Trace Logged] (trace.py)
```

---

## 🔍 Tracing System

The application includes comprehensive execution tracing:

### During Active Session
- Individual steps printed to console
- Shows tool calls with inputs/outputs
- Real-time feedback on validation process

### On Session End
- Complete accumulated trace printed
- Includes all requests from the session
- Exported to JSON with full details

### Trace File Location
- Default: `iam_trace_chat_session_YYYYMMDD_HHMMSS.json`
- Cache file: `.trace_session_cache` (tracks current session)

### Example Trace Structure
```json
{
  "session_timestamp": "2026-01-12T07:33:44",
  "total_requests": 2,
  "total_steps": 4,
  "stack": [
    {
      "step": 1,
      "tool": "rag_similarity_search",
      "input": { "query": "I need HR Analyst in Workday", "k": 1 },
      "output": "Retrieved 1 document(s): [...]"
    },
    ...
  ]
}
```

---

## 🔧 Configuration

Edit `backend/config.yaml`:

```yaml
ollama:
  base_url: http://localhost:11434
  llm_model: llama3.1:8b
  embedding_model: nomic-embed-text

chroma:
  host: localhost
  port: 8000
  collection: iam-metadata

toolbox:
  url: http://127.0.0.1:5000

ui:
  title: IAM Access Assistant

entities:
  user:
    table: Users
    id_column: UserID
    name_column: UserName
    error: Invalid user
  # ... more entities
```

---

## 📝 Usage

### Web UI

1. Open `http://localhost:7860`
2. Type your access request:
   - "I need access to the HR Analyst role in the Workday application"
   - "Aaron.Nichols needs the Finance Manager role in NetSuite"
3. View the response (VALID or INVALID)
4. On app close, see the full session trace printed

### Command Line (Testing)

```bash
# Direct Python import
python -c "
from orchestrator import handle_request
result = handle_request('I need HR Analyst in Workday')
print(result)
"
```

---

## ✅ Validation Checklist

Before running the app:

- [ ] Python 3.9+ installed
- [ ] Docker running (all 3 containers up)
- [ ] Ollama running with models pulled
- [ ] MySQL has sample data (`SELECT * FROM iamdb.Users`)
- [ ] ChromaDB has ingested data (run ingest.py)
- [ ] Toolbox is responding (`curl http://127.0.0.1:5000`)

---

## 🏗️ Architecture Components

### RAG Engine (`rag/rag_engine.py`)
- Semantic search on IAM metadata
- LLM-based validation
- Fallback to MCP if uncertain

### MCP Tools (`mcp/tools/`)
- **SQL Generator**: Creates safe SELECT queries
- **SQL Validator**: Prevents SQL injection
- **Entity Validator**: Checks Users/Apps/Roles tables

### Trace System (`mcp/trace.py`)
- `MCPTraceHandler`: Captures tool execution
- `TraceManager`: Singleton session management
- Automatic JSON export on request completion

---

## 📚 Key Files Explained

| File | Purpose |
|------|---------|
| `app.py` | Gradio UI + session lifecycle |
| `orchestrator.py` | Routes requests to RAG or MCP |
| `rag_engine.py` | Vector search + LLM validation |
| `graph.py` | MCP orchestration & pipeline |
| `extract.py` | NLU for request parameters |
| `validators.py` | Entity validation pipeline |
| `trace.py` | Consolidated tracing system |
| `config.yaml` | All service configurations |

---

## 🗑️ Cleanup

### Stop All Services

```bash
docker stop iam-mysql chromadb iam-toolbox
docker rm iam-mysql chromadb iam-toolbox
```

### Clean Trace Files

```bash
rm -f iam_trace*.json .trace_session_cache
```

---

## 📝 Notes

- Keep Docker running while using the app
- Ollama must be active before starting the application
- Trace files persist between sessions (useful for auditing)
- Use `.gitignore` to ignore trace files and cache
- Configuration is YAML-based for easy customization

---

## 🔐 Security

- All SQL queries are validated before execution
- Only SELECT statements allowed (no INSERT/UPDATE/DELETE)
- Queries restricted to specific tables (Users, Apps, Roles)
- LLM decisions can be audited via trace logs

---

## 📞 Support

For issues:
1. Check the trace output for detailed execution logs
2. Review `config.yaml` for service URLs
3. Verify all Docker containers are running
4. Check Ollama model availability

---

**Last Updated**: January 12, 2026  
**Version**: 2.0 (RAG + MCP Pipeline)
