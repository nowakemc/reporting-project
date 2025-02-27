#!/usr/bin/env python
"""
Metadata Analyzer for File Types

This utility analyzes the metadata JSON fields in the database, categorizing and comparing
metadata across different file types (.eml, .doc, .xls, etc).

It extracts patterns, common fields, and unique fields per file type to understand the
structure and availability of metadata across the document ecosystem.
"""

import duckdb
import pandas as pd
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import seaborn as sns
import numpy as np
from tqdm import tqdm
import argparse

# Default database path (relative to this script)
DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "sample.duckdb")

def connect_to_db(db_path=DEFAULT_DB_PATH):
    """Connect to the DuckDB database"""
    try:
        conn = duckdb.connect(db_path)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_file_types_with_metadata(conn):
    """
    Get a list of file extensions and their counts that have metadata
    """
    query = """
    SELECT o.extension, COUNT(*) as count
    FROM instances i
    JOIN objects o ON i.objectId = o.objectId
    WHERE i.metadata IS NOT NULL 
    AND i.metadata != ''
    AND o.extension IS NOT NULL
    GROUP BY o.extension
    ORDER BY count DESC
    """
    
    return conn.execute(query).fetchdf()

def get_metadata_samples(conn, extension=None, limit=100):
    """
    Get sample metadata records for a specific extension or all extensions
    
    Args:
        conn: Database connection
        extension: File extension to filter (without dot) or None for all
        limit: Maximum number of samples to retrieve
        
    Returns:
        DataFrame with objectId, extension, and metadata
    """
    if extension:
        query = f"""
        SELECT i.objectId, o.extension, i.metadata
        FROM instances i
        JOIN objects o ON i.objectId = o.objectId
        WHERE i.metadata IS NOT NULL 
        AND i.metadata != ''
        AND o.extension = '{extension}'
        LIMIT {limit}
        """
    else:
        query = f"""
        SELECT i.objectId, o.extension, i.metadata
        FROM instances i
        JOIN objects o ON i.objectId = o.objectId
        WHERE i.metadata IS NOT NULL 
        AND i.metadata != ''
        AND o.extension IS NOT NULL
        LIMIT {limit}
        """
    
    return conn.execute(query).fetchdf()

def extract_metadata_structure(metadata_json):
    """
    Extract the structure of metadata JSON (flattened keys)
    
    Args:
        metadata_json: String containing JSON metadata
        
    Returns:
        Set of metadata keys (flattened for nested objects)
    """
    keys = set()
    try:
        # Parse the JSON string into a Python dictionary
        metadata = json.loads(metadata_json)
        
        # Function to recursively extract keys from nested dictionaries
        def extract_keys(d, prefix=''):
            if not isinstance(d, dict):
                return
                
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.add(full_key)
                
                # Recursively process nested dictionaries
                if isinstance(v, dict):
                    extract_keys(v, full_key)
                    
                # Process dictionaries in lists
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            extract_keys(item, full_key)
        
        extract_keys(metadata)
    except json.JSONDecodeError:
        # If JSON is invalid, return empty set
        pass
    except Exception as e:
        print(f"Error extracting metadata structure: {e}")
    
    return keys

def analyze_all_metadata(conn, min_samples=10, max_samples=1000):
    """
    Analyze metadata structures across all file types
    
    Args:
        conn: Database connection
        min_samples: Minimum number of samples per file type to include in analysis
        max_samples: Maximum number of samples to process per file type
        
    Returns:
        Dict with metadata analysis results
    """
    # Get file types with metadata
    file_types_df = get_file_types_with_metadata(conn)
    
    # Filter to types with at least min_samples
    file_types_df = file_types_df[file_types_df['count'] >= min_samples]
    
    results = {}
    
    print(f"Analyzing metadata for {len(file_types_df)} file types...")
    
    for _, row in tqdm(file_types_df.iterrows(), total=len(file_types_df)):
        extension = row['extension']
        total_count = row['count']
        
        # Get samples for this extension
        samples = get_metadata_samples(conn, extension, min(max_samples, total_count))
        
        if len(samples) == 0:
            continue
            
        # Extract key structures for each sample
        extension_keys = defaultdict(int)
        valid_samples = 0
        invalid_samples = 0
        
        for _, sample in samples.iterrows():
            try:
                sample_keys = extract_metadata_structure(sample['metadata'])
                
                # Count occurrence of each key
                for key in sample_keys:
                    extension_keys[key] += 1
                    
                valid_samples += 1
            except Exception:
                invalid_samples += 1
        
        # Calculate key frequencies
        key_frequencies = {
            k: {
                'count': v,
                'percentage': (v / valid_samples) * 100 if valid_samples > 0 else 0
            }
            for k, v in extension_keys.items()
        }
        
        # Store results
        results[extension] = {
            'total_count': total_count,
            'analyzed_count': valid_samples + invalid_samples,
            'valid_samples': valid_samples,
            'invalid_samples': invalid_samples,
            'unique_keys': len(extension_keys),
            'key_frequencies': key_frequencies
        }
    
    return results

