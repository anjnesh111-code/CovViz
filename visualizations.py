import plotly.express as px


def create_daily_trends_chart(df):
    """
    Create a daily trends chart for COVID-19 cases and deaths.
    """
    if df.empty:
        return None

    fig = px.line(df, x='date', y=['new_cases', 'new_deaths'],
                  title='Daily Trends of COVID-19 Cases and Deaths',
                  labels={'value': 'Count', 'variable': 'Metric'},
                  color_discrete_map={'new_cases': 'blue', 'new_deaths': 'red'})

    fig.update_layout(legend_title_text='', hovermode="x unified")
    return fig


def create_cumulative_trends_chart(df):
    """
    Create a cumulative trends chart for COVID-19 data.
    """
    if df.empty:
        return None

    fig = px.line(df, x='date', y=['total_cases', 'total_deaths'],
                  title='Cumulative COVID-19 Cases and Deaths',
                  labels={'value': 'Count', 'variable': 'Metric'},
                  color_discrete_map={'total_cases': 'blue', 'total_deaths': 'red'})

    fig.update_layout(legend_title_text='', hovermode="x unified")
    return fig


def create_world_map(df, metric):
    """
    Create a world map visualization of COVID-19 data.
    """
    if df.empty:
        return None

    fig = px.choropleth(df, locations='country', locationmode='country names',
                        color=metric, hover_name='country',
                        title=f'Global Distribution of {metric.replace("_", " ").title()}',
                        color_continuous_scale='Reds')

    fig.update_layout(geo=dict(showcoastlines=True))
    return fig
import plotly.express as px

def create_country_time_series(data, selected_countries, metric):
    """
    Generate a time series plot for multiple countries.

    Parameters:
    - data (DataFrame): Filtered country-level COVID-19 data.
    - selected_countries (list): List of selected countries for comparison.
    - metric (str): The metric to visualize (e.g., 'total_cases', 'new_cases').

    Returns:
    - A Plotly figure.
    """
    fig = px.line(
        data[data['country'].isin(selected_countries)],
        x='date',
        y=metric,
        color='country',
        title=f"Comparison of {metric.replace('_', ' ').title()} Across Selected Countries",
        labels={'date': 'Date', metric: metric.replace('_', ' ').title()},
        line_shape='spline'
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=metric.replace('_', ' ').title(),
        hovermode="x unified",
        legend_title="Country",
        height=500
    )

    return fig
