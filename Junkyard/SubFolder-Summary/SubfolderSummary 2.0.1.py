import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import base64
from io import BytesIO
import plotly.io as pio
from collections import Counter
import time
import urllib.parse
import hashlib  # For secure handling of credentials
import traceback  # For detailed error tracking
import io  # For in-memory file handling

# Initialize session state for persistent values
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data_loaded = False
    st.session_state.depth_level = 5
    st.session_state.size_threshold = 0
    st.session_state.top_size_n = 10
    st.session_state.top_count_n = 10
    st.session_state.selected_folder = "All Folders"
    st.session_state.metric = "Size"
    st.session_state.viz_type = "Sunburst Chart"
    st.session_state.color_scheme = "Viridis"
    st.session_state.size_unit = "MB"
    # Database-specific state
    st.session_state.db_data = None
    st.session_state.db_query_executed = False
    st.session_state.db_query_success = False

# Set page config
st.set_page_config(layout="wide", page_title="📁 Deep Folder Structure Visualizer", menu_items={
    'Get Help': 'https://github.com/yourusername/folder-visualizer',
    'Report a bug': 'https://github.com/yourusername/folder-visualizer/issues',
    'About': 'This app visualizes folder structures from CSV files or database queries.'
})

# Helper function to safely update session state
def update_session_state(key, value):
    """Safely update session state to prevent reset loops"""
    if key in st.session_state and st.session_state[key] != value:
        st.session_state[key] = value

# Add caching for performance improvement - DISABLED for database queries to fix crashes
def fetch_database_data(url, query, options, auth=None):
    """Fetch data from database without caching to prevent state issues"""
    import requests
    from requests.auth import HTTPBasicAuth
    
    params = {
        "select": query,
        "options": options
    }
    
    # Make the request with or without authentication
    if auth:
        username, password = auth
        response = requests.get(url, params=params, auth=HTTPBasicAuth(username, password))
    else:
        response = requests.get(url, params=params)
        
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")
        
# Process data without caching for database queries
def process_data(data):
    """Process data without caching to prevent state issues"""
    try:
        return pd.read_csv(data)
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return pd.DataFrame()

# Streamlit UI
st.title("📁 Deep Folder Structure Visualizer")
st.markdown("Upload a CSV file with folder structure data to visualize and analyze it.")

# Sidebar for controls
st.sidebar.header("Controls")

# Data Source Selection
data_source = st.sidebar.radio("Select Data Source", ["Upload CSV", "Database Query"])

if data_source == "Upload CSV":
    # File Uploader
    uploaded_file = st.sidebar.file_uploader("Upload your folder summary CSV file", type=["csv"])
