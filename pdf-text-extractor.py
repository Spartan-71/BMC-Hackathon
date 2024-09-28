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
            'remediation': extract_section(rule_text, 'Remediation:', 'Default Value:'),
            'default_value': extract_section(rule_text, 'Default Value:', 'References:'),
            'references': extract_section(rule_text, 'References:', 'CIS Controls:'),
            'cis_controls': extract_section(rule_text, 'CIS Controls:', '$'),
            'audit_command':extract_audit_command(extract_section(rule_text, 'Audit:', 'Remediation:')),
            'remediation_command':extract_remediation_commands(extract_section(rule_text, 'Remediation:', 'Default Value:'))
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

# def extract_audit_command(text):

#     # Extract commands from code blocks
#     code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', text, re.DOTALL)
    
#     if code_blocks:
#         # If code blocks are found, process them
#         commands = []
#         for block in code_blocks:
#             # Split the block into lines and process each line
#             lines = block.strip().split('\n')
#             current_command = ""
#             for line in lines:
#                 line = line.strip()
#                 if line and not line.startswith('#') and not line.startswith('echo') and not line.startswith('}'):
#                     if line.endswith('\\'):
#                         current_command += line[:-1] + " "
#                     else:
#                         current_command += line
#                         if current_command:
#                             commands.append(current_command.strip())
#                             current_command = ""
#             if current_command:
#                 commands.append(current_command.strip())
#     else:
#         # If no code blocks, look for lines starting with '#', '$', or common commands
#         command_pattern = r'^(?:[#$]\s*|(?:chmod|chown|find|stat|cat|grep|awk|sed)\s+)(.+)$'
#         commands = re.findall(command_pattern, text, re.MULTILINE)

#     # Remove duplicates while preserving order
#     seen = set()
#     commands = [x for x in commands if not (x in seen or seen.add(x))]

#     return commands

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

path = 'system_file_permissions.pdf'
document_content = extract_text_from_pdf(path)
extracted_rules = extract_rules(document_content)

# Print the extracted rules
for rule in extracted_rules:
    # print(rule)
    print(f"Rule ID: {rule['id']}")
    # print(f"Title: {rule['title']}")
    # print(f"Profile Applicability: {rule['profile_applicability']}")
    # print(f"Description: {rule['description'][:100]}...")  # Print first 100 characters
    # print(f"Audit: {rule['audit']}")
    print(f"Audit command: {rule['audit_command']}")
    print(f"Remediation command: {rule['remediation_command']}")
    print("=" * 50)