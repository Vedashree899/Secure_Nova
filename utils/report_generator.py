import pandas as pd
import json
import base64
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st

class ReportGenerator:
    """
    Utility class for generating and downloading security reports in multiple formats.
    """
    
    @staticmethod
    def generate_csv_download_link(df, filename="security_report.csv", text="Download CSV"):
        """
        Generate a download link for a pandas DataFrame as CSV.
        
        Args:
            df (pandas.DataFrame): The DataFrame to convert to CSV
            filename (str): The filename for the downloaded file
            text (str): The text to display for the download link
            
        Returns:
            str: HTML download link
        """
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
        return href
    
    @staticmethod
    def generate_excel_download_link(df, filename="security_report.xlsx", text="Download Excel"):
        """
        Generate a download link for a pandas DataFrame as Excel.
        
        Args:
            df (pandas.DataFrame): The DataFrame to convert to Excel
            filename (str): The filename for the downloaded file
            text (str): The text to display for the download link
            
        Returns:
            str: HTML download link
        """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
            # Auto-adjust columns' width
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets['Report'].set_column(col_idx, col_idx, column_width)
        
        excel_data = output.getvalue()
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
        return href
    
    @staticmethod
    def generate_json_download_link(data, filename="security_report.json", text="Download JSON"):
        """
        Generate a download link for a dictionary as JSON.
        
        Args:
            data (dict): The data to convert to JSON
            filename (str): The filename for the downloaded file
            text (str): The text to display for the download link
            
        Returns:
            str: HTML download link
        """
        json_str = json.dumps(data, indent=4)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{filename}">{text}</a>'
        return href
    
    @staticmethod
    def generate_pdf_report(analysis_results, findings_df):
        """
        Generate a PDF report from analysis results.
        Currently, this is a placeholder function and returns None.
        Full PDF implementation would require additional dependencies.
        
        Args:
            analysis_results (dict): The complete analysis results
            findings_df (pandas.DataFrame): The findings as a DataFrame
            
        Returns:
            bytes: The PDF report as bytes
        """
        # This is a placeholder for future PDF report generation
        # For now, we'll use HTML to provide comprehensive reports
        return None
    
    @staticmethod
    def generate_html_report(analysis_results, findings_df):
        """
        Generate an HTML report from analysis results.
        
        Args:
            analysis_results (dict): The complete analysis results
            findings_df (pandas.DataFrame): The findings as a DataFrame
            
        Returns:
            str: The HTML report
        """
        # Get current date and time
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate severity distribution chart
        if not findings_df.empty and 'severity' in findings_df.columns:
            severity_counts = findings_df['severity'].value_counts().reset_index()
            severity_counts.columns = ['Severity', 'Count']
            
            fig = px.bar(
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
                title="Findings by Severity"
            )
            
            severity_chart = fig.to_html(full_html=False, include_plotlyjs='cdn')
        else:
            severity_chart = "<p>No severity data available for visualization.</p>"
        
        # Generate risk gauge
        risk_score = analysis_results.get('risk_score', 'N/A')
        if isinstance(risk_score, str) and risk_score.isdigit():
            risk_score = int(risk_score)
        elif not isinstance(risk_score, (int, float)):
            risk_score = 0
            
        gauge_fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = risk_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Score"},
            gauge = {
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
        
        gauge_chart = gauge_fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Generate findings table HTML
        if not findings_df.empty:
            findings_table = findings_df.to_html(classes='table table-striped', escape=False)
        else:
            findings_table = "<p>No findings available.</p>"
        
        # Generate recommendations list
        recommendations_html = ""
        if 'recommendations' in analysis_results and analysis_results['recommendations']:
            for i, rec in enumerate(analysis_results['recommendations'], 1):
                recommendations_html += f"""
                <div class="recommendation">
                    <h4>{i}. {rec['title']}</h4>
                    <p>{rec['description']}</p>
                </div>
                """
        else:
            recommendations_html = "<p>No recommendations available.</p>"
        
        # Build the full HTML report
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Wolf Security Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #eee;
                }}
                .logo {{
                    max-width: 150px;
                }}
                .report-meta {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }}
                .metrics-container {{
                    display: flex;
                    justify-content: space-around;
                    flex-wrap: wrap;
                    margin: 20px 0;
                }}
                .metric-box {{
                    text-align: center;
                    padding: 15px;
                    margin: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    flex: 1;
                    min-width: 200px;
                }}
                .summary-section {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                }}
                .findings-section {{
                    margin: 30px 0;
                }}
                .visual-section {{
                    margin: 30px 0;
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around;
                }}
                .chart-container {{
                    margin: 15px;
                    flex: 1;
                    min-width: 400px;
                }}
                .table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .table th, .table td {{
                    padding: 12px 15px;
                    border: 1px solid #ddd;
                }}
                .table th {{
                    background-color: #f2f2f2;
                }}
                .table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .recommendations-section {{
                    margin: 30px 0;
                }}
                .recommendation {{
                    margin: 15px 0;
                    padding: 15px;
                    background-color: #e6f7ff;
                    border-left: 5px solid #1890ff;
                    border-radius: 3px;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 2px solid #eee;
                    text-align: center;
                    font-size: 0.9em;
                    color: #666;
                }}
                .critical {{
                    background-color: #ffdddd;
                    color: darkred;
                }}
                .high {{
                    background-color: #ffeecc;
                    color: darkorange;
                }}
                .medium {{
                    background-color: #ffffcc;
                    color: darkgoldenrod;
                }}
                .low {{
                    background-color: #e6ffcc;
                    color: darkgreen;
                }}
                .info {{
                    background-color: #e6f7ff;
                    color: darkblue;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Wolf Security Analysis Report</h1>
                <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
                    <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
                    <path d="M4 22h16"></path>
                    <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
                    <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
                    <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
                </svg>
            </div>
            
            <div class="report-meta">
                <p><strong>Report Date:</strong> {report_date}</p>
                <p><strong>Report Type:</strong> {analysis_results.get('report_type', 'Security Analysis')}</p>
            </div>
            
            <div class="summary-section">
                <h2>Executive Summary</h2>
                <p>{analysis_results.get('summary', 'No summary available')}</p>
            </div>
            
            <div class="metrics-container">
                <div class="metric-box">
                    <h3>Risk Score</h3>
                    <p>{analysis_results.get('risk_score', 'N/A')}/100</p>
                </div>
                <div class="metric-box">
                    <h3>Issues Found</h3>
                    <p>{analysis_results.get('issues_count', 'N/A')}</p>
                </div>
                <div class="metric-box">
                    <h3>Confidence</h3>
                    <p>{analysis_results.get('confidence', 'N/A')}</p>
                </div>
            </div>
            
            <div class="visual-section">
                <div class="chart-container">
                    {gauge_chart}
                </div>
                <div class="chart-container">
                    {severity_chart}
                </div>
            </div>
            
            <div class="findings-section">
                <h2>Detailed Findings</h2>
                {findings_table}
            </div>
            
            <div class="recommendations-section">
                <h2>Recommendations</h2>
                {recommendations_html}
            </div>
            
            <div class="footer">
                <p>Generated by Wolf Security Platform</p>
                <p>Powered by Wolf AI &copy; {datetime.now().year}</p>
            </div>
        </body>
        </html>
        """
        
        return html_report