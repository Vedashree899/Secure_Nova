import os
import google.generativeai as genai
import streamlit as st
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class WolfAPI:
    """
    Wolf API wrapper class for AI-powered security analysis.
    """
    
    def __init__(self, api_key=None):
        """Initialize the Wolf API with the provided key."""
        # Try to get API key from environment or provided key
        env_api_key = os.getenv("WOLF_API_KEY", "")
        self.api_key = api_key or env_api_key
        
        # Log API key status (without revealing the key)
        self.api_key_source = 'environment' if env_api_key else 'user input' if api_key else None
        
        self.model = None
        self.initialized = False
        
        if self.api_key:
            self._initialize_api()
    
    def _initialize_api(self):
        """Initialize the Wolf API with the provided key."""
        try:
            # Configure Wolf API with the provided key
            genai.configure(api_key=self.api_key)
            
            # Clear any previous models from session state
            if 'current_model' in st.session_state:
                del st.session_state.current_model
            
            # Get available models and convert names to Wolf AI format
            available_models = [model.name.replace('gemini', 'wolf') for model in genai.list_models()]
            
            # Filter out non-text models
            available_models = [
                model for model in available_models 
                if not any(x in model.lower() for x in ['vision', 'deprecated'])
            ]
            
            # Store available models in session state
            st.session_state.available_models = available_models
            
            # Available model versions
            preferred_models = [
                'models/wolf-1.5-flash-latest',
                'models/wolf-1.5-flash',
                'models/wolf-1.5-pro-latest',
                'models/wolf-1.5-pro',
                'models/wolf-pro-latest',
                'models/wolf-pro',
            ]
            
            # Try each preferred model in order until one works
            model_found = False
            for model_name in preferred_models:
                try:
                    # Convert Wolf model name back to Gemini for API
                    api_model_name = model_name.replace('wolf', 'gemini')
                    if api_model_name in [m.replace('wolf', 'gemini') for m in available_models]:
                        self.model = genai.GenerativeModel(api_model_name)
                        st.session_state.current_model = model_name  # Store Wolf model name
                        model_found = True
                        break
                except Exception as e:
                    print(f"Error with model {model_name}: {e}")
                    continue
            
            if not model_found:
                # Try with shorter alias names
                alias_models = [
                    'wolf-1.5-flash',
                    'wolf-1.5-pro',
                    'wolf-pro',
                ]
                
                for model_name in alias_models:
                    try:
                        api_model_name = model_name.replace('wolf', 'gemini')
                        if api_model_name in [m.replace('wolf', 'gemini') for m in available_models]:
                            self.model = genai.GenerativeModel(api_model_name)
                            st.session_state.current_model = model_name
                            model_found = True
                            break
                    except Exception as e:
                        print(f"Error with model {model_name}: {e}")
                        continue
            
            # If no preferred models are available, use any safe model
            if not model_found:
                # Filter out explicitly deprecated models
                safe_models = [
                    model for model in available_models 
                    if (
                        'wolf' in model.lower() and 
                        not any(x in model.lower() for x in ['vision', 'deprecated'])
                    )
                ]
                
                if safe_models:
                    try:
                        model_name = safe_models[0]
                        api_model_name = model_name.replace('wolf', 'gemini')
                        self.model = genai.GenerativeModel(api_model_name)
                        st.session_state.current_model = model_name
                        model_found = True
                    except Exception as e:
                        print(f"Error with fallback model: {e}")
                else:
                    # Last resort: use the first available model
                    model_name = available_models[0] if available_models else None
                    if model_name:
                        api_model_name = model_name.replace('wolf', 'gemini')
                        self.model = genai.GenerativeModel(api_model_name)
                        st.session_state.current_model = model_name
                        print(f"Using fallback model: {model_name}")
                    else:
                        raise ValueError("No text generation models available")
            
            self.initialized = True
        except Exception as e:
            st.error(f"Failed to initialize Wolf API: {str(e)}")
            self.initialized = False
            
    def verify_api_key(self):
        """
        Verify if the API key is valid by sending a minimal test request.
        
        Returns:
            dict: A dictionary containing 'valid' (bool) and 'message' (str) keys
        """
        if not self.api_key:
            return {
                "valid": False, 
                "message": "No API key provided"
            }
            
        try:
            # Initialize the API if not already done
            if not self.initialized:
                self._initialize_api()
                
            if not self.initialized:
                return {
                    "valid": False,
                    "message": "Failed to initialize API with provided key"
                }
            
            # Show the model being used for verification
            model_name = getattr(self.model, 'model_name', 'Unknown model')
            
            # Check if we have available models in session state (from _initialize_api)
            if 'available_models' in st.session_state and st.session_state.available_models:
                available_models_str = ", ".join(st.session_state.available_models[:3])
                if len(st.session_state.available_models) > 3:
                    available_models_str += f", and {len(st.session_state.available_models) - 3} more"
            else:
                available_models_str = "No models found"
            
            # Send a minimal test request
            test_prompt = "Echo test"
            response = self.model.generate_content(
                test_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=10
                )
            )
            
            # If we get here, the API key is valid
            return {
                "valid": True,
                "message": f"API key is valid. Using model: {model_name}",
                "available_models": available_models_str
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for common errors
            if "invalid api key" in error_msg.lower():
                return {
                    "valid": False,
                    "message": "Invalid API key"
                }
            elif "quota" in error_msg.lower():
                return {
                    "valid": False,
                    "message": "API quota exceeded"
                }
            elif "not found" in error_msg.lower() and "model" in error_msg.lower():
                return {
                    "valid": False,
                    "message": "The selected model is not available. Please check available models in your Google AI Studio account."
                }
            elif "permission" in error_msg.lower():
                return {
                    "valid": False,
                    "message": "Permission denied. Your account may not have access to the requested model."
                }
            else:
                return {
                    "valid": False,
                    "message": f"API error: {error_msg}"
                }
    
    def analyze_security(self, prompt, context=None, temperature=0.3):
        """
        Perform security analysis using the Wolf API.
        
        Args:
            prompt (str): The security question or data to analyze
            context (dict, optional): Additional context for the analysis
            temperature (float, optional): Controls randomness in the response
            
        Returns:
            dict: The analysis results or error information
        """
        if not self.initialized:
            if not self.api_key:
                return {
                    "error": "API key not provided. Please enter your Wolf API key in the sidebar."
                }
            else:
                self._initialize_api()
                if not self.initialized:
                    return {
                        "error": "Failed to initialize Wolf API. Please check your API key."
                    }
        
        try:
            # Construct the full prompt with context
            if context:
                full_prompt = f"""
                Security Analysis Request:
                {prompt}
                
                Context:
                {json.dumps(context, indent=2)}
                
                Provide a comprehensive security analysis in JSON format with the following structure:
                {{
                    "summary": "Brief summary of findings",
                    "risk_score": "Score from 0-100",
                    "confidence": "Percentage confidence in analysis",
                    "issues_count": Number of issues found,
                    "findings": [
                        {{
                            "id": "Finding ID",
                            "title": "Short title",
                            "description": "Detailed description",
                            "severity": "Critical|High|Medium|Low|Info",
                            "impact": "Description of impact",
                            "likelihood": "High|Medium|Low"
                        }}
                    ],
                    "recommendations": [
                        {{
                            "title": "Recommendation title",
                            "description": "Detailed steps to address the issue"
                        }}
                    ]
                }}
                """
            else:
                full_prompt = f"""
                Security Analysis Request:
                {prompt}
                
                Provide a comprehensive security analysis in JSON format with the following structure:
                {{
                    "summary": "Brief summary of findings",
                    "risk_score": "Score from 0-100",
                    "confidence": "Percentage confidence in analysis",
                    "issues_count": Number of issues found,
                    "findings": [
                        {{
                            "id": "Finding ID",
                            "title": "Short title",
                            "description": "Detailed description",
                            "severity": "Critical|High|Medium|Low|Info",
                            "impact": "Description of impact",
                            "likelihood": "High|Medium|Low"
                        }}
                    ],
                    "recommendations": [
                        {{
                            "title": "Recommendation title",
                            "description": "Detailed steps to address the issue"
                        }}
                    ]
                }}
                """
            
            # Display a spinner while waiting for the API response
            with st.spinner("Wolf AI is analyzing your security data..."):
                # Add small delay to ensure spinner is shown
                time.sleep(0.5)
                
                # Call the Wolf API
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature
                    )
                )
                
                # Process the response
                response_text = response.text
                
                # Extract JSON from the response
                try:
                    # Find JSON content within the response
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_content = response_text[json_start:json_end]
                        analysis_results = json.loads(json_content)
                        return analysis_results
                    else:
                        # If no JSON found, return the whole text as an error
                        return {
                            "error": "Could not parse JSON from response",
                            "raw_response": response_text
                        }
                except json.JSONDecodeError:
                    return {
                        "error": "Invalid JSON in response",
                        "raw_response": response_text
                    }
                
        except Exception as e:
            error_msg = str(e)
            
            # Log the full error for debugging
            print(f"Wolf API Error: {error_msg}")
            
            if "invalid api key" in error_msg.lower():
                return {
                    "error": "Invalid API key provided. Please check your Wolf API key in the sidebar or environment variables."
                }
            elif "quota" in error_msg.lower():
                return {
                    "error": "API quota exceeded. Your Wolf API key has reached its quota limit."
                }
            elif "not found" in error_msg.lower() and "model" in error_msg.lower():
                # For model not found errors, show information about available models and how to fix
                available_models_msg = ""
                if 'available_models' in st.session_state and st.session_state.available_models:
                    if len(st.session_state.available_models) > 0:
                        safe_models = [m for m in st.session_state.available_models 
                                      if not ('vision' in m.lower() or 'deprecated' in m.lower())]
                        
                        if safe_models:
                            available_models_msg = f"\n\nAvailable models: {', '.join(safe_models[:5])}"
                
                # Include information about model deprecation
                return {
                    "error": f"Model error: {error_msg}.\n\nThis may be due to recent changes in Wolf API when some models were deprecated.{available_models_msg}",
                    "troubleshooting": """
                    **Troubleshooting steps:**
                    1. Clear your browser cache and reload the page
                    2. Verify your API key has access to the newer models (wolf-1.5-flash or wolf-1.5-pro)
                    3. Try creating a new API key in Google AI Studio
                    4. Check if your account has access to Wolf 1.5 models (they may require special access)
                    """
                }
            elif "permission" in error_msg.lower():
                return {
                    "error": "Permission denied. Your account may not have access to the requested model."
                }
            else:
                # For other errors, provide more context and troubleshooting steps
                return {
                    "error": f"Error during security analysis: {error_msg}",
                    "troubleshooting": """
                    **Troubleshooting steps:**
                    1. Verify your API key is correct
                    2. Check if you have enabled the Wolf API in your Cloud Console
                    3. Make sure your API key has permission to access Wolf models
                    4. Try creating a new API key in Google AI Studio
                    """
                }
