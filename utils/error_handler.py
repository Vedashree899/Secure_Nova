"""
Error handling utilities for the security platform.
"""
import streamlit as st

def handle_api_error(results):
    """
    Handle API errors consistently across the application.
    
    Args:
        results (dict): The results dictionary from the API call
        
    Returns:
        bool: True if an error was handled, False otherwise
    """
    if "error" in results:
        st.error(results["error"])
        
        # Display helpful message about API key if appropriate
        if "API key" in results["error"]:
            st.warning("""
            **API Key Issue Detected**
            
            Please ensure you have:
            1. Entered a valid Wolf API key in the sidebar
            2. Or set the WOLF_API_KEY in your environment variables
            3. Ensure the API key is valid for Wolf AI
            """)
        
        # Display quota exceeded message
        elif "quota" in results["error"].lower():
            st.warning("""
            **API Quota Exceeded**
            
            Your Wolf API key has reached its quota limit. You can:
            1. Wait for the quota to reset
            2. Use a different API key
            """)
        
        if "raw_response" in results:
            with st.expander("Technical Details"):
                st.code(results["raw_response"])
        
        return True
    
    return False