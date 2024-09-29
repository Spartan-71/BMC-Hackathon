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
    # pattern=r'(7\.(?:1\.\d+|2\.\d+))\s+(.*?)\s*(?:\(Automated\))?\n(Profile Applicability:.*?)(?=(7\.(?:1\.\d+|2\.\d+)|$))'

    matches = re.finditer(pattern, preprocessed_text, re.DOTALL)
    
    rules = []
    for match in matches:
        rule_text = match.group(3)
        rule = {
            'id': match.group(1).strip(),
            'title': match.group(2).strip(),
            'audit': extract_section(rule_text, 'Audit:', 'Remediation:'),
            'remediation': extract_section(rule_text, 'Remediation:', 'Default Value:'),
            'audit_command': extract_audit_command(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'audit_output': extract_audit_output(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'remediation_command': extract_remediation_commands(extract_section(rule_text, 'Remediation:', 'Default Value:'))
        }
        rules.append(rule)
    
    return rules


def extract_section(text, start_marker, end_marker):
    start = text.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
        return text[start:].strip()
    return text[start:end].strip()

def extract_audit_command(text):
    # If no code block, look for lines starting with '#' or '$'
    commands = re.findall(r'^[#$]\s*(.+)$', text, re.MULTILINE)
    if commands:
        return '\n'.join(commands)
    return ""

def extract_audit_output(text):
    """
    Extracts the expected audit output, i.e., what is expected to ensure compliance.
    This often follows the audit command in the document and includes descriptions like "Output should be X" or
    "Ensure that Y is present in the output."
    """
    # Look for phrases indicating expected output or success criteria after audit
    expected_output_patterns = [
        r'expected output[:\-]\s*(.*?)(?=\n|$)',  # "Expected output: X" or "Expected output - X"
        r'output should show[:\-]\s*(.*?)(?=\n|$)',  # "Output should show: Y"
        r'ensure\s+that\s+(.*?)(?=\n|$)',  # "Ensure that Z is present"
    ]
    
    for pattern in expected_output_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return "No specific audit output provided."

def extract_remediation_commands(text):
    # Extract commands
    commands = []
    command_patterns = [
        r'#\s*(.*?)(?=\n|$)',  # Lines starting with #
        r'\$\s*(.*?)(?=\n|$)',  # Lines starting with $
        r'`(.*?)`',  # Text enclosed in backticks
        r'^\s*(chmod|chown|find|stat).*?(?=\n|$)',  # Common Linux commands
    ]

    for pattern in command_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        commands.extend(matches)

    # Clean up commands
    commands = [cmd.strip() for cmd in commands if cmd.strip()]
    
    # Handle multi-line commands
    final_commands = []
    current_command = ""
    for cmd in commands:
        if cmd.endswith('\\'):
            current_command += cmd[:-1] + " "
        else:
            current_command += cmd
            final_commands.append(current_command.strip())
            current_command = ""
    
    if current_command:
        final_commands.append(current_command.strip())

    return final_commands

# Main part of the script
path = 'system_file_permissions.pdf'
document_content = extract_text_from_pdf(path)
extracted_rules = extract_rules(document_content)

# Create a dictionary with Rule ID as the key and the rest of the rule as the value
rules_dict = {rule['id']: {
                'title': rule['title'],
                'audit': rule['audit'],
                'audit_command': rule['audit_command'],
                'audit_output': rule['audit_output'],
                'remediation': rule['remediation'],
                'remediation_command': rule['remediation_command']
              } 
              for rule in extracted_rules}

# Define the path to save the JSON output
json_output_path = 'extracted_rules_with_audit_output.json'

# Save the rules dictionary to a JSON file
with open(json_output_path, 'w') as json_file:
    json.dump(rules_dict, json_file, indent=4)

# Return the path of the saved file
json_output_path
