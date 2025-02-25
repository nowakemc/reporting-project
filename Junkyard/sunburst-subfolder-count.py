import pandas as pd
import plotly.express as px

# Load the CSV file (Update path as needed)
file_path = "foldersummary.csv"  # Replace with your actual file path
df = pd.read_csv(file_path)

# Determine the maximum depth in the folder hierarchy
df["Path Depth"] = df["Subfolder"].apply(lambda x: len(x.split("/")))

# Find the deepest path level to create dynamic columns
max_depth = df["Path Depth"].max()

# Create dynamic columns for each folder level
for i in range(1, max_depth):
    df[f"Level {i}"] = df["Subfolder"].apply(lambda x: x.split("/")[i] if len(x.split("/")) > i else "Unknown")

# Select columns dynamically for Sunburst path
sunburst_path = [f"Level {i}" for i in range(1, max_depth)]

# Create a Sunburst chart for deeper folder levels using file count
fig = px.sunburst(
    df, 
    path=sunburst_path, 
    values="Count",  # Use file count instead of size
    title="Deep Folder Structure - File Count",
    color="Count",  # Color by count
    color_continuous_scale="blues"  # Use a blue gradient for better contrast
)

# Show the interactive plot
fig.show()
