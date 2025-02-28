# Scaling Strategy for Aparavi Reporting Dashboard

This document outlines the strategies for scaling the Aparavi Reporting Dashboard to handle millions of objects (1M, 10M, 25M+).

## Current Limitations

The dashboard is currently optimized for small datasets (<5K objects) with these limitations:
- Full table scans for most queries
- Limited pagination and data windowing
- All data loaded into memory during analysis
- Visualization of complete datasets without sampling
- No query optimization for large datasets

## Scaling Optimizations

### 1. Database Optimizations

#### Indexing Strategy
```sql
-- Add indexing to critical columns
CREATE INDEX IF NOT EXISTS idx_objects_createdAt ON objects(createdAt);
CREATE INDEX IF NOT EXISTS idx_objects_updatedAt ON objects(updatedAt);
CREATE INDEX IF NOT EXISTS idx_objects_extension ON objects(extension);
CREATE INDEX IF NOT EXISTS idx_objects_size ON objects(size);
CREATE INDEX IF NOT EXISTS idx_permissions_objectId ON permissions(objectId);
```

#### Partitioning for Large Tables
For DuckDB 0.8.0+, implement partitioning on date ranges:
```sql
CREATE TABLE objects_partitioned AS 
SELECT * FROM objects 
ORDER BY createdAt;
```

#### Memory Management
```python
# Configure DuckDB for larger datasets
def configure_duckdb_for_scale(conn, memory_limit_gb=4):
    """Configure DuckDB settings for large datasets"""
    memory_limit = memory_limit_gb * 1024 * 1024 * 1024  # Convert to bytes
    conn.execute(f"SET memory_limit='{memory_limit_gb}GB'")
    conn.execute("SET temp_directory='/path/to/temp'")  # Use SSD for temp storage
    conn.execute("PRAGMA threads=8")  # Set thread count based on CPU cores
    conn.execute("PRAGMA force_parallelism")
    return conn
```

### 2. Query Optimization

#### Implement Data Sampling
```python
def sample_large_dataset(db, table, sample_size=100000):
    """Sample data for visualizations when dealing with large datasets"""
    count = db.get_row_count(table)
    
    if count > sample_size:
        # Use reservoir sampling for very large datasets
        query = f"""
        SELECT * FROM {table} 
        WHERE rand() <= {sample_size}/{count}
        LIMIT {sample_size}
        """
        return db.query(query)
    else:
        return db.query(f"SELECT * FROM {table}")
```

#### Incremental Query Processing
```python
def incremental_aggregation(db, table, group_by_column, aggregate_column, batch_size=500000):
    """Process large aggregations in batches"""
    results = {}
    offset = 0
    
    while True:
        batch_query = f"""
        SELECT {group_by_column}, COUNT({aggregate_column}) as count
        FROM {table} 
        LIMIT {batch_size} OFFSET {offset}
        """
        batch = db.query(batch_query)
        
        if batch.empty:
            break
            
        # Accumulate results
        for _, row in batch.iterrows():
            key = row[group_by_column]
            count = row['count']
            results[key] = results.get(key, 0) + count
            
        offset += batch_size
        
    return pd.DataFrame(list(results.items()), columns=[group_by_column, 'count'])
```

#### Time-Window Analysis
```python
def analyze_by_time_window(db, start_date, end_date, interval='month'):
    """Analyze data in specific time windows instead of full dataset"""
    query = f"""
    SELECT 
        DATE_TRUNC('{interval}', TIMESTAMP_MS(createdAt)) as period,
        COUNT(*) as document_count,
        AVG(size) as avg_size
    FROM objects
    WHERE createdAt BETWEEN {start_date.timestamp() * 1000} AND {end_date.timestamp() * 1000}
    GROUP BY 1
    ORDER BY 1
    """
    return db.query(query)
```

### 3. UI/UX Optimizations

#### Data Pagination
Update the dashboard views to implement pagination for all data tables:

