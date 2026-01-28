from core.model_factory import create_llm
from rag.vectorstore import load_vectordb

_vectordb = None
_llm = None

def validate_with_rag(text: str, k=3, filter=None) -> str | None:
    global _vectordb, _llm

    if _vectordb is None:
        _vectordb = load_vectordb()
    if _llm is None:
        _llm = create_llm()

    # Build search filter from metadata fields
    search_filter = None
    if filter:
        # Build Chroma where filter from metadata dict
        # Filter out None values
        filter_dict = {k: v for k, v in filter.items() if v is not None}
        if filter_dict:
            # Chroma supports multiple filter formats
            # For simple AND conditions with multiple fields
            conditions = []
            for field_key, field_val in filter_dict.items():
                conditions.append({field_key: {"$eq": field_val}})
            
            if len(conditions) == 1:
                search_filter = conditions[0]
            else:
                search_filter = {"$and": conditions}

    # Perform similarity search with optional filter
    #results = _vectordb.similarity_search(text, k=k, filter=search_filter) if search_filter else _vectordb.similarity_search(text, k=k)
    search_kwargs = {"k": k, "score_threshold": 0.6}
    if search_filter:
        search_kwargs["filter"] = search_filter
    results = _vectordb.as_retriever(search_kwargs=search_kwargs).invoke(text)
    print("Similarity_score_thershold results:" ,results)

    if not results:
        fallback_kwargs = {"k": k}
        if search_filter:
            fallback_kwargs["filter"] = search_filter
        results = _vectordb.as_retriever(search_kwargs=fallback_kwargs).invoke(text)
        print("similarity results:", results, flush=True)

    # Extract context from results
    context = "\n".join(d.page_content for d in results)

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
    except Exception as e:
        return None

    if out.startswith("VALID") or out.startswith("INVALID"):
        return out

    return None
