import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load the CSV file
file_path = "foldersummary.csv"  # Ensure the file is in the same directory
df = pd.read_csv(file_path)

# Calculate the maximum folder depth dynamically
df['Folder_Depth'] = df['Subfolder'].apply(lambda x: len(x.split('/')) - 1)  # Exclude root
max_levels = df['Folder_Depth'].max()  # Get the max depth

# Extract directory levels dynamically
for i in range(1, max_levels + 1):
    df[f"Level_{i}"] = df['Subfolder'].apply(lambda x: x.split('/')[i] if len(x.split('/')) > i else "N/A")

# Create a dictionary for aggregated file counts at each level
aggregated_data = {f"Level_{i}": df.groupby(f"Level_{i}")['Count'].sum().reset_index() for i in range(1, max_levels + 1)}

# Initialize Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Interactive File Count Visualization"),
    
    # Dropdown to choose directory level
    html.Label("Select Directory Level:"),
    dcc.Dropdown(
        id="directory-level",
        options=[{"label": f"Level {i}", "value": f"Level_{i}"} for i in range(1, max_levels + 1)],
        value="Level_1",
        clearable=False
    ),

    # Graph for interactive visualization
    dcc.Graph(id="bar-chart"),
])

# Callback to update the chart based on the dropdown selection
@app.callback(
    Output("bar-chart", "figure"),
    Input("directory-level", "value")
)
def update_chart(selected_level):
    data = aggregated_data[selected_level]

    fig = px.bar(
        data,
        x="Count",
        y=selected_level,
        orientation="h",
        text="Count",
        color="Count",
        color_continuous_scale="Viridis",
        title=f"File Count by {selected_level}"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