def identify_common_and_unique_fields(analysis_results):
    """
    Identify fields that are common across file types and unique to specific types
    
    Args:
        analysis_results: Dict with metadata analysis results
        
    Returns:
        Dict with common and unique fields information
    """
    all_keys = set()
    extension_keys = {}
    
    # Collect all keys and keys by extension
    for ext, data in analysis_results.items():
        keys = set(data['key_frequencies'].keys())
        extension_keys[ext] = keys
        all_keys.update(keys)
    
    # Find common fields (present in at least 50% of file types)
    file_type_count = len(analysis_results)
    key_presence = {k: 0 for k in all_keys}
    
    for keys in extension_keys.values():
        for k in keys:
            key_presence[k] += 1
    
    # Calculate how common each field is
    common_threshold = max(2, file_type_count * 0.5)  # Present in at least 50% of types or at least 2
    common_fields = {
        k: {
            'count': v,
            'percentage': (v / file_type_count) * 100
        }
        for k, v in key_presence.items()
        if v >= common_threshold
    }
    
    # Find unique fields (present in only one file type)
    unique_fields = {}
    for ext, keys in extension_keys.items():
        unique_to_ext = [k for k in keys if key_presence[k] == 1]
        if unique_to_ext:
            unique_fields[ext] = unique_to_ext
    
    return {
        'common_fields': common_fields,
        'unique_fields': unique_fields
    }

def get_metadata_examples(conn, extension, key_path, limit=5):
    """
    Get example values for a specific metadata field in a file type
    
    Args:
        conn: Database connection
        extension: File extension
        key_path: Metadata key path (e.g., 'author.name')
        limit: Maximum number of examples to return
        
    Returns:
        List of example values
    """
    samples = get_metadata_samples(conn, extension, limit=100)
    
    examples = []
    key_parts = key_path.split('.')
    
    for _, sample in samples.iterrows():
        try:
            metadata = json.loads(sample['metadata'])
            
            # Navigate through the nested structure
            current = metadata
            for part in key_parts:
                if part in current:
                    current = current[part]
                else:
                    current = None
                    break
            
            if current is not None and current != "" and current not in examples:
                examples.append(current)
                if len(examples) >= limit:
                    break
        except:
            continue
    
    return examples

