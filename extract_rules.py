import PyPDF2
import re
import json

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def preprocess_text(text):
    """Clean the extracted text."""
    # Remove bullet points, page numbers, headers, and extra whitespace
    cleaned_text = re.sub(r'^\s*[•●]\s+', '', text, flags=re.MULTILINE)
    cleaned_text = re.sub(r'\n\d+\n', '\n', cleaned_text)
    cleaned_text = re.sub(r'\nCIS [^\n]+\n', '\n', cleaned_text)  # Remove generic headers/footers
    cleaned_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', cleaned_text)  # Join hyphenated words split across lines
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Remove multiple newlines
    return cleaned_text

def extract_rules(text):
    """Extract rules from the preprocessed text."""
    preprocessed_text = preprocess_text(text)
    
    # Regex pattern for extracting rule IDs and content
    pattern = r'((\d+)\.(?:\d+\.\d+))\s+(.*?)\s*(?:\(Automated\))?\n(Profile Applicability:.*?)(?=(?:\d+\.\d+\.\d+|$))'
    
    matches = re.finditer(pattern, preprocessed_text, re.DOTALL)
    
    rules = {}
    for match in matches:
        rule_id = match.group(1).strip()   # Full rule ID like "7.1.1"
        section_id = match.group(2).strip() # Major section like "7"
        rule_text = match.group(4)

        # Define the rule
        rule = {
            'id': rule_id,
            'title': match.group(3).strip(),
            'audit': extract_section(rule_text, 'Audit:', 'Remediation:'),
            'remediation': extract_section(rule_text, 'Remediation:', 'Default Value:'),
            'audit_command': extract_audit_command(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'audit_output': extract_audit_output(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'remediation_command': extract_remediation_commands(extract_section(rule_text, 'Remediation:', 'Default Value:'))
        }

        # Group rules under the corresponding section
        if section_id not in rules:
            rules[section_id] = {
                # 'title': f"Section {section_id}",  # Placeholder, you can replace this by extracting actual section title
                'description': "",  # Placeholder for the section description
                'sub_rules': {}
            }
        
        # Add sub-rule under this section
        rules[section_id]['sub_rules'][rule_id] = rule

    return rules

def extract_section(text, start_marker, end_marker):
    """Extract a section between two markers (e.g., Audit and Remediation)."""
    start = text.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
        return text[start:].strip()
    return text[start:end].strip()

def extract_audit_command(text):
    """Extract audit commands (e.g., commands starting with # or $)."""
    commands = re.findall(r'^[#$]\s*(.+)$', text, re.MULTILINE)
    if commands:
        return '\n'.join(commands)
    return ""

def extract_audit_output(text):
    """Extract expected output from the audit section."""
    expected_output_patterns = [
        r'expected output[:\-]\s*(.*?)(?=\n|$)',  # e.g., "Expected output: X"
        r'output should show[:\-]\s*(.*?)(?=\n|$)',  # e.g., "Output should show: Y"
        r'ensure\s+that\s+(.*?)(?=\n|$)'  # e.g., "Ensure that Z is present"
    ]
    
    for pattern in expected_output_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "No specific audit output provided."

def extract_remediation_commands(text):
    """Extract remediation commands (e.g., commands like chmod, chown)."""
    commands = []
    command_patterns = [
        r'#\s*(.*?)(?=\n|$)',  # Lines starting with #
        r'\$\s*(.*?)(?=\n|$)',  # Lines starting with $
        r'`(.*?)`',  # Text enclosed in backticks
        r'^\s*(chmod|chown|find|stat).*?(?=\n|$)'  # Common Linux commands
    ]

    for pattern in command_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        commands.extend(matches)

    # Clean up commands and handle multi-line commands
    commands = [cmd.strip() for cmd in commands if cmd.strip()]
    
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

# Main script execution
if __name__ == "__main__":
    path = 'CIS.pdf'  # Replace with the correct path to your PDF
    document_content = extract_text_from_pdf(path)
    extracted_rules = extract_rules(document_content)

    # Structure the data into the required format
    rules_dict = {}
    for section_id, section_data in extracted_rules.items():
        rules_dict[section_id] = {
            # 'title': section_data['title'],
            # 'description': section_data['description'],
            'sub_rules': section_data['sub_rules']
        }

    # Define the output path for the JSON file
    json_output_path = 'extracted_rules_with_audit_output.json'

    # Save the extracted rules as a JSON file
    with open(json_output_path, 'w') as json_file:
        json.dump(rules_dict, json_file, indent=4)

    # Print the path to the saved JSON
    print(f"JSON output saved at: {json_output_path}")