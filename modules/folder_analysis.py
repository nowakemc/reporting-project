"""
Module for analyzing and visualizing folder structures.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

def process_folder_paths(df, path_column='parentPath'):
    """Process folder paths to extract hierarchy information.
    
    Args:
        df (DataFrame): DataFrame containing path data
        path_column (str): Column name containing path information
        
    Returns:
        DataFrame: Processed DataFrame with path hierarchy columns
    """
    # Copy the dataframe to avoid modifying the original
    result_df = df.copy()
    
    # Clean up paths (remove leading/trailing slashes)
    result_df['cleaned_path'] = result_df[path_column].str.strip('/')
    
    # Split paths into parts
    result_df['path_parts'] = result_df['cleaned_path'].str.split('/')
    
    # Get maximum path depth
    max_depth = result_df['path_parts'].apply(len).max()
    
    # Create columns for each path level
    for i in range(max_depth):
        result_df[f'level_{i+1}'] = result_df['path_parts'].apply(
            lambda x: x[i] if i < len(x) else None
        )
    
    return result_df, max_depth

def aggregate_by_folder(df, size_column='size', count_column=None, path_column='parentPath', max_depth=None):
    """Aggregate data by folder path to get size and count metrics.
    
    Args:
        df (DataFrame): DataFrame containing path and size data
        size_column (str): Column name containing size information
        count_column (str, optional): Column for counting. If None, each row counts as 1
        path_column (str): Column name containing path information
        max_depth (int, optional): Maximum folder depth to consider
        
    Returns:
        DataFrame: Aggregated data by folder
    """
    # Process paths
    processed_df, detected_max_depth = process_folder_paths(df, path_column)
    
    if max_depth is None or max_depth > detected_max_depth:
        max_depth = detected_max_depth
    
    # Create aggregation dataframes for each level
    aggregated_data = []
    for depth in range(1, max_depth + 1):
        # Group columns to use
        group_cols = [f'level_{i+1}' for i in range(depth)]
        
        # Skip if any required column is missing
        if not all(col in processed_df.columns for col in group_cols):
            continue
            
        # Group by the path levels
        if count_column:
            level_data = processed_df.groupby(group_cols).agg({
                size_column: 'sum',
                count_column: 'sum'
            }).reset_index()
        else:
            level_data = processed_df.groupby(group_cols).agg({
                size_column: 'sum',
                path_column: 'count'  # Count rows as a proxy for file count
            }).reset_index()
            level_data.rename(columns={path_column: 'count'}, inplace=True)
        
        # Create full path
        level_data['full_path'] = level_data.apply(
            lambda row: '/'.join([str(row[col]) for col in group_cols if pd.notna(row[col])]), 
            axis=1
        )
        
        # Add depth level
        level_data['depth'] = depth
        
        aggregated_data.append(level_data)
    
    # Combine all levels
    if aggregated_data:
        combined_df = pd.concat(aggregated_data, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def create_sunburst_chart(df, path_columns, values_column, title, color_column=None, color_scale='viridis'):
    """Create a sunburst chart for visualizing folder hierarchy.
    
    Args:
        df (DataFrame): DataFrame with hierarchy data
        path_columns (list): List of columns forming the path hierarchy
        values_column (str): Column name for values (size or count)
        title (str): Chart title
        color_column (str, optional): Column to use for color scale
        color_scale (str): Color scale to use
        
    Returns:
        Figure: Plotly figure object
    """
    if color_column is None:
        color_column = values_column
        
    fig = px.sunburst(
        df,
        path=path_columns,
        values=values_column,
        color=color_column,
        color_continuous_scale=color_scale,
        title=title
    )
    
    fig.update_layout(
        margin=dict(t=30, l=0, r=0, b=0),
        height=600,
    )
    
    return fig

def create_treemap_chart(df, path_columns, values_column, title, color_column=None, color_scale='viridis'):
    """Create a treemap chart for visualizing folder hierarchy.
    
    Args:
        df (DataFrame): DataFrame with hierarchy data
        path_columns (list): List of columns forming the path hierarchy
        values_column (str): Column name for values (size or count)
        title (str): Chart title
        color_column (str, optional): Column to use for color scale
        color_scale (str): Color scale to use
        
    Returns:
        Figure: Plotly figure object
    """
    if color_column is None:
        color_column = values_column
        
    fig = px.treemap(
        df,
        path=path_columns,
        values=values_column,
        color=color_column,
        color_continuous_scale=color_scale,
        title=title
    )
    
    fig.update_layout(
        margin=dict(t=30, l=0, r=0, b=0),
        height=600,
    )
    
    return fig

def find_top_folders(df, metric_column, n=10):
    """Find top folders by a specific metric.
    
    Args:
        df (DataFrame): DataFrame with folder data
        metric_column (str): Column to sort by (e.g., 'size' or 'count')
        n (int): Number of top folders to return
        
    Returns:
        DataFrame: Top n folders
    """
    return df.sort_values(by=metric_column, ascending=False).head(n)

def format_size(size_bytes):
    """Format size in bytes to human-readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.2f} {units[unit_index]}"

def create_hierarchical_bar_chart(df, category_column, value_column, title, color_column=None, color_scale='viridis'):
    """Create a horizontal bar chart for hierarchical data.
    
    Args:
        df (DataFrame): DataFrame with hierarchy data
        category_column (str): Column for categories (y-axis)
        value_column (str): Column for values (x-axis)
        title (str): Chart title
        color_column (str, optional): Column to use for color scale
        color_scale (str): Color scale to use
        
    Returns:
        Figure: Plotly figure object
    """
    if color_column is None:
        color_column = value_column
        
    fig = px.bar(
        df,
        x=value_column,
        y=category_column,
        orientation='h',
        color=color_column,
        color_continuous_scale=color_scale,
        title=title
    )
    
    fig.update_layout(
        xaxis_title=value_column,
        yaxis_title=None,
        yaxis=dict(categoryorder='total ascending'),
        height=600,
    )
    
    return fig

def get_folder_statistics(df, size_column='size', count_column='count'):
    """Calculate statistics for folder analysis.
    
    Args:
        df (DataFrame): DataFrame with folder data
        size_column (str): Column name for size
        count_column (str): Column name for count
        
    Returns:
        dict: Dictionary with folder statistics
    """
    stats = {}
    
    # Size statistics
    stats['total_size'] = df[size_column].sum()
    stats['avg_size'] = df[size_column].mean()
    stats['median_size'] = df[size_column].median()
    stats['max_size'] = df[size_column].max()
    
    # Count statistics
    stats['total_count'] = df[count_column].sum()
    stats['avg_count'] = df[count_column].mean()
    stats['median_count'] = df[count_column].median()
    stats['max_count'] = df[count_column].max()
    
    # Path statistics
    if 'depth' in df.columns:
        stats['max_depth'] = df['depth'].max()
        stats['avg_depth'] = df['depth'].mean()
    
    return stats
