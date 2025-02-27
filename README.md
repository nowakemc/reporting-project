# Aparavi Reporting Dashboard

A powerful Streamlit application for analyzing document management data from the Aparavi Data Suite. This specialized dashboard provides comprehensive visualization and analysis features to help you understand your document ecosystem.

## Features

- **Comprehensive Analytics**: Analyze file types, storage patterns, permissions, and more
- **Interactive Visualizations**: Explore your data with interactive charts and graphs
- **Metadata Analysis**: Explore and compare metadata structures across different file types
- **Export Capabilities**: Export reports and data in various formats
- **Performance Optimized**: Built with DuckDB for high-performance data analysis
- **Aparavi Branding**: Professionally themed with Aparavi's visual identity

## Screenshots

![Dashboard Overview](https://github.com/nowakemc/reporting-project/raw/main/screenshots/dashboard.png)
![Objects Analysis](https://github.com/nowakemc/reporting-project/raw/main/screenshots/objects.png)
![Storage Analysis](https://github.com/nowakemc/reporting-project/raw/main/screenshots/storage.png)

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Place your Aparavi Data Suite DuckDB database file in the project directory or specify a custom path

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

## How It Works

The Aparavi Reporting Dashboard works by connecting to a DuckDB database that contains document management data from the Aparavi Data Suite. Here's how the different components work together:

### Core Components

1. **Data Connection**: The `DatabaseManager` class in `modules/database.py` handles database connections and query execution. It supports both direct SQL queries and higher-level analysis functions.

2. **Visualization Engine**: The `modules/visualizations.py` file contains functions that transform query results into interactive visualizations using Plotly. These visualizations are designed with the Aparavi color palette for a consistent brand experience.

3. **Navigation & UI**: The Streamlit sidebar provides navigation between different report types. The main panel dynamically renders the corresponding report content based on the user's selection.

4. **Analysis Modules**: Specialized analysis modules in the `modules/` directory provide specific functionality:
   - `folder_analysis.py`: Hierarchical folder structure analysis with sunburst charts
   - `metadata_analysis.py`: Advanced metadata parsing and comparison across file types

### Data Flow

1. User selects a report type from the sidebar
2. The application queries the DuckDB database for relevant data
3. Data is processed and transformed into the appropriate format
4. Visualizations are generated using Plotly with the Aparavi color scheme
5. Results are rendered in the Streamlit interface
6. Users can interact with charts, toggle options, and export results

## Development Process

The Aparavi Reporting Dashboard was developed through the following process:

1. **Initial Framework**: Created a Streamlit application with basic DuckDB connectivity
2. **Core Analytics**: Implemented essential document analytics reports (objects, storage, permissions)
3. **Advanced Analysis**: Added specialized analysis modules for folder structure and metadata
4. **Aparavi Branding**: Transformed the UI with Aparavi's color palette, logos, and styling
5. **Performance Optimization**: Implemented query caching and rendering improvements
6. **Usability Enhancements**: Added export options and improved user interaction flows

### Branding Implementation

The Aparavi branding was implemented by:

1. Centralizing brand colors and styling in `config.py`
2. Adding logo images to the `images/` directory
3. Using custom CSS to apply brand styles throughout the interface
4. Replacing generic titles and descriptions with Aparavi-specific messaging
5. Customizing chart colors to match the Aparavi palette
6. Setting the browser favicon to the Aparavi logo

## Database Schema

The application expects an Aparavi Data Suite DuckDB database with the following tables:

- **objects**: Document objects with metadata
- **instances**: Instances of objects with storage and service information
- **classifications**: Classification and categorization data
- **services**: Service information
- **parentPaths**: File system paths
- **osPermissions**: Permissions data
- **osSecurity**: Security configuration
- **messages**: Message data related to documents
- **tagSets**: Tags for categorization

## Project Structure

```
reporting-project/
├── app.py                    # Main Streamlit app entry point
├── config.py                 # Configuration settings and brand colors
├── requirements.txt          # Dependencies
├── README.md                 # Documentation
├── modules/                  # Modular components
│   ├── database.py           # Database connection and queries
│   ├── visualizations.py     # Chart generation functions
│   ├── folder_analysis.py    # Folder structure analysis
│   └── metadata_analysis.py  # Metadata analysis module
├── utils/                    # Utility scripts
│   ├── analyze_metadata.py   # Metadata analysis utility
│   ├── analyze_relationships.py # Table relationship analysis
│   ├── export_database.py    # Database export utility
│   ├── visualize_schema.py   # Schema visualization utility
│   └── README.md             # Utility documentation
├── images/                   # Image assets for branding
│   ├── logo-48x48.png        # Favicon
│   ├── logo-90x90.png        # Small logo
│   ├── logo-216x216.png      # Medium logo
│   └── logo-255x115.png      # Header logo
└── data/                     # Sample data and database files
```

## Troubleshooting

### Common Issues

- **Database Lock Error**: If you encounter a "Could not set lock on file" error, it means another process is using the database. Close other instances of the app and try again.
- **Missing Libraries**: Make sure to install all the required dependencies with `pip install -r requirements.txt`.
- **DuckDB JSON Functions**: This project has been updated to be compatible with different versions of DuckDB:
  - Older versions of DuckDB may not support `json_array_elements` or other advanced JSON functions
  - The app now uses simplified JSON queries that are more widely compatible
  - If you encounter JSON-related errors, try updating DuckDB to the latest version with `pip install duckdb --upgrade`
  - In case of persistent issues, the app will gracefully degrade functionality rather than crash
- **Date/Time Filtering**: The app now filters out invalid timestamps (like the epoch timestamp from 1970) to ensure more accurate visualizations.

## Adding New Reports

1. Define the report in `config.py`
2. Create a render function in `app.py`
3. Add the report to the report selector

## Version

Current Version: 1.1.0

## License

MIT

## Author

Matt Carpenter - [nowakemc](https://github.com/nowakemc)
