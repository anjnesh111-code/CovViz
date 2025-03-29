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
if not covid_data or 'by_country' not in covid_data or covid_data['by_country'].empty:
    st.error("Failed to load COVID-19 data. Please try again later.")
    st.stop()

# Get the data
country_data = covid_data['by_country']
country_list = covid_data['countries']

# Ensure the dataset has valid dates
if 'date' not in country_data or country_data['date'].isnull().all():
    st.error("Dataset does not contain valid dates.")
    st.stop()

# Get last updated date
last_updated = country_data['date'].max()
st.sidebar.info(f"Data last updated: {last_updated}")

# Sidebar filters
st.sidebar.header("Comparison Filters")

# Country selection
default_countries = ['US', 'India', 'Brazil', 'United Kingdom', 'France']
default_countries = [c for c in default_countries if c in country_list]

selected_countries = st.sidebar.multiselect(
    "Select Countries for Comparison",
    options=country_list,
    default=default_countries[:5]  # Default to first 5 valid countries
)

# Ensure at least two countries are selected
if len(selected_countries) < 2:
    st.warning("Please select at least two countries for comparison.")
    st.stop()

# Date range selection
end_date = last_updated
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
latest_data = filtered_data[filtered_data['date'] == filtered_data['date'].max()]

# Comparative metrics overview
st.header("Comparative Metrics Overview")

# Check if data is available
if latest_data.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# Create a tabular comparison
comparison_data = latest_data.set_index('country')[['total_cases', 'total_deaths', 'new_cases', 'new_deaths', 'total_recovered']]
comparison_data = comparison_data.sort_values('total_cases', ascending=False)

# Format large numbers for display
formatted_comparison = comparison_data.copy()
for col in formatted_comparison.columns:
    formatted_comparison[col] = formatted_comparison[col].apply(utils.format_number)

formatted_comparison.columns = ['Total Cases', 'Total Deaths', 'New Cases', 'New Deaths', 'Total Recovered']

# Display the table
st.table(formatted_comparison)

# Radar chart comparison
st.header("Multi-Metric Radar Comparison")

# Normalize data for radar chart (0-1 scale)
radar_metrics = ['total_cases', 'total_deaths', 'new_cases', 'new_deaths']
radar_data = latest_data.set_index('country')[radar_metrics].copy()

for metric in radar_metrics:
    max_val = radar_data[metric].max()
    if max_val > 0:
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
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    title="Multi-Metric Comparison (Normalized Scale)",
    height=600,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# Bar chart comparison
st.header("Metric Comparison")
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

fig = px.bar(
    latest_data, x='country', y=selected_metric,
    title=f"{metric_options[selected_metric]} by Country",
    color='country', color_discrete_sequence=px.colors.qualitative.Plotly
)

fig.update_layout(xaxis_title="Country", yaxis_title=metric_options[selected_metric], showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Time series comparison
st.header("Time Series Comparison")
try:
    fig = visualizations.create_country_time_series(filtered_data, selected_countries, selected_metric)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating time series comparison: {e}")

# Case fatality rate comparison
st.header("Case Fatality Rate Comparison")

filtered_data['case_fatality_rate'] = (filtered_data['total_deaths'] / filtered_data['total_cases'] * 100).fillna(0).round(2)

fig = px.line(
    filtered_data, x='date', y='case_fatality_rate',
    color='country', title='Case Fatality Rate Over Time (%)',
    line_shape='spline'
)

fig.update_layout(xaxis_title="Date", yaxis_title="Case Fatality Rate (%)", hovermode="x unified", height=500)
st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This page allows you to compare COVID-19 metrics across multiple countries. Use the sidebar to customize your analysis.
""")
