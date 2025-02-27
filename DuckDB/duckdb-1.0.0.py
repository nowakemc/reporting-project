import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import base64
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

# Initialize Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store the current connection
current_conn = None
current_db_path = None

# Set up plotting styles
plt.style.use('ggplot')
sns.set_palette("Set2")

def connect_to_duckdb(db_path):
    """Connect to a DuckDB database file."""
    try:
        conn = duckdb.connect(db_path)
        print(f"Successfully connected to {db_path}")
        return conn
    except Exception as e:
        print(f"Error connecting to DuckDB: {e}")
        return None

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
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def objects_report(conn):
    """Generate report on objects table."""
    report_data = {}
    
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
    
    # Get object creation over time
    creation_over_time = conn.execute("""
        SELECT 
            DATE_TRUNC('month', TIMESTAMP 'epoch' + createdAt/1000 * INTERVAL '1 second') as month,
            COUNT(*) as count
        FROM objects
        GROUP BY month
        ORDER BY month
    """).fetchdf()
    
    # Convert epoch to datetime
    creation_over_time['month'] = pd.to_datetime(creation_over_time['month'])
    
    # Plot file extension distribution
    fig1 = plt.figure(figsize=(10, 6))
    sns.barplot(x='count', y='ext', data=extension_counts)
    plt.title('Top 10 File Extensions')
    plt.tight_layout()
    report_data['extension_dist_img'] = fig_to_base64(fig1)
    
    # Plot object creation over time
    fig2 = plt.figure(figsize=(12, 6))
    plt.plot(creation_over_time['month'], creation_over_time['count'], marker='o')
    plt.title('Object Creation Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Objects')
    plt.tight_layout()
    report_data['creation_timeline_img'] = fig_to_base64(fig2)
    
    # Get summary stats
    total_objects = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
    unique_extensions = conn.execute("SELECT COUNT(DISTINCT extension) FROM objects").fetchone()[0]
    
    # Add summary stats to report data
    report_data['total_objects'] = total_objects
    report_data['unique_extensions'] = unique_extensions
    report_data['top_extensions'] = extension_counts.head(5).to_dict('records')
    
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
        report_data['tag_distribution'] = tag_distribution.to_dict('records')
    except Exception as e:
        print(f"Error analyzing tags: {e}")
        report_data['tag_distribution'] = []
    
    return report_data

def instances_report(conn):
    """Generate report on instances table."""
    report_data = {}
    
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
    fig1 = plt.figure(figsize=(10, 6))
    sns.barplot(x='size_range', y='count', data=size_distribution)
    plt.title('File Size Distribution')
    plt.xlabel('Size Range')
    plt.ylabel('Count')
    plt.tight_layout()
    report_data['size_dist_img'] = fig_to_base64(fig1)
    
    # Add summary stats to report data
    report_data['size_stats'] = {
        'min_size': f"{size_stats[0]/1024:.2f} KB",
        'max_size': f"{size_stats[1]/1024/1024:.2f} MB",
        'avg_size': f"{size_stats[2]/1024:.2f} KB",
        'median_size': f"{size_stats[3]/1024:.2f} KB",
        'total_storage': f"{size_stats[4]/1024/1024/1024:.2f} GB"
    }
    
    # Get time-based stats
    creation_by_month = conn.execute("""
        SELECT 
            DATE_TRUNC('month', TIMESTAMP 'epoch' + createTime/1000 * INTERVAL '1 second') as month,
            COUNT(*) as count,
            SUM(size)/1024/1024 as total_size_mb
        FROM instances
        WHERE createTime IS NOT NULL
        GROUP BY month
        ORDER BY month
    """).fetchdf()
    
    # Convert epoch to datetime
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
    report_data['creation_size_img'] = fig_to_base64(fig2)
    
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
        report_data['service_distribution'] = service_distribution.to_dict('records')
    except Exception as e:
        print(f"Error analyzing services: {e}")
        report_data['service_distribution'] = []
    
    return report_data

def classifications_report(conn):
    """Generate report on classifications."""
    report_data = {}
    
    # Get classification sets distribution
    classification_sets = conn.execute("""
        SELECT 
            classificationSet,
            COUNT(*) as count
        FROM classifications
        GROUP BY classificationSet
        ORDER BY count DESC
    """).fetchdf()
    
    # Plot classification sets
    fig = plt.figure(figsize=(10, 6))
    sns.barplot(x='count', y='classificationSet', data=classification_sets)
    plt.title('Classification Sets Distribution')
    plt.tight_layout()
    report_data['classification_sets_img'] = fig_to_base64(fig)
    
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
        report_data['classified_objects'] = classified_objects.to_dict('records')
    except Exception as e:
        print(f"Error analyzing classified objects: {e}")
        report_data['classified_objects'] = []
    
    # Get summary stats
    total_classifications = conn.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]
    unique_sets = conn.execute("SELECT COUNT(DISTINCT classificationSet) FROM classifications").fetchone()[0]
    
    report_data['total_classifications'] = total_classifications
    report_data['unique_sets'] = unique_sets
    report_data['top_sets'] = classification_sets.head(5).to_dict('records')
    
    return report_data

def parent_path_report(conn):
    """Generate report on parent paths."""
    report_data = {}
    
    # Get path depth distribution
    path_depth = conn.execute("""
        SELECT 
            (LENGTH(parentPath) - LENGTH(REPLACE(parentPath, '/', ''))) as depth,
            COUNT(*) as count
        FROM parentPaths
        GROUP BY depth
        ORDER BY depth
    """).fetchdf()
    
    # Plot path depth
    fig = plt.figure(figsize=(10, 6))
    sns.barplot(x='depth', y='count', data=path_depth)
    plt.title('Path Depth Distribution')
    plt.xlabel('Path Depth (Number of / characters)')
    plt.ylabel('Count')
    plt.tight_layout()
    report_data['path_depth_img'] = fig_to_base64(fig)
    
    # Get summary stats
    total_paths = conn.execute("SELECT COUNT(*) FROM parentPaths").fetchone()[0]
    unique_parents = conn.execute("SELECT COUNT(DISTINCT parentId) FROM parentPaths").fetchone()[0]
    
    report_data['total_paths'] = total_paths
    report_data['unique_parents'] = unique_parents
    
    # Get top-level paths
    top_paths = conn.execute("""
        SELECT 
            SPLIT_PART(parentPath, '/', 1) as top_level,
            COUNT(*) as count
        FROM parentPaths
        GROUP BY top_level
        ORDER BY count DESC
        LIMIT 5
    """).fetchdf()
    
    report_data['top_paths'] = top_paths.to_dict('records')
    
    return report_data

def tags_report(conn):
    """Generate report on tags and tagSets."""
    report_data = {}
    
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
        
        # Plot tag sets distribution
        fig = plt.figure(figsize=(10, 6))
        sns.barplot(x='used_count', y='tagSet', data=tag_sets)
        plt.title('Tag Sets Usage')
        plt.tight_layout()
        report_data['tag_sets_img'] = fig_to_base64(fig)
        
        # Get tag sets summary
        report_data['tag_sets'] = tag_sets.to_dict('records')
        report_data['total_tag_sets'] = len(tag_sets)
        
    except Exception as e:
        print(f"Error analyzing tags: {e}")
        report_data['error'] = str(e)
    
    return report_data

def services_report(conn):
    """Generate report on services."""
    report_data = {}
    
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
        
        # Plot service types
        fig1 = plt.figure(figsize=(10, 6))
        sns.barplot(x='count', y='type', data=service_types)
        plt.title('Service Types Distribution')
        plt.tight_layout()
        report_data['service_types_img'] = fig_to_base64(fig1)
        
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
        
        # Plot service usage
        fig2 = plt.figure(figsize=(12, 6))
        sns.barplot(x='instance_count', y='service_name', data=service_usage)
        plt.title('Service Usage (Instance Count)')
        plt.tight_layout()
        report_data['service_usage_img'] = fig_to_base64(fig2)
        
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
        
        report_data['services'] = services.to_dict('records')
        report_data['service_usage'] = service_usage.to_dict('records')
        report_data['total_services'] = len(services)
        
    except Exception as e:
        print(f"Error analyzing services: {e}")
        report_data['error'] = str(e)
    
    return report_data

def permissions_report(conn):
    """Generate report on osPermissions and osSecurity."""
    report_data = {}
    
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
        
        # Plot permission sets
        fig1 = plt.figure(figsize=(10, 6))
        sns.barplot(x='count', y='permissionSet', data=permission_sets)
        plt.title('Permission Sets Distribution')
        plt.tight_layout()
        report_data['permission_sets_img'] = fig_to_base64(fig1)
        
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
        
        # Plot security authorities
        fig2 = plt.figure(figsize=(10, 6))
        sns.barplot(x='count', y='authority', data=security_authorities)
        plt.title('Security Authorities')
        plt.tight_layout()
        report_data['security_auth_img'] = fig_to_base64(fig2)
        
        # Get summary stats
        total_permissions = conn.execute("SELECT COUNT(*) FROM osPermissions").fetchone()[0]
        unique_permission_sets = conn.execute("SELECT COUNT(DISTINCT permissionSet) FROM osPermissions").fetchone()[0]
        total_security = conn.execute("SELECT COUNT(*) FROM osSecurity").fetchone()[0]
        
        report_data['total_permissions'] = total_permissions
        report_data['unique_permission_sets'] = unique_permission_sets
        report_data['total_security_entries'] = total_security
        report_data['permission_sets'] = permission_sets.to_dict('records')
        report_data['security_authorities'] = security_authorities.to_dict('records')
        
    except Exception as e:
        print(f"Error analyzing permissions: {e}")
        report_data['error'] = str(e)
    
    return report_data

def messages_report(conn):
    """Generate report on messages."""
    report_data = {}
    
    try:
        # Get message time distribution
        message_time_dist = conn.execute("""
            SELECT 
                DATE_TRUNC('month', TIMESTAMP 'epoch' + messageTime/1000 * INTERVAL '1 second') as month,
                COUNT(*) as count
            FROM messages
            GROUP BY month
            ORDER BY month
        """).fetchdf()
        
        # Convert epoch to datetime
        message_time_dist['month'] = pd.to_datetime(message_time_dist['month'])
        
        # Plot message time distribution
        fig = plt.figure(figsize=(12, 6))
        plt.plot(message_time_dist['month'], message_time_dist['count'], marker='o')
        plt.title('Messages Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Messages')
        plt.tight_layout()
        report_data['messages_time_img'] = fig_to_base64(fig)
        
        # Get summary stats
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        
        # Get sample messages (limited to avoid large data transfer)
        sample_messages = conn.execute("""
            SELECT 
                messageId,
                messageGuid,
                TIMESTAMP 'epoch' + messageTime/1000 * INTERVAL '1 second' as time,
                SUBSTRING(message, 1, 100) || CASE WHEN LENGTH(message) > 100 THEN '...' ELSE '' END as message_preview
            FROM messages
            ORDER BY messageTime DESC
            LIMIT 10
        """).fetchdf()
        
        report_data['total_messages'] = total_messages
        report_data['sample_messages'] = sample_messages.to_dict('records')
        
    except Exception as e:
        print(f"Error analyzing messages: {e}")
        report_data['error'] = str(e)
    
    return report_data

