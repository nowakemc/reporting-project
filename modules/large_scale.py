"""
Large Scale Data Handling Module

This module provides tools and utilities for handling large-scale datasets with
millions of objects in the Aparavi Reporting Dashboard. It implements data sampling,
progressive loading, and optimization techniques for DuckDB.
"""

import time
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta


def configure_duckdb_for_scale(db, memory_limit_gb=4):
    """
    Configure DuckDB settings for large datasets
    
    Args:
        db: DatabaseManager instance
        memory_limit_gb: Memory limit in GB
        
    Returns:
        DatabaseManager with optimized settings
    """
    try:
        # Set memory limit (convert GB to bytes)
        db.conn.execute(f"SET memory_limit='{memory_limit_gb}GB'")
        
        # Use system temp directory for overflow
        import tempfile
        temp_dir = tempfile.gettempdir()
        db.conn.execute(f"SET temp_directory='{temp_dir}'")
        
        # Enable parallelism based on available CPU cores
        import multiprocessing
        cores = multiprocessing.cpu_count()
        db.conn.execute(f"PRAGMA threads={cores}")
        db.conn.execute("PRAGMA force_parallelism")
        
        return db
    except Exception as e:
        print(f"Error configuring DuckDB for scale: {e}")
        return db


def create_indexes(db):
    """
    Create indexes on commonly queried columns for better performance
    
    Args:
        db: DatabaseManager instance
        
    Returns:
        Boolean indicating success
    """
    try:
        # Create indexes on columns frequently used in WHERE clauses and joins
        db.conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_createdAt ON objects(createdAt)")
        db.conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_updatedAt ON objects(updatedAt)")
        db.conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_extension ON objects(extension)")
        db.conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_size ON objects(size)")
        
        # Create indexes for foreign key relationships
        db.conn.execute("CREATE INDEX IF NOT EXISTS idx_permissions_objectId ON permissions(objectId)")
        
        return True
    except Exception as e:
        print(f"Error creating indexes: {e}")
        return False


def sample_large_dataset(db, table, sample_size=100000):
    """
    Sample data from large datasets for visualization when full dataset is too large
    
    Args:
        db: DatabaseManager instance
        table: Table name to sample from
        sample_size: Maximum number of records to return
        
    Returns:
        DataFrame with sampled data
    """
    # Get total count
    count = db.get_row_count(table)
    
    # If dataset is smaller than sample size, return all data
    if count <= sample_size:
        return db.query(f"SELECT * FROM {table}")
    
    # For larger datasets, use statistical sampling
    sample_ratio = min(1.0, sample_size / count)
    
    # Use reservoir sampling for very large datasets
    query = f"""
    SELECT * FROM {table} 
    WHERE rand() <= {sample_ratio}
    LIMIT {sample_size}
    """
    
    return db.query(query)


def progressive_data_load(db, query_func, sample_sizes, update_callback=None):
    """
    Progressively load and process data with increasing sample sizes
    
    Args:
        db: DatabaseManager instance
        query_func: Function that takes db and sample_size and returns DataFrame
        sample_sizes: List of increasing sample sizes to try
        update_callback: Callback function to update UI with each result
        
    Returns:
        Final DataFrame with largest successfully processed sample
    """
    result = None
    
    for i, sample_size in enumerate(sorted(sample_sizes)):
        try:
            # Update progress if callback provided
            if update_callback:
                progress = (i + 1) / len(sample_sizes)
                update_callback(progress, f"Processing {sample_size:,} records...")
            
            # Get data for this sample size
            result = query_func(db, sample_size)
            
            # Update visualization if callback provided
            if update_callback:
                update_callback(progress, f"Processed {sample_size:,} records", result)
                
        except Exception as e:
            print(f"Error processing sample size {sample_size}: {e}")
            # Keep the last successful result
            break
    
    return result


