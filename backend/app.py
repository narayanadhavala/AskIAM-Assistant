import gradio as gr
from orchestrator import handle_request
from core.config_loader import load_config
from mcp.trace import get_trace_handler
import atexit

cfg = load_config()

def chat(message, history):
    """Process chat message and maintain conversation history with tracing."""
    result = handle_request(message)
    
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result})
    
    # Get trace information and export
    trace_handler = get_trace_handler()
    trace_handler.export_to_file()
    
    return history, ""

def on_session_end():
    """Called when the app/session closes to print full trace."""
    trace_handler = get_trace_handler()
    print("\n")
    trace_handler.dump_full_session(console_output=True)
    print("\n✓ Session trace archived\n")

with gr.Blocks(title=cfg["ui"]["title"]) as demo:
    gr.Markdown("## IAM Access Validation Assistant")
    gr.Markdown(
        "Ask for access like:\n"
        "- I need access to the HR Analyst role in the Workday application\n"
        "- I need access to the Payroll Admin role in the Salesforce application\n"
        "- I'm Venkata.Dhavala and I need access for Azure Admin role for Azure AD"
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=500, label="Chat")
            textbox = gr.Textbox(placeholder="Type your access request...", lines=3)
            button = gr.Button("Submit", scale=1)

    # Connect chat button and textbox submit
    button.click(
        chat, 
        [textbox, chatbot], 
        [chatbot, textbox]
    )
    textbox.submit(
        chat, 
        [textbox, chatbot], 
        [chatbot, textbox]
    )

# Register session end handler
atexit.register(on_session_end)

demo.launch()
