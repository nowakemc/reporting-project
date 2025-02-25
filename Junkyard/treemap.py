import pandas as pd
import plotly.express as px

# Load the CSV file (Update the path accordingly)
file_path = "foldersummary.csv"  # Replace with your actual file
df = pd.read_csv(file_path)

# Split the subfolder path into hierarchical levels
df["Path Parts"] = df["Subfolder"].str.split("/")

# Extract top-level and second-level folder names
df["Root"] = df["Path Parts"].apply(lambda x: x[1] if len(x) > 1 else "Unknown")
df["Subfolder Level 1"] = df["Path Parts"].apply(lambda x: x[2] if len(x) > 2 else "Unknown")

# Create a Sunburst chart for storage usage
fig = px.sunburst(df, path=["Root", "Subfolder Level 1"], values="Size", title="Folder Storage Usage Sunburst Chart")

# Show the interactive plot
fig.show()
