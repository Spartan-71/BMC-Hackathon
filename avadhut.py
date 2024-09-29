import PyPDF2
import re
import json

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def preprocess_text(text):
    cleaned_text = re.sub(r'^\s*[•●]\s+', '', text, flags=re.MULTILINE)
    cleaned_text = re.sub(r'\n\d+\n', '\n', cleaned_text)
    cleaned_text = re.sub(r'\nCIS Ubuntu Linux 22\.04 LTS Benchmark\n', '\n', cleaned_text)
    cleaned_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', cleaned_text)
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
    return cleaned_text

def extract_rules(text):
    preprocessed_text = preprocess_text(text)
    
    pattern = r'(7\.1\.(?:\d+))\s+(.*?)\s*(?:\(Automated\))?\n(Profile Applicability:.*?)(?=(7\.1\.(?:\d+)|$))'
    
    matches = re.finditer(pattern, preprocessed_text, re.DOTALL)
    
    rules = []
    for match in matches:
        rule_text = match.group(3)
        rule = {
            'id': match.group(1).strip(),
            'title': match.group(2).strip(),
            'audit': extract_section(rule_text, 'Audit:', 'Remediation:'),
            'remediation': extract_section(rule_text, 'Remediation:', 'References:','Default Value:'),
            'audit_command': extract_audit_command(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'remediation_command': extract_remediation_commands(extract_section(rule_text, 'Remediation:', 'Default Value:'))
        }
        rules.append(rule)
    
    return rules

def extract_section(text, start_label, *end_labels):
    end_labels_pattern = '|'.join([re.escape(label) for label in end_labels])
    pattern = rf'{re.escape(start_label)}(.*?)(?={end_labels_pattern}|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_audit_command(text):
    command_patterns = [
        r'^\s*#.*$', 
        r'^\s*\$.*$',  
        r'(?s)```bash(.*?)```',  
        r'(?s)(#!/bin/bash|#!/usr/bin/env bash)(.*?)(?=\n\S|\Z)',  
        r'(?s){\s*(.*?)\s*}',  
    ]

    commands = []

    for pattern in command_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        commands.extend(matches)

    cleaned_commands = []
    for cmd in commands:
        if isinstance(cmd, tuple):  
            cleaned_commands.append(''.join(cmd).strip())
        else:
            cleaned_commands.append(cmd.strip())

    return '\n'.join(cleaned_commands) if cleaned_commands else ""

def extract_remediation_commands(text):
    commands = []
    
    command_patterns = [
        r'#\s*(.*?)(?=\n|$)',  
        r'\$\s*(.*?)(?=\n|$)',  
        r'`([^`]+)`',  
        r'^\s*(chmod|chown|find|stat|mkdir|rm|cp|mv|ln|touch|cat)\s+.*?(?=\n|$)',  
        r'(?s)(#!/bin/bash|#!/usr/bin/env bash|{.*?})',  
        r'(?s)#.*?\n\s*{.*?}\n'  
    ]

    for pattern in command_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        commands.extend(matches)

    commands = [cmd.strip() for cmd in commands if cmd.strip()]
    
    final_commands = []
    current_command = ""
    
    for cmd in commands:
        if cmd.endswith('\\'):
            current_command += cmd[:-1].strip() + " "
        else:
            current_command += cmd.strip()
            final_commands.append(current_command.strip())
            current_command = ""
    
    if current_command:
        final_commands.append(current_command.strip())

    return final_commands

# Main script
path = 'system_file_permissions.pdf'
document_content = extract_text_from_pdf(path)
extracted_rules = extract_rules(document_content)

# Convert to JSON format
rules_json = {rule['id']: rule for rule in extracted_rules}

# Save to JSON file
with open('extracted_rules.json', 'w') as json_file:
    json.dump(rules_json, json_file, indent=4)

# Print the extracted rules
for rule in extracted_rules:
    print(f"Rule ID: {rule['id']}")
    print(f"Title: {rule['title']}")
    print(f"Audit: {rule['audit']}")
    print(f"Remediation: {rule['remediation']}")
    print(f"Audit command: {rule['audit_command']}")
    print(f"Remediation command: {rule['remediation_command']}")
    print("=" * 50)
