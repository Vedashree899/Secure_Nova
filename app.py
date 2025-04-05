import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from datetime import datetime
from utils.api import WolfAPI
from utils.data_processing import process_security_analysis
from utils.report_generator import ReportGenerator
from utils.history_storage import save_analysis_results
from modules.vulnerability_scanner import VulnerabilityScanner
from modules.threat_intelligence import ThreatIntelligence
from modules.malware_analyzer import MalwareAnalyzer
from modules.secure_coding import SecureCoding
from modules.network_security import NetworkSecurity
from modules.history_tracker import HistoryTracker

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Security Platform - Wolf AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'current_project' not in st.session_state:
    st.session_state.current_project = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("WOLF_API_KEY", "")
if 'api_key_verified' not in st.session_state:
    st.session_state.api_key_verified = False

# Sidebar for navigation and configuration
with st.sidebar:
    st.title("Wolf Security AI")
    
    # Logo
    st.markdown("""
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
        <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
        <path d="M4 22h16"></path>
        <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
        <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
        <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
    </svg>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # API Key Input

    # Verify button
    if not st.session_state.api_key_verified and st.button("Verify API Key"):
        if not st.session_state.api_key:
            st.error("Please enter a Wolf API key")
        else:
            with st.spinner("Verifying API key..."):
                # Initialize test API client
                test_api = WolfAPI(st.session_state.api_key)
                
                # Use the dedicated verification method
                verification_result = test_api.verify_api_key()
                
                if verification_result["valid"]:
                    st.success("✅ API key verified successfully!")
                    st.session_state.api_key_verified = True
                    
                    # Show information about the model being used
                    if 'current_model' in st.session_state:
                        model_name = st.session_state.current_model.replace('gemini', 'wolf')
                        st.info(f"🚀 Using model: **{model_name}**")
                        
                    # Show expandable section with available models if present
                    if "available_models" in verification_result:
                        with st.expander("📚 View available Wolf AI models"):
                            models_text = verification_result['available_models'].replace('gemini', 'wolf')
                            st.text(f"{models_text}")
                else:
                    st.error(f"API key verification failed: {verification_result['message']}")
                    st.warning("Please check your API key and try again.")
    
    # Show API key source information
    if os.getenv("WOLF_API_KEY"):
        st.success("✅ API key loaded from environment")
        if not st.session_state.api_key_verified:
            st.session_state.api_key_verified = True  # Auto-verify environment key
    else:
        st.info("💡 You can also set your API key in .env file for persistent storage")
    
    # Project Selection
    st.subheader("Security Projects")
    project_options = [
        "Vulnerability Scanner",
        "Threat Intelligence",
        "Malware Analyzer",
        "Secure Coding Practices",
        "Network Security",
        "History Tracker"
    ]
    selected_project = st.selectbox("Select Project", project_options)
    
    if selected_project != st.session_state.current_project:
        st.session_state.current_project = selected_project
        st.session_state.analysis_results = None
    
    st.divider()
    
    # About section
    st.info("""
    **Wolf Security Platform**
    
    AI-powered security analysis using Wolf API .
    """)

# Main content area
st.title("Wolf Security Platform")
st.subheader(f"Project: {st.session_state.current_project}")

# Initialize Wolf API client
wolf_api = WolfAPI(st.session_state.api_key)

# Check if API key is verified before allowing access to modules
if not st.session_state.api_key_verified:
    st.warning("⚠️ Please verify your API key in the sidebar before using the platform")
    st.info("""
    **Why is API key verification needed?**
    The Wolf Security Platform uses the Wolf API to provide 
    AI-enhanced security analysis. A valid API key is required to access these capabilities.
    
    **Steps to get started:**
    1. Enter your API key in the sidebar
    2. Click the 'Verify API Key' button
    3. Once verified, you can use all security analysis features
    """)
    module = None
# Load the appropriate module based on the selected project
elif st.session_state.current_project == "Vulnerability Scanner":
    module = VulnerabilityScanner(wolf_api)
elif st.session_state.current_project == "Threat Intelligence":
    module = ThreatIntelligence(wolf_api)
elif st.session_state.current_project == "Malware Analyzer":
    module = MalwareAnalyzer(wolf_api)
elif st.session_state.current_project == "Secure Coding Practices":
    module = SecureCoding(wolf_api)
elif st.session_state.current_project == "Network Security":
    module = NetworkSecurity(wolf_api)
elif st.session_state.current_project == "History Tracker":
    module = HistoryTracker(wolf_api)
else:
    st.error("Please select a security project from the sidebar.")
    module = None

# Display the module if one is selected
if module:
    # Run the module's interface method
    analysis_results = module.show_interface()
    
    # Check if analysis was performed
    if analysis_results:
        # Check for API errors
        if "error" in analysis_results:
            st.error(f"🛑 {analysis_results['error']}")
            
            # Display troubleshooting steps if available
            if "troubleshooting" in analysis_results:
                st.warning(analysis_results["troubleshooting"])
                
            # Display raw response if available for debugging
            if "raw_response" in analysis_results:
                with st.expander("Raw API Response (for debugging)"):
                    st.code(analysis_results["raw_response"])
        else:
            st.session_state.analysis_results = analysis_results
            
            # Save to history storage
            project_name = st.session_state.current_project
            save_result = save_analysis_results(analysis_results, project_name)
            if save_result:
                st.success("✅ Analysis results saved to history")
            
            # Process and display results
            with st.expander("Analysis Results", expanded=True):
                # Summary section
                st.subheader("Summary")
                st.write(analysis_results.get('summary', 'No summary available'))
                
                # Metrics row
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Risk Score", analysis_results.get('risk_score', 'N/A'))
                with col2:
                    st.metric("Issues Found", analysis_results.get('issues_count', 'N/A'))
                with col3:
                    st.metric("Confidence", analysis_results.get('confidence', 'N/A'))
                
                # Detailed findings
                if 'findings' in analysis_results and analysis_results['findings']:
                    st.subheader("Detailed Findings")
                    
                    # Store findings DataFrame in session state for reuse
                    findings_df = process_security_analysis(analysis_results['findings'])
                    st.session_state['current_findings_df'] = findings_df
                
                    # Show table with enhanced filtering capabilities
                    st.dataframe(
                        findings_df,
                        use_container_width=True,
                        column_config={
                            "severity": st.column_config.SelectboxColumn(
                                "Severity",
                                help="Severity level of the finding",
                                width="medium",
                                options=["Critical", "High", "Medium", "Low", "Info"],
                            ),
                            "short_description": st.column_config.TextColumn(
                                "Description",
                                help="Brief description of the finding",
                                width="large"
                            ),
                            "id": st.column_config.TextColumn(
                                "ID",
                                help="Unique identifier",
                                width="small"
                            )
                        },
                        hide_index=True
                    )
                    
                    # Visualization
                    if not findings_df.empty and 'severity' in findings_df.columns:
                        st.subheader("Findings by Severity")
                        severity_counts = findings_df['severity'].value_counts().reset_index()
                        severity_counts.columns = ['Severity', 'Count']
                        
                        # Create tabs for different visualizations
                        viz_tab1, viz_tab2 = st.tabs(["Bar Chart", "Pie Chart"])
                        
                        with viz_tab1:
                            # Bar chart
                            fig_bar = px.bar(
                                severity_counts, 
                                x='Severity', 
                                y='Count',
                                color='Severity',
                                color_discrete_map={
                                    'Critical': 'red',
                                    'High': 'orange',
                                    'Medium': 'yellow',
                                    'Low': 'green',
                                    'Info': 'blue'
                                },
                                title="Findings by Severity Level"
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                        
                        with viz_tab2:
                            # Pie chart
                            fig_pie = px.pie(
                                severity_counts,
                                values='Count',
                                names='Severity',
                                color='Severity',
                                color_discrete_map={
                                    'Critical': 'red',
                                    'High': 'orange',
                                    'Medium': 'yellow',
                                    'Low': 'green',
                                    'Info': 'blue'
                                },
                                title="Distribution of Finding Severities"
                            )
                            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                        # Add risk gauge
                        risk_score = analysis_results.get('risk_score', 'N/A')
                        if isinstance(risk_score, str) and risk_score.isdigit():
                            risk_score = int(risk_score)
                        elif not isinstance(risk_score, (int, float)):
                            risk_score = 0
                        
                        gauge_fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=risk_score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Risk Score"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 20], 'color': "green"},
                                    {'range': [20, 40], 'color': "lightgreen"},
                                    {'range': [40, 60], 'color': "yellow"},
                                    {'range': [60, 80], 'color': "orange"},
                                    {'range': [80, 100], 'color': "red"}
                                ]
                            }
                        ))
                        
                        st.plotly_chart(gauge_fig, use_container_width=True)
            
                # Recommendations
                if 'recommendations' in analysis_results and analysis_results['recommendations']:
                    st.subheader("Recommendations")
                    for i, rec in enumerate(analysis_results['recommendations'], 1):
                        st.markdown(f"**{i}. {rec['title']}**")
                        st.markdown(rec['description'])
                        st.markdown("---")
                
                # Add report download section
                if 'findings' in analysis_results and analysis_results['findings']:
                    st.subheader("Download Reports")
                    
                    # We already have findings_df from earlier processing, no need to regenerate
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # CSV Download
                    with col1:
                        # Generate safe filename
                        project_name = st.session_state.current_project or "security"
                        safe_filename = project_name.lower().replace(' ', '_')
                        
                        csv_link = ReportGenerator.generate_csv_download_link(
                            st.session_state.get('current_findings_df', pd.DataFrame()),
                            filename=f"{safe_filename}_report.csv",
                            text="📊 Download CSV"
                        )
                        st.markdown(csv_link, unsafe_allow_html=True)
                    
                    # Excel Download
                    with col2:
                        excel_link = ReportGenerator.generate_excel_download_link(
                            st.session_state.get('current_findings_df', pd.DataFrame()),
                            filename=f"{safe_filename}_report.xlsx",
                            text="📑 Download Excel"
                        )
                        st.markdown(excel_link, unsafe_allow_html=True)
                    
                    # JSON Download
                    with col3:
                        json_link = ReportGenerator.generate_json_download_link(
                            analysis_results,
                            filename=f"{safe_filename}_report.json",
                            text="🔍 Download JSON"
                        )
                        st.markdown(json_link, unsafe_allow_html=True)
                    
                    # HTML Report
                    with col4:
                        if st.button("🌐 Generate HTML Report"):
                            with st.spinner("Generating comprehensive HTML report..."):
                                html_report = ReportGenerator.generate_html_report(
                                    analysis_results, 
                                    st.session_state.get('current_findings_df', pd.DataFrame())
                                )
                                
                                # Convert HTML to base64 for download
                                import base64
                                b64 = base64.b64encode(html_report.encode()).decode()
                                
                                # Create download link
                                href = f'<a href="data:text/html;base64,{b64}" download="{safe_filename}_report.html">📝 Download HTML Report</a>'
                                st.markdown(href, unsafe_allow_html=True)
                                
                                # Show success message
                                st.success("HTML report generated successfully! Click the link above to download.")

# Footer
st.markdown("---")
st.markdown(f"Wolf Security Platform {datetime.now().year}")
