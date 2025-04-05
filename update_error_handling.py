import re
import os

def update_module_file(filepath):
    print(f"Updating file: {filepath}")
    
    # Read the file
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Update the imports
    if 'from utils.error_handler import handle_api_error' not in content:
        import_pattern = r'from utils\.data_processing import .*'
        if re.search(import_pattern, content):
            content = re.sub(import_pattern, r'\g<0>\nfrom utils.error_handler import handle_api_error', content)
        else:
            import_pattern = r'import streamlit as st\nimport pandas as pd'
            if re.search(import_pattern, content):
                content = re.sub(import_pattern, r'\g<0>\nfrom utils.error_handler import handle_api_error', content)
    
    # Update error handling
    error_pattern = r'            # Call the Wolf API\s+results = self\.wolf_api\.analyze_security\(prompt, context\)\s+\s+if "error" in results:\s+st\.error\(results\["error"\]\)\s+(?:if "raw_response" in results:\s+with st\.expander\("Raw Response"\):\s+st\.code\(results\["raw_response"\]\)\s+)?return None'
    
    replacement = '            # Call the Wolf API\n            results = self.wolf_api.analyze_security(prompt, context)\n            \n            # Handle API errors\n            if handle_api_error(results):\n                return None'
    
    content = re.sub(error_pattern, replacement, content)
    
    # Write the file back
    with open(filepath, 'w') as file:
        file.write(content)

# Update all module files
module_files = [
    'modules/vulnerability_scanner.py',
    'modules/threat_intelligence.py',
    'modules/malware_analyzer.py',
    'modules/secure_coding.py',
    'modules/network_security.py'
]

for file in module_files:
    if os.path.exists(file):
        update_module_file(file)
    else:
        print(f"File does not exist: {file}")

print("Update complete!")
