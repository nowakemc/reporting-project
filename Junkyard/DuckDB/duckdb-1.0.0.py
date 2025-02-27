import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import base64
from io import BytesIO
from datetime import datetime
import tempfile

# Set up plotting styles
plt.style.use('ggplot')
sns.set_palette("Set2")

# Set page config
st.set_page_config(
    page_title="DuckDB Document Management Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Functions for database connection and analysis
@st.cache_resource
def connect_to_duckdb(db_path):
    """Connect to a DuckDB database file."""
    try:
        conn = duckdb.connect(db_path)
        return conn, None
    except Exception as e:
        return None, str(e)

def list_tables(conn):
    """List all tables in the DuckDB database."""
    tables = conn.execute("SHOW TABLES").fetchall()
    return [table[0] for table in tables]

def convert_epoch_to_datetime(df, time_columns):
    """Convert epoch timestamps to readable datetime."""
    for col in time_columns:
        if col in df.columns and df[col].dtype in (int, float):
            # Check if timestamps are in milliseconds (common in databases)
            if df[col].max() > 1e10:
                df[col] = pd.to_datetime(df[col], unit='ms')
            else:
                df[col] = pd.to_datetime(df[col], unit='s')
    return df

def fig_to_base64(fig):
    """Convert a matplotlib figure to a base64 encoded image."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def objects_report(conn):
    """Generate report on objects table."""
    st.subheader("Objects Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get file extension distribution
        extension_counts = conn.execute("""
            SELECT 
                COALESCE(extension, 'No Extension') as ext,
                COUNT(*) as count
            FROM objects
            GROUP BY ext
            ORDER BY count DESC
            LIMIT 10
        """).fetchdf()
        
        # Summary stats
        total_objects = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
        unique_extensions = conn.execute("SELECT COUNT(DISTINCT extension) FROM objects").fetchone()[0]
        
        st.metric("Total Objects", f"{total_objects:,}")
        st.metric("Unique File Extensions", f"{unique_extensions:,}")
        
        st.subheader("Top File Extensions")
        st.dataframe(extension_counts, use_container_width=True)
    
    with col2:
        # Get tag distribution if available
        try:
            tag_distribution = conn.execute("""
                SELECT 
                    json_extract_string(value, '$.key') as tag_key,
                    COUNT(*) as count
                FROM objects, 
                     json_each(CASE WHEN tags = '' OR tags IS NULL THEN '[]' ELSE tags END) 
                GROUP BY tag_key
                ORDER BY count DESC
                LIMIT 10
            """).fetchdf()
            
            if not tag_distribution.empty:
                st.subheader("Tag Distribution")
                st.dataframe(tag_distribution, use_container_width=True)
        except Exception as e:
            st.warning(f"Error analyzing tags: {e}")
    
    # Plot file extension distribution
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.barplot(x='count', y='ext', data=extension_counts, ax=ax1)
    ax1.set_title('Top 10 File Extensions')
    plt.tight_layout()
    st.pyplot(fig1)
    
    # Get object creation over time - FIXED DATE HANDLING
    creation_over_time = conn.execute("""
        SELECT 
            DATE_TRUNC('month', to_timestamp(createdAt/1000)) as month,
            COUNT(*) as count
        FROM objects
        GROUP BY month
        ORDER BY month
    """).fetchdf()
    
    # Convert to pandas datetime if needed
    creation_over_time['month'] = pd.to_datetime(creation_over_time['month'])
    
    # Plot object creation over time
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(creation_over_time['month'], creation_over_time['count'], marker='o')
    ax2.set_title('Object Creation Over Time')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Number of Objects')
    plt.tight_layout()
    st.pyplot(fig2)

def instances_report(conn):
    """Generate report on instances table."""
    st.subheader("Instances Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get storage size statistics
        size_stats = conn.execute("""
            SELECT 
                MIN(size) as min_size,
                MAX(size) as max_size,
                AVG(size) as avg_size,
                MEDIAN(size) as median_size,
                SUM(size) as total_size
            FROM instances
            WHERE size IS NOT NULL
        """).fetchone()
        
        # Storage metrics
        st.subheader("Storage Statistics")
        metrics = {
            "Min Size": f"{size_stats[0]/1024:.2f} KB",
            "Max Size": f"{size_stats[1]/1024/1024:.2f} MB",
            "Avg Size": f"{size_stats[2]/1024:.2f} KB",
            "Median Size": f"{size_stats[3]/1024:.2f} KB",
            "Total Storage": f"{size_stats[4]/1024/1024/1024:.2f} GB"
        }
        
        for label, value in metrics.items():
            st.metric(label, value)
    
    with col2:
        # Get service distribution
        try:
            service_distribution = conn.execute("""
                SELECT 
                    s.name as service_name,
                    COUNT(*) as instance_count
                FROM instances i
                JOIN services s ON i.serviceId = s.serviceId
                GROUP BY s.name
                ORDER BY instance_count DESC
            """).fetchdf()
            
            if not service_distribution.empty:
                st.subheader("Service Distribution")
                st.dataframe(service_distribution, use_container_width=True)
        except Exception as e:
            st.warning(f"Error analyzing services: {e}")
    
    # Size distribution
    size_distribution = conn.execute("""
        SELECT 
            CASE
                WHEN size < 1024 THEN 'Under 1KB'
                WHEN size < 1024*1024 THEN '1KB-1MB'
                WHEN size < 1024*1024*10 THEN '1MB-10MB'
                WHEN size < 1024*1024*100 THEN '10MB-100MB'
                ELSE 'Over 100MB'
            END as size_range,
            COUNT(*) as count
        FROM instances
        WHERE size IS NOT NULL
        GROUP BY size_range
        ORDER BY 
            CASE 
                WHEN size_range = 'Under 1KB' THEN 1
                WHEN size_range = '1KB-1MB' THEN 2
                WHEN size_range = '1MB-10MB' THEN 3
                WHEN size_range = '10MB-100MB' THEN 4
                ELSE 5
            END
    """).fetchdf()
    
    # Plot size distribution
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.barplot(x='size_range', y='count', data=size_distribution, ax=ax1)
    ax1.set_title('File Size Distribution')
    ax1.set_xlabel('Size Range')
    ax1.set_ylabel('Count')
    plt.tight_layout()
    st.pyplot(fig1)
    
    # Get time-based stats - FIXED DATE HANDLING
    creation_by_month = conn.execute("""
        SELECT 
            DATE_TRUNC('month', to_timestamp(createTime/1000)) as month,
            COUNT(*) as count,
            SUM(size)/1024/1024 as total_size_mb
        FROM instances
        WHERE createTime IS NOT NULL
        GROUP BY month
        ORDER BY month
    """).fetchdf()
    
    # Convert to pandas datetime if needed
    creation_by_month['month'] = pd.to_datetime(creation_by_month['month'])
    
    # Plot creation over time with file size
    fig2, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Instances', color='tab:blue')
    ax1.plot(creation_by_month['month'], creation_by_month['count'], color='tab:blue', marker='o')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Total Size (MB)', color='tab:red')
    ax2.plot(creation_by_month['month'], creation_by_month['total_size_mb'], color='tab:red', marker='x')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    plt.title('Instance Creation and Size Over Time')
    fig2.tight_layout()
    st.pyplot(fig2)

def classifications_report(conn):
    """Generate report on classifications."""
    st.subheader("Classifications Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get summary stats
        total_classifications = conn.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]
        unique_sets = conn.execute("SELECT COUNT(DISTINCT classificationSet) FROM classifications").fetchone()[0]
        
        st.metric("Total Classifications", f"{total_classifications:,}")
        st.metric("Unique Classification Sets", f"{unique_sets:,}")
    
    # Get classification sets distribution
    classification_sets = conn.execute("""
        SELECT 
            classificationSet,
            COUNT(*) as count
        FROM classifications
        GROUP BY classificationSet
        ORDER BY count DESC
    """).fetchdf()
    
    with col2:
        st.subheader("Top Classification Sets")
        st.dataframe(classification_sets.head(10), use_container_width=True)
    
    # Plot classification sets
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='count', y='classificationSet', data=classification_sets.head(10), ax=ax)
    ax.set_title('Classification Sets Distribution')
    plt.tight_layout()
    st.pyplot(fig)
    
    # Get objects with classifications
    try:
        classified_objects = conn.execute("""
            SELECT 
                c.classificationSet,
                COUNT(DISTINCT i.objectId) as object_count
            FROM classifications c
            JOIN instances i ON i.classificationId = c.classificationId
            GROUP BY c.classificationSet
            ORDER BY object_count DESC
        """).fetchdf()
        
        if not classified_objects.empty:
            st.subheader("Objects with Classifications")
            st.dataframe(classified_objects, use_container_width=True)
            
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(x='object_count', y='classificationSet', data=classified_objects.head(10), ax=ax2)
            ax2.set_title('Objects per Classification Set')
            plt.tight_layout()
            st.pyplot(fig2)
    except Exception as e:
        st.warning(f"Error analyzing classified objects: {e}")

def parent_path_report(conn):
    """Generate report on parent paths."""
    st.subheader("Parent Path Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get summary stats
        total_paths = conn.execute("SELECT COUNT(*) FROM parentPaths").fetchone()[0]
        unique_parents = conn.execute("SELECT COUNT(DISTINCT parentId) FROM parentPaths").fetchone()[0]
        
        st.metric("Total Parent Paths", f"{total_paths:,}")
        st.metric("Unique Parent IDs", f"{unique_parents:,}")
    
    # Get path depth distribution
    path_depth = conn.execute("""
        SELECT 
            (LENGTH(parentPath) - LENGTH(REPLACE(parentPath, '/', ''))) as depth,
            COUNT(*) as count
        FROM parentPaths
        GROUP BY depth
        ORDER BY depth
    """).fetchdf()
    
    with col2:
        # Get top-level paths
        top_paths = conn.execute("""
            SELECT 
                SPLIT_PART(parentPath, '/', 1) as top_level,
                COUNT(*) as count
            FROM parentPaths
            GROUP BY top_level
            ORDER BY count DESC
            LIMIT 10
        """).fetchdf()
        
        st.subheader("Top-level Path Categories")
        st.dataframe(top_paths, use_container_width=True)
    
    # Plot path depth
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='depth', y='count', data=path_depth, ax=ax)
    ax.set_title('Path Depth Distribution')
    ax.set_xlabel('Path Depth (Number of / characters)')
    ax.set_ylabel('Count')
    plt.tight_layout()
    st.pyplot(fig)
    
    # Plot top paths
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    sns.barplot(x='count', y='top_level', data=top_paths, ax=ax2)
    ax2.set_title('Top-level Path Categories')
    plt.tight_layout()
    st.pyplot(fig2)

def tags_report(conn):
    """Generate report on tags and tagSets."""
    st.subheader("Tags Report")
    
    try:
        # Get tag sets distribution
        tag_sets = conn.execute("""
            SELECT 
                tagSet,
                COUNT(*) as used_count
            FROM tagSets
            LEFT JOIN instances ON instances.tagSetId = tagSets.tagSetId
            GROUP BY tagSet
            ORDER BY used_count DESC
        """).fetchdf()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Tag Sets", f"{len(tag_sets):,}")
        
        with col2:
            st.subheader("Tag Sets")
            st.dataframe(tag_sets, use_container_width=True)
        
        # Plot tag sets distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='used_count', y='tagSet', data=tag_sets, ax=ax)
        ax.set_title('Tag Sets Usage')
        plt.tight_layout()
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Error analyzing tags: {e}")

def services_report(conn):
    """Generate report on services."""
    st.subheader("Services Report")
    
    try:
        # Get service types distribution
        service_types = conn.execute("""
            SELECT 
                type,
                COUNT(*) as count
            FROM services
            GROUP BY type
            ORDER BY count DESC
        """).fetchdf()
        
        # Get service details
        services = conn.execute("""
            SELECT 
                serviceId,
                key,
                name,
                type,
                mode,
                accessDelay,
                accessRate,
                accessCost,
                storeCost
            FROM services
            ORDER BY name
        """).fetchdf()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Services", f"{len(services):,}")
            
            st.subheader("Service Types")
            st.dataframe(service_types, use_container_width=True)
        
        with col2:
            # Get service usage
            service_usage = conn.execute("""
                SELECT 
                    s.name as service_name,
                    s.type as service_type,
                    COUNT(i.instanceId) as instance_count
                FROM services s
                LEFT JOIN instances i ON i.serviceId = s.serviceId
                GROUP BY s.name, s.type
                ORDER BY instance_count DESC
            """).fetchdf()
            
            st.subheader("Service Usage")
            st.dataframe(service_usage, use_container_width=True)
        
        # Plot service types
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='count', y='type', data=service_types, ax=ax1)
        ax1.set_title('Service Types Distribution')
        plt.tight_layout()
        st.pyplot(fig1)
        
        # Plot service usage
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        sns.barplot(x='instance_count', y='service_name', data=service_usage, ax=ax2)
        ax2.set_title('Service Usage (Instance Count)')
        plt.tight_layout()
        st.pyplot(fig2)
        
        # Service details table
        st.subheader("Service Details")
        st.dataframe(services, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error analyzing services: {e}")

def permissions_report(conn):
    """Generate report on osPermissions and osSecurity."""
    st.subheader("Permissions Report")
    
    try:
        # Get permission sets distribution
        permission_sets = conn.execute("""
            SELECT 
                permissionSet,
                COUNT(*) as count
            FROM osPermissions
            GROUP BY permissionSet
            ORDER BY count DESC
        """).fetchdf()
        
        # Get security authorities
        security_authorities = conn.execute("""
            SELECT 
                authority,
                COUNT(*) as count,
                SUM(isGroup) as group_count,
                SUM(isLocal) as local_count
            FROM osSecurity
            GROUP BY authority
            ORDER BY count DESC
        """).fetchdf()
        
        # Get summary stats
        total_permissions = conn.execute("SELECT COUNT(*) FROM osPermissions").fetchone()[0]
        unique_permission_sets = conn.execute("SELECT COUNT(DISTINCT permissionSet) FROM osPermissions").fetchone()[0]
        total_security = conn.execute("SELECT COUNT(*) FROM osSecurity").fetchone()[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Permissions", f"{total_permissions:,}")
            st.metric("Unique Permission Sets", f"{unique_permission_sets:,}")
            
            st.subheader("Permission Sets")
            st.dataframe(permission_sets, use_container_width=True)
        
        with col2:
            st.metric("Total Security Entries", f"{total_security:,}")
            
            st.subheader("Security Authorities")
            st.dataframe(security_authorities, use_container_width=True)
        
        # Plot permission sets
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='count', y='permissionSet', data=permission_sets.head(10), ax=ax1)
        ax1.set_title('Permission Sets Distribution')
        plt.tight_layout()
        st.pyplot(fig1)
        
        # Plot security authorities
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='count', y='authority', data=security_authorities.head(10), ax=ax2)
        ax2.set_title('Security Authorities')
        plt.tight_layout()
        st.pyplot(fig2)
        
    except Exception as e:
        st.error(f"Error analyzing permissions: {e}")

def messages_report(conn):
    """Generate report on messages."""
    st.subheader("Messages Report")
    
    try:
        # Get summary stats
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        
        st.metric("Total Messages", f"{total_messages:,}")
        
        # Get message time distribution - FIXED DATE HANDLING
        message_time_dist = conn.execute("""
            SELECT 
                DATE_TRUNC('month', to_timestamp(messageTime/1000)) as month,
                COUNT(*) as count
            FROM messages
            GROUP BY month
            ORDER BY month
        """).fetchdf()
        
        # Convert to pandas datetime if needed
        message_time_dist['month'] = pd.to_datetime(message_time_dist['month'])
        
        # Plot message time distribution
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(message_time_dist['month'], message_time_dist['count'], marker='o')
        ax.set_title('Messages Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Messages')
        plt.tight_layout()
        st.pyplot(fig)
        
        # Get sample messages (limited to avoid large data transfer)
        sample_messages = conn.execute("""
            SELECT 
                messageId,
                messageGuid,
                to_timestamp(messageTime/1000) as time,
                SUBSTRING(message, 1, 100) || CASE WHEN LENGTH(message) > 100 THEN '...' ELSE '' END as message_preview
            FROM messages
            ORDER BY messageTime DESC
            LIMIT 10
        """).fetchdf()
        
        st.subheader("Sample Messages")
        st.dataframe(sample_messages, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error analyzing messages: {e}")

def overview_report(conn):
    """Generate an overview report with key statistics."""
    st.subheader("Database Overview")
    
    try:
        # Get table row counts
        tables = list_tables(conn)
        table_counts = {}
        
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            table_counts[table] = count
        
        # Sort by count
        sorted_counts = {k: v for k, v in sorted(table_counts.items(), key=lambda item: item[1], reverse=True)}
        
        # Get database summary
        total_objects = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
        total_instances = conn.execute("SELECT COUNT(*) FROM instances").fetchone()[0]
        total_storage = conn.execute("SELECT SUM(size) FROM instances WHERE size IS NOT NULL").fetchone()[0]
        
        # Get date range - FIXED DATE HANDLING
        min_date = conn.execute("""
            SELECT MIN(to_timestamp(createTime/1000))
            FROM instances 
            WHERE createTime IS NOT NULL
        """).fetchone()[0]
        
        max_date = conn.execute("""
            SELECT MAX(to_timestamp(createTime/1000)) 
            FROM instances
            WHERE createTime IS NOT NULL
        """).fetchone()[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Objects", f"{total_objects:,}")
        
        with col2:
            st.metric("Total Instances", f"{total_instances:,}")
        
        with col3:
            st.metric("Total Storage", f"{total_storage/1024/1024/1024:.2f} GB" if total_storage else "N/A")
        
        st.subheader("Date Range")
        st.write(f"{min_date} to {max_date}" if min_date and max_date else "N/A")
        
        # Table counts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Table Row Counts")
            counts_df = pd.DataFrame(list(sorted_counts.items()), columns=['table', 'count'])
            st.dataframe(counts_df, use_container_width=True)
        
        with col2:
            # Plot table counts
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.barplot(x='count', y='table', data=counts_df, ax=ax)
            ax.set_title('Database Table Sizes')
            plt.tight_layout()
            st.pyplot(fig)
        
        # Get relationship summary
        try:
            relationship_stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT o.objectId) as unique_objects,
                    COUNT(DISTINCT i.instanceId) as unique_instances,
                    COUNT(DISTINCT o.parentId) as unique_parents,
                    COUNT(DISTINCT i.serviceId) as unique_services,
                    COUNT(DISTINCT i.classificationId) as unique_classifications
                FROM objects o
                LEFT JOIN instances i ON o.objectId = i.objectId
            """).fetchone()
            
            st.subheader("Relationship Summary")
            rel_col1, rel_col2, rel_col3, rel_col4, rel_col5 = st.columns(5)
            
            with rel_col1:
                st.metric("Unique Objects", f"{relationship_stats[0]:,}")
            
            with rel_col2:
                st.metric("Unique Instances", f"{relationship_stats[1]:,}")
            
            with rel_col3:
                st.metric("Unique Parents", f"{relationship_stats[2]:,}")
            
            with rel_col4:
                st.metric("Unique Services", f"{relationship_stats[3]:,}")
            
            with rel_col5:
                st.metric("Unique Classifications", f"{relationship_stats[4]:,}")
        
        except Exception as e:
            st.warning(f"Error getting relationship stats: {e}")
    
    except Exception as e:
        st.error(f"Error generating overview: {e}")

