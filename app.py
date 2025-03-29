import streamlit as st
import pandas as pd
import plotly.express as px
import data_loader
import visualizations
import utils

# Page configuration
st.set_page_config(
    page_title="COVID-19 Global Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display header
st.title("🦠 COVID-19 Global Dashboard")
st.markdown("""
This interactive dashboard provides comprehensive analytics and visualizations for global COVID-19 trends.
Navigate through different pages using the sidebar to explore various aspects of the pandemic data.
""")

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

# Dashboard metadata
last_updated = covid_data['global'].iloc[-1]['date'] if 'global' in covid_data else "Unknown"
st.sidebar.info(f"Data last updated: {last_updated}")

# Main page content
st.subheader("Global COVID-19 Snapshot")

# Key metrics in columns
col1, col2, col3, col4 = st.columns(4)

# Calculate global metrics
if 'global' in covid_data:
    global_data = covid_data['global']
    latest_data = global_data.iloc[-1]
    
    total_cases = int(latest_data['total_cases']) if 'total_cases' in latest_data else 0
    total_deaths = int(latest_data['total_deaths']) if 'total_deaths' in latest_data else 0
    total_recovered = int(latest_data['total_recovered']) if 'total_recovered' in latest_data else 0
    active_cases = total_cases - total_deaths - total_recovered
    
    col1.metric("Total Cases", utils.format_number(total_cases))
    col2.metric("Active Cases", utils.format_number(active_cases))
    col3.metric("Total Deaths", utils.format_number(total_deaths))
    col4.metric("Total Recovered", utils.format_number(total_recovered))
else:
    st.warning("Global summary data not available.")

# Recent trends section
st.subheader("Recent Global Trends")

# Date range selection for main page
end_date = pd.to_datetime(last_updated) if isinstance(last_updated, str) else pd.Timestamp.now()
start_date = end_date - pd.Timedelta(days=30)

date_range = st.slider(
    "Select Date Range for Trends",
    min_value=pd.to_datetime(global_data['date'].min()) if 'global' in covid_data else start_date,
    max_value=pd.to_datetime(global_data['date'].max()) if 'global' in covid_data else end_date,
    value=(start_date, end_date)
)

# Filter data based on selected date range
if 'global' in covid_data:
    filtered_data = global_data[(global_data['date'] >= date_range[0]) & 
                                (global_data['date'] <= date_range[1])]
    
    # Display trend charts
    trend_tab1, trend_tab2 = st.tabs(["New Cases & Deaths", "Cumulative Trends"])
    
    with trend_tab1:
        try:
            st.plotly_chart(visualizations.create_daily_trends_chart(filtered_data), use_container_width=True)
        except Exception as e:
            st.error(f"Error generating daily trends chart: {e}")
    
    with trend_tab2:
        try:
            st.plotly_chart(visualizations.create_cumulative_trends_chart(filtered_data), use_container_width=True)
        except Exception as e:
            st.error(f"Error generating cumulative trends chart: {e}")
else:
    st.warning("Trend data not available.")

# Footer information
st.markdown("---")
st.markdown("""
**Data Source**: Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)  
**Dashboard**: Created with Streamlit, Pandas, and Plotly
""")
