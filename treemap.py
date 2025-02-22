import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load the CSV file
file_path = "foldersummary.csv"  # Ensure the file is in the same directory
df = pd.read_csv(file_path)

# Split folder paths into multiple levels
df["Path_Parts"] = df["Subfolder"].apply(lambda x: x.strip("/").split("/"))

# Create hierarchical data for the treemap
tree_data = []
for _, row in df.iterrows():
    path_parts = row["Path_Parts"]
    for i in range(1, len(path_parts) + 1):
        tree_data.append({
            "Folder": "/".join(path_parts[:i]),  # Full path up to this level
            "Parent": "/".join(path_parts[:i-1]) if i > 1 else "",  # Parent folder
            "Size": row["Size"] if i == len(path_parts) else 0,  # Assign size only at the last level
            "Count": row["Count"] if i == len(path_parts) else 0  # Assign count only at the last level
        })

# Convert to DataFrame and aggregate data at each level
tree_df = pd.DataFrame(tree_data)
tree_df = tree_df.groupby(["Folder", "Parent"], as_index=False).sum()

# Initialize Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Interactive Folder Treemap"),
    
    dcc.Graph(id="treemap"),
])

# Callback to generate treemap
@app.callback(
    Output("treemap", "figure"),
    Input("treemap", "id")  # Placeholder input to trigger initial load
)
def update_treemap(_):
    fig = px.treemap(
        tree_df,
        path=["Parent", "Folder"],  # Define hierarchy
        values="Size",  # Use folder size for visualization
        color="Count",  # Color by file count
        hover_data=["Size", "Count"],  # Show file count and size on hover
        title="Folder Structure - Click to Expand",
    )

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
