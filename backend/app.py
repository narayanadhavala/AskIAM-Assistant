import gradio as gr
from dotenv import load_dotenv
from langgraph_pipeline import invoke_pipeline
from core.config_loader import load_config

# Load environment variables from .env file
load_dotenv()

cfg = load_config()

def chat(message, history):
    """Process chat message using LangGraph pipeline."""
    if not message.strip():
        return history, ""
    
    # Invoke the LangGraph pipeline
    result = invoke_pipeline(message)
    
    # Update conversation history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result})
    
    return history, ""

def get_sample_requests():
    """Return sample IAM access requests."""
    return [
        "I need access to HR Analyst role in Workday",
        "I need access to Payroll Admin role in Salesforce",
        "I need access to IT Admin role in AzureAD"
    ]


# Create Gradio interface
with gr.Blocks(
    title=cfg["ui"]["title"]
) as demo:
    
    gr.Markdown("# 🔐 IAM Access Validation Assistant")
    
    with gr.Column():
        gr.Markdown("### Example Requests:")
        
        with gr.Row():
            sample_buttons = []
            for sample in get_sample_requests():
                sample_buttons.append(
                    gr.Button(sample, scale=1, variant="secondary")
                )
    
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                height=400,
                label="Chat",
                show_label=False
            )
    
    with gr.Row():
        with gr.Column(scale=4):
            textbox = gr.Textbox(
                placeholder="Type your access request...",
                lines=2,
                label="Your Request",
                show_label=True
            )
    
    with gr.Row():    
        submit_btn = gr.Button("Submit", variant="primary")
        clear_btn = gr.Button("Clear", variant="secondary")
    
    # Connect buttons
    submit_btn.click(
        chat,
        [textbox, chatbot],
        [chatbot, textbox]
    )
    
    textbox.submit(
        chat,
        [textbox, chatbot],
        [chatbot, textbox]
    )
    
    clear_btn.click(lambda: ([], ""), outputs=[chatbot, textbox])
    
    # Sample buttons interaction
    for sample in get_sample_requests():
        def create_handler(text):
            def handler():
                return text
            return handler
        
        sample_buttons[get_sample_requests().index(sample)].click(
            create_handler(sample),
            outputs=textbox
        )



def on_app_shutdown():
    """Clean up resources on app shutdown."""
    pass


# Register shutdown handler
import atexit
atexit.register(on_app_shutdown)

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft()
    )

