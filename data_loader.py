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


def fetch_data(url):
    """
    Fetch data from a given URL and return it as a Pandas DataFrame.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching data from {url}: {e}")


def process_time_series(df, category):
    """
    Convert wide-format time series data into a long format.
    """
    df = df.copy()
    id_vars = ['Province/State', 'Country/Region', 'Lat', 'Long']

    if not all(col in df.columns for col in id_vars):
        raise ValueError("Missing expected columns in the dataset.")

    df_long = df.melt(id_vars=id_vars, var_name='date', value_name=category)

    # Convert date column to datetime format
    df_long['date'] = pd.to_datetime(df_long['date'], errors='coerce')

    # Rename columns for consistency
    df_long.rename(columns={'Province/State': 'province', 'Country/Region': 'country',
                            'Lat': 'latitude', 'Long': 'longitude'}, inplace=True)

    return df_long


def load_covid_data():
    """
    Load and process COVID-19 data from JHU CSSE.
    """
    try:
        data_frames = {category: fetch_data(url) for category, url in DATA_URLS.items()}
        processed_data = {}

        confirmed_long = process_time_series(data_frames['confirmed'], 'total_cases')
        deaths_long = process_time_series(data_frames['deaths'], 'total_deaths')

        try:
            recovered_long = process_time_series(data_frames['recovered'], 'total_recovered')
        except Exception:
            recovered_long = None

        merged_data = confirmed_long.merge(
            deaths_long[['province', 'country', 'date', 'total_deaths']],
            on=['province', 'country', 'date'], how='left'
        )

        if recovered_long is not None:
            merged_data = merged_data.merge(
                recovered_long[['province', 'country', 'date', 'total_recovered']],
                on=['province', 'country', 'date'], how='left'
            )
        else:
            merged_data['total_recovered'] = 0

        merged_data.fillna({'province': '', 'total_cases': 0, 'total_deaths': 0, 'total_recovered': 0}, inplace=True)

        merged_data.sort_values(['country', 'province', 'date'], inplace=True)
        merged_data['new_cases'] = merged_data.groupby(['country', 'province'])['total_cases'].diff().fillna(0).clip(
            lower=0)
        merged_data['new_deaths'] = merged_data.groupby(['country', 'province'])['total_deaths'].diff().fillna(0).clip(
            lower=0)

        country_data = merged_data.groupby(['country', 'date']).agg({
            'total_cases': 'sum', 'total_deaths': 'sum',
            'total_recovered': 'sum', 'new_cases': 'sum', 'new_deaths': 'sum'
        }).reset_index()

        global_data = merged_data.groupby('date').agg({
            'total_cases': 'sum', 'total_deaths': 'sum',
            'total_recovered': 'sum', 'new_cases': 'sum', 'new_deaths': 'sum'
        }).reset_index()

        processed_data['raw'] = merged_data
        processed_data['by_country'] = country_data
        processed_data['global'] = global_data
        processed_data['countries'] = sorted(merged_data['country'].dropna().unique())

        if processed_data['global'].empty or processed_data['by_country'].empty:
            raise ValueError("Loaded COVID-19 data is empty after processing.")

        return processed_data

    except Exception as e:
        st.error(f"Error loading COVID-19 data: {e}")
        raise
