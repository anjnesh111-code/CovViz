import pandas as pd
import requests
import io
import streamlit as st

# URLs for COVID-19 data from JHU CSSE repository
DATA_URLS = {
    'confirmed': 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv',
    'deaths': 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv',
    'recovered': 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
}

# Function to fetch data from URLs
def fetch_data(url):
    """
    Fetch data from a given URL
    
    Args:
        url (str): URL to fetch data from
        
    Returns:
        pandas.DataFrame: DataFrame containing fetched data
    
    Raises:
        Exception: If data cannot be fetched or processed
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        raise Exception(f"Error fetching data from {url}: {e}")

# Process time-series data to long format
def process_time_series(df, category):
    """
    Process time series data from wide to long format
    
    Args:
        df (pandas.DataFrame): DataFrame with time series data in wide format
        category (str): Category of data (confirmed, deaths, recovered)
        
    Returns:
        pandas.DataFrame: Processed DataFrame in long format
    """
    # Copy the input dataframe to avoid modifying the original
    df = df.copy()
    
    # Melt the dataframe to convert from wide to long format
    id_vars = ['Province/State', 'Country/Region', 'Lat', 'Long']
    df_long = df.melt(
        id_vars=id_vars,
        var_name='date',
        value_name=category
    )
    
    # Convert date to datetime
    df_long['date'] = pd.to_datetime(df_long['date'])
    
    # Rename columns for consistency
    df_long = df_long.rename(columns={
        'Province/State': 'province',
        'Country/Region': 'country',
        'Lat': 'latitude',
        'Long': 'longitude'
    })
    
    return df_long

# Load COVID-19 data
def load_covid_data():
    """
    Load and process COVID-19 data from JHU CSSE
    
    Returns:
        dict: Dictionary containing processed DataFrames
    """
    try:
        # Fetch data for each category
        data_frames = {}
        for category, url in DATA_URLS.items():
            data_frames[category] = fetch_data(url)
        
        # Process each data frame
        processed_data = {}
        
        # Process confirmed cases
        confirmed_long = process_time_series(data_frames['confirmed'], 'total_cases')
        
        # Process deaths
        deaths_long = process_time_series(data_frames['deaths'], 'total_deaths')
        
        # Process recovered (if available)
        try:
            recovered_long = process_time_series(data_frames['recovered'], 'total_recovered')
        except Exception:
            # Recovered data might not be available
            recovered_long = None
        
        # Merge confirmed and deaths data
        merged_data = pd.merge(
            confirmed_long,
            deaths_long[['province', 'country', 'date', 'total_deaths']],
            on=['province', 'country', 'date'],
            how='left'
        )
        
        # Add recovered data if available
        if recovered_long is not None:
            merged_data = pd.merge(
                merged_data,
                recovered_long[['province', 'country', 'date', 'total_recovered']],
                on=['province', 'country', 'date'],
                how='left'
            )
        else:
            # If recovered data is not available, set to 0
            merged_data['total_recovered'] = 0
        
        # Fill NaN values
        merged_data = merged_data.fillna({
            'province': '',
            'total_cases': 0,
            'total_deaths': 0,
            'total_recovered': 0
        })
        
        # Calculate daily new cases and deaths
        merged_data = merged_data.sort_values(['country', 'province', 'date'])
        merged_data['new_cases'] = merged_data.groupby(['country', 'province'])['total_cases'].diff().fillna(0)
        merged_data['new_deaths'] = merged_data.groupby(['country', 'province'])['total_deaths'].diff().fillna(0)
        
        # Handle negative values (data corrections) - set to 0
        merged_data['new_cases'] = merged_data['new_cases'].clip(lower=0)
        merged_data['new_deaths'] = merged_data['new_deaths'].clip(lower=0)
        
        # Store country-level data
        country_data = merged_data.groupby(['country', 'date']).agg({
            'total_cases': 'sum',
            'total_deaths': 'sum',
            'total_recovered': 'sum',
            'new_cases': 'sum',
            'new_deaths': 'sum'
        }).reset_index()
        
        # Calculate global data
        global_data = merged_data.groupby('date').agg({
            'total_cases': 'sum',
            'total_deaths': 'sum',
            'total_recovered': 'sum',
            'new_cases': 'sum',
            'new_deaths': 'sum'
        }).reset_index()
        
        # Store all processed data
        processed_data['raw'] = merged_data
        processed_data['by_country'] = country_data
        processed_data['global'] = global_data
        
        # Get list of countries for filtering
        processed_data['countries'] = sorted(merged_data['country'].unique())
        
        return processed_data
    
    except Exception as e:
        st.error(f"Error loading COVID-19 data: {e}")
        raise
