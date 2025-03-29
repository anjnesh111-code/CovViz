import streamlit as st

st.set_page_config(
    page_title="Time Series Analysis - COVID-19 Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("COVID-19 Data Visualization Dashboard")

import pandas as pd
import plotly.express as px
import data_loader
import visualizations
import utils


# Function to clear cache
def clear_cache():
    st.cache_data.clear()


# Button to refresh data
if st.button("Refresh Data"):
    clear_cache()

# Display header
st.title("🦠 COVID-19 Global Dashboard")
st.markdown("""
This interactive dashboard provides comprehensive analytics and visualizations for global COVID-19 trends.
Navigate through different pages using the sidebar to explore various aspects of the pandemic data.
""")


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
    if not covid_data or 'global' not in covid_data or covid_data['global'].empty:
        st.error("Global data is missing. Please check your dataset.")
        st.stop()

# Get the latest update date
last_updated = covid_data['global']['date'].max() if 'global' in covid_data else "Unknown"
st.sidebar.info(f"Data last updated: {last_updated}")

# Main page content
st.subheader("Global COVID-19 Snapshot")

# Key metrics in columns
col1, col2, col3, col4 = st.columns(4)

# Calculate global metrics
if 'global' in covid_data and not covid_data['global'].empty:
    global_data = covid_data['global']
    latest_data = global_data.iloc[-1] if not global_data.empty else None

    if latest_data is not None:
        total_cases = int(latest_data['total_cases']) if 'total_cases' in latest_data else 0
        total_deaths = int(latest_data['total_deaths']) if 'total_deaths' in latest_data else 0
        total_recovered = int(latest_data['total_recovered']) if 'total_recovered' in latest_data else 0
        active_cases = total_cases - total_deaths - total_recovered

        col1.metric("Total Cases", utils.format_number(total_cases))
        col2.metric("Active Cases", utils.format_number(active_cases))
        col3.metric("Total Deaths", utils.format_number(total_deaths))
        col4.metric("Total Recovered", utils.format_number(total_recovered))
    else:
        st.warning("No data available for the latest update.")
else:
    st.warning("Global summary data not available.")

# Recent trends section
st.subheader("Recent Global Trends")

# Date range selection for main page
if 'global' in covid_data and not covid_data['global'].empty:
    end_date = covid_data['global']['date'].max()
    start_date = end_date - pd.Timedelta(days=30)

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

    # Filter data based on selected date range
    filtered_data = global_data[
        (global_data['date'] >= pd.to_datetime(date_range[0])) &
        (global_data['date'] <= pd.to_datetime(date_range[1]))
        ]

    # Display trend charts
    trend_tab1, trend_tab2 = st.tabs(["New Cases & Deaths", "Cumulative Trends"])

    with trend_tab1:
        try:
            fig1 = visualizations.create_daily_trends_chart(filtered_data)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("No data available for daily trends.")
        except Exception as e:
            st.error(f"Error generating daily trends chart: {e}")

    with trend_tab2:
        try:
            fig2 = visualizations.create_cumulative_trends_chart(filtered_data)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No data available for cumulative trends.")
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