def overview_report(conn):
    """Generate an overview report with key statistics."""
    report_data = {}
    
    try:
        # Get table row counts
        tables = list_tables(conn)
        table_counts = {}
        
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            table_counts[table] = count
        
        # Sort by count
        sorted_counts = {k: v for k, v in sorted(table_counts.items(), key=lambda item: item[1], reverse=True)}
        
        # Plot table counts
        fig = plt.figure(figsize=(12, 8))
        counts_df = pd.DataFrame(list(sorted_counts.items()), columns=['table', 'count'])
        sns.barplot(x='count', y='table', data=counts_df)
        plt.title('Database Table Sizes')
        plt.tight_layout()
        report_data['table_counts_img'] = fig_to_base64(fig)
        
        # Get database summary
        total_objects = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
        total_instances = conn.execute("SELECT COUNT(*) FROM instances").fetchone()[0]
        total_storage = conn.execute("SELECT SUM(size) FROM instances WHERE size IS NOT NULL").fetchone()[0]
        
        # Get date range
        min_date = conn.execute("""
            SELECT MIN(TIMESTAMP 'epoch' + createTime/1000 * INTERVAL '1 second')
            FROM instances 
            WHERE createTime IS NOT NULL
        """).fetchone()[0]
        
        max_date = conn.execute("""
            SELECT MAX(TIMESTAMP 'epoch' + createTime/1000 * INTERVAL '1 second') 
            FROM instances
            WHERE createTime IS NOT NULL
        """).fetchone()[0]
        
        report_data['table_counts'] = sorted_counts
        report_data['total_objects'] = total_objects
        report_data['total_instances'] = total_instances
        report_data['total_storage'] = f"{total_storage/1024/1024/1024:.2f} GB" if total_storage else "N/A"
        report_data['date_range'] = f"{min_date} to {max_date}" if min_date and max_date else "N/A"
        
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
            
            report_data['relationship_stats'] = {
                'unique_objects': relationship_stats[0],
                'unique_instances': relationship_stats[1],
                'unique_parents': relationship_stats[2],
                'unique_services': relationship_stats[3],
                'unique_classifications': relationship_stats[4]
            }
        except Exception as e:
            print(f"Error getting relationship stats: {e}")
    
    except Exception as e:
        print(f"Error generating overview: {e}")
        report_data['error'] = str(e)
    
    return report_data

# Flask routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    """Connect to a DuckDB database."""
    global current_conn, current_db_path
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Save the uploaded file
        db_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(db_path)
        
        # Connect to the database
        conn = connect_to_duckdb(db_path)
        
        if conn:
            current_conn = conn
            current_db_path = db_path
            tables = list_tables(conn)
            return jsonify({'success': True, 'tables': tables})
        else:
            return jsonify({'error': 'Failed to connect to database'}), 500
    
    return jsonify({'error': 'Unknown error'}), 500

