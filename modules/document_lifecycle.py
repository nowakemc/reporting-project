"""
Document Lifecycle Analysis Module

This module provides analysis of document lifecycle metrics including:
- Document aging analysis
- Modification frequency patterns
- Complete lifecycle timeline visualization

The module relies on timestamp data from the objects and instances tables
to construct comprehensive lifecycle visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta

# Set consistent styling for visualizations
plt.style.use('ggplot')


def analyze_document_age(db):
    """
    Analyze the age distribution of documents in the system.
    
    Args:
        db: Database connection object
        
    Returns:
        DataFrame: Age analysis results
    """
    try:
        # Calculate document age based on creation timestamp
        age_distribution = db.query("""
            WITH document_dates AS (
                SELECT
                    objectId,
                    createdAt,
                    updatedAt,
                    (CAST(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) * 1000 AS BIGINT) - createdAt) / 86400000 AS age_days
                FROM
                    objects
                WHERE
                    createdAt IS NOT NULL
                    AND createdAt > 86400000  -- Filter out dates before 1970-01-02
                    AND createdAt < 4102444800000  -- Filter out dates after 2100-01-01
            )
            SELECT
                CASE
                    WHEN age_days < 30 THEN 'Last 30 Days'
                    WHEN age_days < 90 THEN '30-90 Days'
                    WHEN age_days < 180 THEN '3-6 Months'
                    WHEN age_days < 365 THEN '6-12 Months'
                    WHEN age_days < 730 THEN '1-2 Years'
                    ELSE 'Over 2 Years'
                END AS age_category,
                COUNT(*) AS document_count
            FROM
                document_dates
            GROUP BY
                age_category
            ORDER BY
                CASE
                    WHEN age_category = 'Last 30 Days' THEN 1
                    WHEN age_category = '30-90 Days' THEN 2
                    WHEN age_category = '3-6 Months' THEN 3
                    WHEN age_category = '6-12 Months' THEN 4
                    WHEN age_category = '1-2 Years' THEN 5
                    WHEN age_category = 'Over 2 Years' THEN 6
                END
        """)
        
        return age_distribution
    except Exception as e:
        print(f"Error analyzing document age: {e}")
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['age_category', 'document_count'])


def analyze_modification_frequency(db):
    """
    Analyze how frequently documents are modified after creation.
    
    Args:
        db: Database connection object
        
    Returns:
        DataFrame: Modification frequency analysis
    """
    try:
        # Calculate time between updates and creation
        modification_data = db.query("""
            WITH mod_data AS (
                SELECT
                    objectId,
                    createdAt,
                    updatedAt,
                    CASE
                        WHEN updatedAt IS NULL OR updatedAt <= createdAt THEN 0
                        ELSE (updatedAt - createdAt) / 86400000
                    END AS days_to_first_update
                FROM
                    objects
                WHERE
                    createdAt IS NOT NULL
                    AND createdAt > 86400000  -- Filter out dates before 1970-01-02
                    AND createdAt < 4102444800000  -- Filter out dates after 2100-01-01
            )
            SELECT
                CASE
                    WHEN days_to_first_update = 0 THEN 'Never Updated'
                    WHEN days_to_first_update < 1 THEN 'Same Day'
                    WHEN days_to_first_update < 7 THEN 'Within a Week'
                    WHEN days_to_first_update < 30 THEN 'Within a Month'
                    WHEN days_to_first_update < 90 THEN 'Within 3 Months'
                    ELSE 'After 3+ Months'
                END AS update_category,
                COUNT(*) AS document_count
            FROM
                mod_data
            GROUP BY
                update_category
            ORDER BY
                CASE
                    WHEN update_category = 'Never Updated' THEN 1
                    WHEN update_category = 'Same Day' THEN 2
                    WHEN update_category = 'Within a Week' THEN 3
                    WHEN update_category = 'Within a Month' THEN 4
                    WHEN update_category = 'Within 3 Months' THEN 5
                    WHEN update_category = 'After 3+ Months' THEN 6
                END
        """)
        
        return modification_data
    except Exception as e:
        print(f"Error analyzing modification frequency: {e}")
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['update_category', 'document_count'])


def analyze_document_lifecycle_events(db):
    """
    Analyze the complete timeline of document lifecycle events.
    
    Args:
        db: Database connection object
        
    Returns:
        DataFrame: Document lifecycle events
    """
    try:
        # Get a timeline of events from objects and instances tables
        # Join objects and instances to get creation, modification, and access times
        lifecycle_timeline = db.query("""
            WITH lifecycle_data AS (
                SELECT
                    o.objectId,
                    o.name,
                    o.extension,
                    o.createdAt AS obj_created_at,
                    o.updatedAt AS obj_updated_at,
                    i.createTime AS instance_created_at,
                    i.modifyTime AS instance_modified_at,
                    i.accessTime AS instance_accessed_at
                FROM
                    objects o
                LEFT JOIN
                    instances i ON o.objectId = i.objectId
                WHERE
                    o.createdAt IS NOT NULL
                    AND o.createdAt > 86400000  -- Filter out dates before 1970-01-02
                    AND o.createdAt < 4102444800000  -- Filter out dates after 2100-01-01
            )
            SELECT
                objectId,
                name,
                extension,
                obj_created_at,
                obj_updated_at,
                instance_created_at,
                instance_modified_at,
                instance_accessed_at
            FROM
                lifecycle_data
            ORDER BY
                obj_created_at DESC
            LIMIT 1000
        """)
        
        return lifecycle_timeline
    except Exception as e:
        print(f"Error analyzing document lifecycle events: {e}")
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['objectId', 'name', 'extension', 'obj_created_at', 
                                    'obj_updated_at', 'instance_created_at', 
                                    'instance_modified_at', 'instance_accessed_at'])


def plot_document_age_distribution(age_data, title="Document Age Distribution", figsize=(10, 6)):
    """
    Create a visualization of document age distribution.
    
    Args:
        age_data: DataFrame with age distribution data
        title: Chart title
        figsize: Figure size tuple
        
    Returns:
        matplotlib.figure: Plot figure
    """
    if age_data.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14)
        ax.set_title(title)
        return fig
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create horizontal bar chart
    bars = ax.barh(age_data['age_category'], age_data['document_count'], color='#EF4E0A')
    
    # Add value labels to the bars
    for i, bar in enumerate(bars):
        ax.text(
            bar.get_width() + (max(age_data['document_count']) * 0.02), 
            bar.get_y() + bar.get_height()/2, 
            f"{age_data['document_count'].iloc[i]:,}",
            va='center'
        )
    
    # Set title and labels
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('Number of Documents', fontsize=12)
    ax.set_ylabel('Age Category', fontsize=12)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


def plot_modification_frequency(mod_data, title="Document Modification Frequency", figsize=(10, 6)):
    """
    Create a visualization of document modification frequency.
    
    Args:
        mod_data: DataFrame with modification frequency data
        title: Chart title
        figsize: Figure size tuple
        
    Returns:
        matplotlib.figure: Plot figure
    """
    if mod_data.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14)
        ax.set_title(title)
        return fig
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create bar chart with Aparavi brand colors
    colors = ['#EF4E0A', '#56BBCC', '#51565D', '#080A0D', '#F9F9FB', '#d43d00']
    bars = ax.bar(mod_data['update_category'], mod_data['document_count'], color=colors[:len(mod_data)])
    
    # Add value labels above bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height + 0.1,
            f"{int(height):,}",
            ha='center',
            va='bottom',
            fontsize=10
        )
    
    # Set title and labels
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('Update Timeframe', fontsize=12)
    ax.set_ylabel('Number of Documents', fontsize=12)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


def plot_lifecycle_timeline(lifecycle_data, max_docs=10, figsize=(12, 8)):
    """
    Create a timeline visualization of document lifecycle events.
    
    Args:
        lifecycle_data: DataFrame with lifecycle event data
        max_docs: Maximum number of documents to show
        figsize: Figure size tuple
        
    Returns:
        matplotlib.figure: Plot figure
    """
    if lifecycle_data.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=14)
        ax.set_title("Document Lifecycle Timeline")
        return fig
    
    # Limit to most recent documents
    timeline_data = lifecycle_data.head(max_docs).copy()
    
    # Convert timestamps to datetime objects
    for col in ['obj_created_at', 'obj_updated_at', 'instance_created_at', 
                'instance_modified_at', 'instance_accessed_at']:
        if col in timeline_data.columns:
            timeline_data[col] = pd.to_datetime(timeline_data[col] / 1000, unit='s')
    
    # Create labels for the y-axis (document names)
    labels = []
    for _, row in timeline_data.iterrows():
        name = row['name']
        if len(name) > 30:
            name = name[:27] + "..."
        if pd.notna(row['extension']):
            name = f"{name}.{row['extension']}"
        labels.append(name)
    
    # Create the figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot events for each document
    for i, (_, row) in enumerate(timeline_data.iterrows()):
        y_pos = len(timeline_data) - i - 1  # Reverse order so newest at top
        
        # Plot creation event
        if pd.notna(row['obj_created_at']):
            ax.scatter(row['obj_created_at'], y_pos, color='#EF4E0A', s=100, label='Created', zorder=3)
        
        # Plot update event if it exists and is different from creation
        if pd.notna(row['obj_updated_at']) and row['obj_updated_at'] != row['obj_created_at']:
            ax.scatter(row['obj_updated_at'], y_pos, color='#56BBCC', s=100, marker='s', label='Updated', zorder=3)
            # Draw line from creation to update
            ax.plot([row['obj_created_at'], row['obj_updated_at']], [y_pos, y_pos], 
                    color='#51565D', linestyle='--', alpha=0.5, zorder=2)
        
        # Plot access event if it exists
        if pd.notna(row['instance_accessed_at']):
            ax.scatter(row['instance_accessed_at'], y_pos, color='#51565D', s=80, 
                      marker='^', label='Accessed', zorder=3)
    
    # Set y-axis labels and limits
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.5, len(labels) - 0.5)
    
    # Format the x-axis to show dates nicely
    plt.gcf().autofmt_xdate()
    
    # Set title and labels
    ax.set_title("Document Lifecycle Timeline", fontsize=14)
    ax.set_xlabel('Date', fontsize=12)
    
    # Create a legend without duplicates
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left', bbox_to_anchor=(1, 1))
    
    # Add grid lines
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig
