import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import json
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data_loader
import visualizations
import utils

# Page configuration
st.set_page_config(
    page_title="Geographic View - COVID-19 Dashboard",
    page_icon="🗺️",
    layout="wide"
)

# Title
st.title("🗺️ Geographic View")
st.markdown("Visualize COVID-19 data on an interactive world map.")

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
raw_data = covid_data['raw']
country_data = covid_data['by_country']
last_updated = country_data['date'].max() if 'by_country' in covid_data else "Unknown"

# Dashboard metadata in the sidebar
st.sidebar.info(f"Data last updated: {last_updated}")

# Sidebar filters
st.sidebar.header("Map Filters")

# Date selection
available_dates = sorted(country_data['date'].unique())
default_date_index = len(available_dates) - 1  # Latest date by default

selected_date = st.sidebar.date_input(
    "Select Date for Map",
    value=pd.to_datetime(available_dates[default_date_index]).date(),
    min_value=pd.to_datetime(available_dates[0]).date(),
    max_value=pd.to_datetime(available_dates[default_date_index]).date()
)

# Convert selected_date to datetime for filtering
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
if len(top_countries) > 0:
    # Format the data for display
    display_data = top_countries[['country', selected_metric]].copy()
    display_data.columns = ['Country', metric_options[selected_metric]]
    
    # Format large numbers
    display_data[metric_options[selected_metric]] = display_data[metric_options[selected_metric]].apply(utils.format_number)
    
    st.table(display_data)
else:
    st.info("No country data available for the selected date.")

# Region-level visualization
st.header("Region-Level Visualization")
st.markdown("Visualize COVID-19 data at the province/state level where available.")

# Country selection for region view
country_list = sorted(raw_data['country'].unique())
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

# Check if region/province data is available
regions_available = country_region_data['province'].str.strip().str.len() > 0
has_regions = regions_available.any()

if has_regions:
    # Filter out empty province names
    region_data = country_region_data[regions_available].copy()
    
    # Sort by the selected metric
    region_data = region_data.sort_values(by=selected_metric, ascending=False)
    
    # Create a bar chart for regions
    fig = px.bar(
        region_data,
        x='province',
        y=selected_metric,
        title=f"{metric_options[selected_metric]} by Region in {selected_country_for_regions}",
        color=selected_metric,
        color_continuous_scale='Viridis',
        height=600
    )
    
    fig.update_layout(
        xaxis_title="Region/Province",
        yaxis_title=metric_options[selected_metric],
        xaxis={'categoryorder':'total descending'},
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Create a scatter map for regions if coordinates are available
    if 'latitude' in region_data.columns and 'longitude' in region_data.columns:
        # Filter out entries with missing coordinates
        map_region_data = region_data[(region_data['latitude'].notna()) & (region_data['longitude'].notna())]
        
        if len(map_region_data) > 0:
            st.subheader(f"Region Map of {selected_country_for_regions}")
            
            fig = px.scatter_geo(
                map_region_data,
                lat='latitude',
                lon='longitude',
                color=selected_metric,
                size=selected_metric,
                hover_name='province',
                title=f"{metric_options[selected_metric]} by Region in {selected_country_for_regions}",
                projection="natural earth",
                color_continuous_scale='Viridis',
                size_max=50
            )
            
            # Focus map on the selected country
            mean_lat = map_region_data['latitude'].mean()
            mean_lon = map_region_data['longitude'].mean()
            
            fig.update_geos(
                center=dict(lat=mean_lat, lon=mean_lon),
                projection_scale=4 if selected_country_for_regions in ['US', 'China', 'Russia', 'Canada', 'Brazil'] else 6
            )
            
            fig.update_layout(height=600)
            
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"No region/province level data available for {selected_country_for_regions}.")

# Time-lapse visualization
st.header("COVID-19 Spread Over Time")
st.markdown("View how COVID-19 spread globally over time.")

# Date range selection for time-lapse
end_date = pd.to_datetime(last_updated) if isinstance(last_updated, str) else pd.Timestamp.now()
start_date = end_date - pd.Timedelta(days=30)  # Default to last 30 days

time_lapse_date_range = st.date_input(
    "Select Date Range for Time-Lapse",
    value=(start_date.date(), end_date.date()),
    min_value=pd.to_datetime(country_data['date'].min()).date(),
    max_value=pd.to_datetime(country_data['date'].max()).date()
)

# Convert to datetime for filtering
if len(time_lapse_date_range) == 2:
    start_date, end_date = pd.to_datetime(time_lapse_date_range[0]), pd.to_datetime(time_lapse_date_range[1])
    
    # Filter data for the selected date range
    time_lapse_data = country_data[
        (country_data['date'] >= start_date) & 
        (country_data['date'] <= end_date)
    ]
    
    # Sample dates for the animation (to avoid too many frames)
    date_diff = (end_date - start_date).days
    
    if date_diff > 30:
        # If more than 30 days, sample weekly
        sample_freq = '7D'
    elif date_diff > 14:
        # If more than 14 days, sample every 3 days
        sample_freq = '3D'
    else:
        # Otherwise, use daily
        sample_freq = '1D'
    
    # Create a date range with the appropriate frequency
    date_range = pd.date_range(start=start_date, end=end_date, freq=sample_freq)
    
    # Filter data to include only the sampled dates
    time_lapse_data = time_lapse_data[time_lapse_data['date'].isin(date_range)]
    
    # Create time-lapse visualization
    try:
        fig = px.choropleth(
            time_lapse_data,
            locations='country',
            locationmode='country names',
            color=selected_metric,
            animation_frame='date',
            color_continuous_scale='Viridis',
            range_color=[0, time_lapse_data[selected_metric].quantile(0.95)],  # Cap color scale at 95th percentile
            title=f"{metric_options[selected_metric]} Over Time",
            height=700
        )
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            coloraxis_colorbar=dict(
                title=metric_options[selected_metric]
            )
        )
        
        # Animation settings
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 300
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 300
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating time-lapse visualization: {e}")
else:
    st.warning("Please select both start and end dates for the time-lapse visualization.")

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This page provides geographic visualization of COVID-19 data. Use the sidebar to customize the view.
""")