@app.route('/report/<report_type>')
def get_report(report_type):
    """Generate and return a report."""
    global current_conn
    
    if not current_conn:
        return jsonify({'error': 'Not connected to a database'}), 400
    
    # Define report functions mapping
    report_functions = {
        'overview': overview_report,
        'objects': objects_report,
        'instances': instances_report,
        'classifications': classifications_report,
        'parentPaths': parent_path_report,
        'tags': tags_report,
        'services': services_report,
        'permissions': permissions_report,
        'messages': messages_report
    }
    
    if report_type not in report_functions:
        return jsonify({'error': 'Invalid report type'}), 400
    
    # Generate the report
    try:
        report_data = report_functions[report_type](current_conn)
        return jsonify({'report': report_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/templates/index.html')
def get_template():
    """Serve the index.html template."""
    return render_template('index.html')

# HTML templates
@app.route('/templates')
def get_templates():
    """Return HTML templates as a JSON object."""
    templates = {
        'index': '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckDB Analyzer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .report-container {
            margin-top: 20px;
        }
        .chart-container {
            margin-bottom: 20px;
        }
        .nav-tabs {
            margin-bottom: 20px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .stats-box {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="my-4">DuckDB Document Management Analyzer</h1>
        
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Database Connection
                    </div>
                    <div class="card-body">
                        <form id="db-connect-form">
                            <div class="mb-3">
                                <label for="db-file" class="form-label">Select DuckDB File</label>
                                <input class="form-control" type="file" id="db-file" accept=".duckdb,.db">
                            </div>
                            <button type="submit" class="btn btn-primary">Connect</button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Database Info
                    </div>
                    <div class="card-body" id="db-info">
                        <p>Not connected to a database.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Loading report data...</p>
        </div>
        
        <div id="report-tabs" style="display: none;">
            <ul class="nav nav-tabs" id="reportTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button" role="tab">Overview</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="objects-tab" data-bs-toggle="tab" data-bs-target="#objects" type="button" role="tab">Objects</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="instances-tab" data-bs-toggle="tab" data-bs-target="#instances" type="button" role="tab">Instances</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="classifications-tab" data-bs-toggle="tab" data-bs-target="#classifications" type="button" role="tab">Classifications</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="paths-tab" data-bs-toggle="tab" data-bs-target="#paths" type="button" role="tab">Paths</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="tags-tab" data-bs-toggle="tab" data-bs-target="#tags" type="button" role="tab">Tags</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="services-tab" data-bs-toggle="tab" data-bs-target="#services" type="button" role="tab">Services</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="permissions-tab" data-bs-toggle="tab" data-bs-target="#permissions" type="button" role="tab">Permissions</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="messages-tab" data-bs-toggle="tab" data-bs-target="#messages" type="button" role="tab">Messages</button>
                </li>
            </ul>
            <div class="tab-content" id="reportTabsContent">
                <div class="tab-pane fade show active" id="overview" role="tabpanel"></div>
                <div class="tab-pane fade" id="objects" role="tabpanel"></div>
                <div class="tab-pane fade" id="instances" role="tabpanel"></div>
                <div class="tab-pane fade" id="classifications" role="tabpanel"></div>
                <div class="tab-pane fade" id="paths" role="tabpanel"></div>
                <div class="tab-pane fade" id="tags" role="tabpanel"></div>
                <div class="tab-pane fade" id="services" role="tabpanel"></div>
                <div class="tab-pane fade" id="permissions" role="tabpanel"></div>
                <div class="tab-pane fade" id="messages" role="tabpanel"></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const dbConnectForm = document.getElementById('db-connect-form');
            const dbInfo = document.getElementById('db-info');
            const reportTabs = document.getElementById('report-tabs');
            const loading = document.getElementById('loading');
            
            // Tab content elements
            const tabsContent = {
                overview: document.getElementById('overview'),
                objects: document.getElementById('objects'),
                instances: document.getElementById('instances'),
                classifications: document.getElementById('classifications'),
                paths: document.getElementById('paths'),
                tags: document.getElementById('tags'),
                services: document.getElementById('services'),
                permissions: document.getElementById('permissions'),
                messages: document.getElementById('messages')
            };
            
            // Tab buttons
            const tabButtons = {
                overview: document.getElementById('overview-tab'),
                objects: document.getElementById('objects-tab'),
                instances: document.getElementById('instances-tab'),
                classifications: document.getElementById('classifications-tab'),
                paths: document.getElementById('paths-tab'),
                tags: document.getElementById('tags-tab'),
                services: document.getElementById('services-tab'),
                permissions: document.getElementById('permissions-tab'),
                messages: document.getElementById('messages-tab')
            };
            
            let connectedTables = [];
            
            // Connect to database
            dbConnectForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('db-file');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                loading.style.display = 'block';
                
                fetch('/connect', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                        loading.style.display = 'none';
                        return;
                    }
                    
                    // Update UI
                    connectedTables = data.tables;
                    dbInfo.innerHTML = `
                        <p>Connected to: <strong>${file.name}</strong></p>
                        <p>Available tables:</p>
                        <ul>
                            ${connectedTables.map(table => `<li>${table}</li>`).join('')}
                        </ul>
                    `;
                    
                    // Show tabs
                    reportTabs.style.display = 'block';
                    
                    // Load overview report
                    loadReport('overview');
                })
                .catch(error => {
                    alert('Error: ' + error);
                    loading.style.display = 'none';
                });
            });
            
            // Tab click handlers
            tabButtons.overview.addEventListener('click', () => loadReport('overview'));
            tabButtons.objects.addEventListener('click', () => loadReport('objects'));
            tabButtons.instances.addEventListener('click', () => loadReport('instances'));
            tabButtons.classifications.addEventListener('click', () => loadReport('classifications'));
            tabButtons.paths.addEventListener('click', () => loadReport('parentPaths'));
            tabButtons.tags.addEventListener('click', () => loadReport('tags'));
            tabButtons.services.addEventListener('click', () => loadReport('services'));
            tabButtons.permissions.addEventListener('click', () => loadReport('permissions'));
            tabButtons.messages.addEventListener('click', () => loadReport('messages'));
            
            // Load report data
            function loadReport(reportType) {
                loading.style.display = 'block';
                
                // Check if table exists
                if (reportType !== 'overview') {
                    let tableMap = {
                        'objects': 'objects',
                        'instances': 'instances',
                        'classifications': 'classifications',
                        'parentPaths': 'parentPaths',
                        'tags': 'tagSets',
                        'services': 'services',
                        'permissions': 'osPermissions',
                        'messages': 'messages'
                    };
                    
                    if (!connectedTables.includes(tableMap[reportType])) {
                        const element = tabsContent[reportType === 'parentPaths' ? 'paths' : reportType];
                        element.innerHTML = `
                            <div class="alert alert-warning">
                                The table ${tableMap[reportType]} does not exist in this database.
                            </div>
                        `;
                        loading.style.display = 'none';
                        return;
                    }
                }
                
                fetch(`/report/${reportType}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            alert('Error: ' + data.error);
                            loading.style.display = 'none';
                            return;
                        }
                        
                        // Render the report
                        const reportData = data.report;
                        
                        switch (reportType) {
                            case 'overview':
                                renderOverviewReport(reportData);
                                break;
                            case 'objects':
                                renderObjectsReport(reportData);
                                break;
                            case 'instances':
                                renderInstancesReport(reportData);
                                break;
                            case 'classifications':
                                renderClassificationsReport(reportData);
                                break;
                            case 'parentPaths':
                                renderPathsReport(reportData);
                                break;
                            case 'tags':
                                renderTagsReport(reportData);
                                break;
                            case 'services':
                                renderServicesReport(reportData);
                                break;
                            case 'permissions':
                                renderPermissionsReport(reportData);
                                break;
                            case 'messages':
                                renderMessagesReport(reportData);
                                break;
                        }
                        
                        loading.style.display = 'none';
                    })
                    .catch(error => {
                        alert('Error: ' + error);
                        loading.style.display = 'none';
                    });
            }
            
            // Render report functions
            function renderOverviewReport(data) {
                const element = tabsContent.overview;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Database Summary</h3>
                                <p><strong>Total Objects:</strong> ${data.total_objects.toLocaleString()}</p>
                                <p><strong>Total Instances:</strong> ${data.total_instances.toLocaleString()}</p>
                                <p><strong>Total Storage:</strong> ${data.total_storage}</p>
                                <p><strong>Date Range:</strong> ${data.date_range}</p>
                            </div>
                            
                            <div class="stats-box">
                                <h3>Table Row Counts</h3>
                                <ul>
                                    ${Object.entries(data.table_counts).map(([table, count]) => 
                                        `<li><strong>${table}:</strong> ${count.toLocaleString()}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.relationship_stats ? `
                                <div class="stats-box">
                                    <h3>Relationship Summary</h3>
                                    <p><strong>Unique Objects:</strong> ${data.relationship_stats.unique_objects.toLocaleString()}</p>
                                    <p><strong>Unique Instances:</strong> ${data.relationship_stats.unique_instances.toLocaleString()}</p>
                                    <p><strong>Unique Parents:</strong> ${data.relationship_stats.unique_parents.toLocaleString()}</p>
                                    <p><strong>Unique Services:</strong> ${data.relationship_stats.unique_services.toLocaleString()}</p>
                                    <p><strong>Unique Classifications:</strong> ${data.relationship_stats.unique_classifications.toLocaleString()}</p>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Database Table Sizes</h3>
                        <img src="data:image/png;base64,${data.table_counts_img}" class="img-fluid" alt="Table Counts">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderObjectsReport(data) {
                const element = tabsContent.objects;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Object Summary</h3>
                                <p><strong>Total Objects:</strong> ${data.total_objects.toLocaleString()}</p>
                                <p><strong>Unique File Extensions:</strong> ${data.unique_extensions.toLocaleString()}</p>
                                
                                <h4>Top File Extensions:</h4>
                                <ul>
                                    ${data.top_extensions.map(ext => 
                                        `<li><strong>${ext.ext}:</strong> ${ext.count.toLocaleString()} files</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.tag_distribution && data.tag_distribution.length > 0 ? `
                                <div class="stats-box">
                                    <h3>Tag Distribution</h3>
                                    <ul>
                                        ${data.tag_distribution.map(tag => 
                                            `<li><strong>${tag.tag_key || 'Unknown'}:</strong> ${tag.count.toLocaleString()}</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>File Extension Distribution</h3>
                        <img src="data:image/png;base64,${data.extension_dist_img}" class="img-fluid" alt="File Extensions">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Object Creation Timeline</h3>
                        <img src="data:image/png;base64,${data.creation_timeline_img}" class="img-fluid" alt="Creation Timeline">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderInstancesReport(data) {
                const element = tabsContent.instances;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Size Statistics</h3>
                                <p><strong>Min Size:</strong> ${data.size_stats.min_size}</p>
                                <p><strong>Max Size:</strong> ${data.size_stats.max_size}</p>
                                <p><strong>Average Size:</strong> ${data.size_stats.avg_size}</p>
                                <p><strong>Median Size:</strong> ${data.size_stats.median_size}</p>
                                <p><strong>Total Storage:</strong> ${data.size_stats.total_storage}</p>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.service_distribution && data.service_distribution.length > 0 ? `
                                <div class="stats-box">
                                    <h3>Service Distribution</h3>
                                    <ul>
                                        ${data.service_distribution.map(service => 
                                            `<li><strong>${service.service_name || 'Unknown'}:</strong> ${service.instance_count.toLocaleString()} instances</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>File Size Distribution</h3>
                        <img src="data:image/png;base64,${data.size_dist_img}" class="img-fluid" alt="Size Distribution">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Instance Creation and Size Over Time</h3>
                        <img src="data:image/png;base64,${data.creation_size_img}" class="img-fluid" alt="Creation and Size">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderClassificationsReport(data) {
                const element = tabsContent.classifications;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Classification Summary</h3>
                                <p><strong>Total Classifications:</strong> ${data.total_classifications.toLocaleString()}</p>
                                <p><strong>Unique Classification Sets:</strong> ${data.unique_sets.toLocaleString()}</p>
                                
                                <h4>Top Classification Sets:</h4>
                                <ul>
                                    ${data.top_sets.map(set => 
                                        `<li><strong>${set.classificationSet}:</strong> ${set.count.toLocaleString()} entries</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.classified_objects && data.classified_objects.length > 0 ? `
                                <div class="stats-box">
                                    <h3>Objects with Classifications</h3>
                                    <ul>
                                        ${data.classified_objects.map(obj => 
                                            `<li><strong>${obj.classificationSet}:</strong> ${obj.object_count.toLocaleString()} objects</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Classification Sets Distribution</h3>
                        <img src="data:image/png;base64,${data.classification_sets_img}" class="img-fluid" alt="Classification Sets">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderPathsReport(data) {
                const element = tabsContent.paths;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Path Summary</h3>
                                <p><strong>Total Parent Paths:</strong> ${data.total_paths.toLocaleString()}</p>
                                <p><strong>Unique Parent IDs:</strong> ${data.unique_parents.toLocaleString()}</p>
                                
                                <h4>Top-level Path Categories:</h4>
                                <ul>
                                    ${data.top_paths.map(path => 
                                        `<li><strong>${path.top_level}:</strong> ${path.count.toLocaleString()} entries</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Path Depth Distribution</h3>
                        <img src="data:image/png;base64,${data.path_depth_img}" class="img-fluid" alt="Path Depth">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderTagsReport(data) {
                const element = tabsContent.tags;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Tag Sets Summary</h3>
                                <p><strong>Total Tag Sets:</strong> ${data.total_tag_sets.toLocaleString()}</p>
                                
                                <h4>Tag Sets:</h4>
                                <ul>
                                    ${data.tag_sets.map(set => 
                                        `<li><strong>${set.tagSet}:</strong> ${set.used_count.toLocaleString()} usages</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Tag Sets Usage</h3>
                        <img src="data:image/png;base64,${data.tag_sets_img}" class="img-fluid" alt="Tag Sets">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderServicesReport(data) {
                const element = tabsContent.services;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-12">
                            <div class="stats-box">
                                <h3>Services Summary</h3>
                                <p><strong>Total Services:</strong> ${data.total_services.toLocaleString()}</p>
                                
                                <h4>Service Details:</h4>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Name</th>
                                            <th>Key</th>
                                            <th>Type</th>
                                            <th>Mode</th>
                                            <th>Access Delay</th>
                                            <th>Access Rate</th>
                                            <th>Access Cost</th>
                                            <th>Store Cost</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.services.map(service => `
                                            <tr>
                                                <td>${service.serviceId}</td>
                                                <td>${service.name}</td>
                                                <td>${service.key}</td>
                                                <td>${service.type}</td>
                                                <td>${service.mode}</td>
                                                <td>${service.accessDelay}</td>
                                                <td>${service.accessRate}</td>
                                                <td>${service.accessCost}</td>
                                                <td>${service.storeCost}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Service Types Distribution</h3>
                        <img src="data:image/png;base64,${data.service_types_img}" class="img-fluid" alt="Service Types">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Service Usage</h3>
                        <img src="data:image/png;base64,${data.service_usage_img}" class="img-fluid" alt="Service Usage">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderPermissionsReport(data) {
                const element = tabsContent.permissions;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Permissions Summary</h3>
                                <p><strong>Total Permissions:</strong> ${data.total_permissions.toLocaleString()}</p>
                                <p><strong>Unique Permission Sets:</strong> ${data.unique_permission_sets.toLocaleString()}</p>
                                
                                <h4>Permission Sets:</h4>
                                <ul>
                                    ${data.permission_sets.map(set => 
                                        `<li><strong>${set.permissionSet}:</strong> ${set.count.toLocaleString()} entries</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Security Summary</h3>
                                <p><strong>Total Security Entries:</strong> ${data.total_security_entries.toLocaleString()}</p>
                                
                                <h4>Security Authorities:</h4>
                                <ul>
                                    ${data.security_authorities.map(auth => 
                                        `<li><strong>${auth.authority}:</strong> ${auth.count.toLocaleString()} entries (${auth.group_count} groups, ${auth.local_count} local)</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Permission Sets Distribution</h3>
                        <img src="data:image/png;base64,${data.permission_sets_img}" class="img-fluid" alt="Permission Sets">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Security Authorities</h3>
                        <img src="data:image/png;base64,${data.security_auth_img}" class="img-fluid" alt="Security Authorities">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderMessagesReport(data) {
                const element = tabsContent.messages;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-12">
                            <div class="stats-box">
                                <h3>Messages Summary</h3>
                                <p><strong>Total Messages:</strong> ${data.total_messages.toLocaleString()}</p>
                                
                                <h4>Sample Messages:</h4>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>GUID</th>
                                            <th>Time</th>
                                            <th>Preview</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.sample_messages.map(msg => `
                                            <tr>
                                                <td>${msg.messageId}</td>
                                                <td>${msg.messageGuid}</td>
                                                <td>${msg.time}</td>
                                                <td>${msg.message_preview}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Messages Over Time</h3>
                        <img src="data:image/png;base64,${data.messages_time_img}" class="img-fluid" alt="Messages Over Time">
                    </div>
                `;
                
                element.innerHTML = html;
            }
        });
    </script>
</body>
</html>
        '''
    }
    
    return jsonify(templates)

# Make the templates available
@app.route('/create_templates')
def create_templates():
    """Create template files."""
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckDB Analyzer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .report-container {
            margin-top: 20px;
        }
        .chart-container {
            margin-bottom: 20px;
        }
        .nav-tabs {
            margin-bottom: 20px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .stats-box {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="my-4">DuckDB Document Management Analyzer</h1>
        
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Database Connection
                    </div>
                    <div class="card-body">
                        <form id="db-connect-form">
                            <div class="mb-3">
                                <label for="db-file" class="form-label">Select DuckDB File</label>
                                <input class="form-control" type="file" id="db-file" accept=".duckdb,.db">
                            </div>
                            <button type="submit" class="btn btn-primary">Connect</button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Database Info
                    </div>
                    <div class="card-body" id="db-info">
                        <p>Not connected to a database.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Loading report data...</p>
        </div>
        
        <div id="report-tabs" style="display: none;">
            <ul class="nav nav-tabs" id="reportTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button" role="tab">Overview</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="objects-tab" data-bs-toggle="tab" data-bs-target="#objects" type="button" role="tab">Objects</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="instances-tab" data-bs-toggle="tab" data-bs-target="#instances" type="button" role="tab">Instances</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="classifications-tab" data-bs-toggle="tab" data-bs-target="#classifications" type="button" role="tab">Classifications</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="paths-tab" data-bs-toggle="tab" data-bs-target="#paths" type="button" role="tab">Paths</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="tags-tab" data-bs-toggle="tab" data-bs-target="#tags" type="button" role="tab">Tags</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="services-tab" data-bs-toggle="tab" data-bs-target="#services" type="button" role="tab">Services</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="permissions-tab" data-bs-toggle="tab" data-bs-target="#permissions" type="button" role="tab">Permissions</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="messages-tab" data-bs-toggle="tab" data-bs-target="#messages" type="button" role="tab">Messages</button>
                </li>
            </ul>
            <div class="tab-content" id="reportTabsContent">
                <div class="tab-pane fade show active" id="overview" role="tabpanel"></div>
                <div class="tab-pane fade" id="objects" role="tabpanel"></div>
                <div class="tab-pane fade" id="instances" role="tabpanel"></div>
                <div class="tab-pane fade" id="classifications" role="tabpanel"></div>
                <div class="tab-pane fade" id="paths" role="tabpanel"></div>
                <div class="tab-pane fade" id="tags" role="tabpanel"></div>
                <div class="tab-pane fade" id="services" role="tabpanel"></div>
                <div class="tab-pane fade" id="permissions" role="tabpanel"></div>
                <div class="tab-pane fade" id="messages" role="tabpanel"></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const dbConnectForm = document.getElementById('db-connect-form');
            const dbInfo = document.getElementById('db-info');
            const reportTabs = document.getElementById('report-tabs');
            const loading = document.getElementById('loading');
            
            // Tab content elements
            const tabsContent = {
                overview: document.getElementById('overview'),
                objects: document.getElementById('objects'),
                instances: document.getElementById('instances'),
                classifications: document.getElementById('classifications'),
                paths: document.getElementById('paths'),
                tags: document.getElementById('tags'),
                services: document.getElementById('services'),
                permissions: document.getElementById('permissions'),
                messages: document.getElementById('messages')
            };
            
            // Tab buttons
            const tabButtons = {
                overview: document.getElementById('overview-tab'),
                objects: document.getElementById('objects-tab'),
                instances: document.getElementById('instances-tab'),
                classifications: document.getElementById('classifications-tab'),
                paths: document.getElementById('paths-tab'),
                tags: document.getElementById('tags-tab'),
                services: document.getElementById('services-tab'),
                permissions: document.getElementById('permissions-tab'),
                messages: document.getElementById('messages-tab')
            };
            
            let connectedTables = [];
            
            // Connect to database
            dbConnectForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('db-file');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                loading.style.display = 'block';
                
                fetch('/connect', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                        loading.style.display = 'none';
                        return;
                    }
                    
                    // Update UI
                    connectedTables = data.tables;
                    dbInfo.innerHTML = `
                        <p>Connected to: <strong>${file.name}</strong></p>
                        <p>Available tables:</p>
                        <ul>
                            ${connectedTables.map(table => `<li>${table}</li>`).join('')}
                        </ul>
                    `;
                    
                    // Show tabs
                    reportTabs.style.display = 'block';
                    
                    // Load overview report
                    loadReport('overview');
                })
                .catch(error => {
                    alert('Error: ' + error);
                    loading.style.display = 'none';
                });
            });
            
            // Tab click handlers
            tabButtons.overview.addEventListener('click', () => loadReport('overview'));
            tabButtons.objects.addEventListener('click', () => loadReport('objects'));
            tabButtons.instances.addEventListener('click', () => loadReport('instances'));
            tabButtons.classifications.addEventListener('click', () => loadReport('classifications'));
            tabButtons.paths.addEventListener('click', () => loadReport('parentPaths'));
            tabButtons.tags.addEventListener('click', () => loadReport('tags'));
            tabButtons.services.addEventListener('click', () => loadReport('services'));
            tabButtons.permissions.addEventListener('click', () => loadReport('permissions'));
            tabButtons.messages.addEventListener('click', () => loadReport('messages'));
            
            // Load report data
            function loadReport(reportType) {
                loading.style.display = 'block';
                
                // Check if table exists
                if (reportType !== 'overview') {
                    let tableMap = {
                        'objects': 'objects',
                        'instances': 'instances',
                        'classifications': 'classifications',
                        'parentPaths': 'parentPaths',
                        'tags': 'tagSets',
                        'services': 'services',
                        'permissions': 'osPermissions',
                        'messages': 'messages'
                    };
                    
                    if (!connectedTables.includes(tableMap[reportType])) {
                        const element = tabsContent[reportType === 'parentPaths' ? 'paths' : reportType];
                        element.innerHTML = `
                            <div class="alert alert-warning">
                                The table ${tableMap[reportType]} does not exist in this database.
                            </div>
                        `;
                        loading.style.display = 'none';
                        return;
                    }
                }
                
                fetch(`/report/${reportType}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            alert('Error: ' + data.error);
                            loading.style.display = 'none';
                            return;
                        }
                        
                        // Render the report
                        const reportData = data.report;
                        
                        switch (reportType) {
                            case 'overview':
                                renderOverviewReport(reportData);
                                break;
                            case 'objects':
                                renderObjectsReport(reportData);
                                break;
                            case 'instances':
                                renderInstancesReport(reportData);
                                break;
                            case 'classifications':
                                renderClassificationsReport(reportData);
                                break;
                            case 'parentPaths':
                                renderPathsReport(reportData);
                                break;
                            case 'tags':
                                renderTagsReport(reportData);
                                break;
                            case 'services':
                                renderServicesReport(reportData);
                                break;
                            case 'permissions':
                                renderPermissionsReport(reportData);
                                break;
                            case 'messages':
                                renderMessagesReport(reportData);
                                break;
                        }
                        
                        loading.style.display = 'none';
                    })
                    .catch(error => {
                        alert('Error: ' + error);
                        loading.style.display = 'none';
                    });
            }
            
            // Render report functions
            function renderOverviewReport(data) {
                const element = tabsContent.overview;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Database Summary</h3>
                                <p><strong>Total Objects:</strong> ${data.total_objects.toLocaleString()}</p>
                                <p><strong>Total Instances:</strong> ${data.total_instances.toLocaleString()}</p>
                                <p><strong>Total Storage:</strong> ${data.total_storage}</p>
                                <p><strong>Date Range:</strong> ${data.date_range}</p>
                            </div>
                            
                            <div class="stats-box">
                                <h3>Table Row Counts</h3>
                                <ul>
                                    ${Object.entries(data.table_counts).map(([table, count]) => 
                                        `<li><strong>${table}:</strong> ${count.toLocaleString()}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.relationship_stats ? `
                                <div class="stats-box">
                                    <h3>Relationship Summary</h3>
                                    <p><strong>Unique Objects:</strong> ${data.relationship_stats.unique_objects.toLocaleString()}</p>
                                    <p><strong>Unique Instances:</strong> ${data.relationship_stats.unique_instances.toLocaleString()}</p>
                                    <p><strong>Unique Parents:</strong> ${data.relationship_stats.unique_parents.toLocaleString()}</p>
                                    <p><strong>Unique Services:</strong> ${data.relationship_stats.unique_services.toLocaleString()}</p>
                                    <p><strong>Unique Classifications:</strong> ${data.relationship_stats.unique_classifications.toLocaleString()}</p>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Database Table Sizes</h3>
                        <img src="data:image/png;base64,${data.table_counts_img}" class="img-fluid" alt="Table Counts">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderObjectsReport(data) {
                const element = tabsContent.objects;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Object Summary</h3>
                                <p><strong>Total Objects:</strong> ${data.total_objects.toLocaleString()}</p>
                                <p><strong>Unique File Extensions:</strong> ${data.unique_extensions.toLocaleString()}</p>
                                
                                <h4>Top File Extensions:</h4>
                                <ul>
                                    ${data.top_extensions.map(ext => 
                                        `<li><strong>${ext.ext}:</strong> ${ext.count.toLocaleString()} files</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.tag_distribution && data.tag_distribution.length > 0 ? `
                                <div class="stats-box">
                                    <h3>Tag Distribution</h3>
                                    <ul>
                                        ${data.tag_distribution.map(tag => 
                                            `<li><strong>${tag.tag_key || 'Unknown'}:</strong> ${tag.count.toLocaleString()}</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>File Extension Distribution</h3>
                        <img src="data:image/png;base64,${data.extension_dist_img}" class="img-fluid" alt="File Extensions">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Object Creation Timeline</h3>
                        <img src="data:image/png;base64,${data.creation_timeline_img}" class="img-fluid" alt="Creation Timeline">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderInstancesReport(data) {
                const element = tabsContent.instances;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Size Statistics</h3>
                                <p><strong>Min Size:</strong> ${data.size_stats.min_size}</p>
                                <p><strong>Max Size:</strong> ${data.size_stats.max_size}</p>
                                <p><strong>Average Size:</strong> ${data.size_stats.avg_size}</p>
                                <p><strong>Median Size:</strong> ${data.size_stats.median_size}</p>
                                <p><strong>Total Storage:</strong> ${data.size_stats.total_storage}</p>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.service_distribution && data.service_distribution.length > 0 ? `
                                <div class="stats-box">
                                    <h3>Service Distribution</h3>
                                    <ul>
                                        ${data.service_distribution.map(service => 
                                            `<li><strong>${service.service_name || 'Unknown'}:</strong> ${service.instance_count.toLocaleString()} instances</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>File Size Distribution</h3>
                        <img src="data:image/png;base64,${data.size_dist_img}" class="img-fluid" alt="Size Distribution">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Instance Creation and Size Over Time</h3>
                        <img src="data:image/png;base64,${data.creation_size_img}" class="img-fluid" alt="Creation and Size">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderClassificationsReport(data) {
                const element = tabsContent.classifications;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Classification Summary</h3>
                                <p><strong>Total Classifications:</strong> ${data.total_classifications.toLocaleString()}</p>
                                <p><strong>Unique Classification Sets:</strong> ${data.unique_sets.toLocaleString()}</p>
                                
                                <h4>Top Classification Sets:</h4>
                                <ul>
                                    ${data.top_sets.map(set => 
                                        `<li><strong>${set.classificationSet}:</strong> ${set.count.toLocaleString()} entries</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            ${data.classified_objects && data.classified_objects.length > 0 ? `
                                <div class="stats-box">
                                    <h3>Objects with Classifications</h3>
                                    <ul>
                                        ${data.classified_objects.map(obj => 
                                            `<li><strong>${obj.classificationSet}:</strong> ${obj.object_count.toLocaleString()} objects</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Classification Sets Distribution</h3>
                        <img src="data:image/png;base64,${data.classification_sets_img}" class="img-fluid" alt="Classification Sets">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderPathsReport(data) {
                const element = tabsContent.paths;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Path Summary</h3>
                                <p><strong>Total Parent Paths:</strong> ${data.total_paths.toLocaleString()}</p>
                                <p><strong>Unique Parent IDs:</strong> ${data.unique_parents.toLocaleString()}</p>
                                
                                <h4>Top-level Path Categories:</h4>
                                <ul>
                                    ${data.top_paths.map(path => 
                                        `<li><strong>${path.top_level}:</strong> ${path.count.toLocaleString()} entries</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Path Depth Distribution</h3>
                        <img src="data:image/png;base64,${data.path_depth_img}" class="img-fluid" alt="Path Depth">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderTagsReport(data) {
                const element = tabsContent.tags;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Tag Sets Summary</h3>
                                <p><strong>Total Tag Sets:</strong> ${data.total_tag_sets.toLocaleString()}</p>
                                
                                <h4>Tag Sets:</h4>
                                <ul>
                                    ${data.tag_sets.map(set => 
                                        `<li><strong>${set.tagSet}:</strong> ${set.used_count.toLocaleString()} usages</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Tag Sets Usage</h3>
                        <img src="data:image/png;base64,${data.tag_sets_img}" class="img-fluid" alt="Tag Sets">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderServicesReport(data) {
                const element = tabsContent.services;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-12">
                            <div class="stats-box">
                                <h3>Services Summary</h3>
                                <p><strong>Total Services:</strong> ${data.total_services.toLocaleString()}</p>
                                
                                <h4>Service Details:</h4>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Name</th>
                                            <th>Key</th>
                                            <th>Type</th>
                                            <th>Mode</th>
                                            <th>Access Delay</th>
                                            <th>Access Rate</th>
                                            <th>Access Cost</th>
                                            <th>Store Cost</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.services.map(service => `
                                            <tr>
                                                <td>${service.serviceId}</td>
                                                <td>${service.name}</td>
                                                <td>${service.key}</td>
                                                <td>${service.type}</td>
                                                <td>${service.mode}</td>
                                                <td>${service.accessDelay}</td>
                                                <td>${service.accessRate}</td>
                                                <td>${service.accessCost}</td>
                                                <td>${service.storeCost}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Service Types Distribution</h3>
                        <img src="data:image/png;base64,${data.service_types_img}" class="img-fluid" alt="Service Types">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Service Usage</h3>
                        <img src="data:image/png;base64,${data.service_usage_img}" class="img-fluid" alt="Service Usage">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderPermissionsReport(data) {
                const element = tabsContent.permissions;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Permissions Summary</h3>
                                <p><strong>Total Permissions:</strong> ${data.total_permissions.toLocaleString()}</p>
                                <p><strong>Unique Permission Sets:</strong> ${data.unique_permission_sets.toLocaleString()}</p>
                                
                                <h4>Permission Sets:</h4>
                                <ul>
                                    ${data.permission_sets.map(set => 
                                        `<li><strong>${set.permissionSet}:</strong> ${set.count.toLocaleString()} entries</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="stats-box">
                                <h3>Security Summary</h3>
                                <p><strong>Total Security Entries:</strong> ${data.total_security_entries.toLocaleString()}</p>
                                
                                <h4>Security Authorities:</h4>
                                <ul>
                                    ${data.security_authorities.map(auth => 
                                        `<li><strong>${auth.authority}:</strong> ${auth.count.toLocaleString()} entries (${auth.group_count} groups, ${auth.local_count} local)</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Permission Sets Distribution</h3>
                        <img src="data:image/png;base64,${data.permission_sets_img}" class="img-fluid" alt="Permission Sets">
                    </div>
                    
                    <div class="chart-container">
                        <h3>Security Authorities</h3>
                        <img src="data:image/png;base64,${data.security_auth_img}" class="img-fluid" alt="Security Authorities">
                    </div>
                `;
                
                element.innerHTML = html;
            }
            
            function renderMessagesReport(data) {
                const element = tabsContent.messages;
                
                if (data.error) {
                    element.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }
                
                let html = `
                    <div class="row">
                        <div class="col-md-12">
                            <div class="stats-box">
                                <h3>Messages Summary</h3>
                                <p><strong>Total Messages:</strong> ${data.total_messages.toLocaleString()}</p>
                                
                                <h4>Sample Messages:</h4>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>GUID</th>
                                            <th>Time</th>
                                            <th>Preview</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.sample_messages.map(msg => `
                                            <tr>
                                                <td>${msg.messageId}</td>
                                                <td>${msg.messageGuid}</td>
                                                <td>${msg.time}</td>
                                                <td>${msg.message_preview}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Messages Over Time</h3>
                        <img src="data:image/png;base64,${data.messages_time_img}" class="img-fluid" alt="Messages Over Time">
                    </div>
                `;
                
                element.innerHTML = html;
            }
        });
    </script>
</body>
</html>
        ''')
    
    return jsonify({'success': True})

# Run the application
if __name__ == '__main__':
    # Create templates
    create_templates()
    app.run(debug=True, host='0.0.0.0', port=5000)