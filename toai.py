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


def generate_bash_script_together(json_data, OS):
    # Create the prompt using the provided JSON data
    prompt = (
        "You are a professional bash Script Generator. Generate a bash script specifically for that implements security rules based on the following JSON structure."
        "Each rule should be defined as a function that checks the file permissions, displays the current settings, and attempts to remediate any issues according to the specifications in the JSON."
        "Include robust error handling for scenarios where permissions cannot be modified or files do not exist."
        "Ensure to include error handling for situations where permissions cannot be changed or files do not exist. "
        "Just the script. No additional text or explanations before or after the script STRICTLY."  
        "Additionally, include comments throughout the script for clarity. Here is the JSON with the rules: "
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
    return trim_script(response.choices[0].message.content)

