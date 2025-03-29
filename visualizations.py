import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Create daily trends chart
def create_daily_trends_chart(data):
    """
    Create a chart showing daily new cases and deaths
    
    Args:
        data (pandas.DataFrame): Data containing date, new_cases, and new_deaths
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add traces
    fig.add_trace(
        go.Bar(
            x=data['date'],
            y=data['new_cases'],
            name="New Cases",
            marker_color='#3498db',
            opacity=0.7
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Line(
            x=data['date'],
            y=data['new_deaths'],
            name="New Deaths",
            marker_color='#e74c3c',
            line=dict(width=3)
        ),
        secondary_y=True,
    )
    
    # Set titles
    fig.update_layout(
        title_text="Daily New Cases and Deaths",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        margin=dict(l=10, r=10, t=60, b=10)
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="New Cases", secondary_y=False)
    fig.update_yaxes(title_text="New Deaths", secondary_y=True)
    
    return fig

# Create cumulative trends chart
def create_cumulative_trends_chart(data):
    """
    Create a chart showing cumulative cases, deaths, and recovered
    
    Args:
        data (pandas.DataFrame): Data containing date, total_cases, total_deaths, total_recovered
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['total_cases'],
            name="Total Cases",
            mode='lines',
            line=dict(width=3, color='#3498db'),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.1)'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['total_deaths'],
            name="Total Deaths",
            mode='lines',
            line=dict(width=3, color='#e74c3c'),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.1)'
        )
    )
    
    if 'total_recovered' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['total_recovered'],
                name="Total Recovered",
                mode='lines',
                line=dict(width=3, color='#2ecc71'),
                fill='tozeroy',
                fillcolor='rgba(46, 204, 113, 0.1)'
            )
        )
    
    # Set titles
    fig.update_layout(
        title_text="Cumulative COVID-19 Trends",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        margin=dict(l=10, r=10, t=60, b=10),
        yaxis_title="Count"
    )
    
    return fig

# Create world map visualization
def create_world_map(data, metric='total_cases', date=None):
    """
    Create a world map showing COVID-19 metrics by country
    
    Args:
        data (pandas.DataFrame): Data containing countries and metrics
        metric (str): Metric to display on the map (total_cases, total_deaths, etc.)
        date (str): Specific date to filter data
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Filter data for the specific date if provided
    if date is not None:
        data = data[data['date'] == date]
    
    # Aggregate data by country
    if 'country' in data.columns:
        map_data = data.groupby('country').agg({
            metric: 'sum',
            'latitude': 'first',
            'longitude': 'first'
        }).reset_index()
    else:
        # Return empty figure if data is not properly formatted
        return go.Figure().update_layout(title_text="No data available for map")
    
    # Create metric label for display
    metric_label = ' '.join(word.capitalize() for word in metric.split('_'))
    
    # Create choropleth map
    fig = px.choropleth(
        map_data,
        locations='country',
        locationmode='country names',
        color=metric,
        hover_name='country',
        color_continuous_scale='Viridis',
        range_color=[0, map_data[metric].quantile(0.95)],  # Cap color scale at 95th percentile
        title=f"{metric_label} by Country",
        height=600
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(
            title=metric_label
        )
    )
    
    return fig

# Create comparison bar chart
def create_country_comparison_chart(data, countries, metric='total_cases', date=None):
    """
    Create a bar chart comparing countries for a specific metric
    
    Args:
        data (pandas.DataFrame): Data containing countries and metrics
        countries (list): List of countries to include in comparison
        metric (str): Metric to compare (total_cases, total_deaths, etc.)
        date (str): Specific date to filter data
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Filter data for the specific date if provided
    if date is not None:
        data = data[data['date'] == date]
    
    # Filter for selected countries
    data = data[data['country'].isin(countries)]
    
    # Aggregate data by country
    if len(data) > 0:
        comparison_data = data.groupby('country').agg({
            metric: 'sum'
        }).reset_index()
        
        # Sort by the metric in descending order
        comparison_data = comparison_data.sort_values(metric, ascending=False)
        
        # Create metric label for display
        metric_label = ' '.join(word.capitalize() for word in metric.split('_'))
        
        # Create bar chart
        fig = px.bar(
            comparison_data,
            x='country',
            y=metric,
            title=f"{metric_label} by Country",
            color=metric,
            color_continuous_scale='Viridis',
            text=metric
        )
        
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        
        fig.update_layout(
            xaxis_title="Country",
            yaxis_title=metric_label,
            height=500,
            margin=dict(l=10, r=10, t=60, b=10)
        )
        
        return fig
    else:
        # Return empty figure if no data is available
        return go.Figure().update_layout(title_text="No data available for selected countries")

# Create time series for country comparison
def create_country_time_series(data, countries, metric='total_cases'):
    """
    Create a line chart comparing countries over time
    
    Args:
        data (pandas.DataFrame): Data containing dates, countries and metrics
        countries (list): List of countries to include in comparison
        metric (str): Metric to compare (total_cases, total_deaths, etc.)
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Filter for selected countries
    filtered_data = data[data['country'].isin(countries)]
    
    if len(filtered_data) > 0:
        # Create metric label for display
        metric_label = ' '.join(word.capitalize() for word in metric.split('_'))
        
        # Create line chart
        fig = px.line(
            filtered_data,
            x='date',
            y=metric,
            color='country',
            title=f"{metric_label} Over Time by Country",
            line_shape='spline',
            render_mode='svg'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=metric_label,
            legend_title="Country",
            hovermode="x unified",
            height=500,
            margin=dict(l=10, r=10, t=60, b=10)
        )
        
        return fig
    else:
        # Return empty figure if no data is available
        return go.Figure().update_layout(title_text="No data available for selected countries")

# Create a heatmap for daily new cases
def create_heatmap(data, countries, metric='new_cases'):
    """
    Create a heatmap of daily values for selected countries
    
    Args:
        data (pandas.DataFrame): Data containing dates, countries and metrics
        countries (list): List of countries to include in the heatmap
        metric (str): Metric to display (new_cases, new_deaths, etc.)
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Filter for selected countries
    filtered_data = data[data['country'].isin(countries)]
    
    if len(filtered_data) > 0:
        # Pivot the data to create a matrix suitable for a heatmap
        pivot_data = filtered_data.pivot_table(
            index='country',
            columns='date',
            values=metric,
            aggfunc='sum'
        )
        
        # Create metric label for display
        metric_label = ' '.join(word.capitalize() for word in metric.split('_'))
        
        # Create heatmap
        fig = px.imshow(
            pivot_data.iloc[:, -90:],  # Show last 90 days for better visibility
            labels=dict(x="Date", y="Country", color=metric_label),
            title=f"{metric_label} Heatmap by Country (Last 90 Days)",
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            height=500,
            margin=dict(l=10, r=10, t=60, b=10),
            xaxis=dict(tickangle=45)
        )
        
        return fig
    else:
        # Return empty figure if no data is available
        return go.Figure().update_layout(title_text="No data available for selected countries")

# Create a bubble chart for comparing multiple metrics
def create_bubble_chart(data, date=None, countries=None):
    """
    Create a bubble chart comparing total cases, deaths, and recovery
    
    Args:
        data (pandas.DataFrame): Data containing countries and metrics
        date (str): Specific date to filter data
        countries (list): List of countries to include
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Filter data for the specific date if provided
    if date is not None:
        data = data[data['date'] == date]
    
    # Filter for selected countries if provided
    if countries is not None:
        data = data[data['country'].isin(countries)]
    
    # Aggregate data by country
    if len(data) > 0:
        bubble_data = data.groupby('country').agg({
            'total_cases': 'sum',
            'total_deaths': 'sum',
            'total_recovered': 'sum'
        }).reset_index()
        
        # Calculate case fatality rate
        bubble_data['case_fatality_rate'] = (bubble_data['total_deaths'] / bubble_data['total_cases'] * 100).round(2)
        
        # Create bubble chart
        fig = px.scatter(
            bubble_data,
            x='total_cases',
            y='total_deaths',
            size='total_recovered',
            color='case_fatality_rate',
            hover_name='country',
            log_x=True,
            log_y=True,
            size_max=60,
            color_continuous_scale='Viridis',
            title='COVID-19 Cases vs Deaths (Bubble Size = Recovered)'
        )
        
        fig.update_layout(
            xaxis_title="Total Cases (log scale)",
            yaxis_title="Total Deaths (log scale)",
            coloraxis_colorbar_title="Fatality Rate (%)",
            height=600,
            margin=dict(l=10, r=10, t=60, b=10)
        )
        
        return fig
    else:
        # Return empty figure if no data is available
        return go.Figure().update_layout(title_text="No data available for the selected criteria")
