import duckdb
import pandas as pd
from datetime import datetime


class DatabaseManager:
    """Class to manage database connections and queries."""
    
    def __init__(self, db_path):
        """Initialize database connection.
        
        Args:
            db_path (str): Path to DuckDB database file
        """
        self.db_path = db_path
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to the DuckDB database."""
        try:
            self.conn = duckdb.connect(self.db_path)
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def list_tables(self):
        """List all tables in the database.
        
        Returns:
            list: List of table names
        """
        if not self.conn:
            return []
            
        tables = self.conn.execute("SHOW TABLES").fetchall()
        return [table[0] for table in tables]
    
    def get_table_schema(self, table_name):
        """Get schema for a specific table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            DataFrame: Table schema
        """
        schema = self.conn.execute(f"PRAGMA table_info('{table_name}')").fetchdf()
        return schema
    
    def query(self, query_str, params=None):
        """Execute query and return pandas DataFrame.
        
        Args:
            query_str (str): SQL query string
            params (dict, optional): Parameters for query
            
        Returns:
            pandas.DataFrame: Result of query
        """
        try:
            if params:
                result = self.conn.execute(query_str, params).fetchdf()
            else:
                result = self.conn.execute(query_str).fetchdf()
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def safe_query(self, query_str, fallback_query=None, params=None):
        """Execute query with a fallback option if the primary query fails.
        
        Args:
            query_str (str): Primary SQL query string
            fallback_query (str, optional): Fallback SQL query if primary fails
            params (dict, optional): Parameters for query
            
        Returns:
            pandas.DataFrame: Result of query
        """
        try:
            return self.query(query_str, params)
        except Exception as e:
            print(f"Primary query failed: {e}")
            if fallback_query:
                try:
                    return self.query(fallback_query, params)
                except Exception as e:
                    print(f"Fallback query also failed: {e}")
            return pd.DataFrame()
    
    def get_version(self):
        """Get DuckDB version information.
        
        Returns:
            str: DuckDB version
        """
        try:
            version_info = self.conn.execute("SELECT version()").fetchone()[0]
            return version_info
        except Exception as e:
            print(f"Error getting version: {e}")
            return "Unknown"
    
    def get_row_count(self, table_name):
        """Get row count for a table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            int: Number of rows in the table
        """
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        return count
    
    def get_object_stats(self):
        """Get statistics about objects in the database.
        
        Returns:
            dict: Dictionary containing object statistics
        """
        stats = {}
        
        # Total objects
        stats['total_objects'] = self.get_row_count('objects')
        
        # File extension distribution
        ext_query = """
            SELECT 
                COALESCE(extension, 'No Extension') as ext,
                COUNT(*) as count
            FROM objects
            GROUP BY ext
            ORDER BY count DESC
            LIMIT 10
        """
        stats['extensions'] = self.query(ext_query)
        
        # Creation time range
        time_query = """
            SELECT 
                MIN(createdAt) as min_time,
                MAX(createdAt) as max_time
            FROM objects
            WHERE createdAt IS NOT NULL
        """
        times = self.query(time_query)
        if not times.empty:
            stats['min_time'] = datetime.fromtimestamp(times['min_time'][0]/1000)
            stats['max_time'] = datetime.fromtimestamp(times['max_time'][0]/1000)
        
        return stats
    
    def get_storage_stats(self):
        """Get storage statistics.
        
        Returns:
            dict: Dictionary containing storage statistics
        """
        size_query = """
            SELECT 
                MIN(size) as min_size,
                MAX(size) as max_size,
                AVG(size) as avg_size,
                MEDIAN(size) as median_size,
                SUM(size) as total_size
            FROM instances
            WHERE size IS NOT NULL
        """
        sizes = self.query(size_query)
        
        if sizes.empty:
            return {}
            
        stats = {
            "min_size": sizes['min_size'][0],
            "max_size": sizes['max_size'][0],
            "avg_size": sizes['avg_size'][0],
            "median_size": sizes['median_size'][0],
            "total_size": sizes['total_size'][0]
        }
        
        return stats
        
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