else:
    # Database Query
    st.sidebar.subheader("Database Connection")
    
    # Only show input fields if query not executed or no successful data
    if not st.session_state.db_query_executed or not st.session_state.db_query_success:
        server_url = st.sidebar.text_input("Server URL", value="http://10.1.10.163")
        query_endpoint = st.sidebar.text_input(
            "Query Endpoint", 
            value="/server/api/v3/database/query"
        )
        
        # Authentication settings
        use_auth = st.sidebar.checkbox("Use Basic Authentication", value=True)
        
        auth = None
        if use_auth:
            auth_col1, auth_col2 = st.sidebar.columns(2)
            with auth_col1:
                username = st.text_input("Username", type="default")
            with auth_col2:
                password = st.text_input("Password", type="password")
            
            if username and password:
                auth = (username, password)
            elif use_auth:
                st.sidebar.warning("Authentication enabled but credentials not provided")
        
        # Query customization options
        st.sidebar.subheader("Query Options")
        limit = st.sidebar.number_input("Result Limit", min_value=100, max_value=100000, value=25000, step=1000)
        class_filter = st.sidebar.text_input("Class ID Filter", value="idxobject")
        
        query = f"""
        SELECT    
          COMPONENTS(parentPath, 25) AS Subfolder,
          SUM(size) as "Size",
          COUNT(name) as "Count"
        WHERE ClassID LIKE '{class_filter}'
        GROUP BY Subfolder
        ORDER BY SUM(size) Desc
        LIMIT {limit}
        """
        
        # Display the query with option to edit
        st.sidebar.subheader("SQL Query")
        query = st.sidebar.text_area("Edit Query (Optional)", value=query, height=200)
    else:
        # Show a summary of the last query when data is loaded
        st.sidebar.info(f"Using data from previous query to server: {st.session_state.db_server_url}")
        
        # Add option to edit query parameters
        if st.sidebar.checkbox("Edit Query Parameters", value=False):
            # Reset the query state
            if st.sidebar.button("Reset Query Parameters"):
                st.session_state.db_query_executed = False
                st.session_state.db_data = None
                st.experimental_rerun()
    
    # Execute query button
    fetch_button_disabled = use_auth and (not username or not password)
    
    if fetch_button_disabled:
        st.sidebar.button("Fetch Data", disabled=True, help="Please enter authentication credentials")
        fetch_data = False
    else:
        fetch_data = st.sidebar.button("Fetch Data")
    
    uploaded_file = None
    if fetch_data:
        try:
            # Measure query execution time
            start_time = time.time()
            
            # Construct the full URL
            full_url = f"{server_url.rstrip('/')}{query_endpoint}"
            options_json = '{"format":"csv","stream":true}'
            
            with st.spinner("Fetching data from database..."):
                # Use cached function to fetch data
                csv_data = fetch_database_data(full_url, query, options_json, auth)
                
                # Create a file-like object from the response content
                from io import StringIO
                uploaded_file = StringIO(csv_data)
                
                # Calculate query time
                query_time = time.time() - start_time
                
                # Show success message with timing info
                st.sidebar.success(f"Successfully fetched data ({len(csv_data)} bytes) in {query_time:.2f} seconds")
                
                # Show authentication status if used
                if auth:
                    st.sidebar.info(f"Authenticated as user: {username}")
                
                # Add option to save the raw CSV
                csv_b64 = base64.b64encode(csv_data.encode()).decode()
                download_link = f'<a href="data:file/csv;base64,{csv_b64}" download="folder_data_raw.csv">Download Raw CSV Data</a>'
                st.sidebar.markdown(download_link, unsafe_allow_html=True)
        except Exception as e:
            error_message = str(e)
            st.sidebar.error(f"Error: {error_message}")
            
            # Provide more helpful error messages for common issues
            if "401" in error_message:
                st.sidebar.warning("Authentication failed. Please check your username and password.")
            elif "Connection" in error_message or "Timeout" in error_message:
                st.sidebar.warning("Could not connect to the server. Please verify the URL and network connection.")
            elif "500" in error_message:
                st.sidebar.warning("Server error. The query might be invalid or the server is experiencing issues.")

