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
    page_title="Comparative Analysis - COVID-19 Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Comparative Analysis")
st.markdown("Compare COVID-19 trends and metrics across multiple countries.")

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
country_data = covid_data['by_country']
country_list = covid_data['countries']
last_updated = country_data['date'].max() if 'by_country' in covid_data else "Unknown"

# Dashboard metadata in the sidebar
st.sidebar.info(f"Data last updated: {last_updated}")

# Sidebar filters
st.sidebar.header("Comparison Filters")

# Country selection
default_countries = ['US', 'India', 'Brazil', 'United Kingdom', 'France']
default_countries = [c for c in default_countries if c in country_list]

selected_countries = st.sidebar.multiselect(
    "Select Countries for Comparison",
    options=country_list,
    default=default_countries[:5]  # Default to first 5 countries from the default list that exist in the data
)

# Ensure at least two countries are selected
if len(selected_countries) < 2:
    st.warning("Please select at least two countries for comparison.")
    st.stop()

# Date range selection
end_date = pd.to_datetime(last_updated) if isinstance(last_updated, str) else pd.Timestamp.now()
start_date = end_date - pd.Timedelta(days=90)  # Default to last 90 days

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(start_date.date(), end_date.date()),
    min_value=pd.to_datetime(country_data['date'].min()).date(),
    max_value=pd.to_datetime(country_data['date'].max()).date()
)

# Filter data based on selected date range and countries
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_data = country_data[
        (country_data['date'] >= pd.to_datetime(start_date)) & 
        (country_data['date'] <= pd.to_datetime(end_date)) &
        (country_data['country'].isin(selected_countries))
    ]
else:
    filtered_data = country_data[country_data['country'].isin(selected_countries)]

# Get the latest data for each selected country
latest_date = filtered_data['date'].max()
latest_data = filtered_data[filtered_data['date'] == latest_date]

# Comparative metrics overview
st.header("Comparative Metrics Overview")

# Create a tabular comparison
comparison_data = latest_data.set_index('country')[['total_cases', 'total_deaths', 'new_cases', 'new_deaths', 'total_recovered']].sort_values('total_cases', ascending=False)

# Format large numbers for display
formatted_comparison = comparison_data.copy()
for col in formatted_comparison.columns:
    formatted_comparison[col] = formatted_comparison[col].apply(utils.format_number)

# Rename columns for display
formatted_comparison.columns = ['Total Cases', 'Total Deaths', 'New Cases', 'New Deaths', 'Total Recovered']

# Display the table
st.table(formatted_comparison)

# Radar chart comparison
st.header("Multi-Metric Radar Comparison")

# Prepare data for radar chart
radar_metrics = ['total_cases', 'total_deaths', 'new_cases', 'new_deaths']
radar_data = latest_data.set_index('country')[radar_metrics].copy()

# Normalize data for radar chart (0-1 scale)
for metric in radar_metrics:
    max_val = radar_data[metric].max()
    if max_val > 0:  # Avoid division by zero
        radar_data[metric] = radar_data[metric] / max_val

# Create radar chart
fig = go.Figure()

for country in radar_data.index:
    fig.add_trace(go.Scatterpolar(
        r=radar_data.loc[country].values.tolist(),
        theta=[metric.replace('_', ' ').title() for metric in radar_metrics],
        fill='toself',
        name=country
    ))

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 1]
        )
    ),
    title="Multi-Metric Comparison (Normalized Scale)",
    height=600,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# Bar chart comparison
st.header("Metric Comparison")

# Metric selection for comparison
metric_options = {
    'total_cases': 'Total Cases',
    'new_cases': 'New Cases',
    'total_deaths': 'Total Deaths',
    'new_deaths': 'New Deaths',
    'total_recovered': 'Total Recovered'
}

selected_metric = st.selectbox(
    "Select Metric for Comparison",
    list(metric_options.keys()),
    format_func=lambda x: metric_options[x]
)

# Create bar chart
fig = px.bar(
    latest_data,
    x='country',
    y=selected_metric,
    title=f"{metric_options[selected_metric]} by Country",
    color='country',
    color_discrete_sequence=px.colors.qualitative.Plotly
)

fig.update_layout(
    xaxis_title="Country",
    yaxis_title=metric_options[selected_metric],
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Time series comparison
st.header("Time Series Comparison")

# Create time series chart
try:
    fig = visualizations.create_country_time_series(filtered_data, selected_countries, selected_metric)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating time series comparison: {e}")

# Case fatality rate comparison
st.header("Case Fatality Rate Comparison")

# Calculate case fatality rate
filtered_data['case_fatality_rate'] = (filtered_data['total_deaths'] / filtered_data['total_cases'] * 100).round(2)

# Create CFR time series chart
fig = px.line(
    filtered_data,
    x='date',
    y='case_fatality_rate',
    color='country',
    title='Case Fatality Rate Over Time (%)',
    line_shape='spline'
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Case Fatality Rate (%)",
    legend_title="Country",
    hovermode="x unified",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Current CFR comparison
latest_cfr = latest_data.set_index('country')['case_fatality_rate'].sort_values(ascending=False)

fig = px.bar(
    latest_cfr.reset_index(),
    x='country',
    y='case_fatality_rate',
    title='Current Case Fatality Rate by Country (%)',
    color='country',
    color_discrete_sequence=px.colors.qualitative.Plotly
)

fig.update_layout(
    xaxis_title="Country",
    yaxis_title="Case Fatality Rate (%)",
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Bubble chart comparison
st.header("Multi-Metric Bubble Chart")
st.markdown("Compare total cases (x-axis), total deaths (y-axis), and total recovered (bubble size).")

try:
    bubble_fig = visualizations.create_bubble_chart(latest_data, countries=selected_countries)
    st.plotly_chart(bubble_fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating bubble chart: {e}")

# Daily new cases and deaths comparison
st.header("Daily Cases Heatmap")

try:
    heatmap_fig = visualizations.create_heatmap(filtered_data, selected_countries, 'new_cases')
    st.plotly_chart(heatmap_fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating heatmap: {e}")

# Growth rate comparison
st.header("Growth Rate Comparison")

# Calculate weekly growth rates for all metrics
growth_metrics = ['total_cases', 'total_deaths']
growth_data = filtered_data.copy()

# Calculate growth rates for each country and metric
for country in selected_countries:
    for metric in growth_metrics:
        country_data = growth_data[growth_data['country'] == country]
        growth_data.loc[growth_data['country'] == country, f'{metric}_growth'] = country_data[metric].pct_change(periods=7) * 100

# Create growth rate comparison chart
growth_tab1, growth_tab2 = st.tabs(["Cases Growth Rate", "Deaths Growth Rate"])

with growth_tab1:
    try:
        fig = px.line(
            growth_data.dropna(subset=['total_cases_growth']),
            x='date',
            y='total_cases_growth',
            color='country',
            title='Weekly Growth Rate of Total Cases (%)',
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
        st.error(f"Error generating cases growth rate chart: {e}")

with growth_tab2:
    try:
        fig = px.line(
            growth_data.dropna(subset=['total_deaths_growth']),
            x='date',
            y='total_deaths_growth',
            color='country',
            title='Weekly Growth Rate of Total Deaths (%)',
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
        st.error(f"Error generating deaths growth rate chart: {e}")

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This page allows you to compare COVID-19 metrics across multiple countries. Use the sidebar to customize your analysis.
""")
