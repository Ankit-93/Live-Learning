import streamlit as st
import os, uuid
import logging
from src.controller.agent_cacher import AgentManager
from dotenv import load_dotenv
import tempfile
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format="-->%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True  # Auto-login for now
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'manager' not in st.session_state:
    st.session_state.manager = AgentManager()
if 'llm_type' not in st.session_state:
    st.session_state.llm_type = "Google"
if 'tools_used' not in st.session_state:
    st.session_state.tools_used = ""
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main app styling */
    .stApp {
        background:  Linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }
    
    /* Chat container */
    .main-chat-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
    }
    
    /* Message styling */
    .message-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 18px 18px 4px 18px;
        margin: 12px 0;
        max-width: 85%;
        margin-left: auto;
        margin-right: 10px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
    }
    
    .message-user:before {
        content: '';
        position: absolute;
        right: -8px;
        top: 0;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-left-color: #667eea;
        border-top: 0;
        border-right: 0;
    }
    
    .message-assistant {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
        color: #333;
        padding: 15px 20px;
        border-radius: 18px 18px 18px 4px;
        margin: 12px 0;
        max-width: 85%;
        margin-right: auto;
        margin-left: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        position: relative;
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    .message-assistant:before {
        content: '';
        position: absolute;
        left: -8px;
        top: 0;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-right-color: #f5f7fa;
        border-top: 0;
        border-left: 0;
    }
    
    /* File upload styling */
    .uploaded-file {
        background: rgba(255, 255, 255, 0.1);
        border: 1px dashed rgba(102, 126, 234, 0.3);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid rgba(102, 126, 234, 0.2);
        padding: 12px 16px;
        font-size: 16px;
    }
    
    /* Sidebar box styling */
    .sidebar-box {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

def login_page():
    """Login page UI"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("""
            <div style='text-align: center; padding: 40px 20px;'>
                <h1 style='color: #667eea; font-size: 42px; margin-bottom: 20px;'>🧠</h1>
                <h2 style='color: #333; margin-bottom: 30px;'>AI Learning Assistant</h2>
                <p style='color: #666; margin-bottom: 40px;'>Powered by LlamaIndex Tools</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("🚀 Login to Continue", use_container_width=True)
                
                if submit:
                    expected_user = os.environ.get("GRADIO_USER", "admin")
                    expected_pass = os.environ.get("GRADIO_PASS", "admin123")
                    
                    if username == expected_user and password == expected_pass:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please try again.")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style='text-align: center; margin-top: 20px; color: rgba(255, 255, 255, 0.8);'>
                <small>Default credentials: admin / admin123</small>
            </div>
            """, unsafe_allow_html=True)

def main_app():
    """Main application UI"""
    # Main container with gradient background
    st.markdown("🧠 AI Learning Assistant")
    
    # Header with session controls
    col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
    
    with col1:
        #st.markdown(f"### 🧠 AI Learning Assistant")
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
    
    with col2:
        st.session_state.llm_type = st.selectbox(
            "🤖 LLM Model",
            ["Google", "OpenAI", "HuggingFace", "Mistral"],
            index=0,
            label_visibility="collapsed"
        )
    
    with col3:
        if st.button("🔄 New", help="Start a new chat session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.session_state.tools_used = ""
            st.session_state.full_response = ""
            st.session_state.uploaded_files = []
            st.success("✨ New session created!")
            st.rerun()
    
    with col4:
        if st.button("🚪 Logout", type="secondary", help="Logout from the application", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    st.markdown("---")
    
    # Main chat area
    col_chat, col_sidebar = st.columns([3, 1])
    
    with col_chat:
        # Chat display area
        chat_container = st.container(height=500)
        
        with chat_container:
            if st.session_state.chat_history:
                for idx, message in enumerate(st.session_state.chat_history):
                    if isinstance(message, dict):
                        role = message.get("role", "")
                        content = message.get("content", "")
                        files = message.get("files", [])
                        
                        if role == "user":
                            # User message with files
                            st.markdown(f"""
                            <div class='message-user'>
                                <div style='font-weight: 600; margin-bottom: 8px;'>👤 You</div>
                                <div>{content}</div>
                            """, unsafe_allow_html=True)
                            
                            # Display uploaded files if any
                            if files:
                                st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
                                for file_info in files:
                                    file_icon = "📄"
                                    if file_info.get('type', '').startswith('image'):
                                        file_icon = "🖼️"
                                    elif file_info.get('type', '').startswith('video'):
                                        file_icon = "🎬"
                                    elif file_info.get('type', '').startswith('audio'):
                                        file_icon = "🎵"
                                    
                                    st.markdown(f"""
                                    <div class='uploaded-file'>
                                        {file_icon} <strong>{file_info.get('name', 'File')}</strong>
                                        <small style='color: rgba(255,255,255,0.8); margin-left: auto;'>
                                            {file_info.get('size', '')}
                                        </small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        elif role == "assistant":
                            # Assistant message
                            st.markdown(f"""
                            <div class='message-assistant'>
                                <div style='font-weight: 600; margin-bottom: 8px;'>🤖 Assistant</div>
                                <div>{content}</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                # Welcome message when no chat history
                st.markdown("""
                <div style='text-align: center; padding: 60px 20px; color: #666;'>
                    <h1 style='font-size: 72px; margin-bottom: 20px;'>🧠</h1>
                    <h2 style='color: #667eea; margin-bottom: 20px;'>Welcome to AI Learning Assistant!</h2>
                    <p style='font-size: 16px; line-height: 1.6; max-width: 500px; margin: 0 auto 30px;'>
                        I'm here to help you learn and explore concepts using advanced AI tools.
                        Ask me anything about ML/DL algorithms, upload files for analysis, or request explanations!
                    </p>
                    <div style='background: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 12px; margin-top: 30px;'>
                        <h4 style='color: #667eea; margin-bottom: 10px;'>💡 Try asking:</h4>
                        <p style='margin: 5px 0;'>• "Explain neural networks"</p>
                        <p style='margin: 5px 0;'>• "What is gradient descent?"</p>
                        <p style='margin: 5px 0;'>• "Upload a PDF and summarize it"</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Input area
        st.markdown("---")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "📁 Upload files for analysis",
            type=['txt', 'pdf', 'docx', 'pptx', 'xlsx', 'csv', 'json', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="Upload documents, images, or data files for analysis"
        )
        
        # Update uploaded files in session state
        if uploaded_files:
            st.session_state.uploaded_files = []
            for file in uploaded_files:
                # Get file size in readable format
                size = file.size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                
                st.session_state.uploaded_files.append({
                    'name': file.name,
                    'type': file.type,
                    'size': size_str,
                    'data': file.getvalue()
                })
            
            # Display uploaded files
            with st.expander(f"📁 Uploaded Files ({len(st.session_state.uploaded_files)})", expanded=True):
                for file_info in st.session_state.uploaded_files:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{file_info['name']}**")
                    with col2:
                        st.markdown(f"`{file_info['size']}`")
        
        # Query input
        col_input, col_submit = st.columns([5, 1])
        
        with col_input:
            query = st.text_input(
                "💭 Your learning query",
                placeholder="Ask about ML/DL algorithms, upload files for analysis, or request explanations...",
                label_visibility="collapsed"
            )
        
        with col_submit:
            submit = st.button("🚀 Send", type="primary", use_container_width=True)
            # In your Streamlit app, update the query processing:

            if submit and query:
                try:
                    # Get agent
                    agent = st.session_state.manager.get_agent(
                        st.session_state.session_id, 
                        llm_type=st.session_state.llm_type
                    )
                    
                    # Add user message to chat
                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": query,
                        "files": st.session_state.uploaded_files if st.session_state.uploaded_files else []
                    })
                    
                    # Process query with uploaded files
                    updated_history, tools_used, response = agent.process_query(
                        query, 
                        uploaded_files=st.session_state.uploaded_files
                    )
                    
                    # Update session state
                    st.session_state.chat_history = updated_history
                    st.session_state.tools_used = tools_used
                    st.session_state.full_response = response
                    
                    # Save agent
                    st.session_state.manager.save_agent(st.session_state.session_id, agent)
                    
                    # Clear uploaded files for next query
                    st.session_state.uploaded_files = []
                    
                    # Rerun to update UI
                    st.rerun()
                    
                except Exception as e:
                    logging.error(f"Error processing query: {e}")
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": f"❌ Sorry, I encountered an error: {str(e)}"
                    })
                    st.rerun()
        
        # Additional buttons
        col_clear, col_load, col_spacer = st.columns([1, 1, 4])
        
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.tools_used = ""
                st.session_state.full_response = ""
                st.session_state.uploaded_files = []
                st.rerun()
        
        with col_load:
            if st.button("📥 Load History", use_container_width=True):
                try:
                    agent = st.session_state.manager.get_agent(
                        st.session_state.session_id, 
                        st.session_state.llm_type
                    )
                    st.session_state.chat_history = agent.chat_history
                    st.success("✅ Chat history loaded!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error loading history: {e}")
    
    with col_sidebar:
        # Sidebar tools and response
        st.markdown("<div class='sidebar-box'>", unsafe_allow_html=True)
        st.markdown("### 🛠️ Tools Used")
        
        if st.session_state.tools_used:
            tools_list = st.session_state.tools_used.split(',') if st.session_state.tools_used else []
            for tool in tools_list:
                if tool.strip():
                    st.markdown(f"• **{tool.strip()}**")
        else:
            st.info("No tools used yet")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-box'>", unsafe_allow_html=True)
        st.markdown("### 📋 Full Response")
        
        if st.session_state.full_response:
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #667eea;'>
                {st.session_state.full_response}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Waiting for response...")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Session info
        st.markdown("<div class='sidebar-box'>", unsafe_allow_html=True)
        st.markdown("### ℹ️ Session Info")
        st.markdown(f"""
        - **Model**: {st.session_state.llm_type}
        - **Messages**: {len(st.session_state.chat_history)}
        - **Files**: {len(st.session_state.uploaded_files)}
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Process query when submitted
    if submit and query:
        try:
            # Get agent
            agent = st.session_state.manager.get_agent(
                st.session_state.session_id, 
                llm_type=st.session_state.llm_type
            )
            
            # Prepare message with files
            user_message = {
                "role": "user",
                "content": query,
                "files": st.session_state.uploaded_files.copy() if st.session_state.uploaded_files else []
            }
            
            # Add user message to chat history
            st.session_state.chat_history.append(user_message)
            
            # Process query (you might want to modify this to handle files)
            # For now, we'll just pass the query text
            query_text = query
            if st.session_state.uploaded_files:
                query_text += f"\n\n[Attached {len(st.session_state.uploaded_files)} file(s)]"
            
            updated_history, tools_used, response = agent.process_query(query_text)
            
            # Update session state
            st.session_state.chat_history = updated_history
            st.session_state.tools_used = tools_used
            st.session_state.full_response = response
            
            # Save agent
            st.session_state.manager.save_agent(st.session_state.session_id, agent)
            
            # Clear uploaded files for next query
            st.session_state.uploaded_files = []
            
            # Rerun to update UI
            st.rerun()
            
        except Exception as e:
            logging.error(f"Error processing query: {e}")
            st.error(f"❌ Error: {str(e)}")
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"❌ Sorry, I encountered an error: {str(e)}"
            })
            st.rerun()

# Main app flow
if not st.session_state.logged_in:
    login_page()
else:
    main_app()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style='text-align: center; color: rgba(255, 255, 255, 0.7); padding: 20px;'>
        <small>AI Learning Assistant v1.0 | Powered by LlamaIndex Tools</small>
    </div>
    """, unsafe_allow_html=True)