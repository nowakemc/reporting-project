import duckdb

# Connect to the database
conn = duckdb.connect('sample.duckdb')

# Get all tables
tables = conn.execute('SHOW TABLES').fetchall()

print('Row counts:')
for table in tables:
    table_name = table[0]
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f'{table_name}: {count} rows')
