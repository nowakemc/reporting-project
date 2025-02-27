import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import base64
from io import BytesIO
import plotly.io as pio
from collections import Counter

# Set page config
st.set_page_config(layout="wide", page_title="📁 Deep Folder Structure Visualizer")

# Streamlit UI
st.title("📁 Deep Folder Structure Visualizer")
st.markdown("Upload a CSV file with folder structure data to visualize and analyze it.")

# Sidebar for controls
st.sidebar.header("Controls")

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload your folder summary CSV file", type=["csv"])

if uploaded_file:
    # Load the CSV file
    df = pd.read_csv(uploaded_file)

    # Ensure necessary columns exist
    required_columns = {"Subfolder", "Size", "Count"}
    if not required_columns.issubset(df.columns):
        st.error("The CSV file must contain 'Subfolder', 'Size', and 'Count' columns.")
        st.stop()

    # Extract folder hierarchy
    df["Path Parts"] = df["Subfolder"].str.strip("/").str.split("/")
    max_depth = df["Path Parts"].apply(len).max()  # Find the deepest folder level

    # Create dynamic folder level columns
    for i in range(max_depth):
        df[f"Level {i+1}"] = df["Path Parts"].apply(lambda x: x[i] if len(x) > i else "")

    # Feature 1: Size Unit Toggle
    size_unit = st.sidebar.selectbox(
        "Size Unit", 
        ["Bytes", "KB", "MB", "GB"]
    )
    
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
    depth_level = st.sidebar.slider(
        "Max Folder Depth to Display", 
        min_value=1, 
        max_value=max_depth, 
        value=max_depth
    )

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
        folder_options
    )

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
            path_columns = [f"Adjusted Level {i+1}" for i in range(1, depth_level+1)]
        else:
            # If only showing one level, just show immediate children
            path_columns = ["Level 1"]
    else:
        df_filtered = df.copy()
        path_columns = [f"Level {i+1}" for i in range(1, depth_level+1)]

    # Feature 4: Size Threshold Filter
    max_size = float(df_filtered["Size_Converted"].max())
    min_size = float(df_filtered["Size_Converted"].min())
    size_threshold = st.sidebar.slider(
        f"Minimum Size ({size_label})", 
        min_value=min_size, 
        max_value=max_size, 
        value=min_size, 
        step=(max_size-min_size)/100
    )
    
    # Apply size threshold filter
    df_filtered = df_filtered[df_filtered["Size_Converted"] >= size_threshold]

    # Feature 5: Top N Folders View
    show_top_n = st.sidebar.checkbox("Show Only Top Folders", value=False)
    if show_top_n and not df_filtered.empty:
        top_n = st.sidebar.slider(
            "Number of Top Folders to Display", 
            min_value=5, 
            max_value=min(50, len(df_filtered)), 
            value=min(10, len(df_filtered))
        )
        df_filtered = df_filtered.nlargest(top_n, "Size_Converted")

    # Feature 6: Visualization Type
    viz_type = st.sidebar.radio(
        "Visualization Type", 
        ["Sunburst Chart", "Treemap"]
    )

    # Feature 7: Metric Selection
    metric = st.sidebar.radio(
        "Select Metric to Display:", 
        ["Size", "File Count"]
    )

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
    color_scheme = st.sidebar.selectbox(
        "Color Scheme", 
        list(color_schemes.keys())
    )

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
            if viz_type == "Sunburst Chart":
                fig = px.sunburst(
                    df_filtered,
                    path=path_columns,
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
                    path=path_columns,
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
            st.info("Try adjusting the depth level or folder focus to fix the issue.")
        
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
            top_size_n = st.slider(
                "Number of Top Folders by Size", 
                min_value=5, 
                max_value=min(20, len(df)), 
                value=min(10, len(df))
            )
            
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
            top_count_n = st.slider(
                "Number of Top Folders by File Count", 
                min_value=5, 
                max_value=min(20, len(df)), 
                value=min(10, len(df))
            )
            
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
        
else:
    # Show instructions when no file is uploaded
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