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
if covid_data is None:
    st.error("Failed to load COVID-19 data. Please try again later.")
    st.stop()

# Get the country data
country_data = covid_data['by_country']
country_list = covid_data['countries']
last_updated = country_data['date'].max() if 'by_country' in covid_data else "Unknown"

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
    default=default_countries[:3]  # Default to first 3 countries from the default list that exist in the data
)

# Ensure at least one country is selected
if not selected_countries:
    st.warning("Please select at least one country from the sidebar.")
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
    filtered_country_data = country_data[
        (country_data['date'] >= pd.to_datetime(start_date)) & 
        (country_data['date'] <= pd.to_datetime(end_date)) &
        (country_data['country'].isin(selected_countries))
    ]
else:
    filtered_country_data = country_data[country_data['country'].isin(selected_countries)]

# Metric selection for analysis
metric_options = {
    'total_cases': 'Total Cases',
    'new_cases': 'New Cases',
    'total_deaths': 'Total Deaths',
    'new_deaths': 'New Deaths',
    'total_recovered': 'Total Recovered'
}

selected_metric = st.sidebar.selectbox("Select Metric for Analysis", 
                                      list(metric_options.keys()), 
                                      format_func=lambda x: metric_options[x])

# Country summary statistics
st.header("Country Summary Statistics")

# Get the latest data for each selected country
latest_date = filtered_country_data['date'].max()
latest_country_data = filtered_country_data[filtered_country_data['date'] == latest_date]

# Calculate metrics for each country
country_metrics = []
for country in selected_countries:
    country_data_series = filtered_country_data[filtered_country_data['country'] == country]
    latest_data = latest_country_data[latest_country_data['country'] == country]
    
    if len(latest_data) > 0:
        latest_data = latest_data.iloc[0]
        
        # Calculate 7-day growth rate
        week_ago_data = country_data_series.iloc[-8] if len(country_data_series) > 8 else country_data_series.iloc[0] if len(country_data_series) > 0 else None
        if week_ago_data is not None:
            cases_growth = ((latest_data['total_cases'] - week_ago_data['total_cases']) / week_ago_data['total_cases'] * 100) if week_ago_data['total_cases'] > 0 else 0
            deaths_growth = ((latest_data['total_deaths'] - week_ago_data['total_deaths']) / week_ago_data['total_deaths'] * 100) if week_ago_data['total_deaths'] > 0 else 0
        else:
            cases_growth = 0
            deaths_growth = 0
        
        # Store metrics
        country_metrics.append({
            'country': country,
            'total_cases': int(latest_data['total_cases']),
            'total_deaths': int(latest_data['total_deaths']),
            'total_recovered': int(latest_data['total_recovered']),
            'new_cases': int(latest_data['new_cases']),
            'new_deaths': int(latest_data['new_deaths']),
            'cases_growth': cases_growth,
            'deaths_growth': deaths_growth
        })

# Display metrics in a grid
if country_metrics:
    cols = st.columns(len(country_metrics))
    
    for i, country_metric in enumerate(country_metrics):
        with cols[i]:
            st.subheader(country_metric['country'])
            st.metric("Total Cases", utils.format_number(country_metric['total_cases']), f"{country_metric['cases_growth']:.1f}% in 7 days")
            st.metric("Total Deaths", utils.format_number(country_metric['total_deaths']), f"{country_metric['deaths_growth']:.1f}% in 7 days")
            st.metric("New Cases", utils.format_number(country_metric['new_cases']))
            st.metric("New Deaths", utils.format_number(country_metric['new_deaths']))

# Time series analysis
st.header("Time Series Analysis")

# Create time series chart for selected countries
try:
    st.plotly_chart(visualizations.create_country_time_series(filtered_country_data, selected_countries, selected_metric), use_container_width=True)
except Exception as e:
    st.error(f"Error generating time series chart: {e}")

# Daily new cases/deaths
st.header("Daily New Cases and Deaths")

# Create tabs for different daily metrics
daily_tab1, daily_tab2 = st.tabs(["Daily New Cases", "Daily New Deaths"])

with daily_tab1:
    # Create line chart for daily new cases
    fig = px.line(
        filtered_country_data,
        x='date',
        y='new_cases',
        color='country',
        title='Daily New Cases by Country',
        line_shape='spline'
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="New Cases",
        legend_title="Country",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

with daily_tab2:
    # Create line chart for daily new deaths
    fig = px.line(
        filtered_country_data,
        x='date',
        y='new_deaths',
        color='country',
        title='Daily New Deaths by Country',
        line_shape='spline'
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="New Deaths",
        legend_title="Country",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Country comparison
st.header("Country Comparison")

try:
    # Create country comparison chart
    fig = visualizations.create_country_comparison_chart(
        latest_country_data, 
        selected_countries, 
        metric=selected_metric
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating country comparison chart: {e}")

# 7-day rolling averages
st.header("7-Day Rolling Averages")

# Calculate 7-day rolling averages for each country
for country in selected_countries:
    country_data_series = filtered_country_data[filtered_country_data['country'] == country]
    filtered_country_data.loc[filtered_country_data['country'] == country, 'cases_7day_avg'] = country_data_series['new_cases'].rolling(window=7).mean()
    filtered_country_data.loc[filtered_country_data['country'] == country, 'deaths_7day_avg'] = country_data_series['new_deaths'].rolling(window=7).mean()

# Create tabs for different rolling average metrics
avg_tab1, avg_tab2 = st.tabs(["Cases 7-Day Average", "Deaths 7-Day Average"])

with avg_tab1:
    # Create line chart for 7-day average of new cases
    fig = px.line(
        filtered_country_data,
        x='date',
        y='cases_7day_avg',
        color='country',
        title='7-Day Average of New Cases by Country',
        line_shape='spline'
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="7-Day Average of New Cases",
        legend_title="Country",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

with avg_tab2:
    # Create line chart for 7-day average of new deaths
    fig = px.line(
        filtered_country_data,
        x='date',
        y='deaths_7day_avg',
        color='country',
        title='7-Day Average of New Deaths by Country',
        line_shape='spline'
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="7-Day Average of New Deaths",
        legend_title="Country",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This page allows you to analyze and compare COVID-19 statistics for specific countries.
""")
