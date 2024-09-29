import streamlit as st
import io
from datetime import datetime
import requests
import json

# Backend API URL
API_URL = "http://localhost:8000"  # Adjust this to match your FastAPI server address

def make_api_request(method, endpoint, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{endpoint}", **kwargs)
        response.raise_for_status()  # Raises an HTTPError for bad responses
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

# Check if 'file_uploaded' is in session_state, if not set to False initially
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False

# Upload button below the file uploader
if uploaded_file is not None:
    if st.button("Upload"):
        upload_response = upload_file_to_backend(uploaded_file)
        if upload_response:
            st.success(f"File uploaded: {upload_response['message']}")
            add_to_history(f"Uploaded file: {uploaded_file.name}")
            # Set the flag to True when file is successfully uploaded
            st.session_state.file_uploaded = True
        else:
            st.session_state.file_uploaded = False  # Reset if upload failed

# Only show the following options if the file has been successfully uploaded
if st.session_state.file_uploaded:
    st.markdown("## Options")

    # Fetch Rules Button
    if 'selected_rule_group_id' not in st.session_state:
        st.session_state.selected_rule_group_id = None

    rules_response = query_rules()
    if rules_response:
        rules = rules_response.get("queried_rules", [])
        if rules:
            # Selection options: Hierarchical rule group
            col1, col2 = st.columns([3, 2])  # Adjust the column width for better centering
            with col1:
                selected_rule_group = st.selectbox(
                    "Select Rule Group",
                    options=[f"{rule['id']}: {rule['description']}" for rule in rules],
                    format_func=lambda x: x.split(": ", 1)[1]
                )
                selected_rule_group_id = selected_rule_group.split(":")[0]

                # Store selected rule group ID in session state
                st.session_state.selected_rule_group_id = selected_rule_group_id

            # Check if a rule group is selected, then query for sub-rules
            if st.session_state.selected_rule_group_id:
                sub_rules_response = query_sub_rules(st.session_state.selected_rule_group_id)
                if sub_rules_response:
                    sub_rules = sub_rules_response.get("sub_rules", [])

                    if sub_rules:
                        with col2:
                            selected_sub_rule = st.selectbox(
                                "Select Sub-Rule",
                                options=[f"{st.session_state.selected_rule_group_id}.{sub_rule['id']} : {sub_rule['description']}" for sub_rule in sub_rules],
                                format_func=lambda x: x.split(".", 1)[1]
                            )
                            selected_sub_rule_id = selected_sub_rule.split(":")[0]
                    else:
                        # If no sub-rules exist, only show the main rule
                        selected_sub_rule_id = st.session_state.selected_rule_group_id

                    # Generate Selected Rule Script button
                    # Generate Selected Rule Script button
                    if st.button("Generate Selected Rule Script", use_container_width=True):
                        selected_rule_ids = selected_sub_rule_id[2:-1]  # Wrap the selected sub-rule ID in a list
                        script_response = generate_selected_rule_script(st.session_state.selected_rule_group_id, selected_rule_ids)  # Call the updated function
                        if script_response:
                          # Print the raw response directly for preview in Streamlit
                          st.text_area("Raw API Response", script_response, height=600, key="raw_response_area")
                          
                          # Optionally add to history
                          add_to_history(f"Displayed raw response for Rule ID {selected_sub_rule_id}")


                        

    # Generate Full Script Button
    if st.button("Generate Full Script"):
        full_script_response = generate_full_script(uploaded_file)
        if full_script_response:
            script = full_script_response.get("combined_script", "No script generated.")
            st.text_area("Generated Full Script", script, height=200)
            add_to_history("Generated full script")
            st.session_state.current_script = script

    # Download button (shown only if a script has been generated)
    if 'current_script' in st.session_state:
        if st.button("Download Script"):
            script = st.session_state.get('current_script', "No script generated yet.")
            buffer = io.BytesIO()
            buffer.write(script.encode())
            buffer.seek(0)
            st.download_button(
                label="Click to Download",
                data=buffer,
                file_name="generated_script.sh",
                mime="text/x-sh"
            )
            add_to_history("Downloaded script")

# Styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        margin-top: 10px;  /* Add space between buttons */
    }
    .stFileUploader {
        margin-bottom: 10px;  /* Add margin below file uploader */
    }
    .stTextArea {
        margin-top: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
        padding: 10px;  /* Add padding for better appearance */
    }
</style>
""", unsafe_allow_html=True)
