import json
import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def preprocess_text(text):
    # Remove bullet points and extra whitespace
    cleaned_text = re.sub(r'^\s*[•●]\s+', '', text, flags=re.MULTILINE)
    # Remove page numbers and headers
    cleaned_text = re.sub(r'\n\d+\n', '\n', cleaned_text)
    cleaned_text = re.sub(r'\nCIS Ubuntu Linux 22\.04 LTS Benchmark\n', '\n', cleaned_text)
    # Join hyphenated words split across lines
    cleaned_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', cleaned_text)
    # Remove multiple newlines
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
            'profile_applicability': extract_section(rule_text, 'Profile Applicability:', 'Description:'),
            'description': extract_section(rule_text, 'Description:', 'Rationale:'),
            'rationale': extract_section(rule_text, 'Rationale:', 'Audit:'),
            'audit': extract_section(rule_text, 'Audit:', 'Remediation:'),
            'remediation': extract_section(rule_text, 'Remediation:', 'References:','Default Value:'),
            'default_value': extract_section(rule_text, 'Default Value:', 'References:'),
            'references': extract_section(rule_text, 'References:', 'CIS Controls:'),
            'cis_controls': extract_section(rule_text, 'CIS Controls:', '$'),
            'audit_command':extract_audit_command(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'remediation_command':extract_remediation_commands(extract_section(rule_text, 'Remediation:', 'Default Value:'))
        }
        rules.append(rule)
    
    return rules

def extract_section(text, start_label, *end_labels):
    # Combine all possible end labels into a single pattern
    end_labels_pattern = '|'.join([re.escape(label) for label in end_labels])
    # Create a regex pattern to capture text between start and any of the end labels
    pattern = rf'{re.escape(start_label)}(.*?)(?={end_labels_pattern}|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extract_audit_command(text):
    # Patterns to detect audit commands and script blocks
    command_patterns = [
        r'^\s*#.*$',  # Lines starting with '#'
        r'^\s*\$.*$',  # Lines starting with '$'
        r'(?s)```bash(.*?)```',  # Code block in markdown format (```bash ... ```)
        r'(?s)(#!/bin/bash|#!/usr/bin/env bash)(.*?)(?=\n\S|\Z)',  # Script block starting with shebang
        r'(?s){\s*(.*?)\s*}',  # Block enclosed in curly braces
    ]

    commands = []

    # Loop through each pattern and find matches
    for pattern in command_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        commands.extend(matches)

    # Clean up extracted commands and join them together
    cleaned_commands = []
    for cmd in commands:
        if isinstance(cmd, tuple):  # Handle groups in regex
            cleaned_commands.append(''.join(cmd).strip())
        else:
            cleaned_commands.append(cmd.strip())

    # Return all matched commands, joined by newlines
    return '\n'.join(cleaned_commands) if cleaned_commands else ""


def extract_remediation_commands(text):
    # Extract commands
    commands = []
    
    # Command patterns for scripts and standalone commands
    command_patterns = [
        r'#\s*(.*?)(?=\n|$)',  # Lines starting with #
        r'\$\s*(.*?)(?=\n|$)',  # Lines starting with $
        r'`([^`]+)`',  # Text enclosed in backticks
        r'^\s*(chmod|chown|find|stat|mkdir|rm|cp|mv|ln|touch|cat)\s+.*?(?=\n|$)',  # Common Linux commands
        r'(?s)(#!/bin/bash|#!/usr/bin/env bash|{.*?})',  # Shell script blocks
        r'(?s)#.*?\n\s*{.*?}\n'  # Match inline comments    followed by script blocks
    ]

    # Find all matches for each pattern
    for pattern in command_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        commands.extend(matches)

    # Clean up extracted commands
    commands = [cmd.strip() for cmd in commands if cmd.strip()]
    
    # Handle multi-line commands (where lines end with '\')
    final_commands = []
    current_command = ""
    
    for cmd in commands:
        if cmd.endswith('\\'):
            # Continuation of a multi-line command
            current_command += cmd[:-1].strip() + " "
        else:
            # Complete command (single-line or the last part of a multi-line command)
            current_command += cmd.strip()
            final_commands.append(current_command.strip())
            current_command = ""  # Reset for next command
    
    # If there is any command left in current_command, append it
    if current_command:
        final_commands.append(current_command.strip())

    return final_commands

path = 'system_file_permissions.pdf'
document_content = extract_text_from_pdf(path)
extracted_rules = extract_rules(document_content)

# Create a dictionary with Rule ID as the key and the rest of the rule as the value
rules_dict = {rule['id']: {
                'title': rule['title'],
                'audit': rule['audit'],
                'description': rule['description'],
                # 'audit_command': rule['audit_command'],
                'remediation': rule['remediation'],
                # 'remediation_command': rule['remediation_command']
              } 
              for rule in extracted_rules}

# Define the path to save the JSON output
json_output_path = 'extracted_rules_with_audit_output.json'

# Save the rules dictionary to a JSON file
with open(json_output_path, 'w') as json_file:
    json.dump(rules_dict, json_file, indent=4)

# Return the path of the saved file
json_output_path
