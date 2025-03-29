import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data_loader
import visualizations
import utils

# Page configuration
st.set_page_config(
    page_title="Time Series Analysis - COVID-19 Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Time Series Analysis")
st.markdown("Advanced time series analysis of COVID-19 trends with various metrics and visualizations.")

# Load data with caching
@st.cache_data(ttl=3600*6)  # Cache for 6 hours
def load_data():
    try:
        return data_loader.load_covid_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Display loading spinner
with st.spinner("Loading the latest COVID-19 data..."):
    covid_data = load_data()

# Check if data is loaded successfully
if covid_data is None:
    st.error("Failed to load COVID-19 data. Please try again later.")
    st.stop()

# Get the data
global_data = covid_data['global']
country_data = covid_data['by_country']
country_list = covid_data['countries']
last_updated = global_data.iloc[-1]['date'] if 'global' in covid_data else "Unknown"

# Dashboard metadata in the sidebar
st.sidebar.info(f"Data last updated: {last_updated}")

# Sidebar filters
st.sidebar.header("Time Series Analysis Filters")

# Analysis type selection
analysis_type = st.sidebar.radio(
    "Analysis Type",
    ["Global Analysis", "Country Analysis", "Multi-Country Comparison"]
)

# Date range selection
end_date = pd.to_datetime(last_updated) if isinstance(last_updated, str) else pd.Timestamp.now()
start_date = end_date - pd.Timedelta(days=90)  # Default to last 90 days

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(start_date.date(), end_date.date()),
    min_value=pd.to_datetime(global_data['date'].min()).date(),
    max_value=pd.to_datetime(global_data['date'].max()).date()
)

# Filter data based on selected date range
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_global_data = global_data[
        (global_data['date'] >= pd.to_datetime(start_date)) & 
        (global_data['date'] <= pd.to_datetime(end_date))
    ]
    filtered_country_data = country_data[
        (country_data['date'] >= pd.to_datetime(start_date)) & 
        (country_data['date'] <= pd.to_datetime(end_date))
    ]
else:
    filtered_global_data = global_data
    filtered_country_data = country_data

# Metric selection
metric_options = {
    'total_cases': 'Total Cases',
    'new_cases': 'New Cases',
    'total_deaths': 'Total Deaths',
    'new_deaths': 'New Deaths',
    'total_recovered': 'Total Recovered'
}

selected_metric = st.sidebar.selectbox(
    "Select Primary Metric",
    list(metric_options.keys()),
    format_func=lambda x: metric_options[x]
)

# Global Analysis
if analysis_type == "Global Analysis":
    st.header("Global Time Series Analysis")
    
    # Calculate rolling averages
    rolling_window = st.sidebar.slider("Rolling Average Window (days)", 1, 30, 7)
    
    filtered_global_data[f'{selected_metric}_rolling'] = filtered_global_data[selected_metric].rolling(window=rolling_window).mean()
    
    # Create time series chart with rolling average
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add raw data
    fig.add_trace(
        go.Scatter(
            x=filtered_global_data['date'],
            y=filtered_global_data[selected_metric],
            name=metric_options[selected_metric],
            mode='lines',
            line=dict(color='#3498db', width=1),
            opacity=0.6
        ),
        secondary_y=False
    )
    
    # Add rolling average
    fig.add_trace(
        go.Scatter(
            x=filtered_global_data['date'],
            y=filtered_global_data[f'{selected_metric}_rolling'],
            name=f"{rolling_window}-Day Moving Average",
            mode='lines',
            line=dict(color='#e74c3c', width=3)
        ),
        secondary_y=False
    )
    
    # Add annotations for significant events if needed
    
    fig.update_layout(
        title=f"Global {metric_options[selected_metric]} Over Time with {rolling_window}-Day Moving Average",
        xaxis_title="Date",
        yaxis_title=metric_options[selected_metric],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Growth rate analysis
    st.subheader("Growth Rate Analysis")
    
    # Calculate daily and weekly growth rates
    filtered_global_data['daily_growth_rate'] = filtered_global_data[selected_metric].pct_change() * 100
    filtered_global_data['weekly_growth_rate'] = filtered_global_data[selected_metric].pct_change(periods=7) * 100
    
    # Create growth rate chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=filtered_global_data['date'],
            y=filtered_global_data['weekly_growth_rate'],
            name="Weekly Growth Rate (%)",
            mode='lines',
            line=dict(color='#2ecc71', width=3)
        )
    )
    
    fig.update_layout(
        title=f"Weekly Growth Rate of {metric_options[selected_metric]}",
        xaxis_title="Date",
        yaxis_title="Growth Rate (%)",
        hovermode="x unified",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Seasonality and trend analysis
    st.subheader("Trend Analysis")
    
    # Decompose the time series into trend and seasonality components
    try:
        # Create a decomposition chart - simplified for visualization
        # Compute a simple trend using rolling average
        trend_window = st.slider("Trend Window (days)", 7, 60, 30)
        filtered_global_data['trend'] = filtered_global_data[selected_metric].rolling(window=trend_window).mean()
        filtered_global_data['residual'] = filtered_global_data[selected_metric] - filtered_global_data['trend']
        
        # Create decomposition chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           subplot_titles=["Original Data vs Trend", "Residuals"])
        
        # Original data and trend
        fig.add_trace(
            go.Scatter(
                x=filtered_global_data['date'],
                y=filtered_global_data[selected_metric],
                name=metric_options[selected_metric],
                mode='lines',
                line=dict(color='#3498db')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=filtered_global_data['date'],
                y=filtered_global_data['trend'],
                name=f"Trend ({trend_window}-day window)",
                mode='lines',
                line=dict(color='#e74c3c', width=3)
            ),
            row=1, col=1
        )
        
        # Residuals
        fig.add_trace(
            go.Scatter(
                x=filtered_global_data['date'],
                y=filtered_global_data['residual'],
                name="Residuals",
                mode='lines',
                line=dict(color='#2ecc71')
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=800,
            title=f"Trend Decomposition of {metric_options[selected_metric]}",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error in trend analysis: {e}")

# Country Analysis
elif analysis_type == "Country Analysis":
    # Country selection
    selected_country = st.sidebar.selectbox("Select Country", country_list, index=country_list.index('US') if 'US' in country_list else 0)
    
    st.header(f"Time Series Analysis for {selected_country}")
    
    # Filter data for selected country
    country_specific_data = filtered_country_data[filtered_country_data['country'] == selected_country]
    
    if len(country_specific_data) == 0:
        st.warning(f"No data available for {selected_country} in the selected date range.")
        st.stop()
    
    # Calculate rolling averages
    rolling_window = st.sidebar.slider("Rolling Average Window (days)", 1, 30, 7)
    
    country_specific_data[f'{selected_metric}_rolling'] = country_specific_data[selected_metric].rolling(window=rolling_window).mean()
    
    # Create time series chart with rolling average
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add raw data
    fig.add_trace(
        go.Scatter(
            x=country_specific_data['date'],
            y=country_specific_data[selected_metric],
            name=metric_options[selected_metric],
            mode='lines',
            line=dict(color='#3498db', width=1),
            opacity=0.6
        ),
        secondary_y=False
    )
    
    # Add rolling average
    fig.add_trace(
        go.Scatter(
            x=country_specific_data['date'],
            y=country_specific_data[f'{selected_metric}_rolling'],
            name=f"{rolling_window}-Day Moving Average",
            mode='lines',
            line=dict(color='#e74c3c', width=3)
        ),
        secondary_y=False
    )
    
    fig.update_layout(
        title=f"{selected_country}: {metric_options[selected_metric]} Over Time with {rolling_window}-Day Moving Average",
        xaxis_title="Date",
        yaxis_title=metric_options[selected_metric],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Growth rate analysis
    st.subheader("Growth Rate Analysis")
    
    # Calculate daily and weekly growth rates
    country_specific_data['daily_growth_rate'] = country_specific_data[selected_metric].pct_change() * 100
    country_specific_data['weekly_growth_rate'] = country_specific_data[selected_metric].pct_change(periods=7) * 100
    
    # Create growth rate chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=country_specific_data['date'],
            y=country_specific_data['weekly_growth_rate'],
            name="Weekly Growth Rate (%)",
            mode='lines',
            line=dict(color='#2ecc71', width=3)
        )
    )
    
    fig.update_layout(
        title=f"{selected_country}: Weekly Growth Rate of {metric_options[selected_metric]}",
        xaxis_title="Date",
        yaxis_title="Growth Rate (%)",
        hovermode="x unified",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional metrics for the country
    st.subheader("Key Metrics Over Time")
    
    # Multiple metrics comparison
    metrics_to_show = st.multiselect(
        "Select Metrics to Display",
        ['total_cases', 'new_cases', 'total_deaths', 'new_deaths', 'total_recovered'],
        default=['total_cases', 'total_deaths'],
        format_func=lambda x: metric_options[x] if x in metric_options else x
    )
    
    if metrics_to_show:
        fig = go.Figure()
        
        for metric in metrics_to_show:
            fig.add_trace(
                go.Scatter(
                    x=country_specific_data['date'],
                    y=country_specific_data[metric],
                    name=metric_options[metric] if metric in metric_options else metric,
                    mode='lines'
                )
            )
        
        fig.update_layout(
            title=f"{selected_country}: Multiple Metrics Comparison",
            xaxis_title="Date",
            yaxis_title="Count",
            hovermode="x unified",
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Multi-Country Comparison
else:  # Multi-Country Comparison
    # Country selection for comparison
    default_countries = ['US', 'India', 'Brazil', 'United Kingdom', 'France']
    default_countries = [c for c in default_countries if c in country_list]
    
    selected_countries = st.sidebar.multiselect(
        "Select Countries for Comparison",
        options=country_list,
        default=default_countries[:3]  # Default to first 3 countries from the default list that exist in the data
    )
    
    if not selected_countries:
        st.warning("Please select at least one country from the sidebar.")
        st.stop()
    
    st.header("Multi-Country Time Series Comparison")
    
    # Filter data for selected countries
    multi_country_data = filtered_country_data[filtered_country_data['country'].isin(selected_countries)]
    
    # Time series visualization
    st.subheader(f"Comparison of {metric_options[selected_metric]}")
    
    try:
        fig = visualizations.create_country_time_series(
            multi_country_data, 
            selected_countries, 
            metric=selected_metric
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating time series comparison: {e}")
    
    # Normalize data option
    normalize_data = st.checkbox("Normalize Data (per 100k population)", value=False)
    
    if normalize_data:
        st.info("Note: Population data is estimated and may not be up-to-date. This is for comparative visualization only.")
        
        # Dummy population data (would be replaced with real data in a production setting)
        population_data = {
            'US': 331002651,
            'India': 1380004385,
            'Brazil': 212559417,
            'Russia': 145934462,
            'France': 65273511,
            'United Kingdom': 67886011,
            'Italy': 60461826,
            'Germany': 83783942,
            'Spain': 46754778,
            'China': 1439323776,
            'Japan': 126476461,
            'South Korea': 51269185
        }
        
        # Create a normalized version of the data
        normalized_data = multi_country_data.copy()
        
        for country in selected_countries:
            if country in population_data:
                country_population = population_data.get(country, 100000000)  # Default population as fallback
                country_mask = normalized_data['country'] == country
                normalized_data.loc[country_mask, f'{selected_metric}_normalized'] = normalized_data.loc[country_mask, selected_metric] * 100000 / country_population
            else:
                st.warning(f"Population data not available for {country}. Normalization skipped.")
        
        # Create normalized chart
        try:
            fig = px.line(
                normalized_data,
                x='date',
                y=f'{selected_metric}_normalized',
                color='country',
                title=f"{metric_options[selected_metric]} per 100,000 Population",
                line_shape='spline'
            )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title=f"{metric_options[selected_metric]} per 100,000",
                legend_title="Country",
                hovermode="x unified",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating normalized comparison: {e}")
    
    # Growth rate comparison
    st.subheader("Growth Rate Comparison")
    
    # Calculate weekly growth rates for each country
    growth_data = pd.DataFrame()
    
    for country in selected_countries:
        country_data = multi_country_data[multi_country_data['country'] == country].copy()
        country_data['weekly_growth_rate'] = country_data[selected_metric].pct_change(periods=7) * 100
        growth_data = pd.concat([growth_data, country_data])
    
    # Create growth rate comparison chart
    try:
        fig = px.line(
            growth_data,
            x='date',
            y='weekly_growth_rate',
            color='country',
            title=f"Weekly Growth Rate of {metric_options[selected_metric]} by Country",
            line_shape='spline'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Weekly Growth Rate (%)",
            legend_title="Country",
            hovermode="x unified",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating growth rate comparison: {e}")
    
    # Heatmap visualization
    st.subheader("COVID-19 Heat Map")
    
    # Select metric for heatmap
    heatmap_metric = st.radio(
        "Select Metric for Heat Map",
        ['new_cases', 'new_deaths'],
        format_func=lambda x: metric_options[x] if x in metric_options else x
    )
    
    try:
        fig = visualizations.create_heatmap(
            multi_country_data, 
            selected_countries, 
            metric=heatmap_metric
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating heatmap: {e}")

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This page provides advanced time series analysis of COVID-19 data. Use the sidebar to customize your analysis.
""")
