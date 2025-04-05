import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Directory for storing historical data
HISTORY_DIR = "data/history"

def ensure_history_directory():
    """Ensure the history directory exists."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # Create subdirectories for different projects if they don't exist
    project_dirs = [
        "vulnerability_scanner",
        "threat_intelligence",
        "malware_analyzer",
        "secure_coding",
        "network_security"
    ]
    
    for project in project_dirs:
        os.makedirs(os.path.join(HISTORY_DIR, project), exist_ok=True)
        
    return True

def get_project_directory(project_name):
    """Get the directory for a specific project."""
    # Convert project name to directory name (lowercase with underscores)
    dir_name = project_name.lower().replace(" ", "_")
    return os.path.join(HISTORY_DIR, dir_name)

def save_analysis_results(analysis_results, project_name):
    """
    Save analysis results to the history storage.
    
    Args:
        analysis_results (dict): The analysis results to save
        project_name (str): The name of the project (e.g., "Vulnerability Scanner")
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Ensure directory exists
        ensure_history_directory()
        
        # Get project directory
        project_dir = get_project_directory(project_name)
        
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Add the timestamp to the analysis results
        analysis_results["timestamp"] = timestamp
        analysis_results["recorded_date"] = datetime.now().strftime("%Y-%m-%d")
        analysis_results["recorded_time"] = datetime.now().strftime("%H:%M:%S")
        
        # Create a unique filename
        filename = f"{timestamp}_{project_name.lower().replace(' ', '_')}.json"
        file_path = os.path.join(project_dir, filename)
        
        # Save the data as JSON
        with open(file_path, 'w') as f:
            json.dump(analysis_results, f, indent=2)
            
        return True
    except Exception as e:
        st.error(f"Error saving historical data: {str(e)}")
        return False

def get_history_files(project_name=None):
    """
    Get a list of historical analysis files.
    
    Args:
        project_name (str, optional): Filter by project name
        
    Returns:
        list: List of file paths
    """
    try:
        ensure_history_directory()
        
        if project_name:
            # Get files for a specific project
            project_dir = get_project_directory(project_name)
            if not os.path.exists(project_dir):
                return []
                
            return [os.path.join(project_dir, f) for f in os.listdir(project_dir) 
                   if f.endswith('.json')]
        else:
            # Get all files from all project directories
            all_files = []
            for root, _, files in os.walk(HISTORY_DIR):
                all_files.extend([os.path.join(root, f) for f in files if f.endswith('.json')])
            return all_files
    except Exception as e:
        st.error(f"Error retrieving history files: {str(e)}")
        return []

def load_historical_data(project_name=None, limit=None, sort_by_date=True):
    """
    Load historical analysis data.
    
    Args:
        project_name (str, optional): Filter by project name
        limit (int, optional): Limit the number of records returned
        sort_by_date (bool): Sort by date (newest first)
        
    Returns:
        list: List of analysis result dictionaries
    """
    try:
        # Get all history files
        files = get_history_files(project_name)
        
        # Sort files by timestamp (newest first) if requested
        if sort_by_date:
            files.sort(reverse=True)
        
        # Apply limit if specified
        if limit and isinstance(limit, int):
            files = files[:limit]
        
        # Load data from each file
        data = []
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                    
                    # Extract project from filename
                    filename = os.path.basename(file_path)
                    project = filename.split('_', 1)[1].rsplit('.', 1)[0].replace('_', ' ').title()
                    result['project'] = project
                    
                    data.append(result)
            except Exception as e:
                st.warning(f"Error loading file {file_path}: {str(e)}")
                continue
                
        return data
    except Exception as e:
        st.error(f"Error loading historical data: {str(e)}")
        return []

def get_trend_data(project_name=None, metric="risk_score", days=30):
    """
    Get trend data for visualization over time.
    
    Args:
        project_name (str, optional): Filter by project name
        metric (str): Metric to track (risk_score, issues_count, etc.)
        days (int): Number of days to include
        
    Returns:
        pandas.DataFrame: DataFrame with timestamp and metric columns
    """
    try:
        # Load all historical data for the project
        data = load_historical_data(project_name)
        
        # Extract timestamp and metric
        trend_data = []
        for item in data:
            if metric in item:
                # Convert to numeric if possible
                metric_value = item[metric]
                if isinstance(metric_value, str) and metric_value.isdigit():
                    metric_value = int(metric_value)
                elif not isinstance(metric_value, (int, float)):
                    metric_value = 0
                
                # Extract date from timestamp
                date_str = item.get('recorded_date', 
                                  datetime.strptime(item.get('timestamp', ''), 
                                                    "%Y%m%d_%H%M%S").strftime("%Y-%m-%d"))
                
                trend_data.append({
                    'date': date_str,
                    'project': item.get('project', project_name),
                    metric: metric_value
                })
        
        # Convert to DataFrame
        if trend_data:
            df = pd.DataFrame(trend_data)
            
            # Sort by date
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Filter by days if specified
            if days:
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
                df = df[df['date'] >= cutoff_date]
                
            return df
        else:
            return pd.DataFrame(columns=['date', 'project', metric])
            
    except Exception as e:
        st.error(f"Error generating trend data: {str(e)}")
        return pd.DataFrame(columns=['date', 'project', metric])

