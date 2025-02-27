"""
Aparavi Reporting Dashboard - Main Application

This is the main entry point for the Aparavi Reporting Dashboard, a Streamlit application 
that provides comprehensive analytics and visualizations for document management data
from the Aparavi Data Suite.

The application is built using Streamlit for the UI, DuckDB for data processing, and Plotly for
visualizations. It features a modular architecture with separate components for database
handling, visualizations, and specialized analysis.

Key features:
- Interactive dashboard with multiple report types
- Professional Aparavi branding throughout the interface
- Comprehensive document analytics
- Storage and permission analysis
- Folder structure visualization
- Metadata analysis across different file types
- Export capabilities for further analysis

The Aparavi branding is implemented through:
1. Centralized configuration in config.py
2. Custom CSS for styling
3. Aparavi logo integration in header and favicon
4. Consistent color scheme using Aparavi brand colors
5. Professional, emoji-free interface design
6. Branded messaging and terminology
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import json
import plotly.express as px
import base64
from PIL import Image

# Import configuration
import config

# Import modules
from modules.database import DatabaseManager
from modules.visualizations import (
    plot_bar_chart, plot_time_series, plot_pie_chart, 
    plot_histogram, format_size_bytes
)
from modules.folder_analysis import (
    process_folder_paths, aggregate_by_folder,
    create_sunburst_chart, create_treemap_chart,
    find_top_folders, format_size, create_hierarchical_bar_chart
)
from modules.metadata_analysis import render_metadata_analysis_dashboard

# Get base64 encoded image for favicon
def get_base64_encoded_image(image_path):
    """Get base64 encoded image for embedding in HTML"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Create the favicon using Aparavi's logo
# This replaces the default Streamlit logo with the Aparavi branding in the browser tab
favicon = get_base64_encoded_image(os.path.join(config.IMAGES_DIR, "logo-48x48.png"))

# Set page configuration with Aparavi branding
st.set_page_config(
    page_title=config.APP_TITLE,  # Sets browser tab title to "Aparavi Reporting Dashboard"
    page_icon=f"data:image/png;base64,{favicon}",  # Sets Aparavi logo as favicon
    layout=config.PAGE_LAYOUT,  # Wide layout for better visualization
    initial_sidebar_state=config.SIDEBAR_STATE  # Start with sidebar expanded
)

