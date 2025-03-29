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
    page_title="Country Analysis - COVID-19 Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Title
st.title("🌍 Country Analysis")
st.markdown("Analyze COVID-19 statistics for specific countries.")

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
if covid_data is None or 'by_country' not in covid_data or 'countries' not in covid_data:
    st.error("Failed to load country-level COVID-19 data. Please try again later.")
    st.stop()

# Get the country data
country_data = covid_data['by_country'].copy()
country_list = covid_data['countries']
country_data['date'] = pd.to_datetime(country_data['date'])  # Ensure datetime format

if country_data.empty:
    st.error("No country-level data available.")
    st.stop()

last_updated = country_data['date'].max().date()

# Dashboard metadata in the sidebar
st.sidebar.info(f"Data last updated: {last_updated}")

# Sidebar filters
st.sidebar.header("Country Selection")

# Country selection dropdown
default_countries = ['US', 'India', 'Brazil', 'United Kingdom', 'France']
default_countries = [c for c in default_countries if c in country_list]

selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=country_list,
    default=default_countries[:3] if default_countries else []
)

# Ensure at least one country is selected
if not selected_countries:
    st.warning("Please select at least one country from the sidebar.")
    st.stop()

# Date range selection
min_date = country_data['date'].min().date()
max_date = country_data['date'].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(max_date - pd.Timedelta(days=90), max_date),
    min_value=min_date,
    max_value=max_date
)

# Convert date_range to datetime
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range)
    filtered_country_data = country_data[
        (country_data['date'] >= start_date) &
        (country_data['date'] <= end_date) &
        (country_data['country'].isin(selected_countries))
    ]
else:
    filtered_country_data = country_data[country_data['country'].isin(selected_countries)]

if filtered_country_data.empty:
    st.warning("No data available for the selected countries and date range.")
    st.stop()

# Metric selection for analysis
metric_options = {
    'total_cases': 'Total Cases',
    'new_cases': 'New Cases',
    'total_deaths': 'Total Deaths',
    'new_deaths': 'New Deaths',
    'total_recovered': 'Total Recovered'
}

selected_metric = st.sidebar.selectbox(
    "Select Metric for Analysis",
    list(metric_options.keys()),
    format_func=lambda x: metric_options[x]
)

# Country summary statistics
st.header("Country Summary Statistics")

latest_date = filtered_country_data['date'].max()
latest_country_data = filtered_country_data[filtered_country_data['date'] == latest_date]

# Display country metrics
cols = st.columns(len(selected_countries))

for i, country in enumerate(selected_countries):
    country_data_series = filtered_country_data[filtered_country_data['country'] == country]
    latest_data = latest_country_data[latest_country_data['country'] == country]

    if not latest_data.empty:
        latest_data = latest_data.iloc[0]

        # Calculate 7-day growth rate
        if len(country_data_series) > 8:
            week_ago_data = country_data_series.iloc[-8]
            cases_growth = ((latest_data['total_cases'] - week_ago_data['total_cases']) / week_ago_data['total_cases'] * 100) if week_ago_data['total_cases'] > 0 else 0
            deaths_growth = ((latest_data['total_deaths'] - week_ago_data['total_deaths']) / week_ago_data['total_deaths'] * 100) if week_ago_data['total_deaths'] > 0 else 0
        else:
            cases_growth = deaths_growth = 0

        with cols[i]:
            st.subheader(country)
            st.metric("Total Cases", utils.format_number(latest_data['total_cases']), f"{cases_growth:.1f}% in 7 days")
            st.metric("Total Deaths", utils.format_number(latest_data['total_deaths']), f"{deaths_growth:.1f}% in 7 days")
            st.metric("New Cases", utils.format_number(latest_data['new_cases']))
            st.metric("New Deaths", utils.format_number(latest_data['new_deaths']))

# Time series analysis
st.header("Time Series Analysis")

try:
    st.plotly_chart(visualizations.create_country_time_series(filtered_country_data, selected_countries, selected_metric), use_container_width=True)
except Exception as e:
    st.error(f"Error generating time series chart: {e}")

# Rolling averages
st.header("7-Day Rolling Averages")

# Calculate 7-day rolling averages
for country in selected_countries:
    country_data_series = filtered_country_data[filtered_country_data['country'] == country]
    filtered_country_data.loc[filtered_country_data['country'] == country, 'cases_7day_avg'] = country_data_series['new_cases'].rolling(window=7, min_periods=1).mean()
    filtered_country_data.loc[filtered_country_data['country'] == country, 'deaths_7day_avg'] = country_data_series['new_deaths'].rolling(window=7, min_periods=1).mean()

# Create rolling average plots
avg_tab1, avg_tab2 = st.tabs(["Cases 7-Day Average", "Deaths 7-Day Average"])

with avg_tab1:
    fig = px.line(filtered_country_data, x='date', y='cases_7day_avg', color='country', title='7-Day Average of New Cases by Country')
    st.plotly_chart(fig, use_container_width=True)

with avg_tab2:
    fig = px.line(filtered_country_data, x='date', y='deaths_7day_avg', color='country', title='7-Day Average of New Deaths by Country')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This page allows you to analyze and compare COVID-19 statistics for specific countries.
""")