if uploaded_file:
    # Load the CSV file
    try:
        # Process the data based on source
        if data_source == "Database Query":
            df = process_data(uploaded_file)
        else:
            # For manual uploads, we can still use caching safely
            @st.cache_data(ttl=3600)
            def process_upload(file):
                return pd.read_csv(file)
            
            df = process_upload(uploaded_file)
            
        st.session_state.data_loaded = True
        
        # Display success message
        if data_source == "Upload CSV":
            st.sidebar.success("CSV data loaded successfully!")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.error(traceback.format_exc())
        st.stop()

    # Ensure necessary columns exist
    required_columns = {"Subfolder", "Size", "Count"}
    if not required_columns.issubset(df.columns):
        st.error("The CSV file must contain 'Subfolder', 'Size', and 'Count' columns.")
        if data_source == "Database Query":
            st.error("Your database query must include these column names exactly.")
            if 'db_error' in st.session_state:
                with st.expander("Database Error Details"):
                    st.code(st.session_state.db_error)
        st.stop()

    # Extract folder hierarchy
    try:
        df["Path Parts"] = df["Subfolder"].str.strip("/").str.split("/")
        max_depth = df["Path Parts"].apply(len).max()  # Find the deepest folder level
    except Exception as e:
        st.error(f"Error processing folder paths: {str(e)}")
        st.error("Please make sure your data contains a 'Subfolder' column with proper path format.")
        st.stop()
    
    # Create compressed path representation for very deep paths
    MAX_SUPPORTED_LEVELS = 10  # Maximum levels for visualization
    
    if max_depth > MAX_SUPPORTED_LEVELS:
        st.warning(f"Your folder structure is very deep ({max_depth} levels). Visualizing with a compressed representation.")
        
        # Create standard level columns up to the supported max
        for i in range(MAX_SUPPORTED_LEVELS):
            if i < 3:  # First 3 levels as is
                df[f"Level {i+1}"] = df["Path Parts"].apply(lambda x: x[i] if len(x) > i else "")
            elif i == 3:  # Middle level shows collapsed representation
                df[f"Level {i+1}"] = df["Path Parts"].apply(
                    lambda x: f"[{len(x) - 6} more...]" if len(x) > MAX_SUPPORTED_LEVELS else 
                              (x[i] if len(x) > i else "")
                )
            else:  # Last levels (if available)
                # For paths that are too deep, show the last levels
                # For paths that aren't as deep, just show the normal level
                df[f"Level {i+1}"] = df["Path Parts"].apply(
                    lambda x: x[len(x) - (MAX_SUPPORTED_LEVELS - i)] if len(x) > MAX_SUPPORTED_LEVELS 
                              else (x[i] if len(x) > i else "")
                )
    else:
        # If max depth is within limits, create normal level columns
        for i in range(max_depth):
            df[f"Level {i+1}"] = df["Path Parts"].apply(lambda x: x[i] if len(x) > i else "")

    # Feature 1: Size Unit Toggle
    size_unit = st.sidebar.selectbox(
        "Size Unit", 
        ["Bytes", "KB", "MB", "GB"],
        index=["Bytes", "KB", "MB", "GB"].index(st.session_state.size_unit)
    )
    update_session_state('size_unit', size_unit)
    
    # Convert size based on selected unit
    if size_unit == "Bytes":
        df["Size_Converted"] = df["Size"]
        size_label = "Bytes"
    elif size_unit == "KB":
        df["Size_Converted"] = df["Size"] / 1024
        size_label = "KB"
    elif size_unit == "MB":
        df["Size_Converted"] = df["Size"] / (1024 * 1024)
        size_label = "MB"
    else:  # GB
        df["Size_Converted"] = df["Size"] / (1024 * 1024 * 1024)
        size_label = "GB"

    # Calculate total values for percentage calculation
    total_size = df["Size_Converted"].sum()
    total_count = df["Count"].sum()

    # Calculate percentages
    df["Size_Percentage"] = (df["Size_Converted"] / total_size) * 100
    df["Count_Percentage"] = (df["Count"] / total_count) * 100

    # Feature 2: Depth Control Slider
    available_levels = min(max_depth, 10)  # Limit to 10 levels to prevent visualization errors
    
    # Use a workaround for slider reset issues
    if 'depth_level' not in st.session_state or st.session_state.depth_level > available_levels:
        st.session_state.depth_level = min(available_levels, 5)
        
    depth_level = st.sidebar.slider(
        "Max Folder Depth to Display", 
        min_value=1, 
        max_value=available_levels, 
        value=st.session_state.depth_level,
        key="depth_level_slider"
    )
    update_session_state('depth_level', depth_level)

    # Feature 3: Folder Filter/Focus
    # First create a list of unique folders and subfolders for the dropdown
    all_paths = []
    for idx, row in df.iterrows():
        path_parts = row["Path Parts"]
        for i in range(1, len(path_parts) + 1):
            partial_path = "/".join(path_parts[:i])
            if partial_path and partial_path not in all_paths:
                all_paths.append(partial_path)
    
    folder_options = ["All Folders"] + sorted(all_paths)
    selected_folder = st.sidebar.selectbox(
        "Focus on Specific Folder", 
        folder_options,
        index=folder_options.index(st.session_state.selected_folder) if st.session_state.selected_folder in folder_options else 0
    )
    update_session_state('selected_folder', selected_folder)

    # Filter data based on selected folder
    if selected_folder != "All Folders":
        # Filter to include only selected folder and its subfolders
        df_filtered = df[df["Subfolder"].str.startswith(selected_folder)]
        
        # Adjust paths for visualization - make the selected folder the root
        if depth_level > 1:
            # Count segments in the selected path
            prefix_segments = len(selected_folder.split("/"))
            
            # Create new level columns adjusted for the selected path prefix
            for i in range(depth_level):
                level_idx = i + 1
                df_filtered[f"Adjusted Level {level_idx}"] = df_filtered["Path Parts"].apply(
                    lambda x: x[prefix_segments + i - 1] if len(x) > prefix_segments + i - 1 else ""
                )
                
            # Use the adjusted level columns for visualization
            path_columns = [f"Adjusted Level {i+1}" for i in range(min(depth_level, available_levels))]
        else:
            # If only showing one level, just show immediate children
            path_columns = ["Level 1"]
    else:
        df_filtered = df.copy()
        # Ensure we only use columns that exist
        path_columns = [f"Level {i+1}" for i in range(min(depth_level, available_levels))]

    # Feature 4: Size Threshold Filter
    max_size = float(df_filtered["Size_Converted"].max())
    min_size = float(df_filtered["Size_Converted"].min())
    
    # Initialize or update threshold in session state
    if st.session_state.size_threshold < min_size or st.session_state.size_threshold > max_size:
        st.session_state.size_threshold = min_size
        
    size_threshold = st.sidebar.slider(
        f"Minimum Size ({size_label})", 
        min_value=min_size, 
        max_value=max_size, 
        value=st.session_state.size_threshold, 
        step=(max_size-min_size)/100,
        key="size_threshold_slider"
    )
    update_session_state('size_threshold', size_threshold)
    
    # Apply size threshold filter - safely with error handling
    try:
        df_filtered = df_filtered[df_filtered["Size_Converted"] >= size_threshold]
    except Exception as e:
        st.warning(f"Error applying size filter: {str(e)}")
        # Continue with original data
        df_filtered = df_filtered

    # Feature 5: Top N Folders View
    show_top_n = st.sidebar.checkbox("Show Only Top Folders", value=False, key="show_top_n_checkbox")
    if show_top_n and not df_filtered.empty:
        default_top_n = min(10, len(df_filtered))
        max_top_n = min(50, len(df_filtered))
        
        top_n = st.sidebar.slider(
            "Number of Top Folders to Display", 
            min_value=5, 
            max_value=max_top_n, 
            value=default_top_n,
            key="top_n_slider"
        )
        
        # Apply filter safely
        try:
            if len(df_filtered) > top_n:
                df_filtered = df_filtered.nlargest(top_n, "Size_Converted")
        except Exception as e:
            st.sidebar.error(f"Error filtering top folders: {str(e)}")
            # Fallback to not filtering if there's an error

    # Feature 6: Visualization Type
    viz_type = st.sidebar.radio(
        "Visualization Type", 
        ["Sunburst Chart", "Treemap"],
        index=0 if st.session_state.viz_type == "Sunburst Chart" else 1,
        key="viz_type_radio"
    )
    update_session_state('viz_type', viz_type)

    # Feature 7: Metric Selection
    metric = st.sidebar.radio(
        "Select Metric to Display:", 
        ["Size", "File Count"],
        index=0 if st.session_state.metric == "Size" else 1,
        key="metric_radio"
    )
    update_session_state('metric', metric)

    # Feature 8: Custom Color Schemes
    color_schemes = {
        "Viridis": "viridis", 
        "Plasma": "plasma", 
        "Inferno": "inferno", 
        "Magma": "magma",
        "Cividis": "cividis",
        "Turbo": "turbo",
        "Blues": "blues",
        "Greens": "greens",
        "Reds": "reds",
        "YlOrRd": "YlOrRd",
        "YlGnBu": "YlGnBu"
    }
    
    color_scheme_options = list(color_schemes.keys())
    default_index = color_scheme_options.index(st.session_state.color_scheme) if st.session_state.color_scheme in color_scheme_options else 0
    
    color_scheme = st.sidebar.selectbox(
        "Color Scheme", 
        color_scheme_options,
        index=default_index,
        key="color_scheme_select"
    )
    update_session_state('color_scheme', color_scheme)

    # Main content area - only proceed if we have data to show
    if not df_filtered.empty:
        st.subheader("Folder Structure Visualization")
        
        # Configure visualization based on selected metric
        if metric == "Size":
            value_column = "Size_Converted"
            color_column = "Size_Converted"
            percentage_column = "Size_Percentage"
            hover_data = {
                "Size_Converted": f":.2f {size_label}",
                "Size_Percentage": ":.2f%",
            }
            color_label = f"Size ({size_label})"
        else:  # File Count
            value_column = "Count"
            color_column = "Count"
            percentage_column = "Count_Percentage"
            hover_data = {
                "Count": ":d",
                "Count_Percentage": ":.2f%",
            }
            color_label = "File Count"
        
        # Create visualization based on selected type
        try:
            # Check if path columns exist in the dataframe
            valid_path_columns = [col for col in path_columns if col in df_filtered.columns]
            
            if not valid_path_columns:
                st.error("No valid path columns found. Please adjust depth level or check your data.")
                st.stop()
                
            # Create visualization based on selected type
            if viz_type == "Sunburst Chart":
                fig = px.sunburst(
                    df_filtered,
                    path=valid_path_columns,
                    values=value_column,
                    title=f"📊 Folder Structure {metric}" + (f" - {selected_folder}" if selected_folder != "All Folders" else ""),
                    color=color_column,
                    color_continuous_scale=color_schemes[color_scheme],
                    hover_data=hover_data,
                    branchvalues="total"
                )
            else:  # Treemap
                fig = px.treemap(
                    df_filtered,
                    path=valid_path_columns,
                    values=value_column,
                    title=f"📊 Folder Structure {metric}" + (f" - {selected_folder}" if selected_folder != "All Folders" else ""),
                    color=color_column,
                    color_continuous_scale=color_schemes[color_scheme],
                    hover_data=hover_data,
                    branchvalues="total"
                )
            
            fig.update_layout(
                margin=dict(t=50, l=10, r=10, b=10),
                coloraxis_colorbar=dict(
                    title=color_label,
                )
            )
            
            # Show the interactive visualization
            st.plotly_chart(fig, use_container_width=True)
            
            # Feature 9: Export Options
            st.subheader("Export Options")
            col1, col2 = st.columns(2)
            
            # Export image
            with col1:
                export_format = st.selectbox(
                    "Export Image Format", 
                    ["PNG", "SVG", "PDF", "JPEG"]
                )
                
                if st.button(f"Export as {export_format}"):
                    # Convert the figure to the selected format
                    img_bytes = pio.to_image(fig, format=export_format.lower())
                    
                    # Create a download link
                    b64 = base64.b64encode(img_bytes).decode()
                    href = f'<a href="data:image/{export_format.lower()};base64,{b64}" download="folder_structure.{export_format.lower()}">Download {export_format} Image</a>'
                    st.markdown(href, unsafe_allow_html=True)
            
            # Export data
            with col2:
                export_data_format = st.selectbox(
                    "Export Data Format", 
                    ["CSV", "Excel", "JSON"]
                )
                
                if st.button(f"Export Data as {export_data_format}"):
                    if export_data_format == "CSV":
                        csv = df_filtered.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="folder_data.csv">Download CSV File</a>'
                    elif export_data_format == "Excel":
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_filtered.to_excel(writer, sheet_name='Folder Data', index=False)
                        buffer.seek(0)
                        b64 = base64.b64encode(buffer.read()).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="folder_data.xlsx">Download Excel File</a>'
                    else:  # JSON
                        json_str = df_filtered.to_json(orient='records')
                        b64 = base64.b64encode(json_str.encode()).decode()
                        href = f'<a href="data:application/json;base64,{b64}" download="folder_data.json">Download JSON File</a>'
                    
                    st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error creating visualization: {str(e)}")
            st.info("This error often occurs when trying to visualize too many folder levels. Try reducing the 'Max Folder Depth to Display' setting in the sidebar.")
            
            # Show technical details in an expandable section
            with st.expander("Technical Details"):
                st.write("Error details:", str(e))
                st.write("Available columns:", df_filtered.columns.tolist())
                st.write("Attempted path columns:", path_columns)
                if 'valid_path_columns' in locals():
                    st.write("Valid path columns:", valid_path_columns)
        
        # Feature 10: Statistics Panel
        st.subheader("Folder Statistics")
        
        # Create columns for statistics layout
        stat_col1, stat_col2 = st.columns(2)
        
        with stat_col1:
            st.write("**Size Statistics**")
            
            # Largest folder by size
            largest_folder = df.loc[df["Size"].idxmax()]
            st.write(f"Largest Folder: {largest_folder['Subfolder']} ({largest_folder['Size_Converted']:.2f} {size_label})")
            
            # Total Size
            st.write(f"Total Size: {total_size:.2f} {size_label}")
            
            # Average folder size
            avg_size = df["Size_Converted"].mean()
            st.write(f"Average Folder Size: {avg_size:.2f} {size_label}")
            
            # Size Distribution
            st.write(f"Size Distribution (Quartiles in {size_label}):")
            size_quartiles = np.percentile(df["Size_Converted"], [25, 50, 75])
            st.write(f"- 25%: {size_quartiles[0]:.2f}")
            st.write(f"- 50% (Median): {size_quartiles[1]:.2f}")
            st.write(f"- 75%: {size_quartiles[2]:.2f}")
            
        with stat_col2:
            st.write("**Structure Statistics**")
            
            # Folder with most files
            most_files_folder = df.loc[df["Count"].idxmax()]
            st.write(f"Folder with Most Files: {most_files_folder['Subfolder']} ({most_files_folder['Count']} files)")
            
            # Total files
            st.write(f"Total Files: {total_count}")
            
            # Number of folders
            num_folders = len(df)
            st.write(f"Total Folders: {num_folders}")
            
            # Average files per folder
            avg_files = df["Count"].mean()
            st.write(f"Average Files per Folder: {avg_files:.2f}")
            
            # Deepest nested folder
            deepest_folder = df.loc[df["Path Parts"].apply(len).idxmax()]
            st.write(f"Deepest Nested Folder: {deepest_folder['Subfolder']} (Depth: {len(deepest_folder['Path Parts'])})")
            
            # Number of empty folders
            empty_folders = len(df[df["Count"] == 0])
            st.write(f"Empty Folders: {empty_folders}")
        
        # Feature 11: Path Distribution Analysis
        st.subheader("Path Distribution Analysis")
        
        # Add refresh/recalculate button for database fetched data
        if data_source == "Database Query":
            last_refresh = time.strftime('%Y-%m-%d %H:%M:%S')
            st.caption(f"Last data refresh: {last_refresh}")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Refresh Data", key="refresh_data_button"):
                    # For database mode, reset state to force new query
                    if data_source == "Database Query":
                        st.session_state.db_query_executed = False
                        st.session_state.db_data = None
                    # For CSV mode, clear caches
                    else:
                        try:
                            st.cache_data.clear()
                        except:
                            pass
                    # Rerun the app
                    st.experimental_rerun()
        
        # Count folders at each depth
        depth_counts = Counter(df["Path Parts"].apply(len))
        depths = sorted(depth_counts.keys())
        counts = [depth_counts[d] for d in depths]
        
        # Create histogram of folder depths
        depth_fig = px.bar(
            x=depths, 
            y=counts, 
            labels={"x": "Folder Depth", "y": "Number of Folders"},
            title="Distribution of Folder Depths"
        )
        
        # Draw a vertical line at the average depth
        avg_depth = sum(d * c for d, c in zip(depths, counts)) / sum(counts)
        depth_fig.add_vline(
            x=avg_depth, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Avg: {avg_depth:.1f}",
            annotation_position="top right"
        )
        
        st.plotly_chart(depth_fig, use_container_width=True)
        
        # Feature 12: Top folders by size and by count
        st.subheader("Top Folders Analysis")
        
        top_col1, top_col2 = st.columns(2)
        
        # Top folders by size
        with top_col1:
            max_top_folders = min(50, len(df))
            
            # Set or maintain slider value
            if 'top_size_n' not in st.session_state or st.session_state.top_size_n > max_top_folders:
                st.session_state.top_size_n = min(10, max_top_folders)
                
            top_size_n = st.slider(
                "Number of Top Folders by Size", 
                min_value=5, 
                max_value=max_top_folders, 
                value=st.session_state.top_size_n,
                key="top_size_slider"
            )
            update_session_state('top_size_n', top_size_n)
            
            top_size = df.nlargest(top_size_n, "Size_Converted")
            
            # Truncate long folder names for better display
            top_size["Display_Name"] = top_size["Subfolder"].apply(
                lambda x: x.split("/")[-1] if x.split("/")[-1] else x.split("/")[-2] if len(x.split("/")) > 1 else x
            )
            
            size_bar_fig = px.bar(
                top_size,
                x="Size_Converted",
                y="Display_Name",
                orientation="h",
                title=f"Top {top_size_n} Folders by Size",
                labels={"Size_Converted": f"Size ({size_label})", "Display_Name": "Folder Name"},
                color="Size_Converted",
                color_continuous_scale=color_schemes[color_scheme],
                hover_data={"Subfolder": True}
            )
            
            st.plotly_chart(size_bar_fig, use_container_width=True)
        
        # Top folders by file count
        with top_col2:
            max_top_folders = min(50, len(df))
            
            # Set or maintain slider value
            if 'top_count_n' not in st.session_state or st.session_state.top_count_n > max_top_folders:
                st.session_state.top_count_n = min(10, max_top_folders)
                
            top_count_n = st.slider(
                "Number of Top Folders by File Count", 
                min_value=5, 
                max_value=max_top_folders, 
                value=st.session_state.top_count_n,
                key="top_count_slider"
            )
            update_session_state('top_count_n', top_count_n)
            
            top_count = df.nlargest(top_count_n, "Count")
            
            # Truncate long folder names for better display
            top_count["Display_Name"] = top_count["Subfolder"].apply(
                lambda x: x.split("/")[-1] if x.split("/")[-1] else x.split("/")[-2] if len(x.split("/")) > 1 else x
            )
            
            count_bar_fig = px.bar(
                top_count,
                x="Count",
                y="Display_Name",
                orientation="h",
                title=f"Top {top_count_n} Folders by File Count",
                labels={"Count": "File Count", "Display_Name": "Folder Name"},
                color="Count",
                color_continuous_scale=color_schemes[color_scheme],
                hover_data={"Subfolder": True}
            )
            
            st.plotly_chart(count_bar_fig, use_container_width=True)
    else:
        st.warning("No data to display after applying filters. Try adjusting your filtering options.")
        
elif data_source == "Upload CSV":
    # Show instructions when no file is uploaded but upload option selected
    st.markdown("""
    ## Instructions
    1. Use the file uploader in the sidebar to upload your folder summary CSV file.
    2. The CSV must have the following columns:
       - `Subfolder`: The path to each folder
       - `Size`: The size of the folder in bytes
       - `Count`: The number of files in the folder

    ### Features:
    - Switch between Sunburst and Treemap visualizations
    - Focus on specific subfolders
    - Control the visualization depth
    - Change size units (B, KB, MB, GB)
    - Filter by size threshold
    - Show only top N folders
    - Customize color schemes
    - Export visualizations and data
    - View comprehensive folder statistics
    - Analyze path distribution
    """)
    
    # Sample data preview
    st.subheader("Example CSV Format")
    sample_data = pd.DataFrame([
        {"Subfolder": "/home/user/documents", "Size": 1048576, "Count": 15},
        {"Subfolder": "/home/user/documents/work", "Size": 524288, "Count": 8},
        {"Subfolder": "/home/user/pictures", "Size": 3145728, "Count": 25}
    ])
    st.dataframe(sample_data)