"""
Security & Governance Analysis Module

This module provides analysis of security and governance metrics including:
- Permission distribution analysis
- Access pattern analysis
- Security compliance reporting

The module utilizes data from objects, osPermissions, and osSecurity tables
to build comprehensive security analytics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.cm as cm

# Set consistent styling for visualizations
plt.style.use('ggplot')


def analyze_permissions(db):
    """
    Analyze the distribution of permissions across documents.
    
    Args:
        db: Database connection object
        
    Returns:
        dict: Dictionary containing permission analysis dataframes
    """
    try:
        # Get permission distribution
        perm_distribution = db.query("""
            SELECT 
                CASE
                    WHEN p.permissionSet IS NULL THEN 'No Permissions'
                    WHEN p.permissionSet = '' THEN 'None'
                    WHEN p.permissionSet LIKE '%read%' AND p.permissionSet LIKE '%write%' THEN 'Read & Write'
                    WHEN p.permissionSet LIKE '%read%' THEN 'Read Only'
                    WHEN p.permissionSet LIKE '%write%' THEN 'Write Only'
                    ELSE 'Other'
                END as permission_type,
                COUNT(*) as count
            FROM 
                objects o
            LEFT JOIN 
                osPermissions p ON o.permissionId = p.permissionId
            GROUP BY 
                permission_type
            ORDER BY 
                count DESC
        """)
        
        # Get owner distribution - extract potential owner info from permissionSet
        owner_distribution = db.query("""
            SELECT 
                CASE
                    WHEN p.permissionSet IS NULL THEN 'Unknown'
                    WHEN p.permissionSet = '' THEN 'Unknown'
                    WHEN p.permissionSet LIKE '%:%' THEN SUBSTRING(p.permissionSet, 0, POSITION(':' IN p.permissionSet))
                    ELSE 'System'
                END as owner,
                COUNT(*) as count
            FROM 
                objects o
            LEFT JOIN 
                osPermissions p ON o.permissionId = p.permissionId
            GROUP BY 
                owner
            ORDER BY 
                count DESC
            LIMIT 10
        """)
        
        # Get security entity distribution based on available columns
        security_distribution = db.query("""
            SELECT 
                COALESCE(s.name, 'None') as security_entity,
                COUNT(*) as count
            FROM 
                objects o
            LEFT JOIN 
                osPermissions p ON o.permissionId = p.permissionId
            LEFT JOIN
                osSecurity s ON p.nodeObjectId = s.nodeObjectId
            GROUP BY 
                security_entity
            ORDER BY 
                count DESC
            LIMIT 10
        """)
        
        return {
            'permissions': perm_distribution,
            'owners': owner_distribution,
            'security': security_distribution
        }
    except Exception as e:
        print(f"Error analyzing permissions: {e}")
        # Return empty DataFrames with expected structure
        return {
            'permissions': pd.DataFrame(columns=['permission_type', 'count']),
            'owners': pd.DataFrame(columns=['owner', 'count']),
            'security': pd.DataFrame(columns=['security_entity', 'count'])
        }


def analyze_access_patterns(db):
    """
    Analyze when and how documents are accessed.
    
    Args:
        db: Database connection object
        
    Returns:
        dict: Dictionary containing access pattern analysis dataframes
    """
    try:
        # Get access frequency by hour of day
        hourly_access = db.query("""
            SELECT 
                EXTRACT(HOUR FROM to_timestamp(accessTime/1000)) as hour_of_day,
                COUNT(*) as access_count
            FROM 
                instances
            WHERE 
                accessTime IS NOT NULL
                AND accessTime > 86400000  -- Filter out dates before 1970-01-02
                AND accessTime < 4102444800000  -- Filter out dates after 2100-01-01
            GROUP BY 
                hour_of_day
            ORDER BY 
                hour_of_day
        """)
        
        # Get access frequency by day of week
        daily_access = db.query("""
            SELECT 
                EXTRACT(DOW FROM to_timestamp(accessTime/1000)) as day_of_week,
                COUNT(*) as access_count
            FROM 
                instances
            WHERE 
                accessTime IS NOT NULL
                AND accessTime > 86400000  -- Filter out dates before 1970-01-02
                AND accessTime < 4102444800000  -- Filter out dates after 2100-01-01
            GROUP BY 
                day_of_week
            ORDER BY 
                day_of_week
        """)
        
        # If data exists, replace day numbers with day names
        if not daily_access.empty and 'day_of_week' in daily_access.columns:
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            daily_access['day_name'] = daily_access['day_of_week'].apply(lambda x: day_names[int(x)] if x < 7 else f"Day {int(x)}")
        
        # Get time gap between creation and first access
        access_gap = db.query("""
            SELECT 
                CASE
                    WHEN (i.accessTime - o.createdAt) < 0 THEN 'Before Creation'
                    WHEN (i.accessTime - o.createdAt) = 0 THEN 'Same Time'
                    WHEN (i.accessTime - o.createdAt) < 3600000 THEN 'Within 1 Hour'
                    WHEN (i.accessTime - o.createdAt) < 86400000 THEN 'Within 1 Day'
                    WHEN (i.accessTime - o.createdAt) < 604800000 THEN 'Within 1 Week'
                    WHEN (i.accessTime - o.createdAt) < 2592000000 THEN 'Within 1 Month'
                    ELSE 'After 1+ Month'
                END as access_gap,
                COUNT(*) as count
            FROM 
                objects o
            JOIN 
                instances i ON o.objectId = i.objectId
            WHERE 
                o.createdAt IS NOT NULL
                AND i.accessTime IS NOT NULL
                AND o.createdAt > 86400000  -- Filter out dates before 1970-01-02
                AND o.createdAt < 4102444800000  -- Filter out dates after 2100-01-01
            GROUP BY 
                access_gap
            ORDER BY 
                CASE
                    WHEN access_gap = 'Before Creation' THEN 1
                    WHEN access_gap = 'Same Time' THEN 2
                    WHEN access_gap = 'Within 1 Hour' THEN 3
                    WHEN access_gap = 'Within 1 Day' THEN 4
                    WHEN access_gap = 'Within 1 Week' THEN 5
                    WHEN access_gap = 'Within 1 Month' THEN 6
                    WHEN access_gap = 'After 1+ Month' THEN 7
                    ELSE 8
                END
        """)
        
        return {
            'hourly': hourly_access,
            'daily': daily_access,
            'access_gap': access_gap
        }
    except Exception as e:
        print(f"Error analyzing access patterns: {e}")
        # Return empty DataFrames with expected structure
        return {
            'hourly': pd.DataFrame(columns=['hour_of_day', 'access_count']),
            'daily': pd.DataFrame(columns=['day_of_week', 'access_count', 'day_name']),
            'access_gap': pd.DataFrame(columns=['access_gap', 'count'])
        }


def plot_permission_distribution(perm_data, title="Permission Distribution", figsize=(10, 6)):
    """
    Create a visualization of permission distribution.
    
    Args:
        perm_data: DataFrame with permission distribution data
        title: Chart title
        figsize: Figure size tuple
        
    Returns:
        matplotlib.figure: Plot figure
    """
    if perm_data.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No permission data available", ha='center', va='center', fontsize=14)
        ax.set_title(title)
        return fig
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Define Aparavi brand colors for different permission types
    colors = {
        'Read & Write': '#EF4E0A',  # Aparavi orange
        'Read Only': '#56BBCC',     # Aparavi teal
        'Write Only': '#51565D',    # Aparavi gray
        'None': '#F9F9FB',          # Aparavi light bg
        'No Permissions': '#d43d00', # Darker Aparavi orange
        'Other': '#080A0D'          # Aparavi dark
    }
    
    # Create color list matching the data
    color_list = [colors.get(ptype, '#cccccc') for ptype in perm_data['permission_type']]
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        perm_data['count'], 
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=color_list
    )
    
    # Style the percentage labels
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')
    
    # Create legend with counts
    legend_labels = [f"{row['permission_type']} ({row['count']:,})" 
                     for _, row in perm_data.iterrows()]
    ax.legend(wedges, legend_labels, title="Permission Types", 
              loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    ax.set_title(title, fontsize=14)
    
    plt.tight_layout()
    return fig


def plot_access_heatmap(hourly_data, title="Document Access Patterns by Hour", figsize=(12, 8)):
    """
    Create a heatmap visualization of access patterns by hour.
    
    Args:
        hourly_data: DataFrame with hourly access data
        title: Chart title
        figsize: Figure size tuple
        
    Returns:
        matplotlib.figure: Plot figure
    """
    if hourly_data.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No access pattern data available", ha='center', va='center', fontsize=14)
        ax.set_title(title)
        return fig
    
    # Prepare data for 24-hour heatmap
    hours = np.arange(24)
    hour_labels = [f"{h:02d}:00" for h in hours]
    
    # Create full 24-hour dataframe
    full_hours = pd.DataFrame({'hour_of_day': hours})
    hourly_data = pd.merge(full_hours, hourly_data, on='hour_of_day', how='left').fillna(0)
    
    # Reshape for heatmap (24 hours x 1 row)
    heatmap_data = hourly_data['access_count'].values.reshape(1, 24)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap with custom colormap (Aparavi orange to teal)
    cmap = sns.color_palette("YlOrRd", as_cmap=True)
    sns.heatmap(heatmap_data, cmap=cmap, annot=True, fmt="g", linewidths=.5, ax=ax)
    
    # Set labels
    ax.set_title(title, fontsize=14)
    ax.set_yticks([])  # No y-tick labels since we only have one row
    ax.set_xticks(np.arange(24) + 0.5)
    ax.set_xticklabels(hour_labels, rotation=45)
    ax.set_xlabel('Hour of Day', fontsize=12)
    
    plt.tight_layout()
    return fig


def plot_access_gap(gap_data, title="Time Between Creation and First Access", figsize=(10, 6)):
    """
    Create a visualization of the gap between document creation and first access.
    
    Args:
        gap_data: DataFrame with access gap data
        title: Chart title
        figsize: Figure size tuple
        
    Returns:
        matplotlib.figure: Plot figure
    """
    if gap_data.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No access gap data available", ha='center', va='center', fontsize=14)
        ax.set_title(title)
        return fig
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create horizontal bar chart with Aparavi brand colors
    colors = ['#EF4E0A', '#56BBCC', '#51565D', '#080A0D', '#F9F9FB', '#d43d00', '#cccccc']
    bars = ax.barh(gap_data['access_gap'], gap_data['count'], 
                  color=colors[:len(gap_data)])
    
    # Add value labels to the bars
    for i, bar in enumerate(bars):
        ax.text(
            bar.get_width() + (max(gap_data['count']) * 0.02), 
            bar.get_y() + bar.get_height()/2, 
            f"{gap_data['count'].iloc[i]:,}",
            va='center'
        )
    
    # Set title and labels
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('Number of Documents', fontsize=12)
    ax.set_ylabel('Time Gap', fontsize=12)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig
