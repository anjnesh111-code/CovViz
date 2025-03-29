import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data_loader
import visualizations
import utils

# Page configuration
st.set_page_config(
    page_title="Global Overview - COVID-19 Dashboard",
    page_icon="🌎",
    layout="wide"
)

# Title
st.title("🌎 Global Overview")
st.markdown("This page provides an overview of global COVID-19 statistics and trends.")

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

# Extract required datasets
global_data = covid_data.get('global', None)
country_data = covid_data.get('by_country', None)

if global_data is None or country_data is None:
    st.error("Missing required data. Please check your dataset.")
    st.stop()

# Get last updated date
last_updated = global_data.iloc[-1]['date'] if not global_data.empty else "Unknown"

# Sidebar metadata
st.sidebar.info(f"Data last updated: {last_updated}")

# Global metrics at the top
st.header("Global COVID-19 Metrics")

# Get latest global metrics
latest_data = global_data.iloc[-1] if not global_data.empty else None

if latest_data is not None:
    total_cases = int(latest_data.get('total_cases', 0))
    total_deaths = int(latest_data.get('total_deaths', 0))
    total_recovered = int(latest_data.get('total_recovered', 0))
    active_cases = total_cases - total_deaths - total_recovered

    # Growth rates
    week_ago_data = global_data.iloc[-8] if len(global_data) > 8 else global_data.iloc[0]
    cases_growth = ((latest_data['total_cases'] - week_ago_data['total_cases']) / week_ago_data['total_cases'] * 100) if week_ago_data['total_cases'] > 0 else 0
    deaths_growth = ((latest_data['total_deaths'] - week_ago_data['total_deaths']) / week_ago_data['total_deaths'] * 100) if week_ago_data['total_deaths'] > 0 else 0

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", utils.format_number(total_cases), f"{cases_growth:.1f}% in 7 days")
    col2.metric("Active Cases", utils.format_number(active_cases))
    col3.metric("Total Deaths", utils.format_number(total_deaths), f"{deaths_growth:.1f}% in 7 days")
    col4.metric("Total Recovered", utils.format_number(total_recovered))
else:
    st.warning("No global data available.")

# Sidebar filters for global view
st.sidebar.header("Global View Filters")

# Set valid date range
valid_start_date = pd.to_datetime(country_data['date'].min()).date()
valid_end_date = pd.to_datetime(country_data['date'].max()).date()

# Sidebar date selection
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(valid_start_date, valid_end_date),
    min_value=valid_start_date,
    max_value=valid_end_date
)

# Filter data based on selected date range
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_global_data = global_data[
        (global_data['date'] >= pd.to_datetime(start_date)) &
        (global_data['date'] <= pd.to_datetime(end_date))
    ]
else:
    filtered_global_data = global_data

# Show trends
st.header("Global COVID-19 Trends")
trend_tab1, trend_tab2 = st.tabs(["Daily Trends", "Cumulative Trends"])

with trend_tab1:
    try:
        st.plotly_chart(visualizations.create_daily_trends_chart(filtered_global_data), use_container_width=True)
    except Exception as e:
        st.error(f"Error generating daily trends chart: {e}")

with trend_tab2:
    try:
        st.plotly_chart(visualizations.create_cumulative_trends_chart(filtered_global_data), use_container_width=True)
    except Exception as e:
        st.error(f"Error generating cumulative trends chart: {e}")

# Moving averages
st.header("7-Day Moving Averages")

# Calculate moving averages
if 'new_cases' in filtered_global_data.columns and 'new_deaths' in filtered_global_data.columns:
    filtered_global_data['cases_7day_avg'] = filtered_global_data['new_cases'].rolling(window=7).mean()
    filtered_global_data['deaths_7day_avg'] = filtered_global_data['new_deaths'].rolling(window=7).mean()
else:
    st.warning("New cases and deaths data unavailable for calculating moving averages.")

# Plot moving averages
fig = px.line(
    filtered_global_data,
    x='date',
    y=['cases_7day_avg', 'deaths_7day_avg'],
    title='7-Day Moving Averages of New Cases and Deaths',
    labels={'value': 'Count', 'variable': 'Metric'},
    color_discrete_map={
        'cases_7day_avg': '#3498db',
        'deaths_7day_avg': '#e74c3c'
    }
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="7-Day Average",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    legend_title_text='',
    hovermode="x unified",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Top affected countries
st.header("Top Affected Countries")

# Metric selection
metric_options = {
    'total_cases': 'Total Cases',
    'total_deaths': 'Total Deaths',
    'new_cases': 'New Cases',
    'new_deaths': 'New Deaths'
}

selected_metric = st.selectbox("Select Metric for Top Countries", list(metric_options.keys()), format_func=lambda x: metric_options[x])

# Get latest data for country comparison
latest_date = filtered_global_data['date'].max()
latest_data = country_data[country_data['date'] == latest_date]

# Get top 10 countries
top_countries = latest_data.groupby('country')[selected_metric].sum().nlargest(10).reset_index()

# Plot top countries
fig = px.bar(
    top_countries,
    x='country',
    y=selected_metric,
    title=f'Top 10 Countries by {metric_options[selected_metric]}',
    color=selected_metric,
    color_continuous_scale='Viridis',
    text=selected_metric
)

st.plotly_chart(fig, use_container_width=True)

# Global map
st.header("Global Distribution")

map_metric = st.selectbox("Select Metric for Map", metric_options.keys(), format_func=lambda x: metric_options[x])

if not latest_data.empty:
    try:
        st.plotly_chart(visualizations.create_world_map(latest_data, metric=map_metric), use_container_width=True)
    except Exception as e:
        st.error(f"Error generating world map: {e}")
else:
    st.warning("No country-level data available for visualization.")

# Footer
st.markdown("---")
st.markdown("**Data Source**: JHU CSSE | This dashboard provides an overview of global COVID-19 trends.")

