from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from extract_rules import extract_text_from_pdf, extract_rules  # Import functions
import toai

app = FastAPI()

# Allowed frontend origins
origins = [
    "http://localhost:8001",  # Add your frontend URL here
    "http://127.0.0.1:8001",  # Alternative localhost address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows access from these origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],   # Allows all headers
)

# Directory to store uploaded files and JSON output
UPLOAD_DIRECTORY = "./uploaded_files"
JSON_OUTPUT_DIRECTORY = "./json_output"

# Create directories if they don't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(JSON_OUTPUT_DIRECTORY, exist_ok=True)

# In-memory storage for extracted rules
extracted_rules = {}

# Function to extract rules from the uploaded PDF content using the imported functions
def extract_rules_from_pdf(pdf_content: bytes) -> Dict[str, Dict[str, Dict]]:
    # Save the uploaded file temporarily
    temp_pdf_path = os.path.join(UPLOAD_DIRECTORY, "temp_uploaded_file.pdf")
    with open(temp_pdf_path, "wb") as temp_file:
        temp_file.write(pdf_content)

    # Use the existing extract_text_from_pdf to extract the text content
    extracted_text = extract_text_from_pdf(temp_pdf_path)

    # Use the existing extract_rules to extract rules from the text content
    extracted_rules_list = extract_rules(extracted_text)

    # Return the extracted rules directly
    return extracted_rules_list

# Function to save extracted rules to a JSON file
def save_rules_to_json(rules: Dict, filename: str) -> str:
    json_file_path = os.path.join(JSON_OUTPUT_DIRECTORY, filename)
    
    # Save the extracted rules to a JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(rules, json_file, indent=4)
    
    return json_file_path

# API to upload file, extract rules, and save to JSON
@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    global extracted_rules

    # Read the uploaded file content
    pdf_content = await file.read()

    # Extract rules from the uploaded file
    extracted_rules = extract_rules_from_pdf(pdf_content)

    # Save the extracted rules to a JSON file
    json_filename = f"{os.path.splitext(file.filename)[0]}_extracted_rules.json"
    json_file_path = save_rules_to_json(extracted_rules, json_filename)

    # Save the uploaded file locally (optional)
    file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_location, "wb") as f:
        f.write(pdf_content)
    
    return {
        "message": f"File '{file.filename}' uploaded and rules extracted successfully!",
        "json_file": json_file_path
    }

# API to query extracted rules and populate the dropdown
@app.get("/rules/query")
async def query_rules():
    if not extracted_rules:
        raise HTTPException(status_code=404, detail="No rules found. Please upload a file first.")
    
    # Return rule ID along with description in a hierarchical format
    rules_with_ids = []
    for rule_id, rule_data in extracted_rules.items():
        sub_rules = [{"id": sub_id, "description": sub_data['title']} for sub_id, sub_data in rule_data['sub_rules'].items()]
        rules_with_ids.append({
            "id": rule_id,
            "description": f"Rule {rule_id}",
            "sub_rules": sub_rules
        })

    return {"queried_rules": rules_with_ids}

# API to query sub-rules by rule ID
@app.get("/rules/{rule_id}/sub")
async def query_sub_rules(rule_id: str):
    global extracted_rules

    # Find the rule with the given ID
    rule = extracted_rules.get(rule_id, None)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    # Return sub-rules if they exist
    sub_rules = [{"id": sub_id, "description": sub_data['title']} for sub_id, sub_data in rule['sub_rules'].items()]
    return {"sub_rules": sub_rules}

# Mock function to generate scripts for a rule
def generate_script_for_rule(rule_id: str) -> str:
    # Simulated script generation
    scripts = {
        "7.1.1": "chmod 644 /etc/passwd",
        "7.1.2": "chmod 644 /etc/passwd -",
        "7.1.3": "chmod 644 /etc/group"
    }
    return scripts.get(rule_id, "# No script available for this rule.")

# API to generate script for specific rule
@app.post("/scripts/generate/query")
async def generate_query_script(rule_ids: List[str]):
    generated_scripts = []

    # Generate a script for each rule ID provided
    for rule_id in rule_ids:
        script = generate_script_for_rule(rule_id)
        if script:
            generated_scripts.append(f"# Script for Rule ID {rule_id}\n{script}")
    
    if not generated_scripts:
        raise HTTPException(status_code=404, detail="No scripts generated for the provided rule IDs.")
    
    return {"generated_scripts": generated_scripts}

# New API to query a specific sub-rule by rule_id and sub_id
@app.get("/rules/{rule_id}/sub/{sub_id}")
async def get_sub_rule_by_id(rule_id: str, sub_id: str):
    global extracted_rules

    # Retrieve the main rule using the rule_id
    rule = extracted_rules.get(rule_id, None)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    # Retrieve the sub-rule using the sub_id
    sub_rule = rule['sub_rules'].get(sub_id, None)
    if not sub_rule:
        raise HTTPException(status_code=404, detail="Sub-rule not found.")

    toai_output = toai.generate_bash_script_together(sub_rule)

    print(toai_output)
    print(type(toai_output))
    # Return the key-value pair for the sub-rule
    return str(toai_output)

# API to generate full script after file upload
@app.post("/scripts/generate/full")
async def generate_full_script(file: UploadFile = File(...)):
    global extracted_rules

    # Simulate reading the file and extracting rules
    pdf_content = await file.read()
    extracted_rules = extract_rules_from_pdf(pdf_content)

    # Generate a full script for all rules
    full_script = ""
    for rule_id, rule_data in extracted_rules.items():
        rule_script = generate_script_for_rule(rule_id)
        full_script += f"# Script for {rule_data['title']}\n{rule_script}\n\n"
    
        # Check if sub-rules exist and generate script for them
        if 'sub_rules' in rule_data and rule_data['sub_rules']:
            for sub_id, sub_data in rule_data['sub_rules'].items():
                sub_rule_script = generate_script_for_rule(sub_id)
                full_script += f"# Script for {sub_data['title']}\n{sub_rule_script}\n\n"
    
    return {"combined_script": full_script}