```python
def paginated_data_view(db, table, page_size=100, page=1):
    """Return paginated data for display"""
    offset = (page - 1) * page_size
    query = f"SELECT * FROM {table} LIMIT {page_size} OFFSET {offset}"
    data = db.query(query)
    
    # Get total count for pagination controls
    total = db.get_row_count(table)
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
```

#### Progressive Loading
Implement progressive loading of visualizations:

```python
def progressive_visualization(data_function, update_interval=1000):
    """Create visualizations that load progressively"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    chart_placeholder = st.empty()
    
    # Initial low-resolution view
    sample_data = data_function(sample_size=10000)
    chart = create_visualization(sample_data)
    chart_placeholder.pyplot(chart)
    
    # Update with more data progressively
    for i, sample_size in enumerate([50000, 100000, 500000, 1000000]):
        progress = (i + 1) / 4
        progress_bar.progress(progress)
        status_text.text(f"Loading visualization ({sample_size} records)...")
        
        updated_data = data_function(sample_size=sample_size)
        updated_chart = create_visualization(updated_data)
        chart_placeholder.pyplot(updated_chart)
        time.sleep(0.5)  # Give UI time to update
    
    progress_bar.progress(1.0)
    status_text.text("Visualization complete!")
```

#### Background Processing
```python
def background_analysis(db, analysis_func, key):
    """Run intensive analysis in background thread"""
    # Check if analysis is already cached
    if key in st.session_state:
        return st.session_state[key]
    
    # Run in background if not cached
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def cached_analysis():
        return analysis_func(db)
    
    with st.spinner(f"Running analysis (this may take a moment)..."):
        result = cached_analysis()
        st.session_state[key] = result
    
    return result
```

### 4. Infrastructure Enhancements

#### Memory Configuration
For 25M+ objects, configure system with at least:
- 16GB RAM for Streamlit application
- SSD storage for DuckDB files and temp storage

#### Distributed Processing
For very large datasets (>25M objects), consider a hybrid approach:
1. Use DuckDB for interactive queries and visualizations (with sampling)
2. Pre-compute intensive aggregations using distributed systems (Spark/Dask) 
3. Store pre-computed results in the DuckDB database

```python
def precompute_large_aggregations(source_data_path, output_db_path):
    """
    Use external tools to precompute aggregations for very large datasets
    This would be run as a scheduled job before users access the dashboard
    """
    import subprocess
    
    # Example: Run a Spark job to precompute aggregations
    cmd = [
        "spark-submit",
        "--class", "org.aparavi.reporting.Precompute",
        "--master", "local[*]",
        "/path/to/aparavi-precompute.jar",
        source_data_path,
        output_db_path
    ]
    
    subprocess.run(cmd, check=True)
```

### 5. Caching Strategy

#### Multi-level Caching
```python
def get_data_with_caching(db, query_key, query_func, ttl=3600, force_refresh=False):
    """
    Multi-level caching strategy:
    1. Memory cache (session_state) for fastest access
    2. Disk cache for persistence between sessions
    3. Database materialized views for complex queries
    """
    cache_key = f"cache_{query_key}"
    
    # Check if force refresh requested
    if force_refresh and cache_key in st.session_state:
        del st.session_state[cache_key]
    
    # Return from memory cache if available
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # Try disk cache via st.cache_data
    @st.cache_data(ttl=ttl)
    def cached_query():
        return query_func(db)
    
    # Execute and cache
    result = cached_query()
    st.session_state[cache_key] = result
    
    return result
```

#### Materialized Views
For very complex but frequently accessed data:

