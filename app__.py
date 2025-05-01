# --- Gradio App ---
import uuid
import gradio as gr
from src.controller.agent import ChatBot


chatbot = ChatBot()
session_store = {}
session = ""

def build_request(user_input):
    return {
        "query": user_input,
        "metadata": {
            "user_id": "123",
            "timestamp": "2025-04-20T12:00:00"
        }
    }

def chat(session_id, user_input, history):
    if session_id not in session_store:
        session_store[session_id] = []

    if user_input.strip():
        request = build_request(user_input)
        agent = chatbot.agent_cacher.get_agent_for(session_id, request)
        reply = agent.agentic_chat(user_input)

        session_store[session_id].append(("You", user_input))
        session_store[session_id].append(("Agent", reply))

    updated_history = [(sender, message) for sender, message in session_store[session_id]]
    return reply, ""

with gr.Blocks() as demo:
    gr.Markdown("# 🧠 Chat with LlamaIndex Agent")

    with gr.Row():
        if not session:
            session = uuid.uuid4()
        session_id = gr.Textbox(label="Session ID", value=session)

    with gr.Row():
        chatbot_ui = gr.Chatbot(label="Chat History", height=400)

    with gr.Row():
        user_input = gr.Textbox(label="Your Query", placeholder="Enter your query here...")

    with gr.Row():
        send_btn = gr.Button("Send")

    send_btn.click(
        chat,
        inputs=[session_id, user_input, chatbot_ui],
        outputs=[chatbot_ui, user_input],
    )

if __name__ == "__main__":
    demo.launch()