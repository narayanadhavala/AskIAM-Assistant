"""
LangGraph pipeline for IAM Access Validation.
Integrates MCP (Model Context Protocol) and RAG (Retrieval Augmented Generation) as nodes.
"""

import asyncio
from typing_extensions import TypedDict
from typing import Optional, List
from langgraph.graph import StateGraph, START, END
from core.types import IAMState
from core.model_factory import create_llm
from core.config_loader import load_config
from core.langfuse_integration import log_event, trace_request
from mcp.extract import extract_request_unified
from mcp.validators import run_validations
from rag.rag_engine import validate_with_rag


# Initialize components
llm = create_llm()
config = load_config()


# Node 1: Initialize Request
def initialize_request(state: IAMState) -> IAMState:
    """Initialize the request and prepare for processing."""
    if "processing_steps" not in state or state["processing_steps"] is None:
        state["processing_steps"] = []
    
    state["processing_steps"].append("initialize_request")
    
    log_event(
        "node",
        node_name="initialize_request",
        input_data={"raw_request": state.get("raw_request")},
        output_data={"status": "initialized", "processing_steps": state["processing_steps"]}
    )
    
    return state


# Node 2: Extract Entities (MCP) - Parallel Execution
def extract_entities(state: IAMState) -> IAMState:
    """Extract user, application, and role using parallel asyncio execution.
    
    All three entities are extracted concurrently using asyncio.gather(),
    significantly improving performance from sequential extraction.
    Single Ollama instance handles all requests efficiently via request queuing.
    """
    state["processing_steps"].append("extract_entities")
    input_state = {
        "raw_request": state.get("raw_request"),
        "user_name": state.get("user_name"),
        "application_name": state.get("application_name"),
        "role_name": state.get("role_name")
    }
    state = asyncio.run(extract_request_unified(state))
    
    output_state = {
        "user_name": state.get("user_name"),
        "application_name": state.get("application_name"),
        "role_name": state.get("role_name"),
        "error": state.get("error")
    }
    log_event("node", node_name="extract_entities", input_data=input_state, output_data=output_state)
    
    return state


# Node 3: RAG Validation
def rag_validation(state: IAMState) -> IAMState:
    """Validate request using RAG against knowledge base."""
    state["processing_steps"].append("rag_validation")
    
    input_state = {
        "raw_request": state.get("raw_request"),
        "application_name": state.get("application_name"),
        "role_name": state.get("role_name"),
        "user_name": state.get("user_name"),
        "has_error": state.get("error") is not None
    }
    
    if state.get("error"):
        state["rag_validation"] = "SKIPPED"
        state["rag_documents"] = []
    else:
        try:
            rag_result = validate_with_rag(state["raw_request"], k=3, filter={"AppName": state.get("application_name"), "RoleName": state.get("role_name"), "UserName": state.get("user_name")})
            state["rag_validation"] = rag_result if rag_result and rag_result.startswith("VALID") else None
            state["rag_documents"] = []
        except Exception as e:
            state["rag_validation"] = f"RAG_ERROR: {str(e)}"
            state["rag_documents"] = []
    
    log_event(
        "node",
        node_name="rag_validation",
        input_data=input_state,
        output_data={"rag_validation": state.get("rag_validation"), "error": state.get("error")}
    )
    
    return state


# Node 4: MCP Validation
def mcp_validation(state: IAMState) -> IAMState:
    """Validate request using MCP validators against IAM database.
    
    Performs validations:
    1. User, Application, Role existence
    2. Role membership in Application
    """
    state["processing_steps"].append("mcp_validation")
    
    input_state = {
        "user_name": state.get("user_name"),
        "application_name": state.get("application_name"),
        "role_name": state.get("role_name"),
        "has_error": state.get("error") is not None
    }
    
    if state.get("error"):
        state["mcp_validation"] = "FAILED"
        state["mcp_errors"] = [state.get("error", "Unknown error")]
    else:
        try:
            state = run_validations(state)
            
            if state.get("error"):
                state["mcp_validation"] = "FAILED"
                state["mcp_errors"] = [state["error"]]
            else:
                state["mcp_validation"] = "PASSED"
                state["mcp_errors"] = []
        except Exception as e:
            state["mcp_validation"] = "FAILED"
            state["mcp_errors"] = [str(e)]
    
    log_event(
        "node",
        node_name="mcp_validation",
        input_data=input_state,
        output_data={"mcp_validation": state.get("mcp_validation"), "mcp_errors": state.get("mcp_errors", [])}
    )
    
    return state


