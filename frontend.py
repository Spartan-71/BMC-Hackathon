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

def generate_selected_rule_script(rule_id, sub_rule_id,os):
    return make_api_request("GET", f"/rules/{rule_id}/sub/{sub_rule_id}" , params={"os": os})

def generate_full_script(file, os):
    files = {"file": (file.name, file.getvalue(), file.type)}
    return make_api_request("POST", "/scripts/generate/full", files=files, params={"os": os})

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

os_options = ["Ubuntu", "Rocky", "Arch", "Windows", "macOS", "CentOS", "Fedora", "Debian"]

selected_os = st.selectbox("Select Operating System", options=os_options)
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

    # Fetch Rules Button
    if 'selected_rule_group_id' not in st.session_state:
        st.session_state.selected_rule_group_id = None

    # Fetch Rules
    rules_response = query_rules()
    if rules_response:
        rules = rules_response.get("queried_rules", [])
        if rules:
            # Selection options: Hierarchical rule group
            col1, col2 = st.columns([2,3])  # Adjust the column width for better centering
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

                    # Add "All" option to the sub-rules selection
                    sub_rules_options = ["all: All Sub-Rules"] + [
                        f"{sub_rule['id']}: {sub_rule['description']}" for sub_rule in sub_rules
                    ]

                    if sub_rules:
                        with col2:
                            selected_sub_rule = st.selectbox(
                                "Select Sub-Rule",
                                options=sub_rules_options,
                                format_func=lambda x: x.split(".", 0)[0]  # Only show the description in the dropdown
                            )
                            selected_sub_rule_id = selected_sub_rule.split(":")[0]  # Extract the ID correctly
                    else:
                        # If no sub-rules exist, only show the main rule
                        selected_sub_rule_id = st.session_state.selected_rule_group_id
                        st.info("No sub-rules available. Using main rule.")
                    # Generate Selected Rule Script button
                    if st.button("Generate Selected Rule Script", use_container_width=True):
                        # If "all" is selected, pass "all" as the sub_rule_id
                        if selected_sub_rule_id == "all":
                            script_response = generate_selected_rule_script(st.session_state.selected_rule_group_id, "all",selected_os)
                        else:   
                            # Pass the selected sub-rule ID to the backend
                            script_response = generate_selected_rule_script(st.session_state.selected_rule_group_id, selected_sub_rule_id,selected_os)
                        
                        if script_response:
                            if isinstance(script_response , dict):
                                script = script_response.get("script", "No script generated.")
                            else:
                                script = script_response
                            st.session_state.current_script = script
                            st.session_state.script_history.append((selected_sub_rule_id, script))
                            add_to_history(f"Generated script for Rule ID {selected_sub_rule_id}")
                            st.success("Script generated successfully.")
                        else:
                            st.error("Failed to generate script.")

    # Generate Full Script Button
    if st.button("Generate Full Script"):
        full_script_response = generate_full_script(uploaded_file,selected_os)
        if full_script_response:
            script = full_script_response.get("combined_script", "No script generated.")
            st.session_state.current_script = script
            add_to_history("Generated full script for {selected_os}")
            st.success("Full script generated successfully.")
        else:
            st.error("Failed to generate full script.")

    # Display the generated script
    if st.session_state.current_script:
        st.markdown("## Generated Script")
        st.text_area("Script", value=st.session_state.current_script, height=300,disabled=True, key="current_script")

        col1,col2 = st.columns(2)

        with col1:
            if st.button("Copy Script", key="copy_current"):
                pyperclip.copy(st.session_state.current_script)
                st.success("Current script copied to clipboard.")

        with col2:
            buffer = io.BytesIO()
            buffer.write(st.session_state.current_script.encode())
            buffer.seek(0)
            st.download_button(
                label="Download Script",
                data=buffer,
                file_name="generated_script_{selected_os.lower()}.sh",
                mime="text/x-sh",
                key="download_script"
            )

    if st.session_state.script_history:
      st.markdown("## Script Generation History")
      for i, (rule_id, hist_script) in enumerate(reversed(st.session_state.script_history)):
          with st.expander(f"Script for Rule ID {rule_id} (#{len(st.session_state.script_history)-i})"):
              st.text_area(f"Script {len(st.session_state.script_history)-i}", 
                          hist_script,
                          height=250,
                          disabled=True,
                          key=f"hist_script_{i}")
              
              col1, col2 = st.columns(2)

              with col1:
                  if st.button(f"Copy Script #{len(st.session_state.script_history)-i}", key=f"copy_hist_{i}"):
                      pyperclip.copy(hist_script)
                      st.success(f"Script #{len(st.session_state.script_history)-i} copied to clipboard.")

                    
              with col2:
                  buffer = io.BytesIO()
                  buffer.write(hist_script.encode())
                  buffer.seek(0)
                  st.download_button(
                      label=f"Download Script #{len(st.session_state.script_history)-i}",
                      data=buffer,
                      file_name=f"generated_script_{rule_id}.sh",
                      mime="text/x-sh",
                      key=f"download_hist_{i}"
                  )

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
    .stSelectbox {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)