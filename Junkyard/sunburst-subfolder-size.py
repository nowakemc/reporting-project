import pandas as pd
import plotly.express as px

# Load the CSV file (Update path as needed)
file_path = "foldersummary.csv"  # Replace with your actual file path
df = pd.read_csv(file_path)

# Convert Size from bytes to MB
df["Size_MB"] = df["Size"] / (1024 * 1024)

# Determine the maximum depth in the folder hierarchy
df["Path Depth"] = df["Subfolder"].apply(lambda x: len(x.split("/")))

# Find the deepest path level to create dynamic columns
max_depth = df["Path Depth"].max()

# Create dynamic columns for each folder level
for i in range(1, max_depth):
    df[f"Level {i}"] = df["Subfolder"].apply(lambda x: x.split("/")[i] if len(x.split("/")) > i else "Unknown")

# Select columns dynamically for Sunburst path
sunburst_path = [f"Level {i}" for i in range(1, max_depth)]

# Create a Sunburst chart for deeper folder levels
fig = px.sunburst(
    df, 
    path=sunburst_path, 
    values="Size_MB", 
    title="Deep Folder Storage Usage Sunburst Chart (in MB)",
    color="Size_MB",  # Color by size
    color_continuous_scale="viridis"  # Use a colorful gradient
)

# Show the interactive plot
fig.show()