# Custom CSS to implement Aparavi branding and styling throughout the application
# This CSS overrides the default Streamlit styling with Aparavi's brand colors and UI elements
st.markdown("""
<style>
    /* Main header styling using Aparavi brand colors */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #080A0D;  /* Aparavi dark color for text */
        margin-bottom: 1rem;
    }
    
    /* Header container for the Aparavi logo */
    .aparavi-header {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    /* Aparavi logo styling */
    .aparavi-logo {
        max-width: 255px;
        margin-bottom: 1rem;
    }
    
    /* Report description styling with Aparavi brand colors */
    .report-header {
        background-color: #F9F9FB;  /* Aparavi light background */
        padding: 1.5rem;
        border-radius: 5px;
        border-left: 5px solid #EF4E0A;  /* Aparavi orange as accent */
        margin-bottom: 2rem;
    }
    
    /* Section headers with Aparavi teal accents */
    .section-header {
        color: #51565D;  /* Aparavi gray for text */
        border-bottom: 2px solid #56BBCC;  /* Aparavi teal for section dividers */
        padding-bottom: 0.5rem;
    }
    
    /* Buttons styled with Aparavi primary orange */
    .stButton>button {
        background-color: #EF4E0A;  /* Aparavi primary orange */
        color: white;
    }
    
    /* Button hover state with slightly darker orange */
    .stButton>button:hover {
        background-color: #d43d00;  /* Darker shade of Aparavi orange */
        color: white;
    }
    
    /* Metric container styling */
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #e8f4f8;
        border-radius: 5px;
        padding: 15px;
        margin: 15px 0;
    }
    .st-bx {
        background-color: #ffffff;
    }
    footer {font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# Cache connection to avoid reconnection on each rerun
@st.cache_resource
def get_database_connection(db_path):
    """Get a cached database connection"""
    return DatabaseManager(db_path)

def render_header():
    """
    Render application header and description
    
    The header is a critical component of the Aparavi branding implementation.
    It displays the Aparavi logo prominently at the top of the page, followed by
    the application title and a welcome message that references Aparavi Data Suite.
    The styling uses Aparavi's brand colors with appropriate spacing and typography.
    """
    # Display Aparavi logo at the top of the application
    # This is the primary branding element visible to users
    st.markdown(f"""
    <div class="aparavi-header">
        <img src="data:image/png;base64,{get_base64_encoded_image(config.APP_LOGO)}" class="aparavi-logo" alt="Aparavi Logo">
    </div>
    """, unsafe_allow_html=True)
    
    # Display application title with Aparavi branding
    # Using custom CSS class 'main-header' styled with Aparavi's typography and colors
    st.markdown(f"<h1 class='main-header'>{config.APP_TITLE}</h1>", unsafe_allow_html=True)
    
    # Welcome message with explicit reference to Aparavi Data Suite
    # Using the report-header class styled with Aparavi's colors and border accents
    st.markdown("""
    <div class="report-header">
    <p>Welcome to the Aparavi Reporting Dashboard, providing comprehensive analytics and visualization of document management data from Aparavi Data Suite. 
    Analyze file types, storage patterns, permissions, and more to gain insights into your document ecosystem.</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """
    Render sidebar with navigation and options
    
    The sidebar reinforces the Aparavi branding with a smaller logo at the top,
    followed by navigation options and an "About" section that further references
    the Aparavi Data Suite. The styling is consistent with the main dashboard, using
    Aparavi's brand colors and typography.
    """
    with st.sidebar:
        # Logo in sidebar for consistent branding across all navigation states
        # Using the square version of the Aparavi logo for better fit in the sidebar
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <img src="data:image/png;base64,{get_base64_encoded_image(config.IMAGES_DIR / 'logo-90x90.png')}" width="90" alt="Aparavi Logo">
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("## Navigation")
        
        # Database selector
        db_path = st.text_input(
            "Database Path", 
            value=config.DEFAULT_DB_PATH,
            help="Enter the path to your DuckDB database file"
        )
        
        # Report selection
        report_options = list(config.REPORTS.keys())
        report_labels = [f"{config.REPORTS[r]['title']}" for r in report_options]
        
        selected_report_label = st.radio("Select Report", report_labels)
        selected_report = report_options[report_labels.index(selected_report_label)]
        
        # Options
        st.markdown("## Options")
        
        # Chart style
        chart_style = st.selectbox(
            "Chart Style",
            ["ggplot", "seaborn-darkgrid", "seaborn-deep", "fivethirtyeight", "dark_background"],
            index=0
        )
        
        # Export options
        st.markdown("## Export")
        export_format = st.selectbox("Export Format", config.EXPORT_FORMATS)
        
        # About section
        st.markdown("---")
        st.markdown("### About")
        st.markdown(f"""
        **Aparavi Reporting Dashboard**  
        Version 1.1.0  
        {datetime.now().year} - Aparavi Data Suite
        """)
        
    return {
        "db_path": db_path,
        "selected_report": selected_report,
        "chart_style": chart_style,
        "export_format": export_format
    }

def render_overview_report(db):
    """Render overview dashboard with key metrics"""
    st.markdown("<h2 class='section-header'>Dashboard Overview</h2>", unsafe_allow_html=True)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Total objects
    total_objects = db.get_row_count('objects')
    with col1:
        st.metric("Total Documents", f"{total_objects:,}")
    
    # Total storage
    storage_stats = db.get_storage_stats()
    if storage_stats:
        with col2:
            total_size = format_size_bytes(storage_stats["total_size"])
            st.metric("Total Storage", total_size)
    
        with col3:
            avg_size = format_size_bytes(storage_stats["avg_size"])
            st.metric("Average Size", avg_size)
    
    # Total instances
    total_instances = db.get_row_count('instances')
    with col4:
        st.metric("Total Instances", f"{total_instances:,}")
    
    # Charts row
    st.markdown("<h3 class='subsection-header'>Document Analysis</h3>", unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # File extension distribution
        extension_counts = db.query("""
            SELECT 
                COALESCE(extension, 'No Extension') as ext,
                COUNT(*) as count
            FROM objects
            GROUP BY ext
            ORDER BY count DESC
            LIMIT 10
        """)
        
        if not extension_counts.empty:
            fig = plot_bar_chart(
                extension_counts, 
                'count', 'ext', 
                'Top File Extensions',
                'Count', 'Extension',
                figsize=(10, 6),
                horizontal=True
            )
            st.pyplot(fig)
    
    with chart_col2:
        # Object creation over time
        creation_over_time = db.query("""
            SELECT 
                DATE_TRUNC('month', to_timestamp(createdAt/1000)) as month,
                COUNT(*) as count
            FROM objects
            WHERE createdAt IS NOT NULL
            GROUP BY month
            ORDER BY month
        """)
        
        if not creation_over_time.empty:
            # Convert to pandas datetime if needed
            creation_over_time['month'] = pd.to_datetime(creation_over_time['month'])
            
            fig = plot_time_series(
                creation_over_time,
                'month', 'count',
                'Document Creation Over Time',
                'Date', 'Number of Documents',
                figsize=(10, 6)
            )
            st.pyplot(fig)
    
    # Storage distribution
    st.markdown("<h3 class='subsection-header'>Storage Analysis</h3>", unsafe_allow_html=True)
    
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        # Size distribution
        size_distribution = db.query("""
            SELECT 
                CASE
                    WHEN size < 1024 THEN 'Under 1KB'
                    WHEN size < 1024*1024 THEN '1KB-1MB'
                    WHEN size < 1024*1024*10 THEN '1MB-10MB'
                    WHEN size < 1024*1024*100 THEN '10MB-100MB'
                    ELSE 'Over 100MB'
                END as size_range,
                COUNT(*) as count
            FROM instances
            WHERE size IS NOT NULL
            GROUP BY size_range
            ORDER BY 
                CASE 
                    WHEN size_range = 'Under 1KB' THEN 1
                    WHEN size_range = '1KB-1MB' THEN 2
                    WHEN size_range = '1MB-10MB' THEN 3
                    WHEN size_range = '10MB-100MB' THEN 4
                    WHEN size_range = 'Over 100MB' THEN 5
                END
        """)
        
        if not size_distribution.empty:
            fig = plot_pie_chart(
                size_distribution,
                'count', 'size_range',
                'Document Size Distribution',
                figsize=(8, 8)
            )
            st.pyplot(fig)
    
    with chart_col4:
        # Service distribution
        try:
            service_distribution = db.query("""
                SELECT 
                    s.name as service_name,
                    COUNT(*) as instance_count
                FROM instances i
                JOIN services s ON i.serviceId = s.serviceId
                GROUP BY s.name
                ORDER BY instance_count DESC
            """)
            
            if not service_distribution.empty:
                fig = plot_bar_chart(
                    service_distribution,
                    'instance_count', 'service_name',
                    'Document Distribution by Service',
                    'Count', 'Service',
                    figsize=(10, 6),
                    horizontal=True
                )
                st.pyplot(fig)
        except Exception as e:
            st.warning(f"Could not generate service distribution: {e}")

def render_objects_report(db):
    """Render objects analysis report"""
    st.markdown("<h2 class='section-header'>Objects Analysis</h2>", unsafe_allow_html=True)
    
    # Total objects
    total_objects = db.get_row_count('objects')
    st.metric("Total Documents", f"{total_objects:,}")
    
    # File extensions
    st.markdown("<h3 class='subsection-header'>File Types</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # File extension distribution
        extension_counts = db.query("""
            SELECT 
                COALESCE(extension, 'No Extension') as ext,
                COUNT(*) as count
            FROM objects
            GROUP BY ext
            ORDER BY count DESC
            LIMIT 15
        """)
        
        if not extension_counts.empty:
            st.dataframe(extension_counts, use_container_width=True)
    
    with col2:
        # Visualize extension distribution
        if not extension_counts.empty:
            # Limit to top 10 for better visualization
            top_extensions = extension_counts.head(10)
            
            fig = plot_bar_chart(
                top_extensions, 
                'count', 'ext', 
                'Top File Extensions',
                'Count', 'Extension',
                figsize=(10, 6),
                horizontal=True
            )
            st.pyplot(fig)
    
    # Object creation over time
    st.markdown("<h3 class='subsection-header'>Document Timeline</h3>", unsafe_allow_html=True)
    
    # Creation timeline
    creation_over_time = db.query("""
        SELECT 
            DATE_TRUNC('month', to_timestamp(createdAt/1000)) as month,
            COUNT(*) as count
        FROM objects
        WHERE createdAt IS NOT NULL
        GROUP BY month
        ORDER BY month
    """)
    
    if not creation_over_time.empty:
        # Convert to pandas datetime if needed
        creation_over_time['month'] = pd.to_datetime(creation_over_time['month'])
        
        fig = plot_time_series(
            creation_over_time,
            'month', 'count',
            'Document Creation Timeline',
            'Date', 'Number of Documents',
            figsize=(12, 6)
        )
        st.pyplot(fig)
    
    # Tags analysis
    st.markdown("<h3 class='subsection-header'>Tags Analysis</h3>", unsafe_allow_html=True)
    
    try:
        # Tag distribution
        tag_distribution = db.query("""
            SELECT 
                json_extract_string(value, '$.key') as tag_key,
                COUNT(*) as count
            FROM objects, 
                 json_each(CASE WHEN tags = '' OR tags IS NULL THEN '[]' ELSE tags END) 
            GROUP BY tag_key
            ORDER BY count DESC
            LIMIT 20
        """)
        
        if not tag_distribution.empty and len(tag_distribution) > 0:
            st.dataframe(tag_distribution, use_container_width=True)
            
            # Visualize tag distribution
            fig = plot_bar_chart(
                tag_distribution.head(10), 
                'count', 'tag_key', 
                'Top Tags',
                'Count', 'Tag',
                figsize=(10, 6),
                horizontal=True
            )
            st.pyplot(fig)
        else:
            st.info("No tags found in the objects table")
    except Exception as e:
        st.warning(f"Error analyzing tags: {e}")

def render_instances_report(db):
    """Render instances and storage analysis report"""
    st.markdown("<h2 class='section-header'>Instances & Storage</h2>", unsafe_allow_html=True)
    
    # Storage statistics
    st.markdown("<h3 class='subsection-header'>Storage Statistics</h3>", unsafe_allow_html=True)
    
    storage_stats = db.get_storage_stats()
    if storage_stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_size = format_size_bytes(storage_stats["total_size"])
            st.metric("Total Storage", total_size)
        
        with col2:
            avg_size = format_size_bytes(storage_stats["avg_size"])
            st.metric("Average Size", avg_size)
        
        with col3:
            min_size = format_size_bytes(storage_stats["min_size"])
            st.metric("Min Size", min_size)
        
        with col4:
            max_size = format_size_bytes(storage_stats["max_size"])
            st.metric("Max Size", max_size)
    
    # Size distribution visualization
    size_distribution = db.query("""
        SELECT 
            CASE
                WHEN size < 1024 THEN 'Under 1KB'
                WHEN size < 1024*1024 THEN '1KB-1MB'
                WHEN size < 1024*1024*10 THEN '1MB-10MB'
                WHEN size < 1024*1024*100 THEN '10MB-100MB'
                ELSE 'Over 100MB'
            END as size_range,
            COUNT(*) as count
        FROM instances
        WHERE size IS NOT NULL
        GROUP BY size_range
        ORDER BY 
            CASE 
                WHEN size_range = 'Under 1KB' THEN 1
                WHEN size_range = '1KB-1MB' THEN 2
                WHEN size_range = '1MB-10MB' THEN 3
                WHEN size_range = '10MB-100MB' THEN 4
                WHEN size_range = 'Over 100MB' THEN 5
            END
    """)
    
    if not size_distribution.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(size_distribution, use_container_width=True)
        
        with col2:
            fig = plot_pie_chart(
                size_distribution,
                'count', 'size_range',
                'Document Size Distribution',
                figsize=(8, 8)
            )
            st.pyplot(fig)
    
    # Service distribution
    st.markdown("<h3 class='subsection-header'>Service Distribution</h3>", unsafe_allow_html=True)
    
    try:
        service_distribution = db.query("""
            SELECT 
                s.name as service_name,
                COUNT(*) as instance_count,
                SUM(i.size) as total_size
            FROM instances i
            JOIN services s ON i.serviceId = s.serviceId
            GROUP BY s.name
            ORDER BY instance_count DESC
        """)
        
        if not service_distribution.empty:
            # Add formatted size column
            service_distribution['formatted_size'] = service_distribution['total_size'].apply(format_size_bytes)
            
            st.dataframe(service_distribution, use_container_width=True)
            
            # Visualize service distribution
            fig = plot_bar_chart(
                service_distribution, 
                'instance_count', 'service_name', 
                'Document Distribution by Service',
                'Count', 'Service',
                figsize=(10, 6),
                horizontal=True
            )
            st.pyplot(fig)
    except Exception as e:
        st.warning(f"Error analyzing services: {e}")

def render_folder_structure_report(db):
    """Render folder structure analysis report"""
    st.markdown("<h2 class='section-header'>Folder Structure</h2>", unsafe_allow_html=True)
    
    # Query parent paths data
    parent_paths_df = db.query("""
        SELECT * FROM parentPaths
        WHERE parentPath IS NOT NULL AND parentPath != ''
    """)
    
    if parent_paths_df.empty:
        st.warning("No folder structure data found in the database.")
        return
    
    # Get objects with parent paths
    objects_with_paths = db.query("""
        SELECT 
            o.objectId,
            o.name,
            o.extension,
            p.parentPath,
            i.size
        FROM 
            objects o
        JOIN
            parentPaths p ON o.parentId = p.parentId
        LEFT JOIN
            instances i ON o.objectId = i.objectId
        WHERE 
            p.parentPath IS NOT NULL AND p.parentPath != ''
    """)
    
    if objects_with_paths.empty:
        st.warning("No objects with folder paths found in the database.")
        return
    
    # Process folder paths to create hierarchy
    processed_df, max_depth = process_folder_paths(objects_with_paths, 'parentPath')
    
    # Sidebar options for folder analysis
    st.sidebar.markdown("### Folder Analysis Options")
    
    # Depth control
    depth_level = st.sidebar.slider(
        "Max Folder Depth", 
        min_value=1, 
        max_value=max_depth, 
        value=min(3, max_depth)
    )
    
    # Metric selection
    metric = st.sidebar.radio(
        "Analysis Metric",
        ["Size", "Count"],
        index=0
    )
    
    # Aggregation
    aggregated_df = aggregate_by_folder(
        objects_with_paths, 
        size_column='size', 
        path_column='parentPath',
        max_depth=depth_level
    )
    
    # Display stats
    total_size = aggregated_df['size'].sum() if not aggregated_df.empty else 0
    total_count = aggregated_df['count'].sum() if not aggregated_df.empty else 0
    
    st.markdown("<h3 class='subsection-header'>Folder Structure Summary</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Folders", len(aggregated_df) if not aggregated_df.empty else 0)
    with col2:
        st.metric("Total Size", format_size(total_size))
    with col3:
        st.metric("Total Files", f"{total_count:,}")
    
    # Create visualizations
    st.markdown("<h3 class='subsection-header'>Folder Structure Visualization</h3>", unsafe_allow_html=True)
    
    # Select visualization type
    viz_type = st.radio(
        "Visualization Type", 
        ["Sunburst Chart", "Treemap", "Bar Chart"],
        horizontal=True
    )
    
    if not aggregated_df.empty:
        # Prepare path columns for visualization
        path_columns = ['full_path']
        
        # Value column based on metric selection
        value_column = 'size' if metric == 'Size' else 'count'
        
        # Create visualization based on selection
        if viz_type == "Sunburst Chart":
            fig = create_sunburst_chart(
                aggregated_df,
                path_columns=path_columns,
                values_column=value_column,
                title=f"Folder Structure - {metric} Distribution",
                color_scale='viridis' if metric == 'Size' else 'blues'
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Treemap":
            fig = create_treemap_chart(
                aggregated_df,
                path_columns=path_columns,
                values_column=value_column,
                title=f"Folder Structure - {metric} Distribution",
                color_scale='viridis' if metric == 'Size' else 'blues'
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Bar Chart":
            # Get top folders
            top_n = st.slider("Number of Top Folders to Show", 5, 30, 15)
            top_folders = find_top_folders(aggregated_df, value_column, n=top_n)
            
            fig = create_hierarchical_bar_chart(
                top_folders,
                category_column='full_path',
                value_column=value_column,
                title=f"Top {top_n} Folders by {metric}",
                color_scale='viridis' if metric == 'Size' else 'blues'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for visualization after applying filters.")

def render_storage_sunburst_report(db):
    """Render storage sunburst visualization report"""
    st.markdown("<h2 class='section-header'>Storage Sunburst</h2>", unsafe_allow_html=True)
    
    # Query objects with size data
    objects_with_size = db.query("""
        SELECT 
            o.objectId,
            o.name,
            o.extension,
            p.parentPath,
            i.size
        FROM 
            objects o
        JOIN
            parentPaths p ON o.parentId = p.parentId
        JOIN
            instances i ON o.objectId = i.objectId
        WHERE 
            p.parentPath IS NOT NULL AND 
            p.parentPath != '' AND
            i.size IS NOT NULL AND
            i.size > 0
    """)
    
    if objects_with_size.empty:
        st.warning("No objects with size data found in the database.")
        return
    
    # Unit selection for size display
    size_unit = st.sidebar.selectbox(
        "Size Unit", 
        ["Bytes", "KB", "MB", "GB"],
        index=2  # Default to MB
    )
    
    # Convert size based on selected unit
    if size_unit == "Bytes":
        objects_with_size["Size_Converted"] = objects_with_size["size"]
        size_label = "Bytes"
    elif size_unit == "KB":
        objects_with_size["Size_Converted"] = objects_with_size["size"] / 1024
        size_label = "KB"
    elif size_unit == "MB":
        objects_with_size["Size_Converted"] = objects_with_size["size"] / (1024 * 1024)
        size_label = "MB"
    else:  # GB
        objects_with_size["Size_Converted"] = objects_with_size["size"] / (1024 * 1024 * 1024)
        size_label = "GB"
    
    # Process folder paths
    processed_df, max_depth = process_folder_paths(objects_with_size, 'parentPath')
    
    # Depth control
    depth_level = st.sidebar.slider(
        "Max Folder Depth (Storage)", 
        min_value=1, 
        max_value=max_depth, 
        value=min(3, max_depth)
    )
    
    # Create full path column with proper depth levels
    path_columns = [f'level_{i+1}' for i in range(depth_level)]
    
    # Create sunburst chart
    fig = px.sunburst(
        processed_df,
        path=path_columns,
        values="Size_Converted",
        color="Size_Converted",
        color_continuous_scale="viridis",
        title=f"Storage Usage by Folder ({size_label})"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display statistics
    st.markdown("<h3 class='subsection-header'>Storage Statistics</h3>", unsafe_allow_html=True)
    
    total_size = objects_with_size["Size_Converted"].sum()
    max_size = objects_with_size["Size_Converted"].max()
    avg_size = objects_with_size["Size_Converted"].mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Storage", f"{total_size:.2f} {size_label}")
    with col2:
        st.metric("Largest File", f"{max_size:.2f} {size_label}")
    with col3:
        st.metric("Average File Size", f"{avg_size:.2f} {size_label}")
    
    # Top folders by storage
    st.markdown("<h3 class='subsection-header'>Top Folders by Storage</h3>", unsafe_allow_html=True)
    
    folder_storage = objects_with_size.groupby('parentPath')['Size_Converted'].sum().reset_index()
    folder_storage = folder_storage.sort_values('Size_Converted', ascending=False).head(10)
    
    st.dataframe(
        folder_storage.rename(columns={'parentPath': 'Folder Path', 'Size_Converted': f'Size ({size_label})'}),
        use_container_width=True
    )

def render_file_distribution_report(db):
    """Render file distribution analysis report"""
    st.markdown("<h2 class='section-header'>File Distribution</h2>", unsafe_allow_html=True)
    
    # Query file extension data
    file_extensions = db.query("""
        SELECT 
            COALESCE(extension, 'Unknown') as extension,
            COUNT(*) as count,
            p.parentPath
        FROM 
            objects o
        LEFT JOIN
            parentPaths p ON o.parentId = p.parentId
        GROUP BY 
            extension, p.parentPath
        ORDER BY 
            count DESC
    """)
    
    if file_extensions.empty:
        st.warning("No file extension data found in the database.")
        return
    
    # File type categories
    file_categories = {
        'documents': ['doc', 'docx', 'pdf', 'txt', 'rtf', 'odt', 'md', 'xps'],
        'spreadsheets': ['xls', 'xlsx', 'csv', 'ods', 'tsv', 'numbers'],
        'presentations': ['ppt', 'pptx', 'odp', 'key'],
        'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'heic', 'heif'],
        'audio': ['mp3', 'wav', 'aac', 'ogg', 'flac', 'wma', 'm4a'],
        'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v'],
        'archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
        'code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'go', 'php', 'rb', 'pl', 'rs', 'ts'],
        'data': ['json', 'xml', 'yaml', 'yml', 'toml', 'sql', 'db', 'sqlite'],
        'executables': ['exe', 'app', 'msi', 'dll', 'so', 'bin', 'dmg']
    }
    
    # Categorize extensions
    def categorize_extension(ext):
        ext = ext.lower().replace('.', '')
        for category, extensions in file_categories.items():
            if ext in extensions:
                return category
        return 'other'
    
    file_extensions['category'] = file_extensions['extension'].apply(categorize_extension)
    
    # Metrics by category
    category_counts = file_extensions.groupby('category')['count'].sum().reset_index()
    category_counts = category_counts.sort_values('count', ascending=False)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='subsection-header'>Files by Category</h3>", unsafe_allow_html=True)
        
        fig = px.pie(
            category_counts, 
            values='count', 
            names='category',
            title='File Distribution by Category',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("<h3 class='subsection-header'>Top File Extensions</h3>", unsafe_allow_html=True)
        
        top_extensions = file_extensions.groupby('extension')['count'].sum().reset_index()
        top_extensions = top_extensions.sort_values('count', ascending=False).head(10)
        
        fig = px.bar(
            top_extensions,
            x='extension',
            y='count',
            title='Top 10 File Extensions',
            color='count',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # File distribution by folder
    st.markdown("<h3 class='subsection-header'>File Type Distribution by Folder</h3>", unsafe_allow_html=True)
    
    # Group by folder and category
    folder_category = file_extensions.groupby(['parentPath', 'category'])['count'].sum().reset_index()
    
    # Get top folders by file count
    top_folders = folder_category.groupby('parentPath')['count'].sum().sort_values(ascending=False).head(5).index.tolist()
    
    # Filter for top folders
    top_folder_data = folder_category[folder_category['parentPath'].isin(top_folders)]
    
    if not top_folder_data.empty:
        fig = px.bar(
            top_folder_data,
            x='parentPath',
            y='count',
            color='category',
            title='File Type Distribution in Top Folders',
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough folder data to visualize distribution.")

def render_metadata_analysis_report(db):
    """Render metadata analysis report"""
    report_info = config.REPORTS["metadata_analysis"]
    st.markdown(f"<h2 class='section-header'>{report_info['title']}</h2>", unsafe_allow_html=True)
    st.markdown(report_info['description'])
    
    # Call the render function from the metadata_analysis module
    render_metadata_analysis_dashboard(db)

def render_report(db, selected_report):
    """Render the selected report"""
    if selected_report == "overview":
        render_overview_report(db)
    elif selected_report == "objects":
        render_objects_report(db)
    elif selected_report == "instances":
        render_instances_report(db)
    elif selected_report == "folder_structure":
        render_folder_structure_report(db)
    elif selected_report == "storage_sunburst":
        render_storage_sunburst_report(db)
    elif selected_report == "file_distribution":
        render_file_distribution_report(db)
    elif selected_report == "metadata_analysis":
        render_metadata_analysis_report(db)
    else:
        # Display placeholder for other reports
        report_info = config.REPORTS[selected_report]
        st.markdown(f"<h2 class='section-header'>{report_info['title']}</h2>", unsafe_allow_html=True)
        st.markdown(report_info['description'])
        st.info("This report is under development and will be available in a future release.")

def main():
    """Main application entry point"""
    # Render header
    render_header()
    
    # Render sidebar and get options
    options = render_sidebar()
    
    # Connect to database
    try:
        db = get_database_connection(options["db_path"])
        
        # Check connection
        tables = db.list_tables()
        if not tables:
            st.error("Could not retrieve tables from the database. Please check the database path and try again.")
            return
        
        # Render the selected report
        render_report(db, options["selected_report"])
        
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        st.info("Please check that the database path is correct and that the file exists.")

if __name__ == "__main__":
    main()
