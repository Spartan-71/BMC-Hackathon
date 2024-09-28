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
            'cis_controls': extract_section(rule_text, 'CIS Controls:', '$')
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

path = 'system_file_permissions.pdf'
document_content = extract_text_from_pdf(path)
extracted_rules = extract_rules(document_content)

# Print the extracted rules
for rule in extracted_rules:
    print(f"Rule ID: {rule['id']}")
    print(f"Title: {rule['title']}")
    print(f"Profile Applicability: {rule['profile_applicability']}")
    print(f"Description: {rule['description'][:100]}...")  # Print first 100 characters
    print(f"Audit: {rule['audit']}")
    print(f"remediation: {rule['remediation']}")
    print("=" * 50)