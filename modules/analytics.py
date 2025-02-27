"""
Advanced analytics module for document data analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def time_series_analysis(data, time_column, value_column, freq='M'):
    """Perform time series analysis on document data.
    
    Args:
        data (DataFrame): Data with timestamps and values
        time_column (str): Column containing timestamps
        value_column (str): Column containing values to analyze
        freq (str): Frequency for resampling ('D'=daily, 'W'=weekly, 'M'=monthly)
        
    Returns:
        dict: Dictionary with time series analysis results
    """
    # Ensure time column is datetime
    df = data.copy()
    if not pd.api.types.is_datetime64_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    # Set time column as index
    df = df.set_index(time_column)
    
    # Resample data to specified frequency
    resampled = df[value_column].resample(freq).sum()
    
    # Calculate growth rate
    growth_rate = resampled.pct_change().dropna()
    
    # Calculate moving averages
    ma_3 = resampled.rolling(window=3).mean()
    ma_6 = resampled.rolling(window=6).mean()
    
    # Detect outliers (simple method: values > 2 std devs from mean)
    mean = resampled.mean()
    std = resampled.std()
    outliers = resampled[(resampled > mean + 2*std) | (resampled < mean - 2*std)]
    
    # Predict next period (simple forecast - average of last 3 periods)
    if len(resampled) >= 3:
        forecast = resampled[-3:].mean()
    else:
        forecast = resampled.mean() if not resampled.empty else None
    
    # Return results
    results = {
        'original': data,
        'resampled': resampled.reset_index(),
        'growth_rate': growth_rate.reset_index(),
        'moving_avg_3': ma_3.reset_index(),
        'moving_avg_6': ma_6.reset_index(),
        'outliers': outliers.reset_index() if not outliers.empty else pd.DataFrame(),
        'forecast': forecast
    }
    
    return results

def size_distribution_analysis(sizes):
    """Analyze file size distribution.
    
    Args:
        sizes (Series): Series containing file sizes in bytes
        
    Returns:
        dict: Dictionary with size analysis results
    """
    # Remove any NaN values
    clean_sizes = sizes.dropna()
    
    if clean_sizes.empty:
        return {}
    
    # Basic statistics
    stats = {
        'count': len(clean_sizes),
        'min': clean_sizes.min(),
        'max': clean_sizes.max(),
        'mean': clean_sizes.mean(),
        'median': clean_sizes.median(),
        'std': clean_sizes.std(),
        'total': clean_sizes.sum()
    }
    
    # Calculate percentiles
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        stats[f'p{p}'] = np.percentile(clean_sizes, p)
    
    # Size categories
    size_categories = {
        'tiny': (0, 1024),  # 0-1KB
        'small': (1024, 1024*1024),  # 1KB-1MB
        'medium': (1024*1024, 1024*1024*10),  # 1MB-10MB
        'large': (1024*1024*10, 1024*1024*100),  # 10MB-100MB
        'huge': (1024*1024*100, float('inf'))  # >100MB
    }
    
    category_counts = {}
    for category, (min_size, max_size) in size_categories.items():
        category_counts[category] = len(clean_sizes[(clean_sizes >= min_size) & (clean_sizes < max_size)])
    
    stats['categories'] = category_counts
    
    # Calculate size histogram data
    hist_data = np.histogram(clean_sizes, bins=20)
    stats['histogram'] = {
        'counts': hist_data[0].tolist(),
        'bins': hist_data[1].tolist()
    }
    
    return stats

def file_type_analysis(extensions):
    """Analyze file type distribution.
    
    Args:
        extensions (Series): Series containing file extensions
        
    Returns:
        dict: Dictionary with file type analysis
    """
    # Clean extensions (remove leading dots, convert to lowercase)
    clean_extensions = extensions.str.replace(r'^\.*', '', regex=True).str.lower()
    
    # Count unique extensions
    extension_counts = clean_extensions.value_counts()
    
    # Group by file type category
    file_categories = {
        'documents': ['doc', 'docx', 'pdf', 'txt', 'rtf', 'odt', 'md', 'xps'],
        'spreadsheets': ['xls', 'xlsx', 'csv', 'ods', 'tsv', 'numbers'],
        'presentations': ['ppt', 'pptx', 'odp', 'key'],
        'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'heic', 'heif'],
        'audio': ['mp3', 'wav', 'aac', 'ogg', 'flac', 'wma', 'm4a'],
        'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v'],
        'archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
        'code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'go', 'php', 'rb', 'pl', 'rs', 'ts'],
        'data': ['json', 'xml', 'yaml', 'yml', 'toml', 'sql', 'db', 'sqlite'],
        'executables': ['exe', 'app', 'msi', 'dll', 'so', 'bin', 'dmg']
    }
    
    category_counts = {}
    for category, exts in file_categories.items():
        category_counts[category] = clean_extensions[clean_extensions.isin(exts)].count()
    
    # Add 'other' category for uncategorized extensions
    categorized_extensions = [ext for category_exts in file_categories.values() for ext in category_exts]
    category_counts['other'] = clean_extensions[~clean_extensions.isin(categorized_extensions)].count()
    
    return {
        'extension_counts': extension_counts.to_dict(),
        'categories': category_counts
    }

def user_access_analysis(permissions_data):
    """Analyze user access patterns.
    
    Args:
        permissions_data (DataFrame): DataFrame with permission data
        
    Returns:
        dict: Dictionary with user access analysis
    """
    # This is a simplified analysis - would need to be customized based on actual permission structure
    
    # Count permissions by type
    permission_counts = permissions_data['permissionSet'].value_counts().to_dict()
    
    # Simple categorization - would need adjustment for actual permission format
    permission_categories = {
        'full_access': permissions_data['permissionSet'].str.contains(r'\*p[0-9]+:4\*', regex=True).sum(),
        'read_only': permissions_data['permissionSet'].str.contains(r'\*p[0-9]+:1\*', regex=True).sum(),
        'no_access': permissions_data['permissionSet'].str.contains(r'\*p[0-9]+:0\*', regex=True).sum()
    }
    
    return {
        'permission_counts': permission_counts,
        'categories': permission_categories
    }

def document_aging_analysis(creation_timestamps, current_time=None):
    """Analyze document age distribution.
    
    Args:
        creation_timestamps (Series): Series with document creation timestamps (epoch milliseconds)
        current_time (int, optional): Current time as epoch milliseconds. If None, uses current time.
        
    Returns:
        dict: Dictionary with document age analysis
    """
    if current_time is None:
        current_time = int(datetime.now().timestamp() * 1000)
    
    # Convert timestamps to datetime
    clean_timestamps = pd.to_datetime(creation_timestamps, unit='ms')
    
    # Calculate age in days
    current_datetime = pd.to_datetime(current_time, unit='ms')
    age_days = (current_datetime - clean_timestamps).dt.total_seconds() / (24 * 3600)
    
    # Define age categories
    age_categories = {
        'today': (0, 1),  # Less than 1 day
        'this_week': (1, 7),  # 1-7 days
        'this_month': (7, 30),  # 7-30 days
        'this_quarter': (30, 90),  # 30-90 days
        'this_year': (90, 365),  # 90-365 days
        'older': (365, float('inf'))  # More than a year
    }
    
    # Count documents in each age category
    category_counts = {}
    for category, (min_age, max_age) in age_categories.items():
        category_counts[category] = len(age_days[(age_days >= min_age) & (age_days < max_age)])
    
    # Calculate basic statistics
    stats = {
        'min_age_days': age_days.min(),
        'max_age_days': age_days.max(),
        'mean_age_days': age_days.mean(),
        'median_age_days': age_days.median(),
        'categories': category_counts
    }
    
    return stats
