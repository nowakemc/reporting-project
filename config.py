"""
Configuration settings for the DuckDB Document Analysis app.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Default database path
DEFAULT_DB_PATH = str(BASE_DIR / "sample.duckdb")

# Cache settings
CACHE_TTL = 3600  # Cache time to live in seconds

# UI Configuration
APP_TITLE = "DuckDB Document Management Analyzer"
APP_ICON = "📊"
PAGE_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Time format for display
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Chart configuration
CHART_THEME = "streamlit"  # Options: streamlit, plotly, etc.
DEFAULT_CHART_WIDTH = 700
DEFAULT_CHART_HEIGHT = 400

# Color schemes
CHART_COLORS = {
    "primary": ["#FF4B4B", "#6272A4", "#8BE9FD", "#50FA7B", "#FFB86C", "#FF79C6", "#BD93F9"],
    "categorical": ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692"],
    "sequential": ["#0d0887", "#46039f", "#7201a8", "#9c179e", "#bd3786", "#d8576b", "#ed7953", "#fb9f3a", "#fdca26", "#f0f921"],
}

# Export configuration
EXPORT_FORMATS = ["csv", "json", "xlsx"]
MAX_EXPORT_ROWS = 100000  # Maximum number of rows to export

# Report configuration
REPORTS = {
    "overview": {
        "title": "Dashboard Overview",
        "icon": "📈",
        "description": "High-level overview of document management statistics"
    },
    "objects": {
        "title": "Objects Analysis",
        "icon": "📄",
        "description": "Analysis of document objects and their properties"
    },
    "instances": {
        "title": "Instances & Storage",
        "icon": "💾",
        "description": "Analysis of document instances and storage metrics"
    },
    "classifications": {
        "title": "Classifications",
        "icon": "🏷️",
        "description": "Analysis of document classifications and categories"
    },
    "permissions": {
        "title": "Security & Permissions",
        "icon": "🔒",
        "description": "Analysis of document permissions and access controls"
    },
    "services": {
        "title": "Services",
        "icon": "🔧",
        "description": "Analysis of services interacting with documents"
    },
    "messages": {
        "title": "Messages",
        "icon": "💬",
        "description": "Analysis of message data related to documents"
    },
    "folder_structure": {
        "title": "Folder Structure",
        "icon": "📁",
        "description": "Visualization and analysis of folder hierarchies"
    },
    "storage_sunburst": {
        "title": "Storage Sunburst",
        "icon": "🔆",
        "description": "Interactive sunburst visualization of storage usage by folder"
    },
    "file_distribution": {
        "title": "File Distribution",
        "icon": "📊",
        "description": "Distribution of files across folder hierarchy"
    }
}
