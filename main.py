from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from extract_rules import extract_text_from_pdf, extract_rules  # Import functions
import toai
from motor.motor_asyncio import AsyncIOMotorClient 

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

# MongoDB connection string
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")

# Initialize MongoDB client and database
client = AsyncIOMotorClient(MONGODB_URL)
db = client['my_database']  # Replace with your actual database name

@app.get("/test-mongo-connection")
async def test_mongo_connection():
    try:
        # The ping command is cheap and does not require auth.
        await client.admin.command('ping')
        return {"message": "MongoDB connection successful!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MongoDB connection string
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")

# Initialize MongoDB client and database
client = AsyncIOMotorClient(MONGODB_URL)
db = client['my_database']  # Replace with your actual database name

@app.get("/test-mongo-connection")
async def test_mongo_connection():
    try:
        # The ping command is cheap and does not require auth.
        await client.admin.command('ping')
        return {"message": "MongoDB connection successful!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# Function to generate script for specific rule or all sub-rules if "all" is selected
async def generate_script_for_rule(rule_id: str, os: str) -> str:
    global extracted_rules

    # Find the rule with the given ID
    rule = extracted_rules.get(rule_id, None)
    if not rule:
        return f"# No rule found for Rule ID {rule_id}."

    # Start building the script for the rule
    full_script = ""

    # If there are sub-rules, generate script for each and check MongoDB cache
    for sub_id in rule['sub_rules'].keys():
        sub_rule_script = await generate_subrule_script(rule_id, sub_id, os)
        full_script += f"{sub_rule_script}\n\n"  # No titles or headings, just scripts
    
    return full_script

# Function to check MongoDB for sub-rule scripts or generate them using toai
async def generate_subrule_script(rule_id: str, sub_id: str, os: str) -> str:
    collection = db['sub_rule_scripts']
    
    # Check if the script exists in MongoDB
    script_doc = await collection.find_one({'rule_id': rule_id, 'sub_id': sub_id, 'os': os})

    # If script is found, return it
    if script_doc and 'bash_script' in script_doc:
        return script_doc['bash_script']

    # Otherwise, generate the script using toai
    rule = extracted_rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    sub_rule = rule['sub_rules'].get(sub_id, None)
    if not sub_rule:
        raise HTTPException(status_code=404, detail="Sub-rule not found.")
    
    # Generate the script without additional headings or comments
    toai_output = toai.generate_bash_script_together(sub_rule, os)
    
    # Cache the generated script in MongoDB
    await collection.insert_one({'rule_id': rule_id, 'sub_id': sub_id, 'os': os, 'bash_script': toai_output})
    
    return toai_output

# API to generate script for specific rule or all sub-rules if "all" is selected
# @app.post("/scripts/generate/query")
# async def generate_query_script(rule_ids: List[str], sub_rule_ids: List[str] = None, ):
#     generated_scripts = []

#     # Generate a script for each rule ID provided
#     for rule_id in rule_ids:
#         if sub_rule_ids and "all" in sub_rule_ids:
#             # If "all" is selected, generate the full script for the entire rule
#             script = await generate_script_for_rule(rule_id, os)
#         else:
#             # Otherwise, generate for specific sub-rule(s)
#             for sub_rule_id in sub_rule_ids or ["all"]:
#                 script = await generate_script_for_rule(rule_id) if sub_rule_id == "all" else await generate_subrule_script(rule_id, sub_rule_id)
#         if script:
#             generated_scripts.append(f"{script}")
    
#     if not generated_scripts:
#         raise HTTPException(status_code=404, detail="No scripts generated for the provided rule IDs.")
    
#     return {"generated_scripts": generated_scripts}

# API to query a specific sub-rule by rule_id and sub_id, or all sub-rules if "all" is selected
@app.get("/rules/{rule_id}/sub/{sub_id}")
async def get_sub_rule_by_id(rule_id: str, sub_id: str, os: str = Query(None)):
    # If sub_id is "all", generate the full script for the rule
    if sub_id == "all":
        return await generate_script_for_rule(rule_id, os)

    # Otherwise, generate the script for the specific sub-rule
    return await generate_subrule_script(rule_id, sub_id, os)

# API to generate full script after file upload
@app.post("/scripts/generate/full")
async def generate_full_script(file: UploadFile = File(...)):
    global extracted_rules

    # Simulate reading the file and extracting rules
    pdf_content = await file.read()
    extracted_rules = extract_rules_from_pdf(pdf_content)

    # Generate a full script for all rules and their sub-rules
    full_script = ""
    for rule_id in extracted_rules.keys():
        full_script += await generate_script_for_rule(rule_id)  # Generate script for the entire rule (including sub-rules)
    
    return {"combined_script": full_script}

# # New API to query a specific sub-rule by rule_id and sub_id
# @app.get("/rules/{rule_id}/sub/{sub_id}")
# async def get_sub_rule_by_id(rule_id: str, sub_id: str):
#     global extracted_rules

#     # Retrieve the main rule using the rule_id
#     rule = extracted_rules.get(rule_id, None)
#     if not rule:
#         raise HTTPException(status_code=404, detail="Rule not found.")
#     # Retrieve the sub-rule using the sub_id
#     sub_rule = rule['sub_rules'].get(sub_id, None)
#     if not sub_rule:
#         raise HTTPException(status_code=404, detail="Sub-rule not found.")

#     # Access the MongoDB collection
#     collection = db['sub_rule_scripts']

#     # Check if the script for this sub_rule is already in the database
#     script_doc = await collection.find_one({'sub_id': sub_id})

#     if script_doc and 'bash_script' in script_doc:
#         # Return the existing bash script from the database
#         return script_doc['bash_script']
#     else:
#         # Generate the bash script
#         toai_output = toai.generate_bash_script_together(sub_rule)

#         # Store the sub_rule id and the bash script in the database
#         await collection.insert_one({'sub_id': sub_id, 'bash_script': toai_output})

#         # Return the bash script
#         return {'bash_script': toai_output}