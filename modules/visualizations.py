import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import streamlit as st
import base64
from io import BytesIO
from datetime import datetime

# Set matplotlib and seaborn styles
plt.style.use('ggplot')
sns.set_palette("Set2")

def plot_bar_chart(data, x_col, y_col, title, xlabel=None, ylabel=None, figsize=(10, 6), horizontal=False):
    """Create a bar chart.
    
    Args:
        data (DataFrame): Data to plot
        x_col (str): Column for x-axis
        y_col (str): Column for y-axis
        title (str): Chart title
        xlabel (str, optional): Label for x-axis
        ylabel (str, optional): Label for y-axis
        figsize (tuple, optional): Figure size (width, height)
        horizontal (bool, optional): If True, create a horizontal bar chart
        
    Returns:
        Figure: Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if horizontal:
        sns.barplot(x=y_col, y=x_col, data=data, ax=ax)
    else:
        sns.barplot(x=x_col, y=y_col, data=data, ax=ax)
    
    ax.set_title(title)
    
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
        
    plt.tight_layout()
    return fig

def plot_time_series(data, x_col, y_col, title, xlabel=None, ylabel=None, figsize=(12, 6)):
    """Create a time series line chart.
    
    Args:
        data (DataFrame): Data to plot
        x_col (str): Column for x-axis (time)
        y_col (str): Column for y-axis (values)
        title (str): Chart title
        xlabel (str, optional): Label for x-axis
        ylabel (str, optional): Label for y-axis
        figsize (tuple, optional): Figure size (width, height)
        
    Returns:
        Figure: Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(data[x_col], data[y_col], marker='o', linestyle='-')
    ax.set_title(title)
    
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
        
    plt.tight_layout()
    return fig

def plot_pie_chart(data, values, names, title, figsize=(8, 8)):
    """Create a pie chart.
    
    Args:
        data (DataFrame): Data to plot
        values (str): Column for values
        names (str): Column for slice names
        title (str): Chart title
        figsize (tuple, optional): Figure size (width, height)
        
    Returns:
        Figure: Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.pie(data[values], labels=data[names], autopct='%1.1f%%', 
           startangle=90, shadow=False)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax.set_title(title)
    
    plt.tight_layout()
    return fig

def plot_histogram(data, column, bins=20, title=None, xlabel=None, ylabel='Frequency', figsize=(10, 6)):
    """Create a histogram.
    
    Args:
        data (DataFrame): Data to plot
        column (str): Column to plot
        bins (int, optional): Number of bins
        title (str, optional): Chart title
        xlabel (str, optional): Label for x-axis
        ylabel (str, optional): Label for y-axis
        figsize (tuple, optional): Figure size (width, height)
        
    Returns:
        Figure: Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.histplot(data[column], bins=bins, kde=True, ax=ax)
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    plt.tight_layout()
    return fig

def plot_heatmap(data, title=None, figsize=(12, 10), cmap="viridis"):
    """Create a correlation heatmap.
    
    Args:
        data (DataFrame): Correlation data to plot
        title (str, optional): Chart title
        figsize (tuple, optional): Figure size (width, height)
        cmap (str, optional): Colormap name
        
    Returns:
        Figure: Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(data, annot=True, cmap=cmap, linewidths=.5, ax=ax)
    
    if title:
        ax.set_title(title)
    
    plt.tight_layout()
    return fig

def create_download_link(fig, filename):
    """Create a download link for a matplotlib figure.
    
    Args:
        fig (Figure): Matplotlib figure
        filename (str): Filename for download
        
    Returns:
        str: HTML link for download
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">Download {filename}</a>'
    return href
    
def format_size_bytes(size_bytes):
    """Format bytes to human-readable file size.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted file size
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.2f} {units[unit_index]}"
