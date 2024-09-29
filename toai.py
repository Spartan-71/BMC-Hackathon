import os
from together import Together
import json

def trim_script(input_text):
    # Define the start marker for the bash script
    start_marker = '#!/bin/bash'
    # Alternative marker
    alt_marker = '#!~/bin/bash'

    # Find the start position of the bash script
    start_index = input_text.find(start_marker)
    alt_index = input_text.find(alt_marker)

    # Use the first found marker
    if start_index == -1 and alt_index == -1:
        return ''  # Return empty if neither marker is found
    
    # Select the valid start index
    start_index = start_index if start_index != -1 else alt_index

    # Find the end marker (the closing backticks)
    end_index = input_text.find('```', start_index)

    # If the markers are found, return the trimmed output
    if start_index != -1 and end_index != -1:
        return input_text[start_index:end_index].strip()
    else:
        return ''


def generate_bash_script_together(json_data):
    # Create the prompt using the provided JSON data
    prompt = (
        "You are a professions bash Script Generator. Generate a bash script that implements security rules for file permissions based on the following JSON structure"
        "Each rule should be defined as a function that checks the file permissions, displays the current settings, and attempts to remediate any issues according to the specifications in the JSON."
        "Include robust error handling for scenarios where permissions cannot be modified or files do not exist."
        "Ensure to include error handling for situations where permissions cannot be changed or files do not exist. "
        "Strictly provide only the script. No additional text or explanations before or after the script."
        "Additionally, include comments throughout the script for clarity. Here is the JSON with the rules: "
    )
#     json_data = {
#                 "6.2.4.8": {
#                 "title": "Ensure audit tools mode is configured (Automated)",
#                 "audit": "Run the following script to verify the audit tools are mode 0755  or more restrictive:  \n#!/usr/bin/env bash  \n \n{ \n   l_output=\"\" l_output2=\"\" l_perm_mask=\"0022\"  \n   l_maxperm=\"$( printf '%o' $(( 0777 & ~$l_perm_mask )) )\"  \n   a_audit_tools=(\"/sbin/auditctl\" \"/sbin/aureport\" \"/sbin/ausearch\" \n\"/sbin/autrace\" \"/sbin/auditd\" \"/sbin/augenrules\")  \n   for l_audit_tool in \"${a_audit_tools[@]}\"; do  \n      l_mode=\"$(stat -Lc '%#a'  \"$l_audit_tool\")\"  \n      if [ $(( \"$l_mode\" & \"$l_perm_mask\" )) -gt 0 ]; then  \n         l_output2=\"$l_output2 \\n - Audit tool \\\"$l_audit_tool \\\" is mode: \n\\\"$l_mode \\\" and should be mode: \\\"$l_maxperm \\\" or more restrictive\"  \n      else \n         l_output=\"$l_outp ut\\n - Audit tool \\\"$l_audit_tool \\\" is correctly \nconfigured to mode: \\\"$l_mode \\\"\" \n      fi \n   done \n   if [ -z \"$l_output2\" ]; then  \n      echo -e \"\\n- Audit Result: \\n  * PASS * \\n - * Correctly configured * \n:$l_output\"  \n   else \n      echo -e \"\\n- Audit Resu lt:\\n  * FAIL * \\n - * Reasons for audit \nfailure * :$l_output2 \\n\" \n      [ -n \"$l_output\" ] && echo -e \"\\n - * Correctly configured * \n:\\n$l_output \\n\" \n   fi \n   unset a_audit_tools  \n}",
#                 "description": "Ensure audit tools mode is configured (Automated)",
#                 "remediation": "Run the following command to remove more permissive mode from the audit tools:  \n# chmod go -w /sbin/auditctl /sbin/aureport /sbin/ausearch /sbin/autrace \n/sbin/auditd /sbin/augenrules  \nReferences:  \n1. NIST SP 800 -53 Rev. 5: AU -3 \n  \nPage 918 CIS Controls:  \nControls \nVersion  Control  IG 1 IG 2 IG 3 \nv8 3.3 Configure Data Access Control Lists  \n Configure data access control lists based on a user\u2019s need to know. Apply data \naccess control lists, also known as access permissions, to local and remote file \nsystems, databases, and applications.  \u25cf \u25cf \u25cf \nv7 14.6 Protect Information through Access Control Lists  \n Protect all information stored on systems with file system, network share, \nclaims, application, or database specific access control lists. These controls will \nenforce the principle that only authorized individuals should have access to the \ninformation base d on their need to access the information as a part of their \nresponsibilities.  \u25cf \u25cf \u25cf \n \nMITRE ATT&CK Mappings:  \nTechniques / Sub -\ntechniques  Tactics  Mitigations  \nT1070, T1070.002, T1083, \nT1083.000  TA0007  M1022  \nPage 919"
#             }
# }
    # Convert the JSON data into a string format and append to the prompt
    prompt += json.dumps(json_data, indent=2)

    # Initialize Together API client with your API key
    client = Together(api_key='fd6b17884cd99c10bef57b553e0d62c26393dd2ed92348c62f358a7dd20c73e3')

    # Create a request to generate the bash script based on the prompt
    response = client.chat.completions.create(
        model="NousResearch/Hermes-3-Llama-3.1-405B-Turbo",  # Using the specified model
        messages=[{"role": "user", "content": prompt}],  # Add the prompt in the message
        max_tokens=1200,  # Define the maximum length of the generated output
        temperature=0.7,  # Controls randomness in the output
        top_p=0.7,  # Sampling technique to generate more focused outputs
        top_k=50,  # Another sampling parameter
        repetition_penalty=1,  # Penalizes repetitive phrases
        stop=["<|eot_id|>"],  # Define stop conditions for the API call
        stream=False  # Disable streaming for a simpler return
    )

    # Return the generated bash script
    return trim_script(response.choices[0].message.content)

