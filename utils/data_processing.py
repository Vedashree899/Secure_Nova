import pandas as pd
import streamlit as st
import re

def clean_text(text):
    """Clean text input to prevent potential security issues."""
    if not isinstance(text, str):
        return ""
    # Remove any potentially harmful HTML/script tags
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()

def validate_input(input_data, input_type="text"):
    """Validate user input based on expected type."""
    if input_type == "text":
        return clean_text(input_data)
    elif input_type == "url":
        # Basic URL validation
        url_pattern = re.compile(
            r'^(?:http|https)://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if url_pattern.match(input_data):
            return input_data
        return None
    elif input_type == "code":
        # For code, we just clean it but don't do extensive validation
        return clean_text(input_data)
    elif input_type == "ip":
        # Basic IP validation
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if ip_pattern.match(input_data):
            return input_data
        return None
    
    return None

def enrich_findings_data(findings):
    """
    Enrich security findings with additional metadata for improved analysis.
    
    Args:
        findings (list): Raw findings from security analysis
        
    Returns:
        list: Enhanced findings with additional metadata
    """
    if not findings:
        return []
    
    enriched_findings = []
    
    for i, finding in enumerate(findings):
        # Deep copy to avoid modifying original
        enriched_finding = finding.copy()
        
        # Add unique identifier if not present
        if 'id' not in enriched_finding or not enriched_finding['id']:
            enriched_finding['id'] = f"WOLF-{i+1:04d}"
        
        # Standardize severity if present
        if 'severity' in enriched_finding:
            severity = enriched_finding['severity'].lower().strip()
            if severity in ['critical', 'crit']:
                enriched_finding['severity'] = 'Critical'
                enriched_finding['severity_score'] = 5
            elif severity in ['high', 'h']:
                enriched_finding['severity'] = 'High'
                enriched_finding['severity_score'] = 4
            elif severity in ['medium', 'med', 'm']:
                enriched_finding['severity'] = 'Medium'
                enriched_finding['severity_score'] = 3
            elif severity in ['low', 'l']:
                enriched_finding['severity'] = 'Low'
                enriched_finding['severity_score'] = 2
            elif severity in ['info', 'information', 'informational', 'i']:
                enriched_finding['severity'] = 'Info'
                enriched_finding['severity_score'] = 1
            else:
                enriched_finding['severity'] = 'Info'
                enriched_finding['severity_score'] = 1
        else:
            enriched_finding['severity'] = 'Info'
            enriched_finding['severity_score'] = 1
            
        # Standardize likelihood if present
        if 'likelihood' in enriched_finding:
            likelihood = enriched_finding['likelihood'].lower().strip()
            if likelihood in ['high', 'h']:
                enriched_finding['likelihood'] = 'High'
                enriched_finding['likelihood_score'] = 3
            elif likelihood in ['medium', 'med', 'm']:
                enriched_finding['likelihood'] = 'Medium'
                enriched_finding['likelihood_score'] = 2
            elif likelihood in ['low', 'l']:
                enriched_finding['likelihood'] = 'Low'
                enriched_finding['likelihood_score'] = 1
            else:
                enriched_finding['likelihood'] = 'Medium'
                enriched_finding['likelihood_score'] = 2
        else:
            enriched_finding['likelihood'] = 'Medium'
            enriched_finding['likelihood_score'] = 2
        
        # Add complexity information if not present
        if 'complexity' not in enriched_finding:
            # Default to medium complexity
            enriched_finding['complexity'] = 'Medium'
        
        # Add discovery date if not present
        if 'discovered_date' not in enriched_finding:
            from datetime import datetime
            enriched_finding['discovered_date'] = datetime.now().strftime("%Y-%m-%d")
        
        enriched_findings.append(enriched_finding)
    
    return enriched_findings

def process_security_analysis(findings):
    """
    Process security analysis findings into a pandas DataFrame
    for better display and analysis.
    
    Args:
        findings (list): List of finding dictionaries from the API
        
    Returns:
        pandas.DataFrame: Processed findings data
    """
    if not findings:
        return pd.DataFrame()
    
    try:
        # Enrich findings data first
        enriched_findings = enrich_findings_data(findings)
        
        # Create DataFrame from enriched findings
        df = pd.DataFrame(enriched_findings)
        
        # Ensure required columns exist
        required_columns = ['id', 'title', 'severity', 'likelihood']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 'N/A'
        
        # Convert severity to categorical type with specific order
        severity_order = ['Critical', 'High', 'Medium', 'Low', 'Info']
        df['severity'] = pd.Categorical(df['severity'], categories=severity_order, ordered=True)
        
        # Sort by severity
        df = df.sort_values('severity')
        
        # Create additional columns for better visualization
        if 'description' in df.columns:
            # Truncate long descriptions for display
            df['short_description'] = df['description'].apply(
                lambda x: x[:100] + '...' if len(x) > 100 else x
            )
        
        return df
    
    except Exception as e:
        st.error(f"Error processing security findings: {str(e)}")
        return pd.DataFrame()
