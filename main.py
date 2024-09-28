from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import os

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

# Directory to store uploaded files
UPLOAD_DIRECTORY = "./uploaded_files"

# Create directory if it doesn't exist
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# In-memory storage for extracted rules
extracted_rules = []

# Mock function to extract rules from the uploaded document
def extract_rules_from_pdf(pdf_content: bytes) -> List[Dict[str, str]]:
    # Simulated rule extraction (this can be enhanced with actual PDF/XML parsing logic)
    extracted_rules = [
        {
            "id": 1, 
            "description": "Ensure permissions on /etc/passwd are configured",
            "sub_rules": [
                {"sub_id": 1.1, "description": "Ensure /etc/passwd file has 644 permissions"},
                {"sub_id": 1.2, "description": "Ensure the owner of /etc/passwd is root"}
            ]
        },
        {
            "id": 2, 
            "description": "Ensure firewall is configured",
            "sub_rules": [
                {"sub_id": 2.1, "description": "Ensure UFW is enabled"},
                {"sub_id": 2.2, "description": "Ensure only required ports are open"}
            ]
        },
        {
            "id": 3, 
            "description": "Ensure no duplicate UIDs exist",
            "sub_rules": [
                {"sub_id": 3.1, "description": "Check for duplicate UIDs in /etc/passwd"},
                {"sub_id": 3.2, "description": "Resolve duplicate UIDs by assigning unique ones"}
            ]
        },
        {
            "id": 4, 
            "description": "Ensure /etc/shadow is owned by root",
            "sub_rules": [
                {"sub_id": 4.1, "description": "Ensure the ownership of /etc/shadow is root"},
                {"sub_id": 4.2, "description": "Ensure the group ownership of /etc/shadow is root"}
            ]
        },
        {
            "id": 5, 
            "description": "Ensure that SSH root login is disabled",
            "sub_rules": [
                {"sub_id": 5.1, "description": "Check SSH configuration for PermitRootLogin no"},
                {"sub_id": 5.2, "description": "Disable root login via SSH if enabled"}
            ]
        }
    ]
    return extracted_rules

# Mock function to generate scripts for a rule
def generate_script_for_rule(rule_id: int) -> str:
    # Simulated script generation
    scripts = {
        1: "chmod 644 /etc/passwd",
        2: "ufw enable",
        3: "find /etc/passwd -duplicate-uids",
        4: "chown root:root /etc/shadow"
    }
    return scripts.get(rule_id, "# No script available for this rule.")

# API to upload file and generate full script
@app.post("/scripts/generate/full")
async def generate_full_script(file: UploadFile = File(...)):
    global extracted_rules

    # Simulate reading the file and extracting rules (PDF/XML parsing should be implemented here)
    pdf_content = await file.read()
    
    # Extract rules and store them in memory
    extracted_rules = extract_rules_from_pdf(pdf_content)

    # Generate a mock full script for all rules
    full_script = ""
    for rule in extracted_rules:
        rule_script = generate_script_for_rule(rule["id"])
        full_script += f"# Script for {rule['description']}\n{rule_script}\n\n"
    
    return {"combined_script": full_script}

# API to query extracted rules and populate the dropdown
@app.get("/rules/query")
async def query_rules():
    if not extracted_rules:
        raise HTTPException(status_code=404, detail="No rules found. Please upload a file first.")
    return {"queried_rules": extracted_rules}

# API to generate script for specific rule
@app.post("/scripts/generate/query")
async def generate_query_script(rule_ids: List[int]):
    generated_scripts = []

    # Generate a script for each rule ID provided
    for rule_id in rule_ids:
        script = generate_script_for_rule(rule_id)
        if script:
            generated_scripts.append(f"# Script for Rule ID {rule_id}\n{script}")
    
    if not generated_scripts:
        raise HTTPException(status_code=404, detail="No scripts generated for the provided rule IDs.")
    from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
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

# Directory to store uploaded files
UPLOAD_DIRECTORY = "./uploaded_files"

# Create directory if it doesn't exist
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# In-memory storage for extracted rules
extracted_rules = []

