import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Ensure that required modules are accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import data_loader
    import visualizations
    import utils
except ModuleNotFoundError as e:
    st.error(f"Module import error: {e}")
    st.stop()

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
@st.cache_data(ttl=3600 * 6)  # Cache for 6 hours
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

# Extract data
global_data = covid_data.get('global', pd.DataFrame())
country_data = covid_data.get('by_country', pd.DataFrame())
country_list = covid_data.get('countries', [])

# Check for empty datasets
if global_data.empty or country_data.empty:
    st.error("COVID-19 dataset is empty. Please check the data source.")
    st.stop()

last_updated = global_data.iloc[-1]['date'] if not global_data.empty else "Unknown"

# Sidebar metadata
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

# Ensure the default start_date and end_date are within the dataset's range
data_min_date = pd.to_datetime(global_data['date'].min()).date()
data_max_date = pd.to_datetime(global_data['date'].max()).date()

# Adjust start_date and end_date if they exceed dataset limits
start_date = max(start_date.date(), data_min_date)
end_date = min(end_date.date(), data_max_date)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(start_date, end_date),
    min_value=data_min_date,
    max_value=data_max_date
)

# Convert date selection to datetime
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

# Filter data based on selected date range
filtered_global_data = global_data[
    (global_data['date'] >= start_date) &
    (global_data['date'] <= end_date)
    ].copy()

filtered_country_data = country_data[
    (country_data['date'] >= start_date) &
    (country_data['date'] <= end_date)
    ].copy()

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

    # Rolling averages
    rolling_window = st.sidebar.slider("Rolling Average Window (days)", 1, 30, 7)

    filtered_global_data[f'{selected_metric}_rolling'] = (
        filtered_global_data[selected_metric].rolling(window=rolling_window).mean().fillna(0)
    )

    # Time series chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_global_data['date'],
        y=filtered_global_data[selected_metric],
        name=metric_options[selected_metric],
        mode='lines',
        line=dict(color='#3498db', width=1),
        opacity=0.6
    ))
    fig.add_trace(go.Scatter(
        x=filtered_global_data['date'],
        y=filtered_global_data[f'{selected_metric}_rolling'],
        name=f"{rolling_window}-Day Moving Average",
        mode='lines',
        line=dict(color='#e74c3c', width=3)
    ))

    fig.update_layout(
        title=f"Global {metric_options[selected_metric]} Over Time",
        xaxis_title="Date",
        yaxis_title=metric_options[selected_metric],
        hovermode="x unified",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# Country Analysis
elif analysis_type == "Country Analysis":
    selected_country = st.sidebar.selectbox("Select Country", country_list, index=0)

    st.header(f"Time Series Analysis for {selected_country}")

    country_specific_data = filtered_country_data[filtered_country_data['country'] == selected_country].copy()

    if country_specific_data.empty:
        st.warning(f"No data available for {selected_country} in the selected date range.")
        st.stop()

    # Rolling averages
    country_specific_data[f'{selected_metric}_rolling'] = (
        country_specific_data[selected_metric].rolling(window=rolling_window).mean().fillna(0)
    )

    # Time series chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=country_specific_data['date'],
        y=country_specific_data[selected_metric],
        name=metric_options[selected_metric],
        mode='lines',
        line=dict(color='#3498db', width=1),
        opacity=0.6
    ))
    fig.add_trace(go.Scatter(
        x=country_specific_data['date'],
        y=country_specific_data[f'{selected_metric}_rolling'],
        name=f"{rolling_window}-Day Moving Average",
        mode='lines',
        line=dict(color='#e74c3c', width=3)
    ))

    fig.update_layout(
        title=f"{selected_country}: {metric_options[selected_metric]} Over Time",
        xaxis_title="Date",
        yaxis_title=metric_options[selected_metric],
        hovermode="x unified",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# Multi-Country Comparison
else:
    selected_countries = st.sidebar.multiselect("Select Countries", country_list, default=country_list[:3])

    if not selected_countries:
        st.warning("Please select at least one country.")
        st.stop()

    st.header("Multi-Country Time Series Comparison")

    multi_country_data = filtered_country_data[filtered_country_data['country'].isin(selected_countries)]

    try:
        fig = visualizations.create_country_time_series(multi_country_data, selected_countries, metric=selected_metric)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating comparison: {e}")

if filtered_global_data.empty:
    st.warning("No data available for the selected date range.")
    st.stop()


st.plotly_chart(fig, use_container_width=True)


st.markdown("---")
st.markdown("**Data Source**: Johns Hopkins University CSSE")
