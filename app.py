import re, uuid
import json, logging
import gradio as gr
from typing import List, Dict

from data.css import custom_css
from src.controller.agent_cacher import AgentManager
# Configure logging
logging.basicConfig(level=logging.INFO, format="-->%(asctime)s [%(levelname)s] %(message)s")




def create_gradio_interface():
    gr.HTML('<link href="https://fonts.googleapis.com/css2?family=Fira+Code&family=Roboto&display=swap" rel="stylesheet">')
    gr.HTML(custom_css)
    manager = AgentManager()
    
    with gr.Blocks(title="AI Learning Assistant") as demo:
        gr.Markdown("# 🧠 Learn with LlamaIndex Tools")
        logging.info("Starting Learning Application")

        with gr.Row():
            session_id = gr.Textbox(label="Session ID", value=str(uuid.uuid4()), visible=True)
            llm_selector = gr.Dropdown(
                label="LLM Type",
                choices=["Google", "OpenAI", "HuggingFace", "Mistral"],
                value="Google",
                interactive=True
            )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Learning Dialog",
                    height=500,
                    type="messages"
                )
                query_input = gr.Textbox(label="Your Learning Query", placeholder="Ask about ML/DL algorithms...")
                submit_btn = gr.Button("Submit")

            with gr.Column(scale=1):
                gr.Markdown("### Tools Preview")
                tool_output = gr.Textbox(label="Selected Tools", interactive=False)
                response_output = gr.Textbox(label="Full Response", interactive=False, lines=10)

        def process_query(session_id_val, query, chat_history, llm_val):
            print("Session:", session_id)
            print("Query:", query)
            #print("Chat History:", chat_history)
            print("Option selected:", llm_val)
            agent = manager.get_agent(session_id_val, llm_type=llm_val)
            chat_history, tools_used, response = agent.process_query(query)
            manager.save_agent(session_id_val, agent)
            return chat_history, tools_used, response, ""

        submit_btn.click(
            process_query,
            inputs=[session_id, query_input, chatbot, llm_selector],  # ✅ 4 inputs
            outputs=[chatbot, tool_output, response_output, query_input]
        )

        def load_history(session_id_val, llm_val):
            agent = manager.get_agent(session_id_val, llm_val)
            return agent.chat_history

        session_id.change(
            load_history,
            inputs=[session_id, llm_selector],  # ✅ Pass component objects, not .value
            outputs=chatbot
        )

    return demo
if __name__ == "__main__":
    interface = create_gradio_interface()
    interface.launch()