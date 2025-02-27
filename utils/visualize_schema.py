#!/usr/bin/env python
"""
Utility to visualize the database schema and create an entity-relationship diagram.
This generates a visual representation of the database tables and their relationships.
"""

import duckdb
import pandas as pd
import os
import json
from pathlib import Path

# Database connection
DB_PATH = str(Path(__file__).parent.parent / "sample.duckdb")

def get_schema_info():
    """Extract schema information from the database"""
    conn = duckdb.connect(DB_PATH)
    
    # Get all tables
    tables = conn.execute('PRAGMA show_tables').fetchall()
    tables = [table[0] for table in tables]
    
    schema_info = {}
    relationships = []
    
    for table in tables:
        # Get column info
        columns = conn.execute(f'PRAGMA table_info({table})').fetchall()
        column_info = []
        primary_key = None
        
        for col in columns:
            column_info.append({
                'name': col[1],
                'type': col[2],
                'nullable': not col[3],
                'primary_key': bool(col[5])
            })
            
            if col[5]:  # Is primary key
                primary_key = col[1]
        
        schema_info[table] = {
            'columns': column_info,
            'primary_key': primary_key
        }
    
    # Infer relationships based on column names (simplified approach)
    for table1 in tables:
        pk = schema_info[table1]['primary_key']
        if not pk:
            continue
            
        # Look for matching foreign keys in other tables
        for table2 in tables:
            if table1 == table2:
                continue
                
            t2_columns = [col['name'] for col in schema_info[table2]['columns']]
            
            # Check if primary key exists as a column in the second table
            if pk in t2_columns:
                relationships.append({
                    'from_table': table1,
                    'to_table': table2,
                    'from_column': pk,
                    'to_column': pk,
                    'relationship_type': '1:N'  # Simplified assumption
                })
    
    return {
        'tables': schema_info,
        'relationships': relationships
    }

def export_schema_diagram():
    """Export schema as a diagram description file"""
    schema_info = get_schema_info()
    
    # Create directory for output
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    # Save schema to JSON
    with open(output_dir / "schema.json", "w") as f:
        json.dump(schema_info, f, indent=2)
    
    # Generate a PlantUML representation for ER diagrams
    plantuml_content = ["@startuml", "skinparam linetype ortho"]
    
    # Add tables
    for table, info in schema_info['tables'].items():
        plantuml_content.append(f'entity "{table}" {{')
        
        for column in info['columns']:
            column_name = column['name']
            type_info = column['type']
            
            # Formatting: PK gets a special marker, add data type
            if column.get('primary_key'):
                plantuml_content.append(f'  * {column_name} : {type_info} <<PK>>')
            else:
                nullable_mark = "" if column['nullable'] else " [NN]"
                plantuml_content.append(f'  {column_name} : {type_info}{nullable_mark}')
        
        plantuml_content.append('}')
    
    # Add relationships
    for rel in schema_info['relationships']:
        from_table = rel['from_table']
        to_table = rel['to_table']
        plantuml_content.append(f'{from_table} ||--o{{ {to_table} : "{rel["from_column"]}"')
    
    plantuml_content.append("@enduml")
    
    # Save PlantUML file
    with open(output_dir / "schema.puml", "w") as f:
        f.write("\n".join(plantuml_content))
    
    return {
        "json_path": str(output_dir / "schema.json"),
        "puml_path": str(output_dir / "schema.puml")
    }

def generate_schema_summary():
    """Generate a text summary of the schema"""
    schema_info = get_schema_info()
    
    summary = ["# DuckDB Schema Summary", ""]
    
    # Summary statistics
    table_count = len(schema_info['tables'])
    relationship_count = len(schema_info['relationships'])
    
    summary.append(f"## Overview")
    summary.append(f"- Total Tables: {table_count}")
    summary.append(f"- Total Relationships: {relationship_count}")
    summary.append("")
    
    # Table details
    summary.append("## Tables")
    for table, info in schema_info['tables'].items():
        column_count = len(info['columns'])
        pk = info['primary_key'] or "None"
        summary.append(f"### {table}")
        summary.append(f"- Primary Key: {pk}")
        summary.append(f"- Column Count: {column_count}")
        
        # Referenced by
        references = [r for r in schema_info['relationships'] if r['from_table'] == table]
        if references:
            summary.append("- Referenced by:")
            for ref in references:
                summary.append(f"  - {ref['to_table']} (via {ref['to_column']})")
        
        summary.append("")
    
    # Create directory for output
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    # Save summary to markdown
    summary_path = output_dir / "schema_summary.md"
    with open(summary_path, "w") as f:
        f.write("\n".join(summary))
    
    return str(summary_path)

if __name__ == "__main__":
    print("Analyzing database schema...")
    
    # Generate files
    diagram_files = export_schema_diagram()
    summary_file = generate_schema_summary()
    
    print(f"\nSchema analysis complete!")
    print(f"JSON Schema: {diagram_files['json_path']}")
    print(f"PlantUML ER Diagram: {diagram_files['puml_path']}")
    print(f"Markdown Summary: {summary_file}")
    print("\nNote: To view the PlantUML diagram, you can use:")
    print("- Online PlantUML server: https://www.plantuml.com/plantuml/")
    print("- VS Code PlantUML extension")
    print("- PlantUML command-line tool")
