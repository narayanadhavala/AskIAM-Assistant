from core.model_factory import create_llm
from rag.vectorstore import load_vectordb
from mcp.trace import get_trace_handler

_vectordb = None
_llm = None

def validate_with_rag(text: str, k=1) -> str | None:
    global _vectordb, _llm
    trace_handler = get_trace_handler()

    if _vectordb is None:
        _vectordb = load_vectordb()
    if _llm is None:
        _llm = create_llm()

    # Log RAG search start
    trace_handler.on_tool_start(
        {"name": "rag_similarity_search"},
        {"query": text, "k": k}
    )
    
    results = _vectordb.similarity_search(text, k=k)
    
    if not results:
        trace_handler.on_tool_end("No results found")
        return None

    # Log retrieved documents
    retrieved_docs = [
        {
            "content": d.page_content,
            "metadata": d.metadata if hasattr(d, 'metadata') else {}
        }
        for d in results
    ]
    
    context = "\n".join(d.page_content for d in results)
    
    trace_handler.on_tool_end(f"Retrieved {len(results)} document(s): {retrieved_docs}")

    # Log LLM validation
    trace_handler.on_tool_start(
        {"name": "rag_llm_validation"},
        {"query": text, "context_length": len(context)}
    )
    
    prompt = f"""
You are an IAM access validation assistant.

User request:
"{text}"

IAM metadata:
{context}

Rules:
- Respond ONLY with VALID: <reason> or INVALID: <reason>
- One sentence only
- No extra text
"""

    try:
        out = _llm.invoke(prompt).content.strip()
        trace_handler.on_tool_end({"response": out})
    except Exception as e:
        trace_handler.on_tool_end(f"Error: {str(e)}")
        return None

    if out.startswith("VALID") or out.startswith("INVALID"):
        return out

    return None
