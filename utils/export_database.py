#!/usr/bin/env python
"""
Utility to export database tables to various formats (CSV, JSON, Parquet)
for external analysis or backup purposes.
"""

import duckdb
import pandas as pd
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Default database path (relative to this script)
DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "sample.duckdb")

def get_tables(conn):
    """Get list of all tables in the database"""
    result = conn.execute('PRAGMA show_tables').fetchall()
    return [table[0] for table in result]

def export_table(conn, table_name, output_dir, format='csv', sample=False, sample_size=1000):
    """Export a single table to the specified format
    
    Args:
        conn: DuckDB connection
        table_name: Name of the table to export
        output_dir: Directory to save the export
        format: Export format (csv, json, parquet)
        sample: Whether to export only a sample
        sample_size: Number of rows to sample
    
    Returns:
        Path to the exported file
    """
    query = f"SELECT * FROM {table_name}"
    if sample:
        query += f" LIMIT {sample_size}"
    
    df = conn.execute(query).fetch_df()
    
    # Create filename
    filename = f"{table_name}.{format}"
    output_path = output_dir / filename
    
    # Export based on format
    if format == 'csv':
        df.to_csv(output_path, index=False)
    elif format == 'json':
        df.to_json(output_path, orient='records', indent=2)
    elif format == 'parquet':
        df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return output_path

def export_all_tables(db_path, output_dir=None, formats=None, sample=False, sample_size=1000):
    """Export all tables in the database
    
    Args:
        db_path: Path to the DuckDB database
        output_dir: Directory to save exports (defaults to 'exports' in project root)
        formats: List of formats to export (defaults to ['csv'])
        sample: Whether to export only a sample
        sample_size: Number of rows to sample
    
    Returns:
        Dictionary with export statistics
    """
    # Set defaults
    if formats is None:
        formats = ['csv']
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "exports"
    else:
        output_dir = Path(output_dir)
    
    # Create timestamp subfolder to avoid overwriting previous exports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = output_dir / timestamp
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = duckdb.connect(db_path)
    
    # Get list of tables
    tables = get_tables(conn)
    
    export_stats = {
        'database': db_path,
        'timestamp': timestamp,
        'output_directory': str(output_dir),
        'tables_exported': len(tables),
        'formats': formats,
        'sample_mode': sample,
        'sample_size': sample_size if sample else None,
        'exports': {}
    }
    
    # Export each table in each format
    for table in tables:
        export_stats['exports'][table] = {}
        
        for fmt in formats:
            try:
                output_path = export_table(conn, table, output_dir, format=fmt, sample=sample, sample_size=sample_size)
                export_stats['exports'][table][fmt] = {
                    'path': str(output_path),
                    'success': True
                }
            except Exception as e:
                export_stats['exports'][table][fmt] = {
                    'success': False,
                    'error': str(e)
                }
    
    # Write export summary
    with open(output_dir / 'export_summary.json', 'w') as f:
        json.dump(export_stats, f, indent=2)
    
    return export_stats

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Export DuckDB tables to various formats')
    
    parser.add_argument('--db', type=str, default=DEFAULT_DB_PATH,
                        help='Path to DuckDB database file')
    
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory for exports')
    
    parser.add_argument('--formats', type=str, nargs='+', default=['csv'],
                        choices=['csv', 'json', 'parquet'],
                        help='Export formats (multiple can be specified)')
    
    parser.add_argument('--sample', action='store_true',
                        help='Export only a sample of each table')
    
    parser.add_argument('--sample-size', type=int, default=1000,
                        help='Number of rows to sample if --sample is used')
    
    args = parser.parse_args()
    
    print(f"Starting export from {args.db}...")
    
    stats = export_all_tables(
        db_path=args.db,
        output_dir=args.output,
        formats=args.formats,
        sample=args.sample,
        sample_size=args.sample_size
    )
    
    # Print summary
    print(f"\nExport complete!")
    print(f"Exported {stats['tables_exported']} tables to {stats['output_directory']}")
    print(f"Formats: {', '.join(stats['formats'])}")
    
    if stats['sample_mode']:
        print(f"Sample mode: {stats['sample_size']} rows per table")
    
    # Check for any errors
    errors = sum(1 for table in stats['exports'] for fmt in stats['exports'][table] 
                if not stats['exports'][table][fmt]['success'])
    
    if errors > 0:
        print(f"\nWarning: {errors} exports failed. See export_summary.json for details.")
    
    print("\nExport summary saved to:", os.path.join(stats['output_directory'], 'export_summary.json'))

if __name__ == "__main__":
    main()
