import os

def update_env_file():
    """
    Update the .env file with the actual WOLF_API_KEY from environment variables.
    This script is meant to be run once to set up the development environment.
    """
    # Get the API key from environment
    wolf_api_key = os.environ.get("WOLF_API_KEY")
    
    if not wolf_api_key:
        print("Error: WOLF_API_KEY environment variable not found.")
        return False
    
    # Read the current .env file
    try:
        with open(".env", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = ["# Wolf Security Platform Environment Variables\n", "# API Keys\n"]
    
    # Update or add the WOLF_API_KEY line
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("WOLF_API_KEY="):
            lines[i] = f"WOLF_API_KEY={wolf_api_key}\n"
            found = True
            break
    
    if not found:
        lines.append(f"WOLF_API_KEY={wolf_api_key}\n")
    
    # Write the updated content back to the .env file
    with open(".env", "w") as f:
        f.writelines(lines)
    
    print("Successfully updated .env file with WOLF_API_KEY.")
    return True

if __name__ == "__main__":
    update_env_file()