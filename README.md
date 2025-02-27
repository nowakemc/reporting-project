# DuckDB Document Management Analyzer

A powerful Streamlit application for analyzing document management data stored in DuckDB databases. This tool provides comprehensive visualization and analysis features to help you understand your document ecosystem.

## Features

- **Comprehensive Analytics**: Analyze file types, storage patterns, permissions, and more
- **Interactive Visualizations**: Explore your data with interactive charts and graphs
- **Modular Architecture**: Well-organized code structure for easy maintenance and extensions
- **Export Capabilities**: Export reports and data in various formats
- **Performance Optimized**: Built with DuckDB for high-performance data analysis

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
3. Place your DuckDB database file in the project directory or specify a custom path

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Or use the original script:

```bash
streamlit run duckdb-1.0.0.py
```

## Database Schema

The application expects a DuckDB database with the following tables:

- **objects**: Document objects with metadata
- **instances**: Instances of objects with storage and service information
- **classifications**: Classification and categorization data
- **services**: Service information
- **parentPaths**: File system paths
- **osPermissions**: Permissions data
- **osSecurity**: Security configuration
- **messages**: Message data related to documents
- **tagSets**: Tags for categorization

## Development

### Project Structure

```
reporting-project/
├── app.py                 # Main Streamlit app entry point
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── modules/               # Modular components
│   ├── database.py        # Database connection and queries
│   └── visualizations.py  # Chart generation functions
```

### Adding New Reports

1. Define the report in `config.py`
2. Create a render function in `app.py`
3. Add the report to the report selector

## License

MIT

## Author

Matt Carpenter - [nowakemc](https://github.com/nowakemc)
