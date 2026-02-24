# AskIAM Assistant - AI-Powered IAM Access Validation

An intelligent IAM (Identity and Access Management) assistant that validates user access requests using LLM-based decision-making with RAG (Retrieval Augmented Generation), a multi-tool validation pipeline, and comprehensive observability via Langfuse distributed tracing.

---

## 📋 Project Overview

The AskIAM Assistant provides an intelligent chatbot interface for validating IAM access requests. It combines:
- **RAG Engine**: Vector search on IAM metadata using ChromaDB
- **LLM Processing**: Natural language understanding via Ollama
- **MCP Tools**: SQL generation and validation for entity verification
- **Langfuse Observability**: Distributed tracing, structured logging, and performance metrics
- **Async Background Flushing**: Non-blocking trace transmission for optimal performance

---

## Architecture Overview

<p align="center">
  <img src="Architecture Diagram.png" alt="IAM Access Validation Architecture" width="800"/>
</p>

The system captures comprehensive traces across:
- **Node Execution**: Each LangGraph node (initialize → extract → validate → decide → finalize)
- **RAG Operations**: Document retrieval latency, embedding quality, result summaries
- **MCP Tool Calls**: Entity validation, SQL generation/validation/execution
- **Entity Extraction**: LLM inference, confidence scores, context usage
- **SQL Operations**: Query generation, validation results, execution status
- **Validation Steps**: Entity existence checks, relationship validation, error handling

---

## 📁 Project Structure

```
AskIAM-Assistant/
├── backend/                    # Main application
│   ├── app.py                  # Gradio UI 
│   ├── langgraph_pipeline.py   # LangGraph orchestration
│   ├── config.yaml             # Configuration
│   ├── core/                   # Core utilities
│   │   ├── langfuse_integration.py    # Tracing & logging
│   │   ├── config_loader.py           # Config
│   │   ├── model_factory.py           # LLM & embeddings
│   │   └── types.py                   # Type definitions
│   ├── mcp/                    # Entity validation tools
│   │   ├── extract.py          # Entity extraction
│   │   ├── validators.py       # Validation logic
│   │   └── tools/
│   │       ├── entity_validator.py
│   │       ├── sql_generator.py
│   │       └── sql_validator.py
│   └── rag/                    # RAG pipeline
│       ├── rag_engine.py       # Vector search
│       └── vectorstore.py      # ChromaDB setup
│
├── database/
│   ├── iam_sample_data.sql          # Sample data
│   └── chromaDB/
│       ├── ingest.py                # Data ingestion
│       └── Dockerfile.ingest        # Auto-ingest image
│
├── docker-compose.yml          # Docker services
├── requirements.txt            # Dependencies
├── tools.yaml                  # MCP config
└── ReadME.md
```

---

## ⚙️ Prerequisites

- **Python**: 3.9+
- **Docker**: PostgreSQL, ChromaDB, Toolbox
- **Ollama**: LLMs (local)
- **Langfuse Account**: Optional (cloud observability)

---

## 🚀 Quick Start (5 minutes)

### 1. Start Docker Services
```bash
cd /path/to/AskIAM-Assistant
docker-compose up -d
```

### 2. Start Ollama (separate terminal)
```bash
ollama serve

# In another terminal:
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

### 3. Install & Run Application
```bash
cd backend
pip install -r requirements.txt
python app.py
```

Open browser: **http://localhost:7860**

---

## 📊 Request Flow

```
User Query → LangGraph Pipeline → Extract Entities → RAG Search
    ↓
  Valid? → MCP Validation (SQL check) → Final Decision
    ↓
Response (VALID/INVALID) + Async Trace to Langfuse
```

---

## 🐳 Docker & PostgreSQL Commands

### View Container Status
```bash
# Show all containers
docker-compose ps

# View specific service logs
docker-compose logs postgres          # PostgreSQL logs
docker-compose logs chromadb          # ChromaDB logs
docker-compose logs iam-toolbox       # MCP server logs
docker-compose logs -f chroma-ingest  # Watch ingest (live)
```

### PostgreSQL: Connect & Query

**Access PostgreSQL shell:**
```bash
docker-compose exec postgres psql -U postgres -d iamdb
```

**Common PostgreSQL Queries:**

```sql
-- List all tables
\dt

-- View all users
SELECT * FROM users;

-- View all applications
SELECT * FROM applications;

-- View all roles
SELECT * FROM roles;

-- Count records in each table
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as app_count FROM applications;
SELECT COUNT(*) as role_count FROM roles;

-- Find specific user
SELECT * FROM users WHERE user_name LIKE '%john%';

-- Find specific application
SELECT * FROM applications WHERE app_name = 'Salesforce';

-- Find roles for an application
SELECT * FROM roles WHERE app_name = 'Workday';

