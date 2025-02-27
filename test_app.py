"""
Test script for the DuckDB Document Management Analyzer application.
"""

import os
import sys
import unittest
from modules.database import DatabaseManager
from modules.analytics import time_series_analysis, size_distribution_analysis

class TestDocumentAnalyzer(unittest.TestCase):
    """Test cases for the Document Analyzer application."""
    
    def setUp(self):
        """Set up test environment."""
        self.db_path = "sample.duckdb"
        if not os.path.exists(self.db_path):
            print(f"Error: Test database not found at {self.db_path}")
            sys.exit(1)
        
        self.db = DatabaseManager(self.db_path)
    
    def test_database_connection(self):
        """Test database connection."""
        self.assertIsNotNone(self.db.conn, "Database connection failed")
        
        tables = self.db.list_tables()
        self.assertGreater(len(tables), 0, "No tables found in database")
        
        # Check for expected tables
        expected_tables = ['objects', 'instances', 'classifications']
        for table in expected_tables:
            self.assertIn(table, tables, f"Expected table '{table}' not found")
    
    def test_object_count(self):
        """Test object count query."""
        count = self.db.get_row_count('objects')
        self.assertGreater(count, 0, "No objects found in database")
        print(f"Found {count} objects in database")
    
    def test_storage_stats(self):
        """Test storage statistics query."""
        stats = self.db.get_storage_stats()
        self.assertIsNotNone(stats, "Failed to retrieve storage statistics")
        
        # Check for expected keys
        expected_keys = ['total_size', 'avg_size', 'min_size', 'max_size']
        for key in expected_keys:
            self.assertIn(key, stats, f"Expected key '{key}' not found in storage stats")
        
        print(f"Total storage: {stats['total_size']/1024/1024/1024:.2f} GB")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.db:
            self.db.close()

if __name__ == '__main__':
    unittest.main()
