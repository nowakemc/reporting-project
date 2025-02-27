import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import base64
from io import BytesIO
import time
from datetime import datetime
import re
import os
from collections import Counter, defaultdict

# Set page config
st.set_page_config(
    layout="wide",
    page_title="🔍 File Explorer Visualization",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'file_data_loaded' not in st.session_state:
    st.session_state.file_data_loaded = False
    st.session_state.file_extensions = []
    st.session_state.creation_dates = []
    st.session_state.folder_depth = 3
    st.session_state.size_unit = "MB"
    st.session_state.selected_tab = "Folder Structure"

# Helper functions
def convert_size(size_bytes, unit="MB"):
    """Convert size from bytes to specified unit"""
    if pd.isna(size_bytes):
        return 0
        
    if unit == "Bytes":
        return size_bytes
    elif unit == "KB":
        return size_bytes / 1024
    elif unit == "MB":
        return size_bytes / (1024 * 1024)
    elif unit == "GB":
        return size_bytes / (1024 * 1024 * 1024)
    else:
        return size_bytes

def extract_extension(filename):
    """Extract file extension from filename"""
    if pd.isna(filename) or filename == '':
        return "unknown"
        
    parts = str(filename).split('.')
    if len(parts) > 1 and parts[-1]:
        return parts[-1].lower()
    return "no_extension"

def parse_datetime(dt_str):
    """Parse datetime from string with error handling"""
    if pd.isna(dt_str) or dt_str == 'nan' or dt_str == '':
        return None
        
    try:
        # Try common formats
        for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        
        # If all fail, return None
        return None
    except:
        return None

def get_file_age_days(dt_str, reference_date=None):
    """Calculate file age in days"""
    if reference_date is None:
        reference_date = datetime.now()
        
    dt = parse_datetime(dt_str)
    if dt is None:
        return None
        
    delta = reference_date - dt
    return delta.days

def process_folder_path(path):
    """Process folder path into components"""
    if pd.isna(path) or path == '':
        return []
        
    # Convert to string if needed
    path = str(path)
    
    # Remove leading/trailing slashes and split
    clean_path = path.strip('/')
    if not clean_path:
        return []
    return clean_path.split('/')

def aggregate_by_folder(df):
    """Aggregate file data by folder"""
    # Ensure we have a valid dataframe
    if df is None or df.empty:
        st.error("No valid data to aggregate into folders")
        return pd.DataFrame({'parentPath': ['root'], 
                           'folder_size': [0], 
                           'file_count': [0], 
                           'avg_file_size': [0],
                           'deleted_count': [0]})
    
    # Prepare date columns if they exist - convert to consistent type
    date_columns = ['createTime', 'modifyTime']
    for col in date_columns:
        if col in df.columns:
            # Convert all values to strings first to ensure consistent types
            df[col] = df[col].astype(str)
    
    # Group by parentPath with safe aggregations
    try:
        folder_stats = df.groupby('parentPath').agg(
            folder_size=('size', 'sum'),
            file_count=('name', 'count'),
            avg_file_size=('size', 'mean')
        ).reset_index()
        
        # Add time-based stats only if columns exist
        if 'createTime' in df.columns:
            oldest = df.groupby('parentPath')['createTime'].min().reset_index()
            newest = df.groupby('parentPath')['createTime'].max().reset_index()
            folder_stats = folder_stats.merge(oldest, on='parentPath', how='left')
            folder_stats = folder_stats.merge(newest, on='parentPath', how='left', suffixes=('', '_newest'))
            folder_stats.rename(columns={'createTime': 'oldest_file', 'createTime_newest': 'newest_file'}, inplace=True)
        
        # Add deleted count if column exists
        if 'isDeleted' in df.columns:
            deleted = df.groupby('parentPath')['isDeleted'].apply(lambda x: (x == 1).sum()).reset_index()
            folder_stats = folder_stats.merge(deleted, on='parentPath', how='left')
            folder_stats.rename(columns={'isDeleted': 'deleted_count'}, inplace=True)
            folder_stats['deleted_count'] = folder_stats['deleted_count'].fillna(0).astype(int)
        else:
            folder_stats['deleted_count'] = 0
    
    except Exception as e:
        st.error(f"Error aggregating folder data: {str(e)}")
        st.exception(e)
        # Return minimal dataframe to prevent application crash
        return pd.DataFrame({'parentPath': df['parentPath'].unique() if 'parentPath' in df.columns else ['root'], 
                           'folder_size': [0] * (len(df['parentPath'].unique()) if 'parentPath' in df.columns else 1), 
                           'file_count': [0] * (len(df['parentPath'].unique()) if 'parentPath' in df.columns else 1), 
                           'avg_file_size': [0] * (len(df['parentPath'].unique()) if 'parentPath' in df.columns else 1),
                           'deleted_count': [0] * (len(df['parentPath'].unique()) if 'parentPath' in df.columns else 1)})
    
    # Add folder depth
    try:
        folder_stats['folder_components'] = folder_stats['parentPath'].apply(process_folder_path)
        folder_stats['folder_depth'] = folder_stats['folder_components'].apply(len)
    except Exception as e:
        st.warning(f"Error calculating folder depth: {str(e)}")
        # Provide default values
        folder_stats['folder_components'] = [[]] * len(folder_stats)
        folder_stats['folder_depth'] = [0] * len(folder_stats)
    
    return folder_stats

def prepare_folder_hierarchy(folder_stats, max_depth=10):
    """Prepare folder hierarchy for visualization"""
    # Check if folder_stats is None or empty
    if folder_stats is None:
        st.error("No folder statistics available to create hierarchy")
        # Return a minimal valid DataFrame
        return pd.DataFrame({'parentPath': ['root'], 
                          'folder_size': [0], 
                          'file_count': [0],
                          'folder_depth': [1],
                          'Level 1': ['root']})
    
    # Create folder level columns
    try:
        max_actual_depth = max(folder_stats['folder_depth']) if not folder_stats.empty else 0
        for i in range(min(max_actual_depth, max_depth)):
            folder_stats[f'Level {i+1}'] = folder_stats['folder_components'].apply(
                lambda x: x[i] if len(x) > i else ""
            )
    except Exception as e:
        st.error(f"Error creating folder hierarchy: {str(e)}")
        # Create a single level as fallback
        folder_stats['Level 1'] = folder_stats['parentPath'].apply(
            lambda x: x.split('/')[-1] if x and '/' in x else x
        )
    
    return folder_stats

# App title and description
st.title("🔍 File Explorer Visualization")
st.markdown("Upload your file data CSV to analyze and visualize file distribution.")

# Initialize empty DataFrame in case of early errors
df = pd.DataFrame()
folder_stats = pd.DataFrame()
folder_hierarchy = pd.DataFrame()

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload your file data CSV", type=["csv"])

if uploaded_file:
    try:
        # Load data and provide fallback in case of errors
        with st.spinner("Processing file data..."):
            start_time = time.time()
            try:
                df = pd.read_csv(uploaded_file)
                st.sidebar.success(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                st.exception(e)
                # Create a minimal DataFrame to allow the app to continue
                df = pd.DataFrame({
                    'name': ['example.txt'],
                    'parentPath': ['root'],
                    'size': [0]
                })
                st.warning("Created a minimal dataset to allow visualization")

            
            # Check required columns
            required_columns = {'name', 'parentPath', 'size'}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                st.error(f"Missing required columns: {', '.join(missing)}")
                
                # Add missing columns with default values to allow visualization
                for col in missing:
                    if col == 'name':
                        df['name'] = [f"file_{i}" for i in range(len(df))]
                    elif col == 'parentPath':
                        df['parentPath'] = 'root'
                    elif col == 'size':
                        df['size'] = 0
                
                st.warning("Added default values for missing columns to allow basic visualization")
            
            # Clean data and ensure all columns have appropriate types
            # Convert size to numeric, default to 0 for any values that can't be converted
            df['size'] = pd.to_numeric(df['size'], errors='coerce').fillna(0)
            
            # Make sure all text columns are actually text
            text_columns = ['name', 'parentPath']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            
            # Handle nullable columns
            for col in ['isDeleted', 'dupKey', 'classifications']:
                if col in df.columns:
                    # Fill missing values appropriately
                    if col == 'isDeleted':
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    elif col == 'classifications':
                        df[col] = df[col].fillna('')
                    else:
                        df[col] = df[col].fillna('')
            
            # Extract useful features
            df['extension'] = df['name'].apply(extract_extension)
            
            # Parse dates if available
            if 'createTime' in df.columns:
                # First ensure the column is string type
                df['createTime'] = df['createTime'].astype(str)
                df['creation_date'] = df['createTime'].apply(parse_datetime)
                # Only calculate age for valid dates
                df['age_days'] = df.apply(
                    lambda row: get_file_age_days(row['createTime']) if pd.notna(row['creation_date']) else None, 
                    axis=1
                )
            
            if 'modifyTime' in df.columns:
                # First ensure the column is string type
                df['modifyTime'] = df['modifyTime'].astype(str)
                df['modification_date'] = df['modifyTime'].apply(parse_datetime)
                # Only calculate days since modified for valid dates
                df['days_since_modified'] = df.apply(
                    lambda row: get_file_age_days(row['modifyTime']) if pd.notna(row['modification_date']) else None,
                    axis=1
                )
            
            # Get unique file extensions
            extensions = df['extension'].value_counts().to_dict() if 'extension' in df.columns else {}
            st.session_state.file_extensions = extensions
            
            # Aggregate by folder
            try:
                folder_stats = aggregate_by_folder(df)
                if folder_stats is None or folder_stats.empty:
                    st.error("Failed to create folder statistics. Creating a minimal dataset for visualization.")
                    # Create minimal folder stats for the app to continue
                    folder_stats = pd.DataFrame({
                        'parentPath': ['root'],
                        'folder_size': [df['size'].sum()],
                        'file_count': [len(df)],
                        'avg_file_size': [df['size'].mean()],
                        'deleted_count': [0]
                    })
                    folder_stats['folder_components'] = [['root']]
                    folder_stats['folder_depth'] = [1]
                
                folder_hierarchy = prepare_folder_hierarchy(folder_stats)
                if folder_hierarchy is None:
                    st.error("Failed to create folder hierarchy. Creating a minimal dataset for visualization.")
                    # Create minimal hierarchy for the app to continue
                    folder_hierarchy = pd.DataFrame({
                        'parentPath': ['root'],
                        'folder_size': [df['size'].sum()],
                        'file_count': [len(df)],
                        'folder_depth': [1],
                        'Level 1': ['root']
                    })
            except Exception as e:
                st.error(f"Error processing folder structure: {str(e)}")
                st.exception(e)
                # Create minimal datasets to allow the app to continue
                folder_stats = pd.DataFrame({
                    'parentPath': ['root'],
                    'folder_size': [df['size'].sum()],
                    'file_count': [len(df)],
                    'avg_file_size': [df['size'].mean()],
                    'deleted_count': [0],
                    'folder_components': [['root']],
                    'folder_depth': [1]
                })
                folder_hierarchy = pd.DataFrame({
                    'parentPath': ['root'],
                    'folder_size': [df['size'].sum()],
                    'file_count': [len(df)],
                    'folder_depth': [1],
                    'Level 1': ['root']
                })
            
            # Set session state
            st.session_state.file_data = df
            st.session_state.folder_stats = folder_stats
            st.session_state.folder_hierarchy = folder_hierarchy
            st.session_state.file_data_loaded = True
            
            processing_time = time.time() - start_time
            st.sidebar.success(f"Data loaded successfully! ({processing_time:.2f}s)")
            st.sidebar.info(f"Found {len(df)} files across {len(folder_stats)} folders")
    
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}")
        st.exception(e)
        st.stop()

# Main visualization area
if st.session_state.file_data_loaded:
    df = st.session_state.file_data
    folder_stats = st.session_state.folder_stats
    folder_hierarchy = st.session_state.folder_hierarchy
    
    # Create tabs for different visualizations
    tabs = ["Folder Structure", "File Types", "Size Analysis", "Age Analysis"]
    if "classifications" in df.columns:
        tabs.append("Classifications")
    if "isDeleted" in df.columns and df["isDeleted"].sum() > 0:
        tabs.append("Deleted Files")
    if "dupKey" in df.columns:
        tabs.append("Duplicate Analysis")
    
    selected_tab = st.radio("Select Analysis View:", tabs, horizontal=True, 
                            index=tabs.index(st.session_state.selected_tab) if st.session_state.selected_tab in tabs else 0)
    st.session_state.selected_tab = selected_tab
    
    # Display visualization based on selected tab
    if selected_tab == "Folder Structure":
        st.subheader("📁 Folder Structure Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Size unit selection
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
            
            # Folder depth control
            max_depth = min(max(folder_stats['folder_depth']), 10)
            folder_depth = st.slider(
                "Max Folder Depth to Display",
                min_value=1,
                max_value=max_depth,
                value=min(3, max_depth)
            )
            st.session_state.folder_depth = folder_depth
            
            # Visualization options
            viz_type = st.selectbox(
                "Visualization Type",
                ["Sunburst Chart", "Treemap", "Folder Bar Chart"]
            )
            
            # Metric selection
            metric = st.selectbox(
                "Metric to Display",
                ["Folder Size", "File Count", "Average File Size"]
            )
            
            # Color scheme
            color_scheme = st.selectbox(
                "Color Scheme",
                ["Viridis", "Blues", "Reds", "Greens", "YlOrRd", "Turbo"]
            )
        
        with col2:
            # Convert folder sizes based on selected unit
            folder_hierarchy['size_converted'] = folder_hierarchy['folder_size'].apply(
                lambda x: convert_size(x, size_unit)
            )
            
            # Prepare path columns based on selected depth
            path_columns = [f'Level {i+1}' for i in range(min(folder_depth, max_depth))]
            
            # Configure visualization based on metric
            if metric == "Folder Size":
                value_column = "size_converted"
                title_suffix = f"Size ({size_unit})"
                color_column = "size_converted"
                hover_data = ["file_count", "folder_depth"]
            elif metric == "File Count":
                value_column = "file_count"
                title_suffix = "File Count"
                color_column = "file_count"
                hover_data = ["size_converted", "folder_depth"]
            else:  # Average File Size
                value_column = "avg_file_size"
                title_suffix = f"Avg File Size ({size_unit})"
                color_column = "avg_file_size"
                hover_data = ["file_count", "folder_depth"]
            
            # Create visualization
            try:
                if viz_type == "Sunburst Chart":
                    fig = px.sunburst(
                        folder_hierarchy,
                        path=path_columns,
                        values=value_column,
                        color=color_column,
                        color_continuous_scale=color_scheme.lower(),
                        title=f"Folder Structure by {title_suffix}",
                        hover_data=hover_data,
                        branchvalues="total"
                    )
                elif viz_type == "Treemap":
                    fig = px.treemap(
                        folder_hierarchy,
                        path=path_columns,
                        values=value_column,
                        color=color_column,
                        color_continuous_scale=color_scheme.lower(),
                        title=f"Folder Structure by {title_suffix}",
                        hover_data=hover_data,
                        branchvalues="total"
                    )
                else:  # Folder Bar Chart
                    # Get top folders by selected metric
                    if value_column == "size_converted":
                        sort_column = "folder_size"
                    elif value_column == "file_count":
                        sort_column = "file_count"
                    else:
                        sort_column = "avg_file_size"
                    
                    top_folders = folder_hierarchy.sort_values(by=sort_column, ascending=False).head(20)
                    
                    # Extract last folder name for display
                    top_folders['display_name'] = top_folders['parentPath'].apply(
                        lambda x: x.split('/')[-1] if x and '/' in x else x
                    )
                    
                    fig = px.bar(
                        top_folders,
                        x=value_column,
                        y='display_name',
                        orientation='h',
                        color=color_column,
                        color_continuous_scale=color_scheme.lower(),
                        title=f"Top 20 Folders by {title_suffix}",
                        hover_data=['parentPath'] + hover_data,
                        height=600
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                
                fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
                st.info("Try adjusting the folder depth or changing the visualization type.")
        
        # Folder Statistics
        st.subheader("📊 Folder Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Size Statistics**")
            total_size = folder_hierarchy['folder_size'].sum()
            st.write(f"Total Size: {convert_size(total_size, size_unit):.2f} {size_unit}")
            
            largest_folder = folder_hierarchy.loc[folder_hierarchy['folder_size'].idxmax()]
            st.write(f"Largest Folder: {largest_folder['parentPath']} ({convert_size(largest_folder['folder_size'], size_unit):.2f} {size_unit})")
            
            deepest_folders = folder_hierarchy[folder_hierarchy['folder_depth'] == folder_hierarchy['folder_depth'].max()]
            st.write(f"Deepest Folder Level: {folder_hierarchy['folder_depth'].max()}")
            
            st.write(f"Average Folder Size: {convert_size(folder_hierarchy['folder_size'].mean(), size_unit):.2f} {size_unit}")
        
        with col2:
            st.write("**File Statistics**")
            total_files = df.shape[0]
            st.write(f"Total Files: {total_files:,}")
            
            avg_files_per_folder = folder_hierarchy['file_count'].mean()
            st.write(f"Average Files per Folder: {avg_files_per_folder:.2f}")
            
            most_files_folder = folder_hierarchy.loc[folder_hierarchy['file_count'].idxmax()]
            st.write(f"Folder with Most Files: {most_files_folder['parentPath']} ({most_files_folder['file_count']} files)")
            
            empty_folders = (folder_hierarchy['file_count'] == 0).sum()
            st.write(f"Empty Folders: {empty_folders}")
        
        # Folder Depth Distribution
        st.subheader("📏 Folder Depth Distribution")
        depth_counts = folder_hierarchy['folder_depth'].value_counts().sort_index()
        
        depth_fig = px.bar(
            x=depth_counts.index,
            y=depth_counts.values,
            labels={'x': 'Folder Depth', 'y': 'Number of Folders'},
            title="Distribution of Folder Depths",
            color=depth_counts.index,
            color_continuous_scale=color_scheme.lower()
        )
        
        # Add vertical line at average depth
        avg_depth = folder_hierarchy['folder_depth'].mean()
        depth_fig.add_vline(
            x=avg_depth,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Avg: {avg_depth:.1f}",
            annotation_position="top right"
        )
        
        st.plotly_chart(depth_fig, use_container_width=True)
    
    elif selected_tab == "File Types":
        st.subheader("📄 File Type Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Size unit selection
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
            
            # Visualization type
            viz_type = st.selectbox(
                "Visualization Type",
                ["Pie Chart", "Bar Chart", "Treemap"]
            )
            
            # Metric selection
            metric = st.selectbox(
                "Metric to Display",
                ["File Count", "Total Size"]
            )
            
            # Filter options
            min_count = st.slider(
                "Minimum File Count to Display",
                min_value=1,
                max_value=max(10, int(df.shape[0]/100)),
                value=5
            )
            
            # Group extensions option
            group_option = st.selectbox(
                "File Type Grouping",
                ["No Grouping", "Basic Groups", "Detailed Groups"]
            )
        
        with col2:
            # Process file extension data
            extension_data = df.groupby('extension').agg(
                file_count=('name', 'count'),
                total_size=('size', 'sum'),
                avg_size=('size', 'mean')
            ).reset_index()
            
            # Convert sizes
            extension_data['size_converted'] = extension_data['total_size'].apply(
                lambda x: convert_size(x, size_unit)
            )
            extension_data['avg_size_converted'] = extension_data['avg_size'].apply(
                lambda x: convert_size(x, size_unit)
            )
            
            # Filter by minimum count
            extension_data = extension_data[extension_data['file_count'] >= min_count]
            
            # Group extensions if requested
            if group_option != "No Grouping":
                # Define extension groups
                if group_option == "Basic Groups":
                    extension_groups = {
                        "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "pages"],
                        "Spreadsheets": ["xls", "xlsx", "csv", "tsv", "numbers", "ods"],
                        "Presentations": ["ppt", "pptx", "key", "odp"],
                        "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "webp", "heic"],
                        "Audio": ["mp3", "wav", "aac", "flac", "ogg", "m4a", "wma"],
                        "Video": ["mp4", "avi", "mov", "wmv", "mkv", "flv", "webm", "m4v"],
                        "Archives": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"],
                        "Code": ["py", "js", "html", "css", "java", "cpp", "c", "h", "php", "rb", "go", "rs", "swift"],
                        "Data": ["json", "xml", "sql", "db", "sqlite", "yaml", "yml"],
                        "Executables": ["exe", "msi", "app", "dmg", "deb", "rpm"],
                    }
                else:  # Detailed Groups
                    extension_groups = {
                        "PDF": ["pdf"],
                        "Word": ["doc", "docx"],
                        "Text": ["txt", "rtf", "md"],
                        "Excel": ["xls", "xlsx"],
                        "CSV": ["csv", "tsv"],
                        "PowerPoint": ["ppt", "pptx"],
                        "JPEG": ["jpg", "jpeg"],
                        "PNG": ["png"],
                        "GIF": ["gif"],
                        "Vector": ["svg", "eps", "ai"],
                        "Audio": ["mp3", "wav", "aac", "flac", "ogg"],
                        "Video": ["mp4", "avi", "mov", "wmv", "mkv"],
                        "Compressed": ["zip", "rar", "7z", "tar", "gz"],
                        "Python": ["py", "pyc", "ipynb"],
                        "JavaScript": ["js", "jsx", "ts", "tsx"],
                        "Web": ["html", "css", "php"],
                        "Java": ["java", "class", "jar"],
                        "C/C++": ["c", "cpp", "h", "hpp"],
                        "Shell": ["sh", "bash", "zsh"],
                        "Config": ["json", "xml", "yaml", "yml", "ini", "toml"],
                        "Database": ["sql", "db", "sqlite"],
                        "Windows": ["exe", "msi", "dll", "bat"],
                        "MacOS": ["app", "dmg", "pkg"],
                        "Linux": ["deb", "rpm", "run"],
                    }
                
                # Create a mapping from extension to group
                ext_to_group = {}
                for group, extensions in extension_groups.items():
                    for ext in extensions:
                        ext_to_group[ext] = group
                
                # Apply grouping
                df['file_group'] = df['extension'].apply(
                    lambda x: ext_to_group.get(x, "Other")
                )
                
                # Create grouped data
                grouped_data = df.groupby('file_group').agg(
                    file_count=('name', 'count'),
                    total_size=('size', 'sum'),
                    avg_size=('size', 'mean')
                ).reset_index()
                
                # Convert sizes
                grouped_data['size_converted'] = grouped_data['total_size'].apply(
                    lambda x: convert_size(x, size_unit)
                )
                grouped_data['avg_size_converted'] = grouped_data['avg_size'].apply(
                    lambda x: convert_size(x, size_unit)
                )
                
                # Filter by minimum count
                grouped_data = grouped_data[grouped_data['file_count'] >= min_count]
                
                # Replace extension data with grouped data
                extension_data = grouped_data.rename(columns={'file_group': 'extension'})
            
            # Sort data by selected metric
            if metric == "File Count":
                extension_data = extension_data.sort_values('file_count', ascending=False)
                value_column = 'file_count'
                title_suffix = "File Count"
            else:
                extension_data = extension_data.sort_values('total_size', ascending=False)
                value_column = 'size_converted'
                title_suffix = f"Total Size ({size_unit})"
            
            # Create visualization
            try:
                if viz_type == "Pie Chart":
                    fig = px.pie(
                        extension_data,
                        names='extension',
                        values=value_column,
                        title=f"File Types by {title_suffix}",
                        hover_data=['file_count', 'size_converted']
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                
                elif viz_type == "Bar Chart":
                    # Limit to top 20 for bar chart
                    if len(extension_data) > 20:
                        chart_data = extension_data.head(20)
                    else:
                        chart_data = extension_data
                    
                    fig = px.bar(
                        chart_data,
                        x='extension',
                        y=value_column,
                        title=f"Top File Types by {title_suffix}",
                        color='extension',
                        hover_data=['file_count', 'size_converted']
                    )
                
                else:  # Treemap
                    fig = px.treemap(
                        extension_data,
                        path=['extension'],
                        values=value_column,
                        title=f"File Types by {title_suffix}",
                        color=value_column,
                        hover_data=['file_count', 'size_converted']
                    )
                
                fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
        
        # Top extensions stats
        st.subheader("📊 Extension Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top 10 Extensions by Count**")
            top_count = df['extension'].value_counts().head(10)
            count_data = pd.DataFrame({
                'Extension': top_count.index,
                'Count': top_count.values,
                'Percentage': (top_count.values / df.shape[0] * 100).round(2)
            })
            st.dataframe(count_data, use_container_width=True)
        
        with col2:
            st.write("**Top 10 Extensions by Size**")
            ext_size = df.groupby('extension')['size'].sum().sort_values(ascending=False).head(10)
            size_data = pd.DataFrame({
                'Extension': ext_size.index,
                'Size': ext_size.apply(lambda x: f"{convert_size(x, size_unit):.2f} {size_unit}"),
                'Percentage': (ext_size.values / df['size'].sum() * 100).round(2)
            })
            st.dataframe(size_data, use_container_width=True)
        
        # Average file size by extension
        st.subheader("📏 Average File Size by Extension")
        
        # Calculate average size
        avg_size = df.groupby('extension')['size'].mean().sort_values(ascending=False).head(15)
        avg_size_converted = avg_size.apply(lambda x: convert_size(x, size_unit))
        
        avg_fig = px.bar(
            x=avg_size_converted.index,
            y=avg_size_converted.values,
            labels={'x': 'Extension', 'y': f'Average Size ({size_unit})'},
            title=f"Top 15 Extensions by Average File Size ({size_unit})",
            color=avg_size_converted.values,
            text_auto='.2f'
        )
        
        avg_fig.update_layout(xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(avg_fig, use_container_width=True)
    
    elif selected_tab == "Size Analysis":
        st.subheader("📊 File Size Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Size unit selection
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
            
            # Size range options
            max_size = convert_size(df['size'].max(), size_unit)
            
            # Visualization options
            viz_type = st.selectbox(
                "Visualization Type",
                ["Histogram", "Box Plot", "Scatter Plot"]
            )
            
            # File count limit (for performance)
            if len(df) > 10000 and viz_type == "Scatter Plot":
                sample_pct = st.slider(
                    "Sample Size (%)",
                    min_value=1,
                    max_value=100,
                    value=min(100, max(1, int(10000/len(df)*100)))
                )
            else:
                sample_pct = 100
            
            # For histogram
            if viz_type == "Histogram":
                num_bins = st.slider(
                    "Number of Bins",
                    min_value=10,
                    max_value=100,
                    value=30
                )
                
                log_scale = st.checkbox("Use Log Scale for Size", value=True)
        
        with col2:
            # Convert sizes
            df_size = df.copy()
            df_size['size_converted'] = df_size['size'].apply(
                lambda x: convert_size(x, size_unit)
            )
            
            # Sample data if needed
            if sample_pct < 100:
                sample_size = int(len(df_size) * sample_pct / 100)
                df_size = df_size.sample(sample_size)
                st.info(f"Displaying a {sample_pct}% sample ({sample_size:,} files) for performance")
            
            # Create visualization
            try:
                if viz_type == "Histogram":
                    size_data = df_size['size_converted']
                    if log_scale and (size_data > 0).all():
                        size_data = np.log10(size_data.replace(0, 0.000001))
                        x_title = f"Log10(Size in {size_unit})"
                    else:
                        x_title = f"Size ({size_unit})"
                    
                    fig = px.histogram(
                        size_data,
                        nbins=num_bins,
                        title=f"Distribution of File Sizes ({size_unit})",
                        labels={'value': x_title, 'count': 'Number of Files'},
                        marginal="box"
                    )
                
                elif viz_type == "Box Plot":
                    if 'extension' in df_size.columns:
                        # Get top extensions
                        top_exts = df_size['extension'].value_counts().head(15).index.tolist()
                        box_data = df_size[df_size['extension'].isin(top_exts)]
                        
                        fig = px.box(
                            box_data,
                            x='extension',
                            y='size_converted',
                            title=f"File Size Distribution by Extension ({size_unit})",
                            labels={'extension': 'File Extension', 'size_converted': f'Size ({size_unit})'},
                            color='extension'
                        )
                    else:
                        fig = px.box(
                            df_size,
                            y='size_converted',
                            title=f"Overall File Size Distribution ({size_unit})",
                            labels={'size_converted': f'Size ({size_unit})'}
                        )
                
                else:  # Scatter Plot
                    if 'age_days' in df_size.columns:
                        fig = px.scatter(
                            df_size,
                            x='age_days',
                            y='size_converted',
                            title=f"File Size vs. Age ({size_unit})",
                            labels={
                                'age_days': 'Age (days)',
                                'size_converted': f'Size ({size_unit})'
                            },
                            color='extension',
                            opacity=0.7,
                            hover_data=['name', 'parentPath']
                        )
                    else:
                        # Use folder depth instead if age not available
                        df_size['folder_depth'] = df_size['parentPath'].apply(
                            lambda x: len(x.split('/')) if pd.notna(x) else 0
                        )
                        
                        fig = px.scatter(
                            df_size,
                            x='folder_depth',
                            y='size_converted',
                            title=f"File Size vs. Folder Depth ({size_unit})",
                            labels={
                                'folder_depth': 'Folder Depth',
                                'size_converted': f'Size ({size_unit})'
                            },
                            color='extension',
                            opacity=0.7,
                            hover_data=['name', 'parentPath']
                        )
                
                fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
        
        # Size statistics 
        st.subheader("📏 Size Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**General Statistics**")
            total_size = df['size'].sum()
            mean_size = df['size'].mean()
            median_size = df['size'].median()
            
            st.write(f"Total Size: {convert_size(total_size, size_unit):.2f} {size_unit}")
            st.write(f"Mean File Size: {convert_size(mean_size, size_unit):.2f} {size_unit}")
            st.write(f"Median File Size: {convert_size(median_size, size_unit):.2f} {size_unit}")
            
            # Size percentiles
            percentiles = [10, 25, 50, 75, 90, 99]
            size_percentiles = np.percentile(df['size'].values, percentiles)
            st.write("**Size Percentiles**")
            for p, val in zip(percentiles, size_percentiles):
                st.write(f"{p}th Percentile: {convert_size(val, size_unit):.2f} {size_unit}")
        
        with col2:
            st.write("**Size Ranges**")
            
            # Define size ranges based on selected unit
            if size_unit == "Bytes":
                ranges = [
                    (0, 1024, "< 1 KB"),
                    (1024, 10240, "1-10 KB"),
                    (10240, 102400, "10-100 KB"),
                    (102400, 1048576, "100 KB - 1 MB"),
                    (1048576, 10485760, "1-10 MB"),
                    (10485760, 104857600, "10-100 MB"),
                    (104857600, 1073741824, "100 MB - 1 GB"),
                    (1073741824, float('inf'), "> 1 GB")
                ]
            elif size_unit == "KB":
                ranges = [
                    (0, 1, "< 1 KB"),
                    (1, 10, "1-10 KB"),
                    (10, 100, "10-100 KB"),
                    (100, 1024, "100 KB - 1 MB"),
                    (1024, 10240, "1-10 MB"),
                    (10240, 102400, "10-100 MB"),
                    (102400, 1048576, "100 MB - 1 GB"),
                    (1048576, float('inf'), "> 1 GB")
                ]
            elif size_unit == "MB":
                ranges = [
                    (0, 0.001, "< 1 KB"),
                    (0.001, 0.01, "1-10 KB"),
                    (0.01, 0.1, "10-100 KB"),
                    (0.1, 1, "100 KB - 1 MB"),
                    (1, 10, "1-10 MB"),
                    (10, 100, "10-100 MB"),
                    (100, 1024, "100 MB - 1 GB"),
                    (1024, float('inf'), "> 1 GB")
                ]
            else:  # GB
                ranges = [
                    (0, 0.000001, "< 1 KB"),
                    (0.000001, 0.00001, "1-10 KB"),
                    (0.00001, 0.0001, "10-100 KB"),
                    (0.0001, 0.001, "100 KB - 1 MB"),
                    (0.001, 0.01, "1-10 MB"),
                    (0.01, 0.1, "10-100 MB"),
                    (0.1, 1, "100 MB - 1 GB"),
                    (1, float('inf'), "> 1 GB")
                ]
            
            # Count files in each range
            range_counts = []
            for min_val, max_val, label in ranges:
                count = df[(df['size'] >= min_val*1024**(["Bytes", "KB", "MB", "GB"].index(size_unit))) & 
                          (df['size'] < max_val*1024**(["Bytes", "KB", "MB", "GB"].index(size_unit)))].shape[0]
                range_counts.append((label, count, count/len(df)*100))
            
            # Display as a table
            range_df = pd.DataFrame(range_counts, columns=['Size Range', 'File Count', 'Percentage'])
            range_df['Percentage'] = range_df['Percentage'].round(2)
            st.dataframe(range_df, use_container_width=True)
            
            # Display as a chart
            range_fig = px.bar(
                range_df,
                x='Size Range',
                y='File Count',
                title="File Count by Size Range",
                color='Percentage',
                text_auto=True,
                color_continuous_scale='Viridis'
            )
            
            range_fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': [r[2] for r in ranges]})
            st.plotly_chart(range_fig, use_container_width=True)
    
    elif selected_tab == "Age Analysis" and 'creation_date' in df.columns:
        st.subheader("📅 File Age Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Date range options
            min_date = df['creation_date'].min()
            max_date = df['creation_date'].max()
            
            if pd.notna(min_date) and pd.notna(max_date):
                # Date ranges for filtering
                st.write("**Date Range**")
                
                # Try to convert to datetime if they're strings
                if isinstance(min_date, str):
                    min_date = parse_datetime(min_date)
                if isinstance(max_date, str):
                    max_date = parse_datetime(max_date)
                
                # Format dates for display
                min_date_str = min_date.strftime("%Y-%m-%d") if min_date else "Unknown"
                max_date_str = max_date.strftime("%Y-%m-%d") if max_date else "Unknown"
                
                st.write(f"Earliest File: {min_date_str}")
                st.write(f"Latest File: {max_date_str}")
            
            # Visualization options
            viz_type = st.selectbox(
                "Visualization Type",
                ["Timeline", "Histogram", "By Extension", "Calendar Heatmap"]
            )
            
            # For histogram
            if viz_type == "Histogram":
                time_unit = st.selectbox(
                    "Time Unit",
                    ["Day", "Week", "Month", "Year"]
                )
            
            # Size unit for coloring
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
        
        with col2:
            # Filter out rows with missing dates
            df_dates = df.dropna(subset=['creation_date']).copy()
            
            if len(df_dates) == 0:
                st.warning("No valid creation dates found in the data.")
            else:
                # Convert sizes
                df_dates['size_converted'] = df_dates['size'].apply(
                    lambda x: convert_size(x, size_unit)
                )
                
                # Create visualization
                try:
                    if viz_type == "Timeline":
                        # Aggregate by date
                        df_dates['date'] = pd.to_datetime(df_dates['creation_date']).dt.date
                        timeline_data = df_dates.groupby('date').agg(
                            file_count=('name', 'count'),
                            total_size=('size', 'sum')
                        ).reset_index()
                        
                        timeline_data['total_size_converted'] = timeline_data['total_size'].apply(
                            lambda x: convert_size(x, size_unit)
                        )
                        
                        fig = px.scatter(
                            timeline_data,
                            x='date',
                            y='file_count',
                            size='total_size_converted',
                            title="Files Created Over Time",
                            color='total_size_converted',
                            labels={
                                'date': 'Creation Date',
                                'file_count': 'Number of Files',
                                'total_size_converted': f'Total Size ({size_unit})'
                            },
                            hover_data=['total_size_converted']
                        )
                        
                    elif viz_type == "Histogram":
                        # Convert to datetime
                        df_dates['date'] = pd.to_datetime(df_dates['creation_date'])
                        
                        # Group by time unit
                        if time_unit == "Day":
                            df_dates['time_period'] = df_dates['date'].dt.date
                        elif time_unit == "Week":
                            df_dates['time_period'] = df_dates['date'].dt.to_period('W').apply(lambda x: x.start_time.date())
                        elif time_unit == "Month":
                            df_dates['time_period'] = df_dates['date'].dt.to_period('M').apply(lambda x: x.start_time.date())
                        else:  # Year
                            df_dates['time_period'] = df_dates['date'].dt.year
                        
                        # Aggregate by time period
                        hist_data = df_dates.groupby('time_period').agg(
                            file_count=('name', 'count'),
                            total_size=('size', 'sum')
                        ).reset_index()
                        
                        hist_data['total_size_converted'] = hist_data['total_size'].apply(
                            lambda x: convert_size(x, size_unit)
                        )
                        
                        fig = px.bar(
                            hist_data,
                            x='time_period',
                            y='file_count',
                            title=f"File Creation by {time_unit}",
                            labels={
                                'time_period': time_unit,
                                'file_count': 'Number of Files'
                            },
                            color='total_size_converted',
                            hover_data=['total_size_converted'],
                            color_continuous_scale='Viridis'
                        )
                        
                    elif viz_type == "By Extension":
                        # Get top extensions
                        top_exts = df_dates['extension'].value_counts().head(10).index.tolist()
                        
                        # Filter to top extensions
                        ext_data = df_dates[df_dates['extension'].isin(top_exts)].copy()
                        
                        # Convert to datetime
                        ext_data['date'] = pd.to_datetime(ext_data['creation_date']).dt.to_period('M').apply(lambda x: x.start_time.date())
                        
                        # Aggregate by extension and month
                        ext_time_data = ext_data.groupby(['extension', 'date']).agg(
                            file_count=('name', 'count')
                        ).reset_index()
                        
                        fig = px.line(
                            ext_time_data,
                            x='date',
                            y='file_count',
                            color='extension',
                            title="File Creation Trends by Extension",
                            labels={
                                'date': 'Creation Date',
                                'file_count': 'Number of Files',
                                'extension': 'File Extension'
                            }
                        )
                    
                    else:  # Calendar Heatmap
                        if len(df_dates) > 0:
                            # Convert to datetime
                            df_dates['date'] = pd.to_datetime(df_dates['creation_date'])
                            
                            # Extract year and day of year
                            df_dates['year'] = df_dates['date'].dt.year
                            df_dates['day_of_year'] = df_dates['date'].dt.dayofyear
                            
                            # Aggregate by date
                            cal_data = df_dates.groupby(['year', 'day_of_year']).agg(
                                file_count=('name', 'count'),
                                total_size=('size', 'sum')
                            ).reset_index()
                            
                            cal_data['date_str'] = cal_data.apply(
                                lambda x: datetime.strptime(f"{int(x['year'])}-{int(x['day_of_year'])}", "%Y-%j").strftime("%Y-%m-%d"),
                                axis=1
                            )
                            
                            # Convert sizes
                            cal_data['total_size_converted'] = cal_data['total_size'].apply(
                                lambda x: convert_size(x, size_unit)
                            )
                            
                            fig = px.density_heatmap(
                                cal_data,
                                x='day_of_year',
                                y='year',
                                z='file_count',
                                title="File Creation Calendar Heatmap",
                                labels={
                                    'day_of_year': 'Day of Year',
                                    'year': 'Year',
                                    'file_count': 'Number of Files'
                                },
                                hover_data=['date_str', 'total_size_converted']
                            )
                        else:
                            st.warning("No valid dates for calendar heatmap.")
                            # Skip rendering the figure since there's no data
                            fig = None
                    
                    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                    st.plotly_chart(fig, use_container_width=True)
                
                except Exception as e:
                    st.error(f"Error creating visualization: {str(e)}")
        
        # Age statistics
        st.subheader("📊 Age Statistics")
        
        df_dates = df.dropna(subset=['creation_date']).copy()
        if len(df_dates) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Time-Based Statistics**")
                
                # Get earliest and latest dates by extension
                ext_dates = df_dates.groupby('extension').agg(
                    earliest=('creation_date', 'min'),
                    latest=('creation_date', 'max'),
                    count=('name', 'count')
                ).reset_index()
                
                # Sort by count
                ext_dates = ext_dates.sort_values('count', ascending=False).head(10)
                
                # Format dates
                ext_dates['earliest'] = pd.to_datetime(ext_dates['earliest']).dt.strftime('%Y-%m-%d')
                ext_dates['latest'] = pd.to_datetime(ext_dates['latest']).dt.strftime('%Y-%m-%d')
                
                st.write("**Top 10 Extensions by Time Range**")
                st.dataframe(ext_dates, use_container_width=True)
            
            with col2:
                st.write("**File Creation by Year**")
                
                # Group by year
                df_dates['year'] = pd.to_datetime(df_dates['creation_date']).dt.year
                year_counts = df_dates['year'].value_counts().sort_index()
                
                year_fig = px.bar(
                    x=year_counts.index,
                    y=year_counts.values,
                    labels={'x': 'Year', 'y': 'Number of Files'},
                    title="Files Created by Year",
                    color=year_counts.values,
                    color_continuous_scale='Viridis'
                )
                
                st.plotly_chart(year_fig, use_container_width=True)
    
    elif selected_tab == "Classifications" and "classifications" in df.columns:
        st.subheader("🏷️ File Classification Analysis")
        
        # Process classification data
        df_class = df.copy()
        
        # Handle list-like classifications
        if df_class['classifications'].dtype == 'object':
            # Try to detect list format (common formats: JSON lists, comma-separated, etc.)
            sample_vals = df_class['classifications'].dropna().head(100).tolist()
            
            # Check if values look like lists
            contains_lists = False
            for val in sample_vals:
                if val and (val.startswith('[') or ',' in val):
                    contains_lists = True
                    break
            
            if contains_lists:
                # Explode lists into rows (handle common formats)
                class_lists = []
                for val in df_class['classifications'].fillna(''):
                    if pd.isna(val) or val == '':
                        class_lists.append([])
                    elif val.startswith('[') and val.endswith(']'):
                        # Try to parse JSON
                        try:
                            import json
                            class_lists.append(json.loads(val))
                        except:
                            # Fallback to simple splitting
                            class_lists.append([v.strip(' "\'') for v in val[1:-1].split(',')])
                    elif ',' in val:
                        class_lists.append([v.strip() for v in val.split(',')])
                    else:
                        class_lists.append([val])
                
                df_class['classification_list'] = class_lists
                
                # Explode the lists into separate rows
                classification_rows = []
                for idx, row in df_class.iterrows():
                    if not row['classification_list']:
                        classification_rows.append({
                            'name': row['name'],
                            'classification': 'Unclassified',
                            'size': row['size']
                        })
                    else:
                        for cls in row['classification_list']:
                            if cls and cls.strip():  # Skip empty classifications
                                classification_rows.append({
                                    'name': row['name'],
                                    'classification': cls.strip(),
                                    'size': row['size']
                                })
            
                classification_df = pd.DataFrame(classification_rows)
            else:
                # Treat as single values
                classification_df = df_class.rename(columns={'classifications': 'classification'})
                classification_df.loc[pd.isna(classification_df['classification']) | 
                                    (classification_df['classification'] == ''), 'classification'] = 'Unclassified'
        else:
            # Simple case - no need for complex parsing
            classification_df = df_class.rename(columns={'classifications': 'classification'})
            classification_df.loc[pd.isna(classification_df['classification']) | 
                                (classification_df['classification'] == ''), 'classification'] = 'Unclassified'
        
        # Now analyze the classification data
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Size unit selection
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
            
            # Visualization type
            viz_type = st.selectbox(
                "Visualization Type",
                ["Pie Chart", "Bar Chart", "Treemap"]
            )
            
            # Metric selection
            metric = st.selectbox(
                "Metric to Display",
                ["File Count", "Total Size"]
            )
            
            # Classification count limit
            min_count = st.slider(
                "Minimum File Count",
                min_value=1,
                max_value=max(10, int(len(classification_df)/100)),
                value=5
            )
        
        with col2:
            # Aggregate by classification
            class_stats = classification_df.groupby('classification').agg(
                file_count=('name', 'count'),
                total_size=('size', 'sum')
            ).reset_index()
            
            # Convert size
            class_stats['total_size_converted'] = class_stats['total_size'].apply(
                lambda x: convert_size(x, size_unit)
            )
            
            # Filter by minimum count
            class_stats = class_stats[class_stats['file_count'] >= min_count]
            
            # Sort by selected metric
            if metric == "File Count":
                class_stats = class_stats.sort_values('file_count', ascending=False)
                value_column = 'file_count'
                title_suffix = "File Count"
            else:
                class_stats = class_stats.sort_values('total_size', ascending=False)
                value_column = 'total_size_converted'
                title_suffix = f"Total Size ({size_unit})"
            
            # Create visualization
            try:
                if viz_type == "Pie Chart":
                    fig = px.pie(
                        class_stats,
                        names='classification',
                        values=value_column,
                        title=f"File Classifications by {title_suffix}",
                        hover_data=['file_count', 'total_size_converted']
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                
                elif viz_type == "Bar Chart":
                    # Limit to top 20 for bar chart
                    if len(class_stats) > 20:
                        chart_data = class_stats.head(20)
                    else:
                        chart_data = class_stats
                    
                    fig = px.bar(
                        chart_data,
                        x='classification',
                        y=value_column,
                        title=f"Top Classifications by {title_suffix}",
                        color='classification',
                        hover_data=['file_count', 'total_size_converted']
                    )
                
                else:  # Treemap
                    fig = px.treemap(
                        class_stats,
                        path=['classification'],
                        values=value_column,
                        title=f"Classifications by {title_suffix}",
                        color=value_column,
                        hover_data=['file_count', 'total_size_converted']
                    )
                
                fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
        
        # Classification statistics
        st.subheader("📊 Classification Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top 10 Classifications by Count**")
            class_counts = classification_df['classification'].value_counts().head(10)
            count_data = pd.DataFrame({
                'Classification': class_counts.index,
                'Count': class_counts.values,
                'Percentage': (class_counts.values / len(classification_df) * 100).round(2)
            })
            st.dataframe(count_data, use_container_width=True)
        
        with col2:
            st.write("**Top 10 Classifications by Size**")
            class_size = classification_df.groupby('classification')['size'].sum().sort_values(ascending=False).head(10)
            size_data = pd.DataFrame({
                'Classification': class_size.index,
                'Size': class_size.apply(lambda x: f"{convert_size(x, size_unit):.2f} {size_unit}"),
                'Percentage': (class_size.values / classification_df['size'].sum() * 100).round(2)
            })
            st.dataframe(size_data, use_container_width=True)
    
    elif selected_tab == "Deleted Files" and "isDeleted" in df.columns:
        st.subheader("🗑️ Deleted Files Analysis")
        
        # Filter for deleted files
        df_deleted = df[df['isDeleted'] == 1].copy()
        df_active = df[df['isDeleted'] == 0].copy()
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Size unit selection
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
            
            # Visualization type
            viz_type = st.selectbox(
                "Visualization Type",
                ["Overview", "By Extension", "By Folder"]
            )
            
            # Show detailed list
            show_list = st.checkbox("Show Detailed File List", value=False)
            
            # File count limit for list
            if show_list and len(df_deleted) > 100:
                list_limit = st.slider(
                    "List Size Limit",
                    min_value=10,
                    max_value=1000,
                    value=min(100, len(df_deleted))
                )
            else:
                list_limit = 100
        
        with col2:
            # Basic statistics
            total_files = len(df)
            deleted_count = len(df_deleted)
            active_count = len(df_active)
            
            deleted_pct = (deleted_count / total_files * 100) if total_files > 0 else 0
            
            total_size = df['size'].sum()
            deleted_size = df_deleted['size'].sum()
            active_size = df_active['size'].sum()
            
            deleted_size_pct = (deleted_size / total_size * 100) if total_size > 0 else 0
            
            # Convert sizes
            deleted_size_converted = convert_size(deleted_size, size_unit)
            total_size_converted = convert_size(total_size, size_unit)
            active_size_converted = convert_size(active_size, size_unit)
            
            # Display overview
            st.write(f"Total Files: {total_files:,} ({total_size_converted:.2f} {size_unit})")
            st.write(f"Deleted Files: {deleted_count:,} ({deleted_size_converted:.2f} {size_unit})")
            st.write(f"Active Files: {active_count:,} ({active_size_converted:.2f} {size_unit})")
            st.write(f"Percentage Deleted: {deleted_pct:.2f}% of files, {deleted_size_pct:.2f}% of total size")
            
            # Create visualization
            try:
                if viz_type == "Overview":
                    # Create data for pie charts
                    status_counts = pd.DataFrame([
                        {'Status': 'Active', 'Files': active_count, 'Size': active_size_converted},
                        {'Status': 'Deleted', 'Files': deleted_count, 'Size': deleted_size_converted}
                    ])
                    
                    fig1 = px.pie(
                        status_counts,
                        names='Status',
                        values='Files',
                        title="File Status by Count",
                        color='Status',
                        color_discrete_map={'Active': '#3498db', 'Deleted': '#e74c3c'}
                    )
                    fig1.update_traces(textposition='inside', textinfo='percent+label')
                    
                    fig2 = px.pie(
                        status_counts,
                        names='Status',
                        values='Size',
                        title=f"File Status by Size ({size_unit})",
                        color='Status',
                        color_discrete_map={'Active': '#3498db', 'Deleted': '#e74c3c'}
                    )
                    fig2.update_traces(textposition='inside', textinfo='percent+label')
                    
                    st.plotly_chart(fig1, use_container_width=True)
                    st.plotly_chart(fig2, use_container_width=True)
                
                elif viz_type == "By Extension":
                    # Aggregate by extension
                    deleted_by_ext = df_deleted.groupby('extension').agg(
                        file_count=('name', 'count'),
                        total_size=('size', 'sum')
                    ).reset_index()
                    
                    active_by_ext = df_active.groupby('extension').agg(
                        file_count=('name', 'count'),
                        total_size=('size', 'sum')
                    ).reset_index()
                    
                    # Convert sizes
                    deleted_by_ext['size_converted'] = deleted_by_ext['total_size'].apply(
                        lambda x: convert_size(x, size_unit)
                    )
                    
                    active_by_ext['size_converted'] = active_by_ext['total_size'].apply(
                        lambda x: convert_size(x, size_unit)
                    )
                    
                    # Get top extensions by deleted count
                    top_exts = deleted_by_ext.sort_values('file_count', ascending=False).head(10)['extension'].tolist()
                    
                    # Filter data to top extensions
                    deleted_top = deleted_by_ext[deleted_by_ext['extension'].isin(top_exts)]
                    
                    fig = px.bar(
                        deleted_top.sort_values('file_count', ascending=False),
                        x='extension',
                        y='file_count',
                        title="Top 10 Extensions in Deleted Files",
                        color='size_converted',
                        hover_data=['size_converted'],
                        color_continuous_scale='Reds'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Also show deletion rate by extension
                    combined_ext = pd.merge(
                        deleted_by_ext, 
                        active_by_ext,
                        on='extension',
                        suffixes=('_deleted', '_active'),
                        how='outer'
                    ).fillna(0)
                    
                    combined_ext['total_count'] = combined_ext['file_count_deleted'] + combined_ext['file_count_active']
                    combined_ext['deletion_rate'] = (combined_ext['file_count_deleted'] / combined_ext['total_count'] * 100).round(2)
                    
                    # Filter to extensions with at least 10 files total
                    combined_ext = combined_ext[combined_ext['total_count'] >= 10]
                    
                    # Sort by deletion rate
                    combined_ext = combined_ext.sort_values('deletion_rate', ascending=False).head(15)
                    
                    rate_fig = px.bar(
                        combined_ext,
                        x='extension',
                        y='deletion_rate',
                        title="Top 15 Extensions by Deletion Rate (%)",
                        color='deletion_rate',
                        hover_data=['file_count_deleted', 'file_count_active', 'total_count'],
                        color_continuous_scale='Reds',
                        text_auto='.1f'
                    )
                    
                    st.plotly_chart(rate_fig, use_container_width=True)
                
                else:  # By Folder
                    # Aggregate by folder
                    deleted_by_folder = df_deleted.groupby('parentPath').agg(
                        file_count=('name', 'count'),
                        total_size=('size', 'sum')
                    ).reset_index()
                    
                    # Convert sizes
                    deleted_by_folder['size_converted'] = deleted_by_folder['total_size'].apply(
                        lambda x: convert_size(x, size_unit)
                    )
                    
                    # Get top folders by deleted count
                    top_folders = deleted_by_folder.sort_values('file_count', ascending=False).head(15)
                    
                    # Extract folder name for display
                    top_folders['folder_name'] = top_folders['parentPath'].apply(
                        lambda x: x.split('/')[-1] if x and '/' in x else x
                    )
                    
                    folder_fig = px.bar(
                        top_folders,
                        x='file_count',
                        y='folder_name',
                        orientation='h',
                        title="Top 15 Folders with Deleted Files",
                        color='size_converted',
                        hover_data=['parentPath', 'size_converted'],
                        color_continuous_scale='Reds'
                    )
                    
                    st.plotly_chart(folder_fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
        
        # Detailed list of deleted files
        if show_list and len(df_deleted) > 0:
            st.subheader("📋 Deleted Files List")
            
            # Convert sizes
            df_deleted['size_converted'] = df_deleted['size'].apply(
                lambda x: convert_size(x, size_unit)
            )
            
            # Sort by size (descending)
            df_deleted_sorted = df_deleted.sort_values('size', ascending=False).head(list_limit)
            
            # Format for display
            display_cols = ['name', 'parentPath', 'size_converted', 'extension']
            if 'deletedAt' in df_deleted.columns:
                display_cols.append('deletedAt')
            if 'createTime' in df_deleted.columns:
                display_cols.append('createTime')
            
            st.dataframe(df_deleted_sorted[display_cols], use_container_width=True)
    
    elif selected_tab == "Duplicate Analysis" and "dupKey" in df.columns:
        st.subheader("🔄 Duplicate Files Analysis")
        
        # Process duplicate data
        df_dup = df.copy()
        
        # Count occurrences of each dupKey
        dup_counts = df_dup['dupKey'].value_counts()
        
        # Filter for duplicates (dupKey appears more than once)
        duplicate_keys = dup_counts[dup_counts > 1].index.tolist()
        df_duplicates = df_dup[df_dup['dupKey'].isin(duplicate_keys)].copy()
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Size unit selection
            size_unit = st.selectbox(
                "Size Unit",
                ["Bytes", "KB", "MB", "GB"],
                index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
            )
            st.session_state.size_unit = size_unit
            
            # Visualization type
            viz_type = st.selectbox(
                "Visualization Type",
                ["Overview", "By Extension", "By Folder"]
            )
            
            # Show detailed list
            show_list = st.checkbox("Show Detailed Duplicates List", value=False)
            
            # Duplicate count limit for list
            if show_list and len(duplicate_keys) > 50:
                dup_limit = st.slider(
                    "Duplicates to Show",
                    min_value=10,
                    max_value=min(500, len(duplicate_keys)),
                    value=min(50, len(duplicate_keys))
                )
            else:
                dup_limit = 50
        
        with col2:
            # Basic statistics
            total_files = len(df_dup)
            unique_files = len(df_dup) - len(df_duplicates) + len(duplicate_keys)
            duplicate_count = len(df_duplicates) - len(duplicate_keys)
            
            duplicate_pct = (duplicate_count / total_files * 100) if total_files > 0 else 0
            
            # Calculate space wasted by duplicates
            total_size = df_dup['size'].sum()
            
            # Get size of each duplicate key
            dup_sizes = df_duplicates.groupby('dupKey')['size'].first()
            wasted_size = df_duplicates.groupby('dupKey').size().map(lambda x: (x-1)).mul(dup_sizes).sum()
            
            wasted_pct = (wasted_size / total_size * 100) if total_size > 0 else 0
            
            # Convert sizes
            wasted_size_converted = convert_size(wasted_size, size_unit)
            total_size_converted = convert_size(total_size, size_unit)
            
            # Display overview
            st.write(f"Total Files: {total_files:,} ({total_size_converted:.2f} {size_unit})")
            st.write(f"Unique Files: {unique_files:,}")
            st.write(f"Duplicate Files: {duplicate_count:,} ({duplicate_pct:.2f}% of total)")
            st.write(f"Wasted Space: {wasted_size_converted:.2f} {size_unit} ({wasted_pct:.2f}% of total)")
            st.write(f"Number of Duplicate Groups: {len(duplicate_keys):,}")
            
            # Create visualization
            try:
                if viz_type == "Overview":
                    # Create data for pie charts
                    status_counts = pd.DataFrame([
                        {'Status': 'Unique', 'Files': unique_files, 'Wasted': 0},
                        {'Status': 'Duplicate', 'Files': duplicate_count, 'Wasted': wasted_size_converted}
                    ])
                    
                    fig1 = px.pie(
                        status_counts,
                        names='Status',
                        values='Files',
                        title="File Uniqueness by Count",
                        color='Status',
                        color_discrete_map={'Unique': '#3498db', 'Duplicate': '#e74c3c'}
                    )
                    fig1.update_traces(textposition='inside', textinfo='percent+label')
                    
                    # Create histogram of duplicate counts
                    dup_histogram = dup_counts[dup_counts > 1].value_counts().sort_index()
                    
                    fig2 = px.bar(
                        x=dup_histogram.index,
                        y=dup_histogram.values,
                        labels={'x': 'Number of Duplicates', 'y': 'Count of Groups'},
                        title="Distribution of Duplicate Group Sizes",
                        color=dup_histogram.index,
                        color_continuous_scale='Reds'
                    )
                    
                    st.plotly_chart(fig1, use_container_width=True)
                    st.plotly_chart(fig2, use_container_width=True)
                
                elif viz_type == "By Extension":
                    # First, get the duplicate counts by extension
                    dup_by_ext = df_duplicates.groupby('extension').agg(
                        file_count=('name', 'count'),
                        unique_count=('dupKey', 'nunique'),
                        total_size=('size', 'sum')
                    ).reset_index()
                    
                    # Calculate duplicate files
                    dup_by_ext['duplicate_count'] = dup_by_ext['file_count'] - dup_by_ext['unique_count']
                    
                    # Convert sizes
                    dup_by_ext['size_converted'] = dup_by_ext['total_size'].apply(
                        lambda x: convert_size(x, size_unit)
                    )
                    
                    # Sort by duplicate count
                    dup_by_ext = dup_by_ext.sort_values('duplicate_count', ascending=False).head(15)
                    
                    fig = px.bar(
                        dup_by_ext,
                        x='extension',
                        y='duplicate_count',
                        title="Top 15 Extensions with Duplicates",
                        color='size_converted',
                        hover_data=['file_count', 'unique_count', 'size_converted'],
                        color_continuous_scale='Reds',
                        text_auto=True
                    )
                    
                    # Calculate duplication rate by extension
                    all_ext_counts = df_dup.groupby('extension').size()
                    
                    ext_data = []
                    for ext, count in all_ext_counts.items():
                        if ext in dup_by_ext['extension'].values:
                            dup_count = dup_by_ext.loc[dup_by_ext['extension'] == ext, 'duplicate_count'].iloc[0]
                            dup_rate = (dup_count / count) * 100
                        else:
                            dup_count = 0
                            dup_rate = 0
                            
                        ext_data.append({
                            'extension': ext,
                            'total_count': count,
                            'duplicate_count': dup_count,
                            'duplication_rate': dup_rate
                        })
                    
                    ext_rate_df = pd.DataFrame(ext_data)
                    
                    # Filter to extensions with at least 10 files
                    ext_rate_df = ext_rate_df[ext_rate_df['total_count'] >= 10]
                    
                    # Sort by duplication rate and get top 15
                    ext_rate_df = ext_rate_df.sort_values('duplication_rate', ascending=False).head(15)
                    
                    rate_fig = px.bar(
                        ext_rate_df,
                        x='extension',
                        y='duplication_rate',
                        title="Top 15 Extensions by Duplication Rate (%)",
                        color='duplication_rate',
                        hover_data=['duplicate_count', 'total_count'],
                        color_continuous_scale='Reds',
                        text_auto='.1f'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.plotly_chart(rate_fig, use_container_width=True)
                
                else:  # By Folder
                    # Get duplicates by folder
                    dup_by_folder = df_duplicates.groupby('parentPath').agg(
                        file_count=('name', 'count'),
                        unique_count=('dupKey', 'nunique'),
                        total_size=('size', 'sum')
                    ).reset_index()
                    
                    # Calculate duplicate files
                    dup_by_folder['duplicate_count'] = dup_by_folder['file_count'] - dup_by_folder['unique_count']
                    
                    # Convert sizes
                    dup_by_folder['size_converted'] = dup_by_folder['total_size'].apply(
                        lambda x: convert_size(x, size_unit)
                    )
                    
                    # Sort by duplicate count and get top 15
                    top_folders = dup_by_folder.sort_values('duplicate_count', ascending=False).head(15)
                    
                    # Extract folder name for display
                    top_folders['folder_name'] = top_folders['parentPath'].apply(
                        lambda x: x.split('/')[-1] if x and '/' in x else x
                    )
                    
                    folder_fig = px.bar(
                        top_folders,
                        x='duplicate_count',
                        y='folder_name',
                        orientation='h',
                        title="Top 15 Folders with Duplicate Files",
                        color='size_converted',
                        hover_data=['parentPath', 'file_count', 'unique_count'],
                        color_continuous_scale='Reds'
                    )
                    
                    st.plotly_chart(folder_fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
        
        # Detailed list of duplicate groups
        if show_list and len(duplicate_keys) > 0:
            st.subheader("📋 Duplicate File Groups")
            
            # Get top duplicate groups by size impact
            dup_size_impact = df_duplicates.groupby('dupKey').agg(
                count=('name', 'count'),
                size=('size', 'first')
            )
            
            dup_size_impact['wasted_space'] = (dup_size_impact['count'] - 1) * dup_size_impact['size']
            top_dups = dup_size_impact.sort_values('wasted_space', ascending=False).head(dup_limit).index.tolist()
            
            # Display each duplicate group
            for i, dup_key in enumerate(top_dups, 1):
                dup_group = df_duplicates[df_duplicates['dupKey'] == dup_key].copy()
                
                # Calculate wasted space
                file_size = dup_group['size'].iloc[0]
                file_count = len(dup_group)
                
                file_size_converted = convert_size(file_size, size_unit)
                wasted_space = (file_count - 1) * file_size
                wasted_space_converted = convert_size(wasted_space, size_unit)
                
                st.write(f"**Group {i}: {file_count} copies, {file_size_converted:.2f} {size_unit} each, wasting {wasted_space_converted:.2f} {size_unit}**")
                
                # Format for display
                display_cols = ['name', 'parentPath', 'extension']
                if 'createTime' in dup_group.columns:
                    display_cols.append('createTime')
                if 'isDeleted' in dup_group.columns:
                    display_cols.append('isDeleted')
                
                st.dataframe(dup_group[display_cols], use_container_width=True)
                
                if i < len(top_dups):
                    st.markdown("---")

else:
    # Show instructions when no file is uploaded
    st.markdown("""
    ## Instructions
    
    Upload your file data CSV using the uploader in the sidebar. The CSV must contain the following columns:
    
    * `name`: File name
    * `parentPath`: Full path to the parent folder
    * `size`: File size in bytes
    
    ### Optional Columns for Enhanced Features:
    
    * `createTime`: File creation time
    * `modifyTime`: File last modification time  
    * `classifications`: File classifications or tags
    * `isDeleted`: Whether the file is deleted (1=deleted, 0=active)
    * `dupKey`: Duplicate identification key (e.g., MD5/SHA hash)
    
    ### Example Data Format:
    """)
    
    example_data = pd.DataFrame([
        {
            "name": "report.pdf", 
            "parentPath": "/documents/work", 
            "size": 1048576,
            "createTime": "2023-05-15T09:30:00Z",
            "classifications": "confidential",
            "isDeleted": 0,
            "dupKey": "a1b2c3d4"
        },
        {
            "name": "presentation.pptx", 
            "parentPath": "/documents/presentations", 
            "size": 2097152,
            "createTime": "2023-06-12T14:45:00Z",
            "classifications": "internal",
            "isDeleted": 0,
            "dupKey": "e5f6g7h8"
        }
    ])
    
    st.dataframe(example_data, use_container_width=True)