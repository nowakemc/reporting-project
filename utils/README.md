# Utility Tools

This directory contains utility scripts and tools that are not part of the main application but serve supporting functions like analysis, maintenance, and data processing.

## Available Utilities

- **analyze_relationships.py**: Analyzes table relationships in the DuckDB database, focusing on connections through `objectId` and other key fields.
- **visualize_schema.py**: Generates database schema visualizations and documentation including ER diagrams and markdown summaries.
- **export_database.py**: Exports database tables to various formats (CSV, JSON, Parquet) for external analysis or backup.
- **analyze_metadata.py**: Analyzes metadata JSON fields across different file types, identifying common and unique metadata structures.

## Usage

These utilities are designed to be run independently from the command line:

```bash
# Run database relationship analysis
python utils/analyze_relationships.py

# Generate schema visualization and documentation
python utils/visualize_schema.py

# Export database tables (with options)
python utils/export_database.py --formats csv json --sample
python utils/export_database.py --help  # Show all available options

# Analyze metadata across file types
python utils/analyze_metadata.py
python utils/analyze_metadata.py --min-samples 5 --max-samples 500  # With options
```

## Output

Most utilities store their output in the project root directories:

- Schema diagrams and summaries: `reports/` directory
- Table exports: `exports/[timestamp]/` directories
- Analysis reports: `reports/` directory
- Metadata analysis: `reports/metadata_analysis.md` and `reports/metadata_analysis.json`

## Adding New Utilities

When adding new utility scripts:

1. Place the script in this directory
2. Update this README with a brief description
3. Make sure the script includes proper documentation
4. Consider adding a standardized output format for consistency
