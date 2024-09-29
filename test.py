import os
from together import Together
import json

def generate_bash_script_together(json_data):
    # Create the prompt using the provided JSON data
    prompt = (
        "Generate a bash script that implements security rules for file permissions based on the following JSON structure. "
        "Each rule should be represented as a function that checks the file permissions, displays the current settings, "
        "and attempts to remediate any issues according to the specifications in the JSON. "
        "Ensure to include error handling for situations where permissions cannot be changed or files do not exist. "
        "Additionally, include comments for clarity throughout the script. Here is the JSON with the rules: "
    )
    
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
    return response.choices[0].message.content

# Example usage
json_data = {
"7.1.13": {
        "title": "Ensure SUID and SGID files are reviewed (Manual)",
        "audit": "Run the following script to generate a list of SUID and SGID files:  \n#!/usr/bin/env bash  \n \n{ \n   l_output=\"\" l_output2=\"\"  \n   a_suid=(); a_sgid=() # initialize arrays  \n   while IFS= read -r l_mount; do  \n      while  IFS= read -r -d $'\\0' l_file; do  \n         if [ -e \"$l_file\" ]; then  \n            l_mode=\"$(stat -Lc '%#a' \"$l_file\" )\" \n            [ $(( $l_mode & 04000 )) -gt 0 ] && a_suid+=(\"$l_file\")  \n            [ $(( $l_mode & 02000 )) -gt 0 ] && a_sgid+=(\"$l_file\")  \n         fi \n      done < <(find \"$l_mount\" -xdev -type f \\( -perm -2000 -o -perm -4000 \\) \n-print0 2>/dev/null)  \n   done < <(findmnt -Dkerno fstype,target,options | awk '($1 !~ \n/^\\s*(nfs|proc|smb|vfat|iso9660|efivarfs|selinuxfs)/ && $2 !~ \n/^\\/run\\/user\\// && $3 !~/noexec/ && $3 !~/nosuid/) {print $2}')  \n   if ! (( ${#a_suid[@]} > 0 )); then  \n      l_output=\"$l_output \\n - No executable SUID files exist on the system\"  \n   else \n      l_output2=\"$l_output2 \\n - List of \\\"$(printf '%s' \"${#a_suid[@]}\") \\\" \nSUID executable files: \\n$(printf '%s \\n' \"${a_suid[@]}\") \\n - end of list -\\n\" \n   fi \n   if ! (( ${#a_sgid[@]} > 0 )); then  \n      l_output=\"$l_output \\n - No SGID files exist on the system\"  \n   else \n      l_output2=\"$l_output2 \\n - List of \\\"$(printf '%s' \"${#a_sgid[@]}\") \\\" \nSGID executable files: \\n$(printf '%s \\n' \"${a_sgid[@]}\") \\n - end of list -\\n\" \n   fi \n   [ -n \"$l_output2\" ] && l_output 2=\"$l_output2 \\n- Review the preceding \nlist(s) of SUID and/or SGID files to \\n- ensure that no rogue programs have \nbeen introduced onto the system. \\n\"  \n   unset a_arr; unset a_suid; unset a_sgid # Remove arrays  \n   # If l_output2 is empty, Nothing to report  \n   if [ -z \"$l_output2\" ]; then  \n      echo -e \"\\n- Audit Result: \\n$l_output \\n\" \n   else \n      echo -e \"\\n- Audit Result: \\n$l_output2 \\n\" \n      [ -n \"$l_output\" ] && echo -e \"$l_output \\n\" \n   fi \n} \nNote:  on systems with a large number of files, this may be a long running process",
        "description": "The owner of a file can set the file's permissions to run with the owner's or group's \npermissions, even if the user running the program is not the owner or a member of the \ngroup. The most common reason for a SUID or SGID program is to enable users to \nperfo rm functions (such as changing their password) that require root privileges.",
        "remediation": "Ensure that no rogue SUID or SGID programs have been introduced into the system. \nReview the files returned by the action in the Audit section and confirm the integrity of \nthese binaries.  Page 963"
    }
} 

try:
    bash_script = generate_bash_script_together(json_data)
    print("Generated Bash Script:\n", bash_script)
except Exception as e:
    print("Error:", e)