def display_historical_trends(project_name=None):
    """
    Display historical trends in the Streamlit app.
    
    Args:
        project_name (str, optional): Filter by project name
    """
    try:
        # Get data for risk score trend
        risk_df = get_trend_data(project_name, "risk_score")
        issues_df = get_trend_data(project_name, "issues_count")
        
        # Check if we have data
        if risk_df.empty and issues_df.empty:
            st.info("No historical data available for trend analysis. Run some security analyses to collect data.")
            return
        
        # Create tabs for different metrics
        trend_tab1, trend_tab2 = st.tabs(["Risk Score Trends", "Issues Count Trends"])
        
        # Risk Score Trend
        with trend_tab1:
            if not risk_df.empty and 'risk_score' in risk_df.columns:
                st.subheader("Risk Score Over Time")
                
                # Line chart for risk score
                fig = px.line(
                    risk_df, 
                    x='date', 
                    y='risk_score',
                    color='project' if 'project' in risk_df.columns else None,
                    markers=True,
                    title="Security Risk Score Trend"
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Risk Score",
                    yaxis=dict(range=[0, 100])
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary statistics
                st.write("**Risk Score Statistics:**")
                last_score = risk_df['risk_score'].iloc[-1] if len(risk_df) > 0 else "N/A"
                avg_score = risk_df['risk_score'].mean() if len(risk_df) > 0 else "N/A"
                max_score = risk_df['risk_score'].max() if len(risk_df) > 0 else "N/A"
                min_score = risk_df['risk_score'].min() if len(risk_df) > 0 else "N/A"
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Latest Score", f"{last_score:.1f}" if isinstance(last_score, (int, float)) else last_score)
                col2.metric("Average Score", f"{avg_score:.1f}" if isinstance(avg_score, (int, float)) else avg_score)
                col3.metric("Maximum Score", f"{max_score:.1f}" if isinstance(max_score, (int, float)) else max_score)
                col4.metric("Minimum Score", f"{min_score:.1f}" if isinstance(min_score, (int, float)) else min_score)
            else:
                st.info("No risk score data available yet.")
        
        # Issues Count Trend
        with trend_tab2:
            if not issues_df.empty and 'issues_count' in issues_df.columns:
                st.subheader("Security Issues Count Over Time")
                
                # Line chart for issues count
                fig = px.line(
                    issues_df, 
                    x='date', 
                    y='issues_count',
                    color='project' if 'project' in issues_df.columns else None,
                    markers=True,
                    title="Security Issues Count Trend"
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Issues Count"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary statistics
                st.write("**Issues Count Statistics:**")
                last_count = issues_df['issues_count'].iloc[-1] if len(issues_df) > 0 else "N/A"
                avg_count = issues_df['issues_count'].mean() if len(issues_df) > 0 else "N/A"
                max_count = issues_df['issues_count'].max() if len(issues_df) > 0 else "N/A"
                min_count = issues_df['issues_count'].min() if len(issues_df) > 0 else "N/A"
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Latest Count", f"{last_count:.0f}" if isinstance(last_count, (int, float)) else last_count)
                col2.metric("Average Count", f"{avg_count:.1f}" if isinstance(avg_count, (int, float)) else avg_count)
                col3.metric("Maximum Count", f"{max_count:.0f}" if isinstance(max_count, (int, float)) else max_count)
                col4.metric("Minimum Count", f"{min_count:.0f}" if isinstance(min_count, (int, float)) else min_count)
            else:
                st.info("No issues count data available yet.")
                
    except Exception as e:
        st.error(f"Error displaying historical trends: {str(e)}")

def display_security_history_table(project_name=None, limit=10):
    """
    Display a table of historical security analyses.
    
    Args:
        project_name (str, optional): Filter by project name
        limit (int): Maximum number of rows to display
    """
    try:
        # Load historical data
        data = load_historical_data(project_name, limit=limit)
        
        if not data:
            st.info("No historical data available yet. Run some security analyses to collect data.")
            return
        
        # Extract relevant fields
        table_data = []
        for item in data:
            date_str = item.get('recorded_date', '')
            time_str = item.get('recorded_time', '')
            
            # Extract date and time if not explicitly available
            if not date_str or not time_str:
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        date_str = dt.strftime("%Y-%m-%d")
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        pass
            
            # Get project name
            project = item.get('project', project_name or 'Unknown')
            
            # Get risk score
            risk_score = item.get('risk_score', 'N/A')
            if isinstance(risk_score, str) and risk_score.isdigit():
                risk_score = int(risk_score)
                
            # Get issues count
            issues_count = item.get('issues_count', 'N/A')
            if isinstance(issues_count, str) and issues_count.isdigit():
                issues_count = int(issues_count)
                
            # Get summary
            summary = item.get('summary', 'No summary available')
            
            # Add to table data
            table_data.append({
                'Date': date_str,
                'Time': time_str,
                'Project': project,
                'Risk Score': risk_score,
                'Issues': issues_count,
                'Summary': summary[:100] + ('...' if len(summary) > 100 else '')
            })
        
        # Convert to DataFrame
        history_df = pd.DataFrame(table_data)
        
        # Display table
        st.dataframe(
            history_df,
            use_container_width=True,
            column_config={
                "Date": st.column_config.TextColumn(
                    "Date",
                    width="small"
                ),
                "Time": st.column_config.TextColumn(
                    "Time",
                    width="small"
                ),
                "Project": st.column_config.TextColumn(
                    "Project",
                    width="medium"
                ),
                "Risk Score": st.column_config.NumberColumn(
                    "Risk Score",
                    format="%d",
                    width="small"
                ),
                "Issues": st.column_config.NumberColumn(
                    "Issues",
                    format="%d",
                    width="small"
                ),
                "Summary": st.column_config.TextColumn(
                    "Summary",
                    width="large"
                )
            },
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"Error displaying history table: {str(e)}")