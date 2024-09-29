import streamlit as st
import io
from datetime import datetime
import requests
import json
import pyperclip

# Backend API URL
API_URL = "http://localhost:8000"  # Adjust this to match your FastAPI server address

def make_api_request(method, endpoint, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def upload_file_to_backend(file):
    files = {"file": (file.name, file.getvalue(), file.type)}
    return make_api_request("POST", "/files/upload", files=files)

def query_rules():
    return make_api_request("GET", "/rules/query")

def query_sub_rules(rule_id):
    return make_api_request("GET", f"/rules/{rule_id}/sub")

def generate_selected_rule_script(rule_id, sub_rule_id):
    return make_api_request("GET", f"/rules/{rule_id}/sub/{sub_rule_id}")

def generate_full_script(file):
    files = {"file": (file.name, file.getvalue(), file.type)}
    return make_api_request("POST", "/scripts/generate/full", files=files)

def add_to_history(action):
    if 'history' not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action))

# Set page config
st.set_page_config(page_title="Script Generator", layout="wide")

# Sidebar for history
with st.sidebar:
    st.title("Search History")
    if 'history' in st.session_state:
        for time, action in reversed(st.session_state.history):
            st.text(f"{time}: {action}")
    else:
        st.text("No history yet")

# Main container
st.title("Script Generator")

# File upload and upload button
uploaded_file = st.file_uploader("Upload File", type=["txt", "csv", "pdf"])

# Initialize session state variables
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'current_script' not in st.session_state:
    st.session_state.current_script = ""
if 'script_history' not in st.session_state:
    st.session_state.script_history = []

# Upload button below the file uploader
if uploaded_file is not None:
    if st.button("Upload"):
        with st.spinner("Uploading file..."):
            upload_response = upload_file_to_backend(uploaded_file)
        if upload_response:
            st.success(f"File uploaded: {upload_response['message']}")
            add_to_history(f"Uploaded file: {uploaded_file.name}")
            st.session_state.file_uploaded = True
            st.session_state.uploaded_file = uploaded_file
        else:
            st.session_state.file_uploaded = False

# Only show the following options if the file has been successfully uploaded
if st.session_state.file_uploaded:
    st.markdown("## Script Generation Options")

    # Fetch Rules
    rules_response = query_rules()
    if rules_response:
        rules = rules_response.get("queried_rules", [])
        if rules:
            col1, col2 = st.columns([2, 3])
            with col1:
                selected_rule_group = st.selectbox(
                    "Select Rule Group",
                    options=rules,
                    format_func=lambda x: f"{x['id']}: {x['description']}",
                    key="rule_group"
                )
                st.session_state.selected_rule_group_id = selected_rule_group['id']

            if st.session_state.selected_rule_group_id:
                sub_rules_response = query_sub_rules(st.session_state.selected_rule_group_id)
                if sub_rules_response:
                    sub_rules = sub_rules_response.get("sub_rules", [])
                    with col2:
                        if sub_rules:
                            selected_sub_rule = st.selectbox(
                                "Select Sub-Rule",
                                options=sub_rules,
                                format_func=lambda x: f"{x['id']}: {x['description']}",
                                key="sub_rule"
                            )
                            selected_sub_rule_id = selected_sub_rule['id']
                        else:
                            selected_sub_rule_id = st.session_state.selected_rule_group_id
                            st.info("No sub-rules available. Using main rule.")

    # Generate Selected Rule Script button
    if st.button("Generate Selected Rule Script", key="generate_selected"):
        with st.spinner("Generating script..."):
            script_response = generate_selected_rule_script(st.session_state.selected_rule_group_id, selected_sub_rule_id)
        if script_response:
            if isinstance(script_response, dict):
                script = script_response.get('bash_script', 'No script generated.')
            else:
                script = script_response
            st.session_state.current_script = script
            st.session_state.script_history.append((selected_sub_rule_id, script))
            add_to_history(f"Generated script for Rule ID {selected_sub_rule_id}")
            st.success("Script generated successfully!")
        else:
            st.error("Failed to generate script.")

    # Generate Full Script Button
    if st.button("Generate Full Script", key="generate_full"):
        with st.spinner("Generating full script..."):
            full_script_response = generate_full_script(st.session_state.uploaded_file)
        if full_script_response:
            script = full_script_response.get("combined_script", "No script generated.")
            st.session_state.current_script = script
            add_to_history("Generated full script")
            st.success("Full script generated successfully!")
        else:
            st.error("Failed to generate full script.")

    # Display current script
    if st.session_state.current_script:
        st.markdown("### Current Script")
        st.text_area("Generated Script", st.session_state.current_script, height=300, disabled=True, key="current_script")
        
        # Create two equally sized columns for Copy and Download buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Copy Current Script", key="copy_current"):
                pyperclip.copy(st.session_state.current_script)
                st.success("Current script copied to clipboard!")
        with col2:
            buffer = io.BytesIO()
            buffer.write(st.session_state.current_script.encode())
            buffer.seek(0)
            st.download_button(
                label="Download Script",
                data=buffer,
                file_name="generated_script.sh",
                mime="text/x-sh",
                key="download_script"
            )

    # Display history
    if st.session_state.script_history:
        st.markdown("### Script History")
        for i, (rule_id, hist_script) in enumerate(reversed(st.session_state.script_history)):
            with st.expander(f"Script for Rule ID {rule_id} (#{len(st.session_state.script_history)-i})"):
                st.text_area(f"Script {len(st.session_state.script_history)-i}", 
                            hist_script,
                            height=250,
                            disabled=True,
                            key=f"hist_script_{i}")
                # Create two equally sized columns for Copy and Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Copy Script #{len(st.session_state.script_history)-i}", key=f"copy_hist_{i}"):
                        pyperclip.copy(hist_script)
                        st.success(f"Script #{len(st.session_state.script_history)-i} copied to clipboard!")
                with col2:
                    buffer = io.BytesIO()
                    buffer.write(hist_script.encode())
                    buffer.seek(0)
                    st.download_button(
                        label=f"Download Script #{len(st.session_state.script_history)-i}",
                        data=buffer,
                        file_name=f"script_{rule_id}.sh",
                        mime="text/x-sh",
                        key=f"download_hist_{i}"
                    )


# Styling
st.markdown("""
<style>
    /* Make all buttons fill their container's width */
    .stButton>button {
        width: 100%;
        height: 3em;  /* Set a fixed height for consistency */
        margin-top: 10px;
    }
    .stDownloadButton>button {
        width: 100%;
        height: 3em;  /* Set a fixed height for consistency */
        margin-top: 10px;
    }
    .stFileUploader {
        margin-bottom: 10px;
    }
    .stTextArea {   
        margin-top: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
        padding: 10px;
    }
    .stExpander {
        background-color: black;
        border: 1px solid #333;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stExpander .streamlit-expanderHeader {
        color: white;
        background-color: #222;
    }
    .stExpander .streamlit-expanderContent {
        color: white;
    }
    .stTextArea textarea {
        background-color: #333;
        color: white;
    }
</style>
""", unsafe_allow_html=True)