def generate_report(analysis_results, field_analysis, conn, output_dir=None):
    """
    Generate analysis report
    
    Args:
        analysis_results: Dict with metadata analysis results
        field_analysis: Dict with common and unique fields analysis
        conn: Database connection
        output_dir: Directory to save the report
        
    Returns:
        Path to the generated report file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "reports"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / "metadata_analysis.md"
    
    with open(report_file, "w") as f:
        # Report header
        f.write("# File Metadata Analysis Report\n\n")
        
        # Summary statistics
        file_types_count = len(analysis_results)
        total_unique_keys = len({k for data in analysis_results.values() for k in data['key_frequencies']})
        common_fields_count = len(field_analysis['common_fields'])
        
        f.write("## Summary\n\n")
        f.write(f"- **File Types Analyzed**: {file_types_count}\n")
        f.write(f"- **Total Unique Metadata Fields**: {total_unique_keys}\n")
        f.write(f"- **Common Fields** (across 50%+ of file types): {common_fields_count}\n")
        f.write(f"- **Unique Fields**: {sum(len(fields) for fields in field_analysis['unique_fields'].values())}\n\n")
        
        # Common fields section
        f.write("## Common Metadata Fields\n\n")
        f.write("These fields appear in multiple file types:\n\n")
        f.write("| Field | % of File Types | Example Values |\n")
        f.write("|-------|----------------|----------------|\n")
        
        # Sort common fields by percentage (descending)
        sorted_common = sorted(
            field_analysis['common_fields'].items(),
            key=lambda x: x[1]['percentage'],
            reverse=True
        )
        
        for field, stats in sorted_common:
            # Get example from first file type that has this field
            examples = []
            for ext in analysis_results:
                if field in analysis_results[ext]['key_frequencies']:
                    examples = get_metadata_examples(conn, ext, field)
                    if examples:
                        break
            
            example_str = ", ".join(str(e) for e in examples[:3])
            if len(examples) > 3:
                example_str += ", ..."
                
            f.write(f"| `{field}` | {stats['percentage']:.1f}% | {example_str} |\n")
        
        f.write("\n")
        
        # File type specific analysis
        f.write("## File Type Analysis\n\n")
        
        # Sort file types by sample count
        sorted_types = sorted(
            analysis_results.items(),
            key=lambda x: x[1]['analyzed_count'],
            reverse=True
        )
        
        for ext, data in sorted_types:
            f.write(f"### {ext.upper()} Files\n\n")
            
            # Basic statistics
            f.write(f"- **Total Files**: {data['total_count']}\n")
            f.write(f"- **Analyzed**: {data['analyzed_count']} samples\n")
            f.write(f"- **Unique Metadata Fields**: {data['unique_keys']}\n\n")
            
            # Top metadata fields
            f.write("#### Top Metadata Fields\n\n")
            f.write("| Field | Frequency | Example Values |\n")
            f.write("|-------|-----------|----------------|\n")
            
            # Sort fields by frequency
            sorted_fields = sorted(
                data['key_frequencies'].items(),
                key=lambda x: x[1]['percentage'],
                reverse=True
            )
            
            # Show top 10 fields
            for field, stats in sorted_fields[:10]:
                examples = get_metadata_examples(conn, ext, field)
                example_str = ", ".join(str(e) for e in examples[:3])
                if len(examples) > 3:
                    example_str += ", ..."
                    
                f.write(f"| `{field}` | {stats['percentage']:.1f}% | {example_str} |\n")
            
            f.write("\n")
            
            # Unique fields for this file type
            unique_for_type = field_analysis['unique_fields'].get(ext, [])
            if unique_for_type:
                f.write("#### Fields Unique to this File Type\n\n")
                f.write("| Field | Example Values |\n")
                f.write("|-------|----------------|\n")
                
                for field in sorted(unique_for_type)[:10]:  # Show top 10 unique fields
                    examples = get_metadata_examples(conn, ext, field)
                    example_str = ", ".join(str(e) for e in examples[:3])
                    if len(examples) > 3:
                        example_str += ", ..."
                        
                    f.write(f"| `{field}` | {example_str} |\n")
                
                # If there are more unique fields, show a note
                if len(unique_for_type) > 10:
                    f.write(f"\n*Plus {len(unique_for_type) - 10} more unique fields*\n")
                
                f.write("\n")
    
    # Generate companion JSON file with raw data
    json_file = output_dir / "metadata_analysis.json"
    
    with open(json_file, "w") as f:
        json.dump({
            "analysis": analysis_results,
            "field_analysis": field_analysis
        }, f, indent=2)
    
    return str(report_file)

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Analyze metadata JSON fields across file types')
    
    parser.add_argument('--db', type=str, default=DEFAULT_DB_PATH,
                        help='Path to DuckDB database file')
    
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory for analysis report')
    
    parser.add_argument('--min-samples', type=int, default=10,
                        help='Minimum number of samples per file type to include in analysis')
    
    parser.add_argument('--max-samples', type=int, default=1000,
                        help='Maximum number of samples to analyze per file type')
    
    args = parser.parse_args()
    
    print(f"Connecting to database: {args.db}")
    conn = connect_to_db(args.db)
    
    if not conn:
        print("Failed to connect to database. Exiting.")
        return
    
    print("Starting metadata analysis...")
    
    # Get overall metadata statistics
    analysis_results = analyze_all_metadata(
        conn, 
        min_samples=args.min_samples,
        max_samples=args.max_samples
    )
    
    print(f"Analyzed metadata for {len(analysis_results)} file types")
    
    # Analyze common and unique fields
    field_analysis = identify_common_and_unique_fields(analysis_results)
    
    print(f"Identified {len(field_analysis['common_fields'])} common fields across file types")
    
    # Generate report
    report_path = generate_report(
        analysis_results,
        field_analysis,
        conn,
        output_dir=args.output
    )
    
    print(f"\nAnalysis complete! Report generated at: {report_path}")
    print(f"JSON data also available at: {Path(report_path).with_suffix('.json')}")

if __name__ == "__main__":
    main()