# Mock function to extract rules from the uploaded document
def extract_rules_from_pdf(pdf_content: bytes) -> List[Dict[str, str]]:
    # Simulated rule extraction (this can be enhanced with actual PDF/XML parsing logic)
    extracted_rules = [
    {
        "id": 1, 
        "description": "Ensure permissions on /etc/passwd are configured",
        "sub_rules": [
            {"sub_id": 1.1, "description": "Ensure /etc/passwd file has 644 permissions"},
            {"sub_id": 1.2, "description": "Ensure the owner of /etc/passwd is root"}
        ]
    },
    {
        "id": 2, 
        "description": "Ensure firewall is configured",
        "sub_rules": [
            {"sub_id": 2.1, "description": "Ensure UFW is enabled"},
            {"sub_id": 2.2, "description": "Ensure only required ports are open"}
        ]
    },
    {
        "id": 3, 
        "description": "Ensure no duplicate UIDs exist",
        "sub_rules": [
            {"sub_id": 3.1, "description": "Check for duplicate UIDs in /etc/passwd"},
            {"sub_id": 3.2, "description": "Resolve duplicate UIDs by assigning unique ones"}
        ]
    },
    {
        "id": 4, 
        "description": "Ensure /etc/shadow is owned by root",
        "sub_rules": [
            {"sub_id": 4.1, "description": "Ensure the ownership of /etc/shadow is root"},
            {"sub_id": 4.2, "description": "Ensure the group ownership of /etc/shadow is root"}
        ]
    },
    {
        "id": 5, 
        "description": "Ensure that SSH root login is disabled",
        "sub_rules": [
            {"sub_id": 5.1, "description": "Check SSH configuration for PermitRootLogin no"},
            {"sub_id": 5.2, "description": "Disable root login via SSH if enabled"}
        ]
    }
]
    return extracted_rules
        
    
    

# Mock function to generate scripts for a rule
def generate_script_for_rule(rule_id: int) -> str:
    # Simulated script generation
    scripts = {
        1: "chmod 644 /etc/passwd",
        2: "ufw enable",
        3: "find /etc/passwd -duplicate-uids",
        4: "chown root:root /etc/shadow"
    }
    return scripts.get(rule_id, "# No script available for this rule.")

# API to upload file and generate full script
@app.post("/scripts/generate/full")
async def generate_full_script(file: UploadFile = File(...)):
    global extracted_rules

    # Simulate reading the file and extracting rules (PDF/XML parsing should be implemented here)
    pdf_content = await file.read()
    
    # Extract rules and store them in memory
    extracted_rules = extract_rules_from_pdf(pdf_content)

    # Generate a mock full script for all rules
    full_script = ""
    for rule in extracted_rules:
        rule_script = generate_script_for_rule(rule["id"])
        full_script += f"# Script for {rule['description']}\n{rule_script}\n\n"
    
    return {"combined_script": full_script}

# API to query extracted rules and populate the dropdown
# API to query extracted rules and populate the dropdown
@app.get("/rules/query")
async def query_rules():
    if not extracted_rules:
        raise HTTPException(status_code=404, detail="No rules found. Please upload a file first.")
    
    # Return rule ID along with description
    rules_with_ids = [{"id": rule["id"], "description": f"Rule {rule['id']}: {rule['description']}"} for rule in extracted_rules]

    return {"queried_rules": rules_with_ids}

# API to generate script for specific rule
@app.post("/scripts/generate/query")
async def generate_query_script(rule_ids: List[int]):
    generated_scripts = []

    # Generate a script for each rule ID provided
    for rule_id in rule_ids:
        script = generate_script_for_rule(rule_id)
        if script:
            generated_scripts.append(f"# Script for Rule ID {rule_id}\n{script}")
    
    if not generated_scripts:
        raise HTTPException(status_code=404, detail="No scripts generated for the provided rule IDs.")
    
    return {"generated_scripts": generated_scripts}

# API to upload and save the file locally
@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)

        # Save file to the local directory
        with open(file_location, "wb") as f:
            f.write(await file.read())
        
        return {"message": f"File '{file.filename}' uploaded successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="File upload failed.")

@app.get("/rules/query")
async def query_rules():
    if not extracted_rules:
        raise HTTPException(status_code=404, detail="No rules found. Please upload a file first.")
    return {"queried_rules": extracted_rules}
    return {"generated_scripts": generated_scripts}

# API to upload and save the file locally
@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)

        # Save file to the local directory
        with open(file_location, "wb") as f:
            f.write(await file.read())
        
        return {"message": f"File '{file.filename}' uploaded successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="File upload failed.")

# API to query sub-rules by rule ID
# API to query sub-rules by rule ID
@app.get("/rules/{rule_id}/sub")
async def query_sub_rules(rule_id: int):
    global extracted_rules
    # Find the rule with the given ID
    rule = next((r for r in extracted_rules if r["id"] == rule_id), None)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    # Add "ALL" as the first sub-rule option with sub_id set to "ALL"
    sub_rules = [{"rule_id": rule_id, "sub_id": "ALL", "description": "All Sub-Rules"}] + [
        {"rule_id": rule_id, "sub_id": sub_rule["sub_id"], "description": sub_rule["description"]} 
        for sub_rule in rule.get("sub_rules", [])
    ]

    return {"sub_rules": sub_rules}



