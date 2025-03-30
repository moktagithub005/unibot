import streamlit as st
import os
from dotenv import load_dotenv

# LangChain imports
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="UniSole AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        display: flex;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .chat-message.user {
        background-color: #e6f3ff;
        border-left: 5px solid #2196F3;
    }
    .chat-message.bot {
        background-color: #f0f0f0;
        border-left: 5px solid #4CAF50;
    }
    .chat-message .avatar {
        width: 50px;
    }
    .chat-message .avatar img {
        max-width: 40px;
        max-height: 40px;
        border-radius: 50%;
        object-fit: cover;
    }
    .chat-message .message {
        width: 90%;
        padding-left: 0.5rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "default_session"

if "processing_message" not in st.session_state:
    st.session_state.processing_message = False

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "unisole_info" not in st.session_state:
    st.session_state.unisole_info = ""

if "api_key_configured" not in st.session_state:
    st.session_state.api_key_configured = False

# Initialize LLM
@st.cache_resource
def load_llm():
    # Check for GROQ_API_KEY in environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        st.error("GROQ API key not found. Please set the GROQ_API_KEY environment variable or add it to your .env file.")
        st.session_state.api_key_configured = False
        return None
    
    st.session_state.api_key_configured = True
    return ChatGroq(groq_api_key=groq_api_key, model_name="llama3-8b-8192")

# Function to load UniSole info from file
def load_unisole_info():
    try:
        # Try UTF-8 encoding first
        try:
            with open("unisole.txt", "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try with a different encoding
            with open("unisole.txt", "r", encoding="latin-1") as f:
                return f.read()
    except Exception as e:
        st.error(f"Error loading UniSole info: {str(e)}")
        return "Error loading company information. Please check that unisole.txt exists in the same directory as this script."

# Display chat messages
def display_chat_history():
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.container():
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="avatar">
                        <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=user" alt="User Avatar">
                    </div>
                    <div class="message">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f"""
                <div class="chat-message bot">
                    <div class="avatar">
                        <img src="https://api.dicebear.com/7.x/bottts/svg?seed=unisole" alt="Bot Avatar">
                    </div>
                    <div class="message">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

# Function to handle the input and get response
def process_input():
    if st.session_state.user_input and not st.session_state.processing_message:
        user_input = st.session_state.user_input
        st.session_state.user_input = ""  # Clear the input
        
        # Set processing flag to prevent loops
        st.session_state.processing_message = True
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Load UniSole info if not already loaded
        if not st.session_state.unisole_info:
            st.session_state.unisole_info = load_unisole_info()
        
        # Check if API key is configured
        if not st.session_state.api_key_configured:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "I'm sorry, but I can't process your request because the API key hasn't been configured. Please set the GROQ_API_KEY environment variable."
            })
            st.session_state.processing_message = False
            return
        
        # Always include UniSole information in the system prompt
        system_content = f"""You are UniSole, a friendly and intelligent conversational AI assistant created by UniSole startup company.

You represent the UniSole brand, which is a real company focused on empowering individuals and businesses 
through AI solutions and digital transformation.

Here is information about UniSole that you should use to answer questions:
{st.session_state.unisole_info}

Be helpful, concise, and conversational. Your responses should be brief and to the point.
If someone asks about people, technologies, or topics you don't know about, it's okay to say you don't have specific information.
However, as UniSole's representative, always be professional and positive.
Always mention the website https://unisole-empower.vercel.app/ when discussing UniSole's products or services.
"""
        
        # Only keep the last 10 messages in the chat history for the LLM context
        recent_history = st.session_state.chat_history[-10:] if len(st.session_state.chat_history) > 10 else st.session_state.chat_history
        
        messages = [
            {"role": "system", "content": system_content},
        ]
        
        # Add recent conversation history
        for msg in recent_history[:-1]:  # Exclude the last user message
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            else:
                messages.append({"role": "assistant", "content": msg["content"]})
        
        # Add new user input
        messages.append({"role": "user", "content": user_input})
        
        # Get response
        try:
            llm = load_llm()
            if llm:
                response = llm.invoke(messages)
                bot_response = response.content
                
                # Check if this is a company-specific question
                about_unisole = any(keyword in user_input.lower() for keyword in 
                            ["unisole", "your company", "this company", "startup", "who are you", 
                                "what do you do", "company website", "contact", "services"])
                
                # If query is about UniSole but the response doesn't mention the website, add it
                if about_unisole and "unisole-empower.vercel.app" not in bot_response.lower():
                    bot_response += "\n\nYou can learn more about UniSole at our website: https://unisole-empower.vercel.app/"
                
                # Add bot response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
            else:
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": "I'm sorry, but I can't process your request because the API key hasn't been configured. Please set the GROQ_API_KEY environment variable."
                })
        
        except Exception as e:
            st.error(f"Error getting response: {str(e)}")
            st.session_state.chat_history.append({"role": "assistant", "content": "I'm sorry, I encountered an error. Please try again or contact UniSole support."})
        
        # Reset processing flag
        st.session_state.processing_message = False

# Main application
def main():
    st.title("🤖 UniSole AI Assistant")
    st.markdown("""
    <div style="background-color: #e6f3ff; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 1.1em;">
            Welcome to UniSole AI Assistant! I'm here to help answer your questions about UniSole and more.
            Ask me anything about our company, services, or how we can help empower your digital transformation journey.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API key
    load_llm()
    if not st.session_state.api_key_configured:
        st.warning("""
        ⚠️ API key not configured. Please set the GROQ_API_KEY environment variable in your .env file or deployment environment.
        """)
    
    # Try to load UniSole info at startup
    if not st.session_state.unisole_info:
        st.session_state.unisole_info = load_unisole_info()
        
        # Show warning if loading failed
        if "Error loading" in st.session_state.unisole_info:
            st.warning("Could not load UniSole information file. Make sure unisole.txt exists in the same directory.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("UniSole AI Assistant")
        
        # Company logo and branding
        st.image("https://api.dicebear.com/7.x/identicon/svg?seed=unisole", width=150)
        st.markdown("### Empowering through AI solutions")
        
        # Reset conversation
        if st.button("Reset Conversation"):
            st.session_state.chat_history = []
            st.session_state.conversation_id = f"session_{len(st.session_state.chat_history)}"
            st.session_state.processing_message = False
            st.success("Conversation has been reset!")
            
        # Reload company info
        if st.button("Reload Company Info"):
            st.session_state.unisole_info = load_unisole_info()
            if "Error loading" not in st.session_state.unisole_info:
                st.success("Company information reloaded successfully!")
            
        st.markdown("---")
        st.markdown("### About UniSole")
        st.markdown("""
        UniSole is an innovative startup company focused on empowering individuals and businesses through advanced AI solutions and digital transformation.
        
        This conversational AI assistant is powered by:
        - Llama3-8b from Groq
        - Streamlit interface
        
        Visit our website: [unisole-empower.vercel.app](https://unisole-empower.vercel.app/)
        
        Made with ❤️ by UniSole Team
        """)
    
    # Display chat interface
    display_chat_history()
    
    # Input for new message with callback
    st.markdown("---")
    
    # Use a form to prevent auto-rerun
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_input("Your message:", placeholder="Ask me anything about UniSole...")
        submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            st.session_state.user_input = user_input
            st.session_state.processing_message = False
    
    # Process the message after form submission
    if st.session_state.user_input and not st.session_state.processing_message:
        process_input()
        st.rerun()

if __name__ == "__main__":
    main()