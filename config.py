"""
Configuration settings for the Aparavi Reporting Dashboard.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"

# Default database path
DEFAULT_DB_PATH = str(BASE_DIR / "sample.duckdb")

# Cache settings
CACHE_TTL = 3600  # Cache time to live in seconds

# UI Configuration
APP_TITLE = "Aparavi Reporting Dashboard"
APP_LOGO = str(IMAGES_DIR / "logo-255x115.png")
PAGE_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Time format for display
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Chart configuration
CHART_THEME = "streamlit"  # Options: streamlit, plotly, etc.
DEFAULT_CHART_WIDTH = 700
DEFAULT_CHART_HEIGHT = 400

# Aparavi Colors from brand guidelines
# Main colors: #EF4E0A (orange), #56BBCC (teal), with supporting colors
APARAVI_COLORS = {
    "primary": "#EF4E0A",  # Orange
    "secondary": "#56BBCC",  # Teal
    "dark": "#080A0D",  # Dark (almost black)
    "light": "#F9F9FB",  # Light (off-white)
    "gray": "#51565D",  # Medium gray
    "light_gray": "#9BA0A4",  # Light gray
    "blue": "#617698",  # Blue
    "teal_light": "#AED0D5"  # Light teal
}

# Color schemes for charts
CHART_COLORS = {
    "primary": ["#EF4E0A", "#56BBCC", "#617698", "#AED0D5", "#9BA0A4", "#51565D"],
    "categorical": ["#EF4E0A", "#56BBCC", "#617698", "#080A0D", "#9BA0A4", "#AED0D5"],
    "sequential": ["#F9F9FB", "#AED0D5", "#56BBCC", "#617698", "#51565D", "#080A0D"]
}

# Export configuration
EXPORT_FORMATS = ["csv", "json", "xlsx"]
MAX_EXPORT_ROWS = 100000  # Maximum number of rows to export

# Report configuration
REPORTS = {
    "overview": {
        "title": "Dashboard Overview",
        "icon": "",
        "description": "High-level overview of document management statistics"
    },
    "objects": {
        "title": "Objects Analysis",
        "icon": "",
        "description": "Analysis of document objects and their properties"
    },
    "instances": {
        "title": "Instances & Storage",
        "icon": "",
        "description": "Analysis of document instances and storage metrics"
    },
    "classifications": {
        "title": "Classifications",
        "icon": "",
        "description": "Analysis of document classifications and categories"
    },
    "permissions": {
        "title": "Security & Permissions",
        "icon": "",
        "description": "Analysis of document permissions and access controls"
    },
    "services": {
        "title": "Services",
        "icon": "",
        "description": "Analysis of services interacting with documents"
    },
    "messages": {
        "title": "Messages",
        "icon": "",
        "description": "Analysis of message data related to documents"
    },
    "folder_structure": {
        "title": "Folder Structure",
        "icon": "",
        "description": "Visualization and analysis of folder hierarchies"
    },
    "storage_sunburst": {
        "title": "Storage Sunburst",
        "icon": "",
        "description": "Interactive sunburst visualization of storage usage by folder"
    },
    "file_distribution": {
        "title": "File Distribution",
        "icon": "",
        "description": "Distribution of files across folder hierarchy"
    },
    "metadata_analysis": {
        "title": "Metadata Analysis",
        "icon": "",
        "description": "Analysis and comparison of metadata across different file types"
    }
}
