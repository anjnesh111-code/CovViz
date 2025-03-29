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

# Get the global data
global_data = covid_data['global']
last_updated = global_data.iloc[-1]['date'] if 'global' in covid_data else "Unknown"

# Dashboard metadata in the sidebar
st.sidebar.info(f"Data last updated: {last_updated}")

# Global metrics at the top
st.header("Global COVID-19 Metrics")

# Calculate global metrics
latest_data = global_data.iloc[-1]
total_cases = int(latest_data['total_cases']) if 'total_cases' in latest_data else 0
total_deaths = int(latest_data['total_deaths']) if 'total_deaths' in latest_data else 0
total_recovered = int(latest_data['total_recovered']) if 'total_recovered' in latest_data else 0
active_cases = total_cases - total_deaths - total_recovered

# Calculate growth rates
week_ago_data = global_data.iloc[-8] if len(global_data) > 8 else global_data.iloc[0]
cases_growth = ((latest_data['total_cases'] - week_ago_data['total_cases']) / week_ago_data['total_cases'] * 100) if week_ago_data['total_cases'] > 0 else 0
deaths_growth = ((latest_data['total_deaths'] - week_ago_data['total_deaths']) / week_ago_data['total_deaths'] * 100) if week_ago_data['total_deaths'] > 0 else 0

# Key metrics in columns with delta values
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Cases", utils.format_number(total_cases), f"{cases_growth:.1f}% in 7 days")
col2.metric("Active Cases", utils.format_number(active_cases))
col3.metric("Total Deaths", utils.format_number(total_deaths), f"{deaths_growth:.1f}% in 7 days")
col4.metric("Total Recovered", utils.format_number(total_recovered))

# Sidebar filters for global view
st.sidebar.header("Global View Filters")

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
else:
    filtered_global_data = global_data

# Show daily and cumulative trends
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

# Calculate and display rolling averages
st.header("7-Day Moving Averages")

# Calculate 7-day rolling averages
filtered_global_data['cases_7day_avg'] = filtered_global_data['new_cases'].rolling(window=7).mean()
filtered_global_data['deaths_7day_avg'] = filtered_global_data['new_deaths'].rolling(window=7).mean()

# Create time series chart with moving averages
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
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    legend_title_text='',
    hovermode="x unified",
    height=500
)

# Update names in legend
fig.for_each_trace(lambda t: t.update(name=t.name.replace("cases_7day_avg", "New Cases (7-day avg)").replace("deaths_7day_avg", "New Deaths (7-day avg)")))

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

# Get latest date data for country comparison
latest_date = filtered_global_data['date'].max()
latest_data = covid_data['by_country'][covid_data['by_country']['date'] == latest_date]

# Get top 10 countries for the selected metric
top_countries = latest_data.groupby('country')[selected_metric].sum().nlargest(10).reset_index()

# Create bar chart
fig = px.bar(
    top_countries,
    x='country',
    y=selected_metric,
    title=f'Top 10 Countries by {metric_options[selected_metric]}',
    color=selected_metric,
    color_continuous_scale='Viridis',
    text=selected_metric
)

fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig.update_layout(xaxis_title="Country", yaxis_title=metric_options[selected_metric])

st.plotly_chart(fig, use_container_width=True)

# World map visualization
st.header("Global Distribution")

# Metric selection for map
map_metric = st.selectbox("Select Metric for Map", 
                         ['total_cases', 'total_deaths', 'new_cases', 'new_deaths'],
                         format_func=lambda x: ' '.join(word.capitalize() for word in x.split('_')))

# Create world map
country_data_for_map = covid_data['by_country'][covid_data['by_country']['date'] == latest_date]
try:
    st.plotly_chart(visualizations.create_world_map(country_data_for_map, metric=map_metric), use_container_width=True)
except Exception as e:
    st.error(f"Error generating world map: {e}")

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
This dashboard provides an overview of global COVID-19 trends. Navigate to other pages for more detailed analysis.
""")
