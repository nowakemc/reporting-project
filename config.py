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

# Define report categories with nested reports
REPORT_CATEGORIES = {
    "dashboard": {
        "name": "Dashboard",
        "description": "Overview and Executive Summary",
        "reports": {
            "overview": {
                "title": "Executive Summary",
                "description": "High-level dashboard showing key metrics and insights",
                "function": "render_overview_report"
            }
        }
    },
    "content_analysis": {
        "name": "Content Analysis",
        "description": "Analyze document types and content",
        "reports": {
            "objects": {
                "title": "Content Type Analysis",
                "description": "Analyze document types, extensions, and classifications",
                "function": "render_objects_report"
            },
            "metadata": {
                "title": "Metadata Insights",
                "description": "Analyze document metadata patterns and trends",
                "function": "render_metadata_analysis_report"
            }
        }
    },
    "storage_structure": {
        "name": "Storage & Structure",
        "description": "Analyze data storage and organization",
        "reports": {
            "instances": {
                "title": "Storage Analysis",
                "description": "Analyze storage utilization and distribution",
                "function": "render_instances_report"
            },
            "folder_structure": {
                "title": "Directory Structure",
                "description": "Analyze folder hierarchy and document organization",
                "function": "render_folder_structure_report"
            },
            "storage_sunburst": {
                "title": "Storage Distribution",
                "description": "Visualize storage allocation with interactive sunburst chart",
                "function": "render_storage_sunburst_report"
            },
            "file_distribution": {
                "title": "Document Distribution",
                "description": "Analyze how documents are distributed across the system",
                "function": "render_file_distribution_report"
            }
        }
    },
    "document_lifecycle": {
        "name": "Document Lifecycle",
        "description": "Analyze document creation, changes, and aging",
        "reports": {
            "document_age": {
                "title": "Document Aging Analysis",
                "description": "Analyze the age distribution of documents in the system",
                "function": "render_document_age_report"
            },
            "modification_analysis": {
                "title": "Modification Patterns",
                "description": "Analyze how frequently documents are updated over time",
                "function": "render_modification_analysis_report"
            },
            "lifecycle_timeline": {
                "title": "Document Timeline",
                "description": "Visualize the complete timeline of document lifecycle events",
                "function": "render_lifecycle_timeline_report"
            }
        }
    },
    "security_governance": {
        "name": "Security & Governance",
        "description": "Analyze permissions, access patterns, and compliance",
        "reports": {
            "permission_analysis": {
                "title": "Permission Distribution",
                "description": "Analyze how permissions are distributed across documents",
                "function": "render_permission_analysis_report"
            },
            "access_patterns": {
                "title": "Access Patterns",
                "description": "Analyze when and how documents are accessed",
                "function": "render_access_patterns_report"
            }
        }
    }
}

# Maintain backward compatibility with a flat dictionary
# This maps old report keys to new report structure
REPORTS = {
    "overview": REPORT_CATEGORIES["dashboard"]["reports"]["overview"],
    "objects": REPORT_CATEGORIES["content_analysis"]["reports"]["objects"],
    "instances": REPORT_CATEGORIES["storage_structure"]["reports"]["instances"],
    "folder_structure": REPORT_CATEGORIES["storage_structure"]["reports"]["folder_structure"],
    "storage_sunburst": REPORT_CATEGORIES["storage_structure"]["reports"]["storage_sunburst"],
    "file_distribution": REPORT_CATEGORIES["storage_structure"]["reports"]["file_distribution"],
    "metadata_analysis": REPORT_CATEGORIES["content_analysis"]["reports"]["metadata"],
    # Add new reports to the backward compatibility mapping
    "document_age": REPORT_CATEGORIES["document_lifecycle"]["reports"]["document_age"],
    "modification_analysis": REPORT_CATEGORIES["document_lifecycle"]["reports"]["modification_analysis"],
    "lifecycle_timeline": REPORT_CATEGORIES["document_lifecycle"]["reports"]["lifecycle_timeline"],
    "permission_analysis": REPORT_CATEGORIES["security_governance"]["reports"]["permission_analysis"],
    "access_patterns": REPORT_CATEGORIES["security_governance"]["reports"]["access_patterns"]
}
