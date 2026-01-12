from langchain_core.callbacks import BaseCallbackHandler
import json
from datetime import datetime
import os

# ==================================================
# MCPTraceHandler - Core trace functionality
# ==================================================

class MCPTraceHandler(BaseCallbackHandler):
    """Captures detailed stack traces of tool execution with inputs and outputs."""
    
    def __init__(self):
        self.step = 0
        self.stack = []
        self.session_file = None
        self.all_steps = []  # Store all steps across multiple requests

    def set_session_file(self, filename):
        """Set the session file for appending traces."""
        self.session_file = filename

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.step += 1
        tool_name = serialized.get("name", "unknown_tool")

        entry = {
            "step": self.step,
            "tool": tool_name,
            "input": input_str,
            "output": None,
        }
        self.stack.append(entry)

        print(f"\n└── Step {self.step}: {tool_name}")
        print("    ├── Input:")
        print(f"    │   {input_str}")

    def on_tool_end(self, output, **kwargs):
        self.stack[-1]["output"] = output
        print("    └── Output:")
        print("        " + str(output))

    def reset(self):
        """Reset for next request but keep session history."""
        if self.stack:
            self.all_steps.extend(self.stack)
        self.step = 0
        self.stack.clear()

    def dump(self, console_output=True):
        """Print trace to console and optionally to file."""
        trace_text = "\nFULL MCP STACK TRACE\n"
        trace_text += "=" * 50 + "\n"
        
        for s in self.stack:
            trace_text += f"Step {s['step']} - {s['tool']}\n"
            trace_text += f"Input: {s['input']}\n"
            trace_text += f"Output: {s['output']}\n"
            trace_text += "-" * 40 + "\n"
        
        if console_output:
            print(trace_text)
        
        return trace_text

    def dump_full_session(self, console_output=True):
        """Print complete accumulated trace for the entire session."""
        all_accumulated_steps = self.all_steps + self.stack
        
        trace_text = "\n" + "=" * 70 + "\n"
        trace_text += "FULL MCP STACK TRACE - SESSION SUMMARY\n"
        trace_text += "=" * 70 + "\n\n"
        
        for s in all_accumulated_steps:
            trace_text += f"Step {s['step']} - {s['tool']}\n"
            trace_text += f"Input: {s['input']}\n"
            trace_text += f"Output: {s['output']}\n"
            trace_text += "-" * 70 + "\n"
        
        trace_text += "\n" + "=" * 70 + "\n"
        trace_text += f"Total Steps: {len(all_accumulated_steps)}\n"
        trace_text += f"Session Ended: {datetime.now().isoformat()}\n"
        trace_text += "=" * 70 + "\n"
        
        if console_output:
            print(trace_text)
        
        return trace_text

    def export_to_file(self, filename=None, format="json"):
        """Export trace to JSON or TXT file (appends to session file)."""
        if filename is None:
            if self.session_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = "txt" if format == "txt" else "json"
                filename = f"iam_trace_{timestamp}.{ext}"
                self.session_file = filename
            else:
                filename = self.session_file
        
        if format == "txt":
            return self._export_to_txt(filename)
        else:
            return self._export_to_json(filename)
    
    def _export_to_json(self, filename):
        """Export trace to JSON file (append mode)."""
        all_accumulated_steps = self.all_steps + self.stack
        
        trace_data = {
            "session_timestamp": datetime.now().isoformat(),
            "total_requests": len([s for s in all_accumulated_steps if s['tool'] in ['extract_request', 'rag_similarity_search']]),
            "total_steps": len(all_accumulated_steps),
            "stack": all_accumulated_steps,
        }
        
        with open(filename, "w") as f:
            json.dump(trace_data, f, indent=2)
        
        print(f"✓ Trace appended to: {filename}")
        return filename
    
    def _export_to_txt(self, filename):
        """Export trace to detailed TXT file (append mode)."""
        all_accumulated_steps = self.all_steps + self.stack
        is_new_file = not os.path.exists(filename)
        mode = "w" if is_new_file else "a"
        
        with open(filename, mode) as f:
            if not is_new_file:
                f.write("\n" + "=" * 70 + "\n")
                f.write("NEW REQUEST\n")
                f.write("=" * 70 + "\n\n")
            else:
                f.write("=" * 70 + "\n")
                f.write("IAM ACCESS VALIDATION - DETAILED EXECUTION TRACE\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Session Started: {datetime.now().isoformat()}\n")
                f.write("\n" + "=" * 70 + "\n")
            
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total Steps in Session: {len(all_accumulated_steps)}\n")
            f.write("\n" + "-" * 70 + "\n")
            f.write("EXECUTION STACK TRACE\n")
            f.write("-" * 70 + "\n\n")
            
            for s in self.stack:
                f.write(f"Step {s['step']}: {s['tool']}\n")
                f.write("-" * 70 + "\n")
                f.write(f"Input:\n{s['input']}\n\n")
                f.write(f"Output:\n{s['output']}\n")
                f.write("\n" + "-" * 70 + "\n\n")
        
        print(f"✓ Trace {'created in' if is_new_file else 'appended to'}: {filename}")
        return filename


# ==================================================
# TraceManager - Session and file management
# ==================================================

class TraceManager:
    """Manages trace sessions, caching, and handler lifecycle."""
    
    _instance = None
    _trace_handler = None
    _session_file = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._trace_handler = MCPTraceHandler()
        self._session_file = self._get_or_create_session_filename()
        self._trace_handler.set_session_file(self._session_file)
        self._initialized = True
    
    @staticmethod
    def _get_or_create_session_filename():
        """Get cached session filename or create a new one."""
        cache_file = ".trace_session_cache"
        
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cached_filename = f.read().strip()
            
            if os.path.exists(cached_filename):
                return cached_filename
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_filename = f"iam_trace_chat_session_{timestamp}.json"
        
        with open(cache_file, "w") as f:
            f.write(session_filename)
        
        print(f"✓ New trace session created: {session_filename}")
        return session_filename
    
    def get_handler(self):
        """Get the trace handler instance."""
        return self._trace_handler
    
    def reset_session(self):
        """Reset the trace session and create a new session file."""
        if os.path.exists(self._session_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"iam_trace_chat_session_archived_{timestamp}.json"
            os.rename(self._session_file, archive_name)
            print(f"✓ Previous session archived to: {archive_name}")
        
        if os.path.exists(".trace_session_cache"):
            os.remove(".trace_session_cache")
        
        self._trace_handler = MCPTraceHandler()
        self._session_file = self._get_or_create_session_filename()
        self._trace_handler.set_session_file(self._session_file)
        print(f"✓ New session started: {self._session_file}")


# ==================================================
# Global instance and convenience functions
# ==================================================

_trace_manager = TraceManager()

def get_trace_handler():
    """Get the global trace handler instance."""
    return _trace_manager.get_handler()

def reset_session():
    """Reset the trace session and create a new session file."""
    _trace_manager.reset_session()
    