def main():
    """Main function for the Streamlit app."""
    st.title("DuckDB Document Management Analyzer")
    
    # Sidebar for file upload
    st.sidebar.header("Database Connection")
    uploaded_file = st.sidebar.file_uploader("Upload DuckDB file", type=["duckdb", "db"])
    
    # Sample database for demo purposes
    use_sample = st.sidebar.checkbox("Use sample database", value=False)
    
    if use_sample:
        # Provide path to a sample database if available
        sample_path = "sample.duckdb"
        if os.path.exists(sample_path):
            conn, error = connect_to_duckdb(sample_path)
            if error:
                st.sidebar.error(f"Error connecting to sample database: {error}")
            else:
                st.sidebar.success(f"Connected to sample database")
                display_reports(conn)
        else:
            st.sidebar.error("Sample database not found")
    
    elif uploaded_file is not None:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.duckdb') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            db_path = tmp_file.name
        
        # Connect to the database
        conn, error = connect_to_duckdb(db_path)
        
        if error:
            st.sidebar.error(f"Error connecting to database: {error}")
        else:
            st.sidebar.success(f"Connected to {uploaded_file.name}")
            
            # Display available tables
            tables = list_tables(conn)
            st.sidebar.subheader("Available Tables")
            st.sidebar.write(", ".join(tables))
            
            # Display reports
            display_reports(conn)
            
        # Clean up temporary file
        try:
            os.unlink(db_path)
        except:
            pass
    else:
        # Instructions when no file is uploaded
        st.write("Please upload a DuckDB database file to begin analysis.")
        st.write("The analyzer will generate reports for tables related to document management:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - **Objects**: Document objects with metadata
            - **Instances**: Storage instances of objects
            - **Classifications**: Classification metadata
            - **Parent Paths**: Path hierarchy information
            - **Tag Sets**: Tag set definitions
            """)
        
        with col2:
            st.markdown("""
            - **Services**: Service configurations
            - **OS Permissions**: Permission sets
            - **OS Security**: Security configurations
            - **Messages**: System messages
            """)

def display_reports(conn):
    """Display tabs with different reports."""
    # Create tabs for different reports
    overview_tab, objects_tab, instances_tab, classifications_tab, paths_tab, tags_tab, services_tab, permissions_tab, messages_tab = st.tabs([
        "Overview", "Objects", "Instances", "Classifications", "Paths", "Tags", "Services", "Permissions", "Messages"
    ])
    
    # Get available tables
    tables = list_tables(conn)
    
    # Display reports in tabs
    with overview_tab:
        overview_report(conn)
    
    with objects_tab:
        if 'objects' in tables:
            objects_report(conn)
        else:
            st.warning("Objects table not found in database")
    
    with instances_tab:
        if 'instances' in tables:
            instances_report(conn)
        else:
            st.warning("Instances table not found in database")
    
    with classifications_tab:
        if 'classifications' in tables:
            classifications_report(conn)
        else:
            st.warning("Classifications table not found in database")
    
    with paths_tab:
        if 'parentPaths' in tables:
            parent_path_report(conn)
        else:
            st.warning("ParentPaths table not found in database")
    
    with tags_tab:
        if 'tagSets' in tables:
            tags_report(conn)
        else:
            st.warning("TagSets table not found in database")
    
    with services_tab:
        if 'services' in tables:
            services_report(conn)
        else:
            st.warning("Services table not found in database")
    
    with permissions_tab:
        if 'osPermissions' in tables and 'osSecurity' in tables:
            permissions_report(conn)
        else:
            st.warning("Permission tables not found in database")
    
    with messages_tab:
        if 'messages' in tables:
            messages_report(conn)
        else:
            st.warning("Messages table not found in database")

if __name__ == "__main__":
    main()