-- Exit PostgreSQL
\q
```

**Run Query Directly (without entering shell):**
```bash
# Single query
docker-compose exec postgres psql -U postgres -d iamdb -c "SELECT * FROM users LIMIT 5;"

# Multiple queries
docker-compose exec postgres psql -U postgres -d iamdb -c "
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION
SELECT 'Applications', COUNT(*) FROM applications
UNION
SELECT 'Roles', COUNT(*) FROM roles;
"

# Export to CSV
docker-compose exec postgres psql -U postgres -d iamdb -c "COPY users TO STDOUT CSV HEADER" > users.csv
```

### ChromaDB: Verify Vector Store
```bash
# Check ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# View collections
docker-compose exec chromadb curl http://localhost:8000/api/v1/collections

# Run ingest manually
docker-compose run chroma-ingest python /app/ingest.py
```

### Service Management

**Restart without losing data:**
```bash
docker-compose restart              # Restart all
docker-compose restart postgres     # Restart one service
```

**Restart and clear data:**
```bash
docker-compose down -v              # Remove volumes
docker-compose up -d                # Start fresh
```

**Check service health:**
```bash
docker-compose ps                   # Shows status (healthy/running)
docker-compose exec postgres pg_isready -U postgres
```

---

## 🔧 Configuration

Edit `backend/config.yaml` to customize:

```yaml
ollama:
  base_url: http://localhost:11434
  llm_model: llama3.1:8b
  embedding_model: nomic-embed-text

chroma:
  host: chromadb              # or "localhost" for local dev
  port: 8000
  collection: iam-metadata

database:
  host: iam-postgres          # or "localhost" for local dev
  port: 5432
  database: iamdb

toolbox:
  url: http://127.0.0.1:5000
```

### Langfuse Configuration (Optional)

Create `.env` in backend directory:
```bash
LANGFUSE_PUBLIC_KEY=pk_your_key
LANGFUSE_SECRET_KEY=sk_your_key
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

Get keys at: https://cloud.langfuse.com

---

## 📝 Using the Application

### Web UI
1. Open http://localhost:7860
2. Type request: *"I need access to HR Analyst role in Workday"*
3. View response: **VALID** or **INVALID**
4. Check Langfuse dashboard for full trace

### Sample Requests
- "I need access to HR Analyst role in Workday"
- "I need access to Payroll Admin role in Salesforce"
- "I need access to IT Admin role in AzureAD"

---

## ✅ Verification Checklist
---

## 🏗️ System Architecture

### Core Components

| Component | Purpose | Tech |
|-----------|---------|------|
| LangGraph Pipeline | Request orchestration & routing | LangGraph |
| RAG Engine | Semantic search & validation | ChromaDB + Ollama |
| MCP Tools | Database queries → SQL execution | Postgres + Toolbox |
| Langfuse Integration | Distributed tracing & observability | Langfuse |
| Gradio UI | Web interface | Gradio |

### Data Flow
```
Request → Entity Extraction (LLM)
        → RAG Vector Search (ChromaDB)
        → Decision: Valid?
        → If No: MCP Validation (SQL)
        → Trace to Langfuse (async)
        → Response
```

---

## 🔐 Security

✅ **Query Validation**: All SQL queries validated before execution  
✅ **Read-Only**: Only SELECT statements allowed  
✅ **Table Restrictions**: Limited to users, applications, roles tables  
✅ **Entity Verification**: Actions based on database records  
✅ **Credentials**: Stored in `.env` (not committed)  

---

## 📞 Common Issues & Solutions

### Issue: "PostgreSQL Connection Timeout"
```bash
# Wait for PostgreSQL to initialize
docker-compose ps postgres

# Should show: Up X seconds (healthy)
```

### Issue: "ChromaDB Data Lost"
```bash
# Data persists in volume - don't use -v flag!
docker-compose down          # ✓ Keeps data
docker-compose down -v       # ✗ Deletes data
```

### Issue: "MCP Tool Server Disconnected"
```bash
# Restart toolbox
docker-compose restart iam-toolbox

# Test connection
cd backend && python test_mcp_local.py
```

### Issue: "Ollama Not Found"
```bash
# Check models are installed
ollama list

# If missing, pull them
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

---

## 🎯 Next Steps

1. ✅ Start Docker: `docker-compose up -d`
2. ✅ Start Ollama: `ollama serve`
3. ✅ Run App: `cd backend && python app.py`
4. ✅ Open UI: http://localhost:7860
5. ✅ Test Request: "I need access to HR Analyst role in Workday"
6. ✅ View Trace: Langfuse dashboard (if configured)

---

**Last Updated**: February 24, 2026  
**Version**: 4.1  
**Status**: Production Ready
