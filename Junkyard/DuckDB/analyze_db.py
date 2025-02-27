import duckdb

# Connect to the database
conn = duckdb.connect('sample.duckdb')

# Get all tables
tables = conn.execute('SHOW TABLES').fetchall()

# Get schema for each table
for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")
    print("-" * 40)
    
    # Get schema
    schema = conn.execute(f"PRAGMA table_info('{table_name}')").fetchdf()
    print(schema)
    
    # Get sample data
    print("\nSample data:")
    sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf()
    print(sample)
    
    # Get row count
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"\nTotal rows: {count}")
