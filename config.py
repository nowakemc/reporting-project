"""
Configuration settings for the Aparavi Reporting Dashboard.

This configuration file centralizes all settings for the Aparavi Reporting Dashboard,
including paths, UI configuration, branding colors, and report definitions.
The Aparavi branding is implemented through color schemes, logo paths, and UI element styling.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"  # Directory for data files and cached results
IMAGES_DIR = BASE_DIR / "images"  # Directory containing Aparavi logo images

# Default database path
DEFAULT_DB_PATH = str(BASE_DIR / "sample.duckdb")  # Path to the Aparavi Data Suite DuckDB database

# Cache settings
CACHE_TTL = 3600  # Cache time to live in seconds for database query results

# UI Configuration
APP_TITLE = "Aparavi Reporting Dashboard"  # Application title displayed in header and browser tab
APP_LOGO = str(IMAGES_DIR / "logo-255x115.png")  # Path to Aparavi logo displayed in header
PAGE_LAYOUT = "wide"  # Use wide layout for better data visualization
SIDEBAR_STATE = "expanded"  # Start with sidebar expanded for easier navigation

# Time format for display
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # Standard datetime format for consistency

# Chart configuration
CHART_THEME = "streamlit"  # Base theme, customized with Aparavi colors
DEFAULT_CHART_WIDTH = 700  # Standard chart width for consistency
DEFAULT_CHART_HEIGHT = 400  # Standard chart height for consistency

# Aparavi Colors from brand guidelines
# These colors are used throughout the application to maintain consistent branding
APARAVI_COLORS = {
    "primary": "#EF4E0A",    # Orange - Primary brand color, used for highlights and primary actions
    "secondary": "#56BBCC",  # Teal - Secondary brand color, used for supporting elements
    "dark": "#080A0D",       # Dark (almost black) - Used for text and borders
    "light": "#F9F9FB",      # Light (off-white) - Used for backgrounds
    "gray": "#51565D",       # Medium gray - Used for secondary text and elements
    "light_gray": "#9BA0A4", # Light gray - Used for tertiary elements and disabled states
    "blue": "#617698",       # Blue - Accent color for variety
    "teal_light": "#AED0D5"  # Light teal - Accent color for variety
}

# Color schemes for different chart types
# These schemes use the Aparavi brand colors in various combinations
CHART_COLORS = {
    "primary": [  # Primary color scheme for most charts
        "#EF4E0A",  # Aparavi Orange
        "#56BBCC",  # Aparavi Teal
        "#617698",  # Aparavi Blue
        "#AED0D5",  # Light Teal
        "#9BA0A4",  # Light Gray
        "#51565D"   # Medium Gray
    ],
    "categorical": [  # For categorical data visualizations
        "#EF4E0A",  # Aparavi Orange
        "#56BBCC",  # Aparavi Teal
        "#617698",  # Aparavi Blue
        "#080A0D",  # Dark
        "#9BA0A4",  # Light Gray
        "#AED0D5"   # Light Teal
    ],
    "sequential": [  # For sequential data visualizations
        "#F9F9FB",  # Light
        "#AED0D5",  # Light Teal
        "#56BBCC",  # Aparavi Teal
        "#617698",  # Aparavi Blue
        "#51565D",  # Medium Gray
        "#080A0D"   # Dark
    ]
}

# Export configuration
EXPORT_FORMATS = ["csv", "json", "xlsx"]  # Supported export formats
MAX_EXPORT_ROWS = 100000  # Maximum number of rows to export for performance

# Report configuration organized into logical categories
# Reports are grouped to provide a more intuitive navigation experience
REPORT_CATEGORIES = {
    "overview": {
        "name": "Dashboard",
        "description": "High-level dashboards and summary views",
        "reports": {
            "overview": {
                "title": "Executive Summary",
                "icon": "",
                "description": "Key metrics and high-level overview of your document ecosystem"
            }
        }
    },
    "content": {
        "name": "Content Analysis",
        "description": "Analyze document content and properties",
        "reports": {
            "objects": {
                "title": "Document Analysis",
                "icon": "",
                "description": "Detailed analysis of documents, file types, and properties"
            },
            "metadata_analysis": {
                "title": "Metadata Insights",
                "icon": "",
                "description": "Explore and compare metadata across different file types"
            },
            "classifications": {
                "title": "Content Categories",
                "icon": "",
                "description": "Analysis of document classifications and categories"
            }
        }
    },
    "storage": {
        "name": "Storage & Structure",
        "description": "Analyze storage usage and folder organization",
        "reports": {
            "instances": {
                "title": "Storage Overview",
                "icon": "",
                "description": "Analysis of storage usage and document instances"
            },
            "folder_structure": {
                "title": "Folder Organization",
                "icon": "",
                "description": "Visual representation of your folder hierarchies"
            },
            "storage_sunburst": {
                "title": "Storage Distribution",
                "icon": "",
                "description": "Interactive visualization of storage usage by folder"
            },
            "file_distribution": {
                "title": "File Distribution",
                "icon": "",
                "description": "Analysis of file distribution across your ecosystem"
            }
        }
    },
    "security": {
        "name": "Security & Governance",
        "description": "Analyze security settings and permissions",
        "reports": {
            "permissions": {
                "title": "Access Controls",
                "icon": "",
                "description": "Analysis of document permissions and security settings"
            },
            "services": {
                "title": "Service Interactions",
                "icon": "",
                "description": "Analysis of services interacting with documents"
            },
            "messages": {
                "title": "System Messages",
                "icon": "",
                "description": "Analysis of system messages related to documents"
            }
        }
    }
}

# Flat dictionary of all reports for backward compatibility
REPORTS = {}
for category in REPORT_CATEGORIES.values():
    for report_id, report in category["reports"].items():
        REPORTS[report_id] = report
