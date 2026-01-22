"""
Enhanced Langfuse telemetry integration for LLM observability.
Implements full tracing for IAM access validation pipeline with LangGraph support.
Based on Langfuse v3 SDK and best practices.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from core.config_loader import load_config

logger = logging.getLogger(__name__)


class TelemetryClient:
    """Enhanced telemetry client for Langfuse integration."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.cfg = load_config()
        langfuse_cfg = self.cfg.get("langfuse", {})
        
        self.enabled = langfuse_cfg.get("enabled", False)
        self.langfuse_client = None
        self.callback_handler = None
        self.debug = os.getenv("LANGFUSE_DEBUG", "false").lower() == "true"
        
        if self.enabled:
            try:
                from langfuse import Langfuse
                from langfuse.langchain import CallbackHandler
                
                # Get credentials from env vars or config
                public_key = os.getenv("LANGFUSE_PUBLIC_KEY") or langfuse_cfg.get("public_key")
                secret_key = os.getenv("LANGFUSE_SECRET_KEY") or langfuse_cfg.get("secret_key")
                base_url = os.getenv("LANGFUSE_BASE_URL") or langfuse_cfg.get("base_url", "https://cloud.langfuse.com")
                
                if not public_key or not secret_key:
                    logger.warning("Langfuse enabled but credentials missing. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
                    self.enabled = False
                else:
                    # Initialize Langfuse client (v3 SDK)
                    self.langfuse_client = Langfuse(
                        public_key=public_key,
                        secret_key=secret_key,
                        base_url=base_url,
                        debug=self.debug
                    )
                    # Get the callback handler for LangChain integration
                    self.callback_handler = CallbackHandler()
                    logger.info(f"Langfuse telemetry initialized (URL: {base_url})")
            except ImportError as e:
                logger.warning(f"Langfuse import failed: {e}. Install with: pip install langfuse")
                self.enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                self.enabled = False
        
        self._initialized = True
    
    def get_langfuse_client(self):
        """Get raw Langfuse client for manual tracing."""
        return self.langfuse_client if self.enabled else None
    
    def get_callback_handler(self):
        """Get LangChain callback handler for LLM tracing."""
        return self.callback_handler if self.enabled else None
    
    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self.enabled
    
    @contextmanager
    def trace(self, name: str, input: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for creating traces with automatic cleanup.
        
        Usage:
            with telemetry.trace("process_request", input={"user_id": "123"}) as span:
                # Do work
                span.update(output={"status": "success"})
        """
        if not self.enabled or not self.langfuse_client:
            yield DummySpan()
            return
        
        try:
            # Langfuse v3 SDK uses trace() method directly
            trace = self.langfuse_client.trace(
                name=name,
                input=input,
                metadata=metadata or {},
            )
            yield trace
            trace.end()
        except Exception as e:
            logger.error(f"Error creating trace '{name}': {e}")
            yield DummySpan()
    
    def create_span(self, name: str, parent_trace_id: Optional[str] = None, 
                   input: Optional[Dict[str, Any]] = None) -> "Span":
        """Create a span within a trace."""
        if not self.enabled or not self.langfuse_client:
            return DummySpan()
        
        try:
            return self.langfuse_client.span(
                name=name,
                trace_id=parent_trace_id,
                input=input,
            )
        except Exception as e:
            logger.error(f"Error creating span '{name}': {e}")
            return DummySpan()
    
    def flush(self):
        """Flush any pending events to Langfuse."""
        if self.enabled and self.langfuse_client:
            try:
                self.langfuse_client.flush()
                logger.debug("Langfuse events flushed")
            except Exception as e:
                logger.warning(f"Error flushing Langfuse events: {e}")


class DummySpan:
    """Dummy span for when telemetry is disabled."""
    
    def update(self, **kwargs):
        return self
    
    def end(self):
        return self
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


def get_telemetry_client() -> TelemetryClient:
    """Get singleton telemetry client."""
    return TelemetryClient()


def get_langchain_callbacks() -> dict:
    """Get callbacks dict for LangChain invocations."""
    client = get_telemetry_client()
    handler = client.get_callback_handler()
    
    if handler:
        return {"callbacks": [handler]}
    return {}
