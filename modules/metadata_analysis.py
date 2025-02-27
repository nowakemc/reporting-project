"""
Metadata Analysis Module

This module provides functions for analyzing and visualizing metadata across different file types.
It helps identify common and unique metadata fields for each file extension, and provides
visualization capabilities for comparing metadata structures.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from collections import defaultdict
from modules.database import DatabaseManager

# Database connection placeholder
_db = None

def get_file_type_counts():
    """Get counts of different file types with metadata"""
    query = """
    SELECT 
        o.extension, 
        COUNT(*) as count
    FROM 
        instances i
    JOIN 
        objects o ON i.objectId = o.objectId
    WHERE 
        i.metadata IS NOT NULL 
        AND i.metadata != ''
        AND o.extension IS NOT NULL
    GROUP BY 
        o.extension
    ORDER BY 
        count DESC
    """
    
    return _db.query(query)

def get_metadata_samples(extension=None, limit=100):
    """Get sample metadata for a specific file extension"""
    if extension:
        query = f"""
        SELECT 
            i.objectId, 
            o.extension, 
            i.metadata
        FROM 
            instances i
        JOIN 
            objects o ON i.objectId = o.objectId
        WHERE 
            i.metadata IS NOT NULL 
            AND i.metadata != ''
            AND o.extension = '{extension}'
        LIMIT {limit}
        """
    else:
        query = f"""
        SELECT 
            i.objectId, 
            o.extension, 
            i.metadata
        FROM 
            instances i
        JOIN 
            objects o ON i.objectId = o.objectId
        WHERE 
            i.metadata IS NOT NULL 
            AND i.metadata != ''
            AND o.extension IS NOT NULL
        ORDER BY RANDOM()
        LIMIT {limit}
        """
    
    return _db.query(query)

def extract_metadata_keys(metadata_json):
    """Extract flattened keys from metadata JSON"""
    keys = set()
    try:
        # Parse JSON
        metadata = json.loads(metadata_json)
        
        # Function to recursively extract keys
        def extract_keys(d, prefix=''):
            if not isinstance(d, dict):
                return
                
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.add(full_key)
                
                # Process nested dicts
                if isinstance(v, dict):
                    extract_keys(v, full_key)
                    
                # Process dicts in lists
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            extract_keys(item, full_key)
        
        extract_keys(metadata)
    except (json.JSONDecodeError, Exception):
        pass
    
    return keys

def analyze_metadata(extension=None, max_samples=100):
    """Analyze metadata for a specific file extension or all extensions"""
    # Get samples
    samples_df = get_metadata_samples(extension, max_samples)
    
    if len(samples_df) == 0:
        return None
    
    # Extract and count keys
    extension_keys = defaultdict(int)
    valid_samples = 0
    
    for _, row in samples_df.iterrows():
        try:
            keys = extract_metadata_keys(row['metadata'])
            for key in keys:
                extension_keys[key] += 1
            valid_samples += 1
        except Exception:
            continue
    
    # Calculate frequencies
    result = {
        'file_type': extension if extension else 'all',
        'total_samples': len(samples_df),
        'valid_samples': valid_samples,
        'unique_keys': len(extension_keys),
        'keys': {
            k: {
                'count': v,
                'percentage': (v / valid_samples) * 100 if valid_samples > 0 else 0
            }
            for k, v in extension_keys.items()
        }
    }
    
    return result

def compare_file_types(file_types, max_samples_per_type=50):
    """Compare metadata keys across different file types"""
    results = {}
    
    for file_type in file_types:
        analysis = analyze_metadata(file_type, max_samples_per_type)
        if analysis:
            results[file_type] = analysis
    
    return results

def get_top_metadata_keys(analysis_result, top_n=10):
    """Get the top N metadata keys for a file type"""
    if not analysis_result or 'keys' not in analysis_result:
        return []
    
    # Sort keys by frequency
    sorted_keys = sorted(
        analysis_result['keys'].items(),
        key=lambda x: x[1]['percentage'],
        reverse=True
    )
    
    # Return top N
    return sorted_keys[:top_n]

def get_metadata_value_examples(extension, key_path, limit=5):
    """Get example values for a specific metadata field"""
    samples = get_metadata_samples(extension, 100)
    
    examples = []
    key_parts = key_path.split('.')
    
    for _, row in samples.iterrows():
        try:
            metadata = json.loads(row['metadata'])
            
            # Navigate the nested structure
            current = metadata
            for part in key_parts:
                if part in current:
                    current = current[part]
                else:
                    current = None
                    break
            
            if current is not None and current != "" and current not in examples:
                examples.append(str(current)[:100])  # Truncate very long values
                if len(examples) >= limit:
                    break
        except:
            continue
    
    return examples

def render_file_type_comparison(file_types=None, max_file_types=10):
    """Render a comparison of metadata across file types"""
    st.header("File Metadata Analysis")
    
    # Get file type counts if not provided
    if not file_types:
        file_type_counts = get_file_type_counts()
        
        if len(file_type_counts) == 0:
            st.warning("No file types with metadata found in the database.")
            return
        
        # Limit to top N file types by default
        file_type_counts = file_type_counts.head(max_file_types)
        file_types = file_type_counts['extension'].tolist()
    
    # Allow user to select file types to compare
    selected_types = st.multiselect(
        "Select file types to compare:",
        options=file_types,
        default=file_types[:3] if len(file_types) >= 3 else file_types
    )
    
    if not selected_types:
        st.info("Please select at least one file type to analyze.")
        return
    
    # Set sampling parameters
    col1, col2 = st.columns(2)
    with col1:
        samples_per_type = st.slider(
            "Max samples per file type:",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )
    
    with col2:
        top_fields = st.slider(
            "Top fields to display:",
            min_value=5,
            max_value=30,
            value=10,
            step=5
        )
    
    # Run comparison
    with st.spinner("Analyzing metadata across file types..."):
        comparison = compare_file_types(selected_types, samples_per_type)
    
    # Display results
    if not comparison:
        st.warning("No metadata analysis results available.")
        return
    
    # Create a summary table
    summary_data = []
    
    for file_type, analysis in comparison.items():
        summary_data.append({
            "File Type": file_type.upper(),
            "Total Samples": analysis['total_samples'],
            "Valid Samples": analysis['valid_samples'],
            "Unique Fields": analysis['unique_keys']
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.subheader("Metadata Summary by File Type")
    st.dataframe(summary_df)
    
    # Create a heatmap for common fields
    st.subheader("Metadata Field Frequency Heatmap")
    
    # Collect all unique keys across file types
    all_keys = set()
    for analysis in comparison.values():
        all_keys.update(analysis['keys'].keys())
    
    # Get top N keys by average frequency
    key_avg_freq = {}
    for key in all_keys:
        frequencies = [
            analysis['keys'].get(key, {'percentage': 0})['percentage']
            for analysis in comparison.values()
        ]
        key_avg_freq[key] = sum(frequencies) / len(frequencies)
    
    top_keys = sorted(
        key_avg_freq.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_fields]
    
    top_key_names = [k for k, _ in top_keys]
    
    # Create heatmap data
    heatmap_data = []
    
    for file_type, analysis in comparison.items():
        for key in top_key_names:
            frequency = analysis['keys'].get(key, {'percentage': 0})['percentage']
            heatmap_data.append({
                'File Type': file_type.upper(),
                'Metadata Field': key,
                'Frequency (%)': frequency
            })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Create heatmap using plotly
    fig = px.density_heatmap(
        heatmap_df,
        x='File Type',
        y='Metadata Field',
        z='Frequency (%)',
        color_continuous_scale='Viridis',
        range_color=[0, 100]
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="File Type",
        yaxis_title="Metadata Field",
        coloraxis_colorbar=dict(title="Frequency (%)")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Field details for selected file type
    st.subheader("Field Details by File Type")
    
    selected_type_for_details = st.selectbox(
        "Select a file type to see field details:",
        options=[t.upper() for t in selected_types],
        index=0
    )
    
    selected_type_for_details = selected_type_for_details.lower()
    
    if selected_type_for_details in comparison:
        analysis = comparison[selected_type_for_details]
        top_fields_for_type = get_top_metadata_keys(analysis, top_fields)
        
        # Create table with example values
        field_details = []
        
        for key, stats in top_fields_for_type:
            examples = get_metadata_value_examples(selected_type_for_details, key)
            example_str = ", ".join(examples) if examples else "No examples available"
            
            field_details.append({
                "Field": key,
                "Frequency (%)": f"{stats['percentage']:.1f}%",
                "Example Values": example_str
            })
        
        field_details_df = pd.DataFrame(field_details)
        st.dataframe(field_details_df, use_container_width=True)
    
    # Metadata structure visualization
    st.subheader("Metadata Field Distribution")
    
    # Create data for bar chart
    bar_data = []
    
    for file_type, analysis in comparison.items():
        bar_data.append({
            "File Type": file_type.upper(),
            "Number of Fields": analysis['unique_keys']
        })
    
    bar_df = pd.DataFrame(bar_data)
    
    # Create bar chart
    fig = px.bar(
        bar_df,
        x="File Type",
        y="Number of Fields",
        title="Number of Unique Metadata Fields by File Type",
        color="Number of Fields",
        color_continuous_scale="Viridis"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw metadata viewer
    st.subheader("Raw Metadata Viewer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        viewer_file_type = st.selectbox(
            "Select file type:",
            options=[t for t in selected_types],
            index=0
        )
    
    with col2:
        num_samples = st.slider(
            "Number of samples to view:",
            min_value=1,
            max_value=10,
            value=1
        )
    
    samples = get_metadata_samples(viewer_file_type, num_samples)
    
    for i, (_, sample) in enumerate(samples.iterrows()):
        st.write(f"**Sample {i+1} - {sample['objectId']}**")
        
        try:
            metadata = json.loads(sample['metadata'])
            st.json(metadata)
        except json.JSONDecodeError:
            st.code(sample['metadata'])

def render_metadata_analysis_dashboard(db=None):
    """Main function to render the metadata analysis dashboard"""
    global _db
    if db is not None:
        _db = db
    
    st.title("Document Metadata Analysis")
    
    st.write("""
    This dashboard analyzes the metadata embedded in different file types, 
    showing patterns in what metadata is available in each format.
    """)
    
    # Get top file types with metadata
    file_type_counts = get_file_type_counts()
    
    if len(file_type_counts) == 0:
        st.warning("No file metadata found in the database.")
        return
    
    # Display file type distribution
    st.subheader("File Type Distribution")
    
    # Create a pie chart of file types
    fig = px.pie(
        file_type_counts,
        values='count',
        names='extension',
        title='Distribution of File Types with Metadata',
        hole=0.4
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show top file types in a table
    st.dataframe(file_type_counts.head(10))
    
    # Render the comparison
    top_types = file_type_counts.head(8)['extension'].tolist()
    render_file_type_comparison(top_types)

if __name__ == "__main__":
    # This will be used when importing this module directly in Streamlit
    render_metadata_analysis_dashboard()
