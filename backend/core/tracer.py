"""
Centralized tracing module for the entire project.
Traces are disabled by default and only enabled with the --trace flag.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from functools import wraps
from pathlib import Path

# Global tracer instance
_tracer: Optional['Tracer'] = None


class Tracer:
    """
    Centralized tracer for capturing execution flow and tool invocations.
    
    Features:
    - Disabled by default
    - Can be enabled via enable() method
    - Captures tool name, input parameters, output result
    - Exports to a single human-readable .txt file
    - Minimal performance impact when disabled
    """
    
    def __init__(self, output_file: str = "trace.txt"):
        """
        Initialize the tracer.
        
        Args:
            output_file: Path to the trace output file (default: trace.txt in project root)
        """
        self.enabled = False
        self.output_file = output_file
        self.traces: list[Dict[str, Any]] = []
        self.start_time = None
        self.execution_id = None
        
    def enable(self) -> None:
        """Enable tracing."""
        self.enabled = True
        self.start_time = datetime.now()
        self.execution_id = self.start_time.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self._write_header()
        
    def disable(self) -> None:
        """Disable tracing and write final summary."""
        if self.enabled:
            self._write_footer()
        self.enabled = False
        
    def is_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self.enabled
    
    def trace_node(self, node_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> None:
        """
        Trace a pipeline node execution.
        
        Args:
            node_name: Name of the node being executed
            input_data: Input state to the node
            output_data: Output state from the node
        """
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "node",
            "node_name": node_name,
            "input": self._serialize(input_data),
            "output": self._serialize(output_data),
        }
        self.traces.append(trace)
        self._write_trace(trace)
    
    def trace_tool(self, tool_name: str, input_params: Dict[str, Any], result: Any) -> None:
        """
        Trace a tool invocation.
        
        Args:
            tool_name: Name of the tool
            input_params: Input parameters to the tool
            result: Result returned by the tool
        """
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool",
            "tool_name": tool_name,
            "input": self._serialize(input_params),
            "output": self._serialize(result),
        }
        self.traces.append(trace)
        self._write_trace(trace)
    
    def trace_function(self, function_name: str, input_params: Dict[str, Any], result: Any) -> None:
        """
        Trace a function call.
        
        Args:
            function_name: Name of the function
            input_params: Input parameters to the function
            result: Result returned by the function
        """
        if not self.enabled:
            return
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "function",
            "function_name": function_name,
            "input": self._serialize(input_params),
            "output": self._serialize(result),
        }
        self.traces.append(trace)
        self._write_trace(trace)
    
    def _serialize(self, obj: Any) -> str:
        """
        Convert an object to a JSON string for tracing.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON string representation
        """
        try:
            return json.dumps(obj, default=str, indent=2)
        except Exception:
            return str(obj)
    
    def _write_header(self) -> None:
        """Write the trace file header."""
        with open(self.output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("EXECUTION TRACE LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Execution ID: {self.execution_id}\n")
            f.write(f"Start Time: {self.start_time.isoformat()}\n")
            f.write(f"Trace Output File: {self.output_file}\n")
            f.write("=" * 80 + "\n\n")
    
    def _write_trace(self, trace: Dict[str, Any]) -> None:
        """
        Write a single trace entry to the file.
        
        Args:
            trace: Trace dictionary to write
        """
        with open(self.output_file, 'a') as f:
            f.write(f"[{trace['timestamp']}] {trace['type'].upper()}: {trace.get('node_name') or trace.get('tool_name') or trace.get('function_name')}\n")
            f.write("-" * 80 + "\n")
            
            if trace['type'] == 'tool':
                f.write(f"Tool: {trace['tool_name']}\n")
            elif trace['type'] == 'node':
                f.write(f"Node: {trace['node_name']}\n")
            elif trace['type'] == 'function':
                f.write(f"Function: {trace['function_name']}\n")
            
            f.write(f"\nInput:\n{trace['input']}\n\n")
            f.write(f"Output:\n{trace['output']}\n")
            f.write("\n" + "=" * 80 + "\n\n")
    
    def _write_footer(self) -> None:
        """Write the trace file footer with summary."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Count trace types
        tool_count = sum(1 for t in self.traces if t['type'] == 'tool')
        node_count = sum(1 for t in self.traces if t['type'] == 'node')
        function_count = sum(1 for t in self.traces if t['type'] == 'function')
        
        with open(self.output_file, 'a') as f:
            f.write("=" * 80 + "\n")
            f.write("EXECUTION SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"End Time: {end_time.isoformat()}\n")
            f.write(f"Duration: {duration:.2f} seconds\n")
            f.write(f"Total Traces: {len(self.traces)}\n")
            f.write(f"  - Nodes: {node_count}\n")
            f.write(f"  - Tools: {tool_count}\n")
            f.write(f"  - Functions: {function_count}\n")
            f.write("=" * 80 + "\n")


def get_tracer(output_file: str = "trace.txt") -> Tracer:
    """
    Get or create the global tracer instance.
    
    Args:
        output_file: Path to the trace output file
        
    Returns:
        The global Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer(output_file)
    return _tracer


def trace_tool_invocation(tool_name: str) -> Callable:
    """
    Decorator to automatically trace tool invocations.
    
    Usage:
        @trace_tool_invocation("my_tool")
        def my_tool(param1: str, param2: int) -> str:
            return result
    
    Args:
        tool_name: Name of the tool for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            
            # Combine args and kwargs for input logging
            input_params = {"args": args, "kwargs": kwargs}
            
            try:
                result = func(*args, **kwargs)
                if tracer.is_enabled():
                    tracer.trace_tool(tool_name, input_params, result)
                return result
            except Exception as e:
                if tracer.is_enabled():
                    tracer.trace_tool(tool_name, input_params, {"error": str(e)})
                raise
        
        return wrapper
    return decorator


def trace_function_call(function_name: str) -> Callable:
    """
    Decorator to automatically trace function calls.
    
    Usage:
        @trace_function_call("my_function")
        def my_function(param1: str) -> str:
            return result
    
    Args:
        function_name: Name of the function for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            
            # Combine args and kwargs for input logging
            input_params = {"args": args, "kwargs": kwargs}
            
            try:
                result = func(*args, **kwargs)
                if tracer.is_enabled():
                    tracer.trace_function(function_name, input_params, result)
                return result
            except Exception as e:
                if tracer.is_enabled():
                    tracer.trace_function(function_name, input_params, {"error": str(e)})
                raise
        
        return wrapper
    return decorator
