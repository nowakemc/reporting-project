import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit UI
st.title("📁 Deep Folder Structure Sunburst Chart")

# File Uploader
uploaded_file = st.file_uploader("Upload your folder summary CSV file", type=["csv"])

if uploaded_file:
    # Load the CSV file
    df = pd.read_csv(uploaded_file)

    # Ensure necessary columns exist
    required_columns = {"Subfolder", "Size", "Count"}
    if not required_columns.issubset(df.columns):
        st.error("The CSV file must contain 'Subfolder', 'Size', and 'Count' columns.")
        st.stop()

    # Convert Size from bytes to MB
    df["Size_MB"] = df["Size"] / (1024 * 1024)

    # Calculate total values for percentage calculation
    total_size_mb = df["Size_MB"].sum()
    total_count = df["Count"].sum()

    # Calculate percentages
    df["Size_Percentage"] = (df["Size_MB"] / total_size_mb) * 100
    df["Count_Percentage"] = (df["Count"] / total_count) * 100

    # Extract folder hierarchy
    df["Path Parts"] = df["Subfolder"].str.strip("/").str.split("/")
    max_depth = df["Path Parts"].apply(len).max()  # Find the deepest folder level

    # Create dynamic folder level columns
    for i in range(max_depth):
        df[f"Level {i+1}"] = df["Path Parts"].apply(lambda x: x[i] if len(x) > i else "Unknown")

    # User selects the metric to display
    metric = st.radio("Select Metric to Display:", ["Size (MB)", "File Count"])

    # Configure Sunburst Chart
    sunburst_path = [f"Level {i+1}" for i in range(max_depth)]
    
    if metric == "Size (MB)":
        value_column = "Size_MB"
        color_column = "Size_MB"
        percentage_column = "Size_Percentage"
        hover_data = {
            "Size_MB": ":.2f MB",  # Format size to two decimal places
            "Size_Percentage": ":.2f%",  # Show percentage
        }
    else:
        value_column = "Count"
        color_column = "Count"
        percentage_column = "Count_Percentage"
        hover_data = {
            "Count": ":d",  # Display count as an integer
            "Count_Percentage": ":.2f%",  # Show percentage
        }

    fig = px.sunburst(
        df, 
        path=sunburst_path, 
        values=value_column, 
        title=f"📊 Deep Folder {metric} Sunburst Chart",
        color=color_column, 
        color_continuous_scale="viridis" if metric == "Size (MB)" else "blues",
        hover_data=hover_data
    )

    # Show the interactive Sunburst Chart
    st.plotly_chart(fig)
