import pandas as pd
import numpy as np

def format_number(num):
    """
    Format numbers for display (e.g., 1000000 to 1M)
    
    Args:
        num (int or float): Number to format
        
    Returns:
        str: Formatted number string
    """
    if num is None:
        return "N/A"
    
    if num == 0:
        return "0"
        
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    
    # Add commas for thousands
    if magnitude == 0:
        return f"{int(num):,}"
    
    # Otherwise use abbreviations
    return f"{num:.1f}{['', 'K', 'M', 'B', 'T'][magnitude]}"

def calculate_growth_rate(data, column, days=7):
    """
    Calculate the growth rate over a specified number of days
    
    Args:
        data (pandas.DataFrame): DataFrame containing the time series data
        column (str): Column name to calculate growth rate for
        days (int): Number of days to calculate growth rate over
        
    Returns:
        float: Growth rate as a percentage
    """
    if len(data) < days:
        return None
    
    # Get the current value and the value 'days' ago
    current = data[column].iloc[-1]
    previous = data[column].iloc[-days-1]
    
    # Calculate growth rate
    if previous == 0:
        return None  # Avoid division by zero
    
    growth_rate = ((current - previous) / previous) * 100
    return growth_rate

def calculate_rolling_average(data, column, window=7):
    """
    Calculate rolling average for a specified column
    
    Args:
        data (pandas.DataFrame): DataFrame containing the time series data
        column (str): Column name to calculate rolling average for
        window (int): Window size for the rolling average
        
    Returns:
        pandas.Series: Series containing the rolling average
    """
    return data[column].rolling(window=window).mean()

def get_top_countries(data, column, n=10, date=None):
    """
    Get the top N countries for a given metric
    
    Args:
        data (pandas.DataFrame): DataFrame containing country data
        column (str): Column name to rank countries by
        n (int): Number of top countries to return
        date (str): Specific date to filter data (if None, use the latest date)
        
    Returns:
        list: List of top country names
    """
    # Filter for specific date if provided
    if date is not None:
        filtered_data = data[data['date'] == date]
    else:
        # Get the latest date
        latest_date = data['date'].max()
        filtered_data = data[data['date'] == latest_date]
    
    # Aggregate by country and get the top N
    top_countries = filtered_data.groupby('country')[column].sum().nlargest(n).index.tolist()
    
    return top_countries

def calculate_per_capita_metrics(data, population_data):
    """
    Calculate per capita metrics (cases and deaths per 100,000 people)
    
    Args:
        data (pandas.DataFrame): DataFrame containing COVID-19 data
        population_data (pandas.DataFrame): DataFrame containing population data by country
        
    Returns:
        pandas.DataFrame: DataFrame with additional per capita columns
    """
    # Make a copy to avoid modifying the original
    result = data.copy()
    
    # Merge with population data
    if 'country' in result.columns and 'population' in population_data.columns:
        result = pd.merge(
            result,
            population_data[['country', 'population']],
            on='country',
            how='left'
        )
        
        # Calculate per capita metrics (per 100,000 people)
        result['cases_per_100k'] = result['total_cases'] * 100000 / result['population']
        result['deaths_per_100k'] = result['total_deaths'] * 100000 / result['population']
        
    return result

def filter_data_by_date_range(data, start_date, end_date):
    """
    Filter data by date range
    
    Args:
        data (pandas.DataFrame): DataFrame containing time series data
        start_date (datetime): Start date
        end_date (datetime): End date
        
    Returns:
        pandas.DataFrame: Filtered DataFrame
    """
    # Ensure dates are datetime objects
    if not isinstance(start_date, pd.Timestamp):
        start_date = pd.to_datetime(start_date)
    
    if not isinstance(end_date, pd.Timestamp):
        end_date = pd.to_datetime(end_date)
    
    # Filter the data
    filtered_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    
    return filtered_data