```sql
-- Example materialized view for document age distribution
CREATE OR REPLACE VIEW document_age_distribution AS
SELECT
    CASE
        WHEN (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) * 1000 - createdAt) / 86400000 < 30 THEN 'Last 30 Days'
        WHEN (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) * 1000 - createdAt) / 86400000 < 90 THEN '30-90 Days'
        WHEN (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) * 1000 - createdAt) / 86400000 < 180 THEN '90-180 Days'
        WHEN (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) * 1000 - createdAt) / 86400000 < 365 THEN '180-365 Days'
        ELSE 'Over 1 Year'
    END AS age_group,
    COUNT(*) AS document_count
FROM objects
WHERE createdAt IS NOT NULL
GROUP BY 1
ORDER BY 
    CASE
        WHEN age_group = 'Last 30 Days' THEN 1
        WHEN age_group = '30-90 Days' THEN 2
        WHEN age_group = '90-180 Days' THEN 3
        WHEN age_group = '180-365 Days' THEN 4
        ELSE 5
    END;
```

## Performance Testing Strategy

### Test Data Generation
```python
def generate_test_data(db_path, object_count=1000000):
    """Generate test data with millions of objects"""
    conn = duckdb.connect(db_path)
    
    # Create larger test dataset
    conn.execute("""
    CREATE TABLE IF NOT EXISTS objects AS
    SELECT
        row_number() OVER () as objectId,
        CASE WHEN random() < 0.4 THEN '.pdf' 
             WHEN random() < 0.6 THEN '.docx' 
             WHEN random() < 0.8 THEN '.xlsx'
             ELSE '.txt'
        END as extension,
        (random() * 10000000)::INTEGER as size,
        (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP - INTERVAL (random() * 365 * 3) DAY) * 1000)::BIGINT as createdAt,
        (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP - INTERVAL (random() * 365 * 2) DAY) * 1000)::BIGINT as updatedAt
    FROM range(1, {object_count+1})
    """)
    
    conn.close()
    print(f"Generated {object_count} test objects")
```

### Benchmarking Key Operations
```python
def benchmark_queries(db_path, queries):
    """Benchmark query performance at different scales"""
    conn = duckdb.connect(db_path)
    db = DatabaseManager(db_path)
    
    results = {}
    for name, query in queries.items():
        start_time = time.time()
        db.query(query)
        end_time = time.time()
        
        results[name] = end_time - start_time
        print(f"Query '{name}' took {results[name]:.4f} seconds")
    
    return results
```

## Implementation Roadmap

1. **Phase 1: Database Optimization**
   - Add proper indexes
   - Implement query optimization
   - Configure DuckDB settings for scale

2. **Phase 2: UI Enhancements**
   - Add pagination to all data tables
   - Implement progressive loading
   - Add data sampling for visualizations

3. **Phase 3: Caching & Performance**
   - Implement multi-level caching
   - Add background processing for complex reports
   - Optimize memory usage

4. **Phase 4: Scale Testing**
   - Generate test datasets (1M, 10M, 25M)
   - Benchmark critical operations
   - Optimize based on benchmark results

## Monitoring and Profiling

```python
def profile_memory_usage():
    """Monitor memory usage during dashboard operation"""
    import psutil
    import matplotlib.pyplot as plt
    
    process = psutil.Process()
    memory_usage = []
    timestamps = []
    
    # Monitor for 60 seconds
    start_time = time.time()
    while time.time() - start_time < 60:
        memory_info = process.memory_info()
        memory_usage.append(memory_info.rss / 1024 / 1024)  # MB
        timestamps.append(time.time() - start_time)
        time.sleep(1)
    
    # Plot memory usage
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, memory_usage)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage Profile')
    plt.grid(True)
    return plt.gcf()
```

## Conclusion

By implementing these optimizations, the Aparavi Reporting Dashboard will be able to efficiently handle datasets of 1M, 10M, and even 25M+ objects. The key is to apply a combination of:

1. Database optimization (indexing, partitioning)
2. Smart data sampling and windowing
3. Progressive loading and visualization techniques
4. Multi-level caching
5. Background processing for intensive operations

For extremely large datasets (25M+), consider implementing a hybrid approach with pre-computed aggregations and materialized views to maintain interactive performance.