def paginated_data_view(db, table, page_size=100, page=1, where_clause=""):
    """
    Return paginated data for display in tables
    
    Args:
        db: DatabaseManager instance
        table: Table name
        page_size: Number of records per page
        page: Current page number (1-indexed)
        where_clause: Optional WHERE clause
        
    Returns:
        Dict with data and pagination info
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Build query
    base_query = f"SELECT * FROM {table}"
    if where_clause:
        base_query += f" WHERE {where_clause}"
    
    # Get paginated data
    query = f"{base_query} LIMIT {page_size} OFFSET {offset}"
    data = db.query(query)
    
    # Get total for pagination
    count_query = f"SELECT COUNT(*) FROM {table}"
    if where_clause:
        count_query += f" WHERE {where_clause}"
    
    total = db.conn.execute(count_query).fetchone()[0]
    total_pages = (total + page_size - 1) // page_size
    
    return {
        'data': data,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_records': total,
            'page_size': page_size
        }
    }


def time_window_analysis(db, start_date=None, end_date=None, interval='month'):
    """
    Analyze data in specific time windows instead of full dataset
    
    Args:
        db: DatabaseManager instance
        start_date: Start date (datetime)
        end_date: End date (datetime)
        interval: Time grouping interval (day, week, month, year)
        
    Returns:
        DataFrame with time series analysis
    """
    # Default to last year if no dates provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=365)
    if not end_date:
        end_date = datetime.now()
    
    # Convert to milliseconds timestamp for database
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    
    query = f"""
    SELECT 
        DATE_TRUNC('{interval}', TIMESTAMP_MS(createdAt)) as period,
        COUNT(*) as document_count,
        AVG(size) as avg_size,
        SUM(size) as total_size
    FROM objects
    WHERE createdAt BETWEEN {start_ms} AND {end_ms}
    GROUP BY 1
    ORDER BY 1
    """
    
    return db.query(query)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_analysis(func, *args, **kwargs):
    """
    Cache analysis results to avoid recalculation
    
    Args:
        func: Analysis function to cache
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Analysis results
    """
    return func(*args, **kwargs)


def detect_scale(db):
    """
    Detect the scale of the database and recommend optimizations
    
    Args:
        db: DatabaseManager instance
        
    Returns:
        Dict with scale information and recommendations
    """
    # Get row counts for main tables
    object_count = db.get_row_count('objects')
    
    # Determine scale category
    if object_count < 10000:
        scale = "small"
    elif object_count < 1000000:
        scale = "medium"
    elif object_count < 10000000:
        scale = "large"
    else:
        scale = "very_large"
    
    # Generate recommendations based on scale
    recommendations = []
    
    if scale == "medium":
        recommendations = [
            "Create indexes on frequently queried columns",
            "Implement data pagination for tables",
            "Use caching for expensive computations"
        ]
    elif scale == "large":
        recommendations = [
            "Create indexes on all queried columns",
            "Implement data sampling for visualizations",
            "Use progressive loading for large reports",
            "Configure DuckDB memory settings",
            "Implement time window filtering"
        ]
    elif scale == "very_large":
        recommendations = [
            "Implement all large-scale optimizations",
            "Consider pre-computing aggregations",
            "Limit interactive queries to recent time windows",
            "Use data partitioning",
            "Consider hybrid approach with specialized analytics engines"
        ]
    
    return {
        'object_count': object_count,
        'scale': scale,
        'recommendations': recommendations
    }


def optimize_database_file(source_db_path, size_threshold_mb=100):
    """
    Create an optimized copy of the database with indexes
    if the database exceeds the specified size threshold.
    
    Args:
        source_db_path: Path to source DuckDB file
        size_threshold_mb: Minimum size in MB to trigger optimization
        
    Returns:
        Dict with optimization metrics (time, original size, new size, path)
    """
    import os
    import time
    import shutil
    import duckdb
    from pathlib import Path
    
    # Check if the database exceeds the size threshold
    source_size_bytes = os.path.getsize(source_db_path)
    source_size_mb = source_size_bytes / (1024 * 1024)
    
    # Skip optimization if database is smaller than threshold
    if source_size_mb < size_threshold_mb:
        return {
            'optimized': False,
            'reason': f"Database size ({source_size_mb:.2f} MB) is below threshold ({size_threshold_mb} MB)",
            'original_path': source_db_path,
            'original_size_mb': source_size_mb
        }
    
    # Create path for optimized database
    source_path = Path(source_db_path)
    optimized_path = source_path.parent / f"{source_path.stem}_optimized{source_path.suffix}"
    
    # Delete the optimized database file if it already exists
    if os.path.exists(optimized_path):
        try:
            os.remove(optimized_path)
        except Exception as e:
            return {
                'optimized': False,
                'error': f"Unable to remove existing optimized database: {str(e)}",
                'original_path': source_db_path,
                'original_size_mb': source_size_mb
            }
    
    # Start timing the optimization process
    start_time = time.time()
    
    # Create a backup copy first
    backup_path = source_path.parent / f"{source_path.stem}_backup{source_path.suffix}"
    shutil.copy2(source_db_path, backup_path)
    
    try:
        # Simplest approach: just make a direct copy of the file
        shutil.copy2(source_db_path, optimized_path)
        
        # Open the new copy and add indexes
        conn = duckdb.connect(str(optimized_path))
        
        # Get list of tables
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        # Add indexes to each table
        for table in table_names:
            # Get column information
            columns = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            indexable_columns = []
            
            for col in columns:
                col_name = col[1]
                col_type = col[2].lower()
                
                # Select columns that are good candidates for indexing
                if any(type_name in col_type for type_name in ['int', 'bigint', 'date', 'timestamp']) or \
                   (('char' in col_type or 'varchar' in col_type) and col_name.lower() in 
                     ['id', 'name', 'key', 'code', 'type', 'status', 'extension']):
                    indexable_columns.append(col_name)
            
            # Create indexes on appropriate columns (limit to 5 per table)
            for col_name in indexable_columns[:5]:
                try:
                    conn.execute(f"CREATE INDEX idx_{table}_{col_name} ON {table}({col_name})")
                except Exception as e:
                    print(f"Warning: Could not create index on {table}.{col_name}: {e}")
        
        # Analyze tables for optimal statistics
        for table in table_names:
            try:
                conn.execute(f"ANALYZE {table}")
            except Exception as e:
                print(f"Warning: Could not analyze table {table}: {e}")
        
        # Force checkpoint to flush optimizations to disk
        conn.execute("CHECKPOINT")
        conn.close()
        
        # Get size of optimized database
        optimized_size_bytes = os.path.getsize(str(optimized_path))
        optimized_size_mb = optimized_size_bytes / (1024 * 1024)
        
        # Calculate metrics
        time_taken = time.time() - start_time
        size_reduction_mb = source_size_mb - optimized_size_mb
        size_reduction_percent = (size_reduction_mb / source_size_mb) * 100 if source_size_mb > 0 else 0
        
        # Return optimization metrics
        return {
            'optimized': True,
            'original_path': source_db_path,
            'optimized_path': str(optimized_path),
            'backup_path': str(backup_path),
            'time_seconds': time_taken,
            'original_size_mb': source_size_mb,
            'optimized_size_mb': optimized_size_mb,
            'size_reduction_mb': size_reduction_mb,
            'size_reduction_percent': size_reduction_percent
        }
            
    except Exception as e:
        # Handle any errors during optimization
        return {
            'optimized': False,
            'error': str(e),
            'original_path': source_db_path,
            'original_size_mb': source_size_mb
        }


def render_scale_info(db):
    """
    Render scale information and recommendations in the dashboard
    
    Args:
        db: DatabaseManager instance
    """
    scale_info = detect_scale(db)
    
    st.subheader("Database Scale Information")
    
    # Show object count with formatting
    st.metric("Total Objects", f"{scale_info['object_count']:,}")
    
    # Show scale category
    scale_category = scale_info['scale'].replace("_", " ").title()
    st.info(f"Scale Category: **{scale_category}**")
    
    # Show recommendations if any
    if scale_info['recommendations']:
        st.subheader("Optimization Recommendations")
        for i, rec in enumerate(scale_info['recommendations']):
            st.markdown(f"{i+1}. {rec}")
        
        # Add action buttons if appropriate
        if scale_info['scale'] in ["medium", "large", "very_large"]:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Indexes"):
                    with st.spinner("Creating indexes..."):
                        success = create_indexes(db)
                        if success:
                            st.success("Indexes created successfully!")
                        else:
                            st.error("Error creating indexes.")
            
            with col2:
                if st.button("Optimize DuckDB"):
                    with st.spinner("Optimizing DuckDB configuration..."):
                        db = configure_duckdb_for_scale(db)
                        st.success("DuckDB optimized for scale!")
