#!/usr/bin/env python
"""
Script to analyze relationships between tables in the Aparavi Data Suite database.
This analyzes the interconnections particularly focusing on objectId.
"""

import duckdb
import pandas as pd
import json
from collections import defaultdict

# Connect to database
DB_PATH = "sample.duckdb"
conn = duckdb.connect(DB_PATH)

def get_tables():
    """Get list of all tables in the database"""
    result = conn.execute('PRAGMA show_tables').fetchall()
    return [table[0] for table in result]

def get_table_schema(table_name):
    """Get schema information for a table"""
    schema = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    return {
        'name': table_name,
        'columns': [col[1] for col in schema],
        'primary_key': next((col[1] for col in schema if col[5]), None),
        'foreign_keys': [col[1] for col in schema if "id" in col[1].lower() and col[5] == 0]
    }

def get_table_count(table_name):
    """Get the number of rows in a table"""
    return conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]

def analyze_join_counts(tables_info):
    """Analyze the number of matching rows between tables based on column names"""
    join_counts = defaultdict(dict)
    
    for i, table1 in enumerate(tables_info):
        for table2 in tables_info[i+1:]:
            # Find common columns with "id" in the name
            common_id_columns = [col for col in table1['columns'] if "id" in col.lower() and col in table2['columns']]
            
            for col in common_id_columns:
                try:
                    # Count matches between tables
                    count = conn.execute(f'''
                        SELECT COUNT(*) 
                        FROM {table1['name']} t1 
                        JOIN {table2['name']} t2 
                        ON t1.{col} = t2.{col}
                    ''').fetchone()[0]
                    
                    if count > 0:
                        join_counts[f"{table1['name']}<->{table2['name']}"][col] = count
                except Exception as e:
                    print(f"Error analyzing join between {table1['name']} and {table2['name']} on {col}: {e}")
    
    return join_counts

def analyze_objectid_relationships():
    """Specifically analyze relationships based on objectId"""
    tables = get_tables()
    relationships = {}
    
    # Find tables with objectId column
    tables_with_objectid = []
    for table in tables:
        schema = get_table_schema(table)
        if 'objectId' in schema['columns']:
            tables_with_objectid.append(table)
            
    print(f"Tables containing objectId: {tables_with_objectid}")
    
    # Analyze relationships through objectId
    for table in tables_with_objectid:
        count = get_table_count(table)
        relationships[table] = {
            'total_rows': count
        }
        
        if table != 'objects':
            try:
                # Count rows that match with objects table
                match_count = conn.execute(f'''
                    SELECT COUNT(*) 
                    FROM {table} t 
                    JOIN objects o 
                    ON t.objectId = o.objectId
                ''').fetchone()[0]
                
                relationships[table]['matches_with_objects'] = match_count
                relationships[table]['match_percentage'] = round((match_count / count) * 100, 2) if count > 0 else 0
            except Exception as e:
                print(f"Error analyzing objectId relationship for {table}: {e}")
    
    return relationships

def analyze_parent_relationships():
    """Analyze relationships based on parentId"""
    tables = get_tables()
    parent_relationships = {}
    
    # Find tables with parentId column
    tables_with_parentid = []
    for table in tables:
        schema = get_table_schema(table)
        if 'parentId' in schema['columns']:
            tables_with_parentid.append(table)
            
    print(f"Tables containing parentId: {tables_with_parentid}")
    
    # Analyze relationships through parentId
    for table in tables_with_parentid:
        count = get_table_count(table)
        parent_relationships[table] = {
            'total_rows': count
        }
        
        if 'parentPaths' in tables:
            try:
                # Count rows that match with parentPaths table
                match_count = conn.execute(f'''
                    SELECT COUNT(*) 
                    FROM {table} t 
                    JOIN parentPaths p 
                    ON t.parentId = p.parentId
                ''').fetchone()[0]
                
                parent_relationships[table]['matches_with_parentPaths'] = match_count
                parent_relationships[table]['match_percentage'] = round((match_count / count) * 100, 2) if count > 0 else 0
            except Exception as e:
                print(f"Error analyzing parentId relationship for {table}: {e}")
    
    return parent_relationships

def sample_joined_data():
    """Get sample of data showing relationships between key tables"""
    # Sample join between objects and instances
    objects_instances = conn.execute('''
        SELECT 
            o.objectId, 
            o.name, 
            o.extension,
            i.instanceId,
            i.size,
            i.createTime,
            i.modifyTime
        FROM 
            objects o
        JOIN 
            instances i ON o.objectId = i.objectId
        LIMIT 5
    ''').fetchall()
    
    # Sample join between objects, instances, and parentPaths
    objects_instances_paths = conn.execute('''
        SELECT 
            o.objectId, 
            o.name, 
            i.size,
            p.parentPath
        FROM 
            objects o
        JOIN 
            instances i ON o.objectId = i.objectId
        JOIN 
            parentPaths p ON o.parentId = p.parentId
        LIMIT 5
    ''').fetchall()
    
    # Sample complex join with classifications
    complex_join = conn.execute('''
        SELECT 
            o.objectId, 
            o.name, 
            i.size,
            p.parentPath,
            c.classificationKey
        FROM 
            objects o
        JOIN 
            instances i ON o.objectId = i.objectId
        JOIN 
            parentPaths p ON o.parentId = p.parentId
        LEFT JOIN
            classifications c ON i.classificationId = c.classificationId
        LIMIT 5
    ''').fetchall()
    
    return {
        'objects_instances': objects_instances,
        'objects_instances_paths': objects_instances_paths,
        'complex_join': complex_join
    }

def main():
    """Main analysis function"""
    # Get all tables and their schemas
    tables = get_tables()
    tables_info = [get_table_schema(table) for table in tables]
    
    # Analyze objectId relationships
    print("\n===== OBJECT ID RELATIONSHIPS =====")
    objectid_relationships = analyze_objectid_relationships()
    print(json.dumps(objectid_relationships, indent=4))
    
    # Analyze parentId relationships
    print("\n===== PARENT ID RELATIONSHIPS =====")
    parent_relationships = analyze_parent_relationships()
    print(json.dumps(parent_relationships, indent=4))
    
    # Get general relationship counts between tables
    print("\n===== TABLE JOIN RELATIONSHIPS =====")
    join_counts = analyze_join_counts(tables_info)
    print(json.dumps(join_counts, indent=4))
    
    # Sample joined data
    print("\n===== SAMPLE JOINED DATA =====")
    samples = sample_joined_data()
    
    print("\nObjects-Instances Join (5 samples):")
    print(samples['objects_instances'])
    
    print("\nObjects-Instances-Paths Join (5 samples):")
    print(samples['objects_instances_paths'])
    
    print("\nComplex Join with Classifications (5 samples):")
    print(samples['complex_join'])
    
    # Summarize findings
    print("\n===== RELATIONSHIP SUMMARY =====")
    print(f"Total tables: {len(tables)}")
    
    tables_with_objectid = [t for t in tables_info if 'objectId' in t['columns']]
    print(f"Tables with objectId: {len(tables_with_objectid)}")
    print(f"- {', '.join(t['name'] for t in tables_with_objectid)}")
    
    tables_with_parentid = [t for t in tables_info if 'parentId' in t['columns']]
    print(f"Tables with parentId: {len(tables_with_parentid)}")
    print(f"- {', '.join(t['name'] for t in tables_with_parentid)}")

if __name__ == "__main__":
    main()
