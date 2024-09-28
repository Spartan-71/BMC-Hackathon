import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

import re

def extract_rules(text):
    pattern = r'(7\.1\.(?:\d+|1[0-9]|2[0-9]))\s+(.*?)\s*(?:\(Automated\))?\n(Profile Applicability:(.*?)\nDescription:(.*?)\nRationale:(.*?)\nAudit:(.*?)\nRemediation:(.*?)\nDefault Value:(.*?)\nReferences:(.*?)CIS Controls:(.*?)(?=7\.1\.(?:\d+|1[0-9]|2[0-9])|\Z))'

    matches = re.finditer(pattern, text, re.DOTALL)
    
    rules = []
    for match in matches:
        rule = {
            'id': match.group(1).strip(),
            'title':match.group(2).strip(),
            'profile_applicability': match.group(3).strip(),
            'description': match.group(4).strip(),
            'rationale': match.group(5).strip(),
            'audit': match.group(6).strip(),
            'remediation': match.group(7).strip(),
            'default_value': match.group(8).strip(),
            'references': match.group(9).strip(),
            'cis_controls': match.group(10).strip()
        }
        rules.append(rule)
    
    return rules

path ='system_file_permissions.pdf'
document_content = extract_text_from_pdf(path)
extracted_rules = extract_rules(document_content)


# Print the extracted rules
for rule in extracted_rules:
    print(f"Rule-> {rule['id']}")
    print(f"title-> {rule['title']}")
    # print(f"Profile Applicability-> {rule['profile_applicability']}")
    # print(f"Description-> {rule['description']}")
    # print(f"Rationale-> {rule['rationale']}")
    # print(f"Audit-> {rule['audit']}")
    # print(f"Remediation-> {rule['remediation']}")
    # print(f"Default Value-> {rule['default_value']}")
    # print(f"References-> {rule['references']}")
    # print(f"CIS Controls-> {rule['cis_controls']}")
    print("\n" + "="*50 + "\n")