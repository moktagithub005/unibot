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

if "api_key_source" not in st.session_state:
    st.session_state.api_key_source = None

if "llm" not in st.session_state:
    st.session_state.llm = None

# Initialize LLM with direct access to the API key from multiple sources
def load_llm():
    api_key = None
    source = None
    
    # Method 1: Try standard Streamlit secrets access
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
            source = "streamlit_secrets"
    except Exception:
        pass
    
    # Method 2: Try direct access to raw secrets
    if not api_key:
        try:
            # Access raw secrets dictionary
            if hasattr(st.secrets, "_secrets"):
                secrets_dict = st.secrets._secrets
                for key in secrets_dict:
                    if key == "GROQ_API_KEY":
                        api_key = secrets_dict[key]
                        source = "raw_secrets"
                        break
                    # Check if it's a nested structure
                    elif isinstance(secrets_dict[key], dict) and "GROQ_API_KEY" in secrets_dict[key]:
                        api_key = secrets_dict[key]["GROQ_API_KEY"]
                        source = f"nested_raw_secrets.{key}"
                        break
        except Exception:
            pass
    
    # Method 3: Parse the raw text to handle format issues
    if not api_key and hasattr(st.secrets, "_secrets"):
        try:
            raw_secrets = str(st.secrets._secrets)
            if "GROQ_API_KEY" in raw_secrets:
                # Extract API key using string parsing
                start_idx = raw_secrets.find("GROQ_API_KEY") + len("GROQ_API_KEY")
                start_quote_idx = raw_secrets.find('"', start_idx)
                end_quote_idx = raw_secrets.find('"', start_quote_idx + 1)
                if start_quote_idx > 0 and end_quote_idx > 0:
                    api_key = raw_secrets[start_quote_idx+1:end_quote_idx]
                    source = "string_parsing"
        except Exception:
            pass

    # Method 4: Try environment variable
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            source = "env_var"
    
    # Method 5: Hardcoded fallback - REMOVE BEFORE DEPLOYMENT
    if not api_key:
        api_key = "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"
        source = "hardcoded_fallback"
    
    if not api_key:
        st.session_state.api_key_configured = False
        st.session_state.api_key_source = None
        return None
    
    # Log where we found the API key (without showing the key itself)
    st.session_state.api_key_configured = True
    st.session_state.api_key_source = source
    
    try:
        llm = ChatGroq(
            groq_api_key=api_key, 
            model_name="llama3-8b-8192"
        )
        # Test the connection with a simple call to validate the API key
        test_response = llm.invoke([{"role": "user", "content": "Test connection"}])
        st.session_state.llm = llm
        return llm
    except Exception as e:
        st.error(f"Error initializing LLM: {str(e)}")
        st.session_state.api_key_configured = False
        st.session_state.api_key_source = None
        return None

# Hardcoded company info as fallback
FALLBACK_INFO = """
UniSole is an innovative startup company focused on empowering individuals and businesses through advanced AI solutions and digital transformation.

Our Mission:
At UniSole, we believe in democratizing access to cutting-edge technology. Our mission is to provide accessible, user-friendly AI tools that solve real-world problems and enhance productivity across various sectors.

Our Products and Services:
- AI Consulting Services
- Custom Chatbot Solutions
- Digital Transformation
- AI Training and Workshops

Visit our website: https://unisole-empower.vercel.app/
"""

# Function to load UniSole info from file
def load_unisole_info():
    # First check if we're on Streamlit Cloud
    is_cloud = os.environ.get('STREAMLIT_SHARING_MODE') is not None
    
    if is_cloud:
        # We're on Streamlit Cloud, use fallback info
        return FALLBACK_INFO
    
    # For local development, try to load from file
    try:
        # Try to find the file in multiple locations
        file_paths = ["unisole.txt", "./unisole.txt", "../unisole.txt"]
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    # Try UTF-8 encoding first
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        return content
                except UnicodeDecodeError:
                    # If UTF-8 fails, try with a different encoding
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                        return content
    except Exception:
        pass
    
    # If all else fails, return fallback info
    return FALLBACK_INFO

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
        
        # Make sure LLM is loaded
        if st.session_state.llm is None:
            llm = load_llm()
        else:
            llm = st.session_state.llm
        
        # Check if API key is configured and LLM is loaded
        if not st.session_state.api_key_configured or llm is None:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "I'm sorry, but I can't process your request because the API connection is not working. Please check the API key configuration."
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
        
        # Get response with error handling
        try:
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
        
        except Exception as e:
            error_message = f"I'm sorry, I encountered an error while processing your request. Please try again or contact UniSole support. Error details: {str(e)}"
            st.session_state.chat_history.append({"role": "assistant", "content": error_message})
            # Try to reinitialize the LLM for the next message
            st.session_state.llm = None
        
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
    
    # Try to load company info at startup
    if not st.session_state.unisole_info:
        st.session_state.unisole_info = load_unisole_info()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("UniSole AI Assistant")
        
        # Company logo and branding
        st.image("https://api.dicebear.com/7.x/identicon/svg?seed=unisole", width=150)
        st.markdown("### Empowering through AI solutions")
        
        # Initialize API connection
        if st.session_state.llm is None:
            try:
                load_llm()
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")
        
        # API Key status
        if st.session_state.api_key_configured:
            st.success(f"✅ API key configured (source: {st.session_state.api_key_source})")
        else:
            st.error("❌ API key not configured")
            st.info("Check environment variables or secrets configuration")
        
        # Reset conversation
        if st.button("Reset Conversation"):
            st.session_state.chat_history = []
            st.session_state.conversation_id = f"session_{len(st.session_state.chat_history)}"
            st.session_state.processing_message = False
            st.success("Conversation has been reset!")
            
        # Reload company info
        if st.button("Reload Company Info"):
            st.session_state.unisole_info = load_unisole_info()
            st.success("Company information reloaded!")
            
        # Reload API connection
        if st.button("Reconnect API"):
            st.session_state.llm = None
            if load_llm():
                st.success("API connection reestablished!")
            else:
                st.error("Failed to connect to API")
            
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