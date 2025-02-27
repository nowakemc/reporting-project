"""
Module for exporting data in various formats.
"""

import pandas as pd
import streamlit as st
import json
import base64
from io import BytesIO
import tempfile
import os
from datetime import datetime

def get_timestamp():
    """Get a formatted timestamp for filenames.
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def dataframe_to_csv(df, filename=None):
    """Convert a DataFrame to CSV download link.
    
    Args:
        df (DataFrame): Pandas DataFrame to convert
        filename (str, optional): Filename to use. If None, generates one.
        
    Returns:
        str: HTML link for download
    """
    if filename is None:
        filename = f"export_{get_timestamp()}.csv"
        
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def dataframe_to_excel(df, filename=None):
    """Convert a DataFrame to Excel download link.
    
    Args:
        df (DataFrame): Pandas DataFrame to convert
        filename (str, optional): Filename to use. If None, generates one.
        
    Returns:
        str: HTML link for download
    """
    if filename is None:
        filename = f"export_{get_timestamp()}.xlsx"
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    processed_data = output.getvalue()
    b64 = base64.b64encode(processed_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def dataframe_to_json(df, filename=None):
    """Convert a DataFrame to JSON download link.
    
    Args:
        df (DataFrame): Pandas DataFrame to convert
        filename (str, optional): Filename to use. If None, generates one.
        
    Returns:
        str: HTML link for download
    """
    if filename is None:
        filename = f"export_{get_timestamp()}.json"
        
    json_data = df.to_json(orient='records', date_format='iso')
    b64 = base64.b64encode(json_data.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def export_dataframe(df, format_type='csv', filename=None):
    """Export a DataFrame in the specified format.
    
    Args:
        df (DataFrame): Pandas DataFrame to export
        format_type (str): Format type (csv, excel, json)
        filename (str, optional): Filename to use. If None, generates one.
        
    Returns:
        str: HTML link for download
    """
    if format_type == 'csv':
        return dataframe_to_csv(df, filename)
    elif format_type == 'xlsx':
        return dataframe_to_excel(df, filename)
    elif format_type == 'json':
        return dataframe_to_json(df, filename)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
        
def export_chart(fig, filename=None, format_type='png'):
    """Export a matplotlib figure.
    
    Args:
        fig: Matplotlib figure to export
        filename (str, optional): Filename to use. If None, generates one.
        format_type (str): Format type (png, pdf, svg)
        
    Returns:
        str: HTML link for download
    """
    if filename is None:
        filename = f"chart_{get_timestamp()}.{format_type}"
        
    buf = BytesIO()
    fig.savefig(buf, format=format_type, dpi=300, bbox_inches='tight')
    buf.seek(0)
    
    data = buf.getvalue()
    b64 = base64.b64encode(data).decode()
    
    mime_types = {
        'png': 'image/png',
        'pdf': 'application/pdf',
        'svg': 'image/svg+xml'
    }
    
    mime = mime_types.get(format_type, 'application/octet-stream')
    href = f'<a href="data:{mime};base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def export_report(report_data, format_type='pdf'):
    """Export a complete report.
    
    Args:
        report_data (dict): Report data including charts and tables
        format_type (str): Format type (pdf, html)
        
    Returns:
        str: HTML link for download
    """
    # This is a placeholder for a more complex report generation feature
    # Would typically use a library like ReportLab, WeasyPrint, or nbconvert
    
    filename = f"report_{get_timestamp()}.{format_type}"
    
    # For now, we'll just create a JSON export of the report data
    json_data = json.dumps(report_data, default=str)
    b64 = base64.b64encode(json_data.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download Report Data</a>'
    return href
