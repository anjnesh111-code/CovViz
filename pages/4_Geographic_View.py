import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import custom modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data_loader
import visualizations
import utils

# Page Configuration
st.set_page_config(
    page_title="Geographic View - COVID-19 Dashboard",
    page_icon="🗺️",
    layout="wide"
)

# Title
st.title("🗺️ Geographic View")
st.markdown("Visualize COVID-19 data on an interactive world map.")


# Load data with caching
@st.cache_data(ttl=21600)  # Cache for 6 hours
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
if covid_data is None or not isinstance(covid_data, dict):
    st.error("Failed to load COVID-19 data. Please try again later.")
    st.stop()

# Extract data
raw_data = covid_data.get('raw', pd.DataFrame())
country_data = covid_data.get('by_country', pd.DataFrame())

# Validate data
if raw_data.empty or country_data.empty:
    st.error("No data available. Please check the source.")
    st.stop()

if 'date' not in country_data.columns:
    st.error("Error: 'date' column is missing from country_data.")
    st.stop()

# Get last updated date
last_updated = country_data['date'].max() if 'date' in country_data else "Unknown"

# Sidebar metadata
st.sidebar.info(f"Data last updated: {last_updated}")

# Sidebar filters
st.sidebar.header("Map Filters")

# Date selection
available_dates = sorted(country_data['date'].unique())

if not available_dates:
    st.error("No available dates for selection.")
    st.stop()

default_date_index = len(available_dates) - 1  # Latest date by default

selected_date = st.sidebar.date_input(
    "Select Date for Map",
    value=pd.to_datetime(available_dates[default_date_index]).date(),
    min_value=pd.to_datetime(available_dates[0]).date(),
    max_value=pd.to_datetime(available_dates[default_date_index]).date()
)

# Convert selected_date to datetime
selected_date = pd.to_datetime(selected_date)

# Metric selection
metric_options = {
    'total_cases': 'Total Cases',
    'new_cases': 'New Cases',
    'total_deaths': 'Total Deaths',
    'new_deaths': 'New Deaths',
    'total_recovered': 'Total Recovered'
}

selected_metric = st.sidebar.selectbox(
    "Select Metric to Display",
    list(metric_options.keys()),
    format_func=lambda x: metric_options[x]
)

# Filter data for selected date
date_filtered_data = country_data[country_data['date'] == selected_date]
date_filtered_raw = raw_data[raw_data['date'] == selected_date]

# World map visualization
st.header(f"Global COVID-19 Distribution: {metric_options[selected_metric]} on {selected_date.strftime('%Y-%m-%d')}")

try:
    map_fig = visualizations.create_world_map(date_filtered_data, metric=selected_metric)
    st.plotly_chart(map_fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating world map: {e}")

# Top countries table
st.subheader(f"Top 10 Countries by {metric_options[selected_metric]}")

# Sort countries by the selected metric
top_countries = date_filtered_data.sort_values(by=selected_metric, ascending=False).head(10)

# Display top countries table
if not top_countries.empty:
    display_data = top_countries[['country', selected_metric]].copy()
    display_data.columns = ['Country', metric_options[selected_metric]]

    # Format large numbers
    display_data[metric_options[selected_metric]] = display_data[metric_options[selected_metric]].apply(
        utils.format_number)

    st.table(display_data)
else:
    st.info("No country data available for the selected date.")

# Region-level visualization
st.header("Region-Level Visualization")
st.markdown("Visualize COVID-19 data at the province/state level where available.")

# Country selection for region view
country_list = sorted(raw_data['country'].dropna().unique())

if not country_list:
    st.error("No countries available in the dataset.")
    st.stop()

default_country = 'US' if 'US' in country_list else country_list[0]

selected_country_for_regions = st.selectbox(
    "Select Country for Region-Level View",
    country_list,
    index=country_list.index(default_country)
)

# Filter data for selected country and date
country_region_data = date_filtered_raw[
    (date_filtered_raw['country'] == selected_country_for_regions)
]

if not country_region_data.empty and 'province' in country_region_data.columns:
    regions_available = country_region_data['province'].str.strip().str.len() > 0
    has_regions = regions_available.any()

    if has_regions:
        region_data = country_region_data[regions_available].copy()
        region_data = region_data.sort_values(by=selected_metric, ascending=False)

        # Bar Chart for Regions
        fig = px.bar(
            region_data,
            x='province',
            y=selected_metric,
            title=f"{metric_options[selected_metric]} by Region in {selected_country_for_regions}",
            color=selected_metric,
            color_continuous_scale='Viridis',
            height=600
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info(f"No region/province-level data available for {selected_country_for_regions}.")

# Time-lapse visualization
st.header("COVID-19 Spread Over Time")
st.markdown("View how COVID-19 spread globally over time.")

# Date range selection for time-lapse
start_date = pd.to_datetime(country_data['date'].min())
end_date = pd.to_datetime(last_updated) if isinstance(last_updated, str) else pd.Timestamp.now()

time_lapse_date_range = st.date_input(
    "Select Date Range for Time-Lapse",
    value=(start_date.date(), end_date.date()),
    min_value=start_date.date(),
    max_value=end_date.date()
)

if len(time_lapse_date_range) == 2:
    start_date, end_date = map(pd.to_datetime, time_lapse_date_range)

    time_lapse_data = country_data[
        (country_data['date'] >= start_date) &
        (country_data['date'] <= end_date)
        ]

    date_diff = (end_date - start_date).days
    sample_freq = '7D' if date_diff > 30 else ('3D' if date_diff > 14 else '1D')
    date_range = pd.date_range(start=start_date, end=end_date, freq=sample_freq)

    time_lapse_data = time_lapse_data[time_lapse_data['date'].isin(date_range)]
    max_val = time_lapse_data[selected_metric].quantile(0.95)
    range_color = [0, max_val] if max_val > 0 else [0, 1]

    try:
        fig = px.choropleth(
            time_lapse_data,
            locations='country',
            locationmode='country names',
            color=selected_metric,
            animation_frame='date',
            color_continuous_scale='Viridis',
            range_color=range_color,
            title=f"{metric_options[selected_metric]} Over Time",
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating time-lapse visualization: {e}")
else:
    st.warning("Please select both start and end dates for the time-lapse visualization.")

# Footer
st.markdown("---")
st.markdown("**Data Source**: Johns Hopkins University CSSE")
