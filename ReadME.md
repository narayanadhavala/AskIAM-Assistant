# AskIAM Assistant - AI-Powered IAM Access Validation

An intelligent IAM (Identity and Access Management) assistant that validates user access requests using LLM-based decision-making with RAG (Retrieval Augmented Generation) and a multi-tool validation pipeline.

---

## 📋 Project Overview

The AskIAM Assistant provides an intelligent chatbot interface for validating IAM access requests. It combines:
- **RAG Engine**: Vector search on IAM metadata using ChromaDB
- **LLM Processing**: Natural language understanding via Ollama
- **MCP Tools**: SQL generation and validation for entity verification

---

## Architecture Overview

<p align="center">
  <img src="Architecture Diagram.png" alt="IAM Access Validation Architecture" width="800"/>
</p>

---

## 📁 Directory Structure

```
AskIAM-Assistant/
├── backend/                         # Main application
│   ├── app.py                       # Gradio UI entry point
│   ├── langgraph_pipeline.py        # LangGraph orchestration
│   ├── config.yaml                  # Configuration (LLM, ChromaDB, tools)
│   ├── requirements.txt             # Python dependencies
│   ├── core/                        # Core utilities
│   │   ├── config_loader.py         # YAML config loader
│   │   ├── model_factory.py         # LLM & embeddings factory
│   │   └── types.py                 # Type definitions
│   ├── mcp/                         # Model Context Protocol tools
│   │   ├── extract.py               # Request extraction
│   │   ├── validators.py            # Entity validation
│   │   ├── state.py                 # State management
│   │   └── tools/
│   │       ├── entity_validator.py  # Generic entity validator
│   │       ├── sql_generator.py     # SQL generation tool
│   │       └── sql_validator.py     # SQL safety validator
│   └── rag/                         # RAG pipeline
│       ├── rag_engine.py            # RAG similarity search & LLM validation
│       └── vectorstore.py           # ChromaDB vector store initialization
│
├── database/                        # Database scripts
│   ├── iam_sample_data.sql          # Sample IAM data
│   └── chromaDB/                    # ChromaDB ingestion
│       ├── ingest.py                # Ingest IAM metadata to vector store
│       └── test-chroma.py           # Test ChromaDB queries
│
├── docker-compose.yml               # Docker services configuration
├── requirements.txt                 # Root-level dependencies
├── tools.yaml                       # MCP toolbox configuration
└── ReadME.md                        

```

---

## ⚙️ Prerequisites

- **OS**: Linux/macOS/Windows (Linux recommended)
- **Python**: 3.9+
- **Docker**: For PostgreSQL, ChromaDB, Toolbox
- **Ollama**: For running LLMs locally

---

## 🚀 Setup Instructions

### Step 1: Clone/Extract the Project

```bash
cd /path/to/AskIAM-Assistant
cd backend
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Start Docker Services

```bash
# Start all required services
docker-compose up -d
```

This starts:
- **PostgreSQL**: IAM database (port 5432)
- **ChromaDB**: Vector store (port 8000)
- **IAM Toolbox**: MCP server for SQL execution

### Step 4: Start Ollama

In a separate terminal:

```bash
ollama serve
```

In another terminal, pull the required models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

### Step 5: Ingest IAM Data into ChromaDB

From the backend directory:

```bash
python ../database/chromaDB/ingest.py
```

### Step 6: Verify Services

Check that all services are running:

```bash
# Check Docker containers
docker ps

# Expected: iam-postgres, chromadb, iam-toolbox containers running
```

### Step 7: Start the Application

From the backend directory:

```bash
python app.py
```

The app will launch on `http://localhost:7860`

---

## 📊 Request Processing Flow

```
User Query
    ↓
[LangGraph Pipeline] (langgraph_pipeline.py)
    ├─→ [1] Initialize Request
    ├─→ [2] Extract Entities (extract.py)
    │   └─→ Parse user, application, and role
    ├─→ [3] RAG Validation (rag_engine.py)
    │   ├─→ Vector similarity search (ChromaDB)
    │   ├─→ LLM-based decision (Ollama)
    │   └─→ Output: VALID/INVALID
    │
    ├─→ [4] Decision Gate (decide_rag_path)
    │   │
    │   ├─ If RAG = VALID ──────────────────┐
    │   │                                   │
    │   └─ If RAG ≠ VALID ──┐               │
    │                       ↓               │
    │                [5] MCP Validation     │
    │                (validators.py)        │
    │                ├─→ Generate SQL       │
    │                ├─→ Validate SQL       │
    │                ├─→ Execute via        │
    │                │   Toolbox/Database   │
    │                └─→ PASSED/FAILED      │
    │                       │               │
    │                       └───────────────┤
    │                                       │
    ├─→ [6] Finalize Response ←─────────────┤
    │   ├─→ Determine final decision
    │   └─→ Generate response message
    │
    └─→ [Response to User]
        └─→ VALID: User can access resource
            INVALID: User cannot access resource

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

---

## ✅ Validation Checklist

Before running the app:

- [ ] Python 3.9+ installed
- [ ] Docker running (all 3 containers up)
- [ ] Ollama running with models pulled
- [ ] PostgreSQL has sample data (`docker exec iam-postgres psql -U postgres -d iamdb -c "SELECT * FROM users"`)
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

---

## 📚 Key Files Explained

| File | Purpose |
|------|---------|
| `app.py` | Gradio UI entry point |
| `langgraph_pipeline.py` | LangGraph orchestration & state management |
| `rag_engine.py` | Vector search + LLM validation |
| `extract.py` | NLU for request parameter extraction |
| `validators.py` | Entity validation pipeline |
| `sql_generator.py` | Safe SQL query generation |
| `sql_validator.py` | SQL safety validation |
| `config.yaml` | All service configurations |

---

## 🗑️ Cleanup

### Stop All Services

```bash
docker stop iam-postgres chromadb iam-toolbox
docker rm iam-postgres chromadb iam-toolbox
```

---

## 📝 Notes

- Keep Docker running while using the app
- Ollama must be active before starting the application
- Configuration is YAML-based for easy customization
- All services are defined in `docker-compose.yml` for easy management

---

## 🔐 Security

- All SQL queries are validated before execution
- Only SELECT statements allowed (no INSERT/UPDATE/DELETE)
- Queries restricted to specific tables (Users, Apps, Roles)
- LLM decisions are based on validated entity data

---

## 📞 Support

For issues:
1. Review `config.yaml` for service URLs and settings
2. Verify all Docker containers are running: `docker ps`
3. Check Ollama model availability: `ollama list`
4. Verify PostgreSQL has sample data: `docker exec iam-postgres psql -U postgres -d iamdb -c "SELECT * FROM users"`
5. Check ChromaDB ingestion: `python ../database/chromaDB/ingest.py`

---

**Last Updated**: January 20, 2026  
**Version**: 3.0