# Gate/Router Node: Decide RAG path
def decide_rag_path(state: IAMState) -> str:
    """Decide whether RAG validation is conclusive or needs MCP backup.
    
    If RAG confirms VALID, skip MCP and finalize.
    Otherwise, run MCP validation as backup.
    """
    if state.get("rag_validation") and state["rag_validation"].startswith("VALID"):
        return "finalize"  # RAG confirms valid, go directly to finalize
    else:
        return "mcp_validation"  # RAG not conclusive, run MCP as backup

# Node 5: Finalize Response
def finalize_response(state: IAMState) -> IAMState:
    """Prepare final response based on validation results."""
    state["processing_steps"].append("finalize")
    
    input_state = {
        "error": state.get("error"),
        "rag_validation": state.get("rag_validation"),
        "mcp_validation": state.get("mcp_validation"),
        "user_name": state.get("user_name"),
        "role_name": state.get("role_name"),
        "application_name": state.get("application_name")
    }
    
    if state.get("error"):
        state["is_valid"] = False
        state["final_response"] = f"INVALID: {state['error']}"
    elif state.get("rag_validation") and state["rag_validation"].startswith("VALID"):
        state["is_valid"] = True
        state["final_response"] = state["rag_validation"]
    elif state.get("mcp_validation") == "PASSED":
        state["is_valid"] = True
        state["final_response"] = (
            f"VALID: {state.get('user_name', 'User')} can request "
            f"{state.get('role_name', 'role')} "
            f"in {state.get('application_name', 'application')}"
        )
    else:
        state["is_valid"] = False
        error_message = state["mcp_errors"][0] if state.get("mcp_errors") else "Validation failed"
        state["final_response"] = f"INVALID: {error_message}"
    
    log_event(
        "node",
        node_name="finalize_response",
        input_data=input_state,
        output_data={"is_valid": state.get("is_valid"), "final_response": state.get("final_response")}
    )
    
    return state


# Build the LangGraph workflow
def build_graph():
    """Construct and compile the LangGraph state machine."""
    workflow = StateGraph(IAMState)
    
    # Add nodes
    workflow.add_node("initialize_request", initialize_request)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("rag_validation", rag_validation)
    workflow.add_node("mcp_validation", mcp_validation)
    workflow.add_node("finalize", finalize_response)
    
    # Add edges (define flow)
    # Start -> Initialize
    workflow.add_edge(START, "initialize_request")
    
    # Initialize -> Extract
    workflow.add_edge("initialize_request", "extract_entities")
    
    # Extract -> RAG Validation
    workflow.add_edge("extract_entities", "rag_validation")
    
    # Conditional edge from RAG:
    # If RAG is VALID -> go to finalize (skip MCP)
    # Otherwise -> go to MCP as backup
    workflow.add_conditional_edges(
        "rag_validation",
        decide_rag_path,
        {
            "finalize": "finalize",
            "mcp_validation": "mcp_validation"
        }
    )
    
    # MCP validation -> Finalize
    workflow.add_edge("mcp_validation", "finalize")
    
    # Finalize -> End
    workflow.add_edge("finalize", END)
    
    # Compile the graph
    graph = workflow.compile()
    return graph


# Compile the pipeline
pipeline = build_graph()


def invoke_pipeline(request: str) -> str:
    """
    Invoke the LangGraph pipeline for IAM access validation.
    
    Args:
        request: The user's access request text
        
    Returns:
        The validation result as a string
    """
    initial_state: IAMState = {
        "raw_request": request,
        "user_name": None,
        "application_name": None,
        "role_name": None,
        "rag_validation": None,
        "rag_documents": [],
        "mcp_validation": None,
        "mcp_errors": [],
        "is_valid": None,
        "error": None,
        "final_response": None,
        "processing_steps": []
    }
    
    # Create a trace for this request
    with trace_request("iam_access_validation", {"request": request}) as trace:
        # Execute the pipeline
        result_state = pipeline.invoke(initial_state)
        
        # Update trace with final result
        trace.update(
            output={
                "is_valid": result_state.get("is_valid"),
                "final_response": result_state.get("final_response")
            }
        )
    
    return result_state.get("final_response", "Error: No response generated")
