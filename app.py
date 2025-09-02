import streamlit as st
import home
import actor
import clustring
import archive
import os
from pathlib import Path
import pandas as pd
from database import db_manager
import json

# Set page config first
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Form styling */
    .stForm {
        background-color: var(--background-color);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }
    
    /* Form elements container */
    .stForm > div {
        width: 100%;
    }
    
    /* Error message container */
    .stAlert {
        margin: 1rem 0;
        width: 100%;
    }
    
    /* Button container */
    .stForm > div:last-child {
        margin-top: 1rem;
    }
    
    /* Form submit text */
    .stForm > div:last-child > div:last-child {
        margin-top: 0.5rem;
        font-size: 0.8rem;
        color: var(--text-color);
        opacity: 0.7;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FF4B4B;
        box-shadow: 0 0 0 1px #FF4B4B;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Title styling */
    h1 {
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border-color);
        margin-bottom: 2rem;
    }
    
    /* Info message styling */
    .stAlert {
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    /* Success message styling */
    .stSuccess {
        border-radius: 10px;
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Error message styling */
    .stError {
        border-radius: 10px;
        animation: shake 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    /* Hide any element containing 'Press Enter to submit form' text */
    [data-testid="stForm"] [aria-live] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Get the directory where the script is located
SCRIPT_DIR = Path(__file__).parent
AUTH_STATE_PATH = SCRIPT_DIR / "auth_state.json"

# Function to save auth state
def save_auth_state(logged_in, username):
    auth_data = {
        'logged_in': logged_in,
        'username': username
    }
    try:
        with open(AUTH_STATE_PATH, 'w') as f:
            json.dump(auth_data, f)
        print(f"Auth state saved: {auth_data}")
    except Exception as e:
        print(f"Error saving auth state: {e}")

# Function to load auth state
def load_auth_state():
    try:
        if AUTH_STATE_PATH.exists():
            with open(AUTH_STATE_PATH, 'r') as f:
                auth_data = json.load(f)
                print(f"Auth state loaded: {auth_data}")
                return auth_data
    except Exception as e:
        print(f"Error loading auth state: {e}")
    return {'logged_in': False, 'username': ''}

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    auth_state = load_auth_state()
    st.session_state['logged_in'] = auth_state['logged_in']
    st.session_state['username'] = auth_state['username']

# Initialize login form state
if 'login_username' not in st.session_state:
    st.session_state['login_username'] = ''
if 'login_password' not in st.session_state:
    st.session_state['login_password'] = ''

if 'recommended_movies' not in st.session_state:
    st.session_state['recommended_movies'] = pd.DataFrame()
if 'selected_movie' not in st.session_state:
    st.session_state['selected_movie'] = None
if 'expanded_detail' not in st.session_state:
    st.session_state['expanded_detail'] = None
if 'selected_genre_accueil' not in st.session_state:
    st.session_state['selected_genre_accueil'] = None
if 'title_suggestions' not in st.session_state:
    st.session_state['title_suggestions'] = []
if 'actor_suggestions' not in st.session_state:
    st.session_state['actor_suggestions'] = []

# Main title
st.title("🎬 Movie Recommender")

# Authentication section
if not st.session_state['logged_in']:
    # Center the login form
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.info("✨ Welcome to Movie Recommender! Please login to continue.")
        
        # Create a form for login with better styling
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_submitted = st.form_submit_button("Login", use_container_width=True)
            with col2:
                register_submitted = st.form_submit_button("Register", use_container_width=True)
            
            if login_submitted:
                print(f"Login attempt for user: {username}")
                if username and password:
                    if db_manager.login_user(username, password):
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        save_auth_state(True, username)
                        st.success(f"Welcome back, {username}! 🎉")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                        print(f"Login failed for user: {username}")
                else:
                    st.error("❌ Please enter both username and password")
            
            if register_submitted:
                print(f"Registration attempt for user: {username}")
                if username and password:
                    if db_manager.register_user(username, password):
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        save_auth_state(True, username)
                        st.success(f"Registration successful! Welcome, {username}! 🎉")
                        st.rerun()
                    else:
                        st.error("❌ Username already taken")
                        print(f"Registration failed for user: {username}")
                else:
                    st.error("❌ Please enter both username and password")
else:
    # Navigation menu
    st.sidebar.title("🎬 Movie Recommender")
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("Logout", use_container_width=True):
        print(f"Logging out user: {st.session_state['username']}")
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        save_auth_state(False, '')
        st.rerun()

    # Main navigation
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigate to:", [
        "🎥 Home",
        "🎭 Movies by Actor",
        "📚 Archives"
    ])


    # Page routing
    if page == "🎥 Home":
        home.app()
    elif page == "🎭 Movies by Actor":
        actor.app()
    elif page == "📚 Archives":
        archive.app()