import streamlit as st
import pandas as pd
import plotly.express as px

# Load and clean data
df = pd.read_csv('Summary_By_Origin_Airport.csv')
airport_coords = pd.read_csv('airports_location.csv')

# Data cleaning functions
def clean_numeric(series):
    if series.dtype == object:
        series = series.str.replace(',', '').str.replace('"', '')
        return pd.to_numeric(series, errors='coerce')
    return series

numeric_cols = ['Total Passengers', 'Domestic Passengers',
                'Outbound International Passengers', 'Inbound International Passengers']
for col in numeric_cols:
    df[col] = clean_numeric(df[col])

df['Year'] = df['Year'].astype(str).str.extract(r'(\d{4})')[0]
df = df.dropna(subset=['Year'])
df['Year'] = df['Year'].astype(int)

df = df.merge(airport_coords, left_on='Origin Airport Code', right_on='code', how='left')
df = df.dropna(subset=['latitude', 'longitude'])

# Sidebar filters
st.set_page_config(layout="wide", page_title="US Flight Analytics Dashboard")
st.markdown("<h1 style='text-align: center; color: white;'>US Flight Analytics Dashboard</h1>", unsafe_allow_html=True)
st.sidebar.header("Filters")

year_min, year_max = int(df['Year'].min()), int(df['Year'].max())
selected_years = st.sidebar.slider("Select Year Range", year_min, year_max, (year_min, year_max))
passenger_type = st.sidebar.radio("Passenger Type", ['Domestic Passengers', 'International Passengers'])
top_n = st.sidebar.selectbox("Top N Airports", [5, 10, 20])

year_range = list(range(selected_years[0], selected_years[1] + 1))
filtered_df = df[df['Year'].isin(year_range)]

# Charts
def create_total_passengers_chart():
    data = filtered_df.groupby('Year')['Total Passengers'].sum().reset_index()
    fig = px.bar(data, x='Year', y='Total Passengers',
                 title="Total Passengers Per Year",
                 color='Total Passengers',
                 color_continuous_scale='viridis',
                 template='plotly_dark')
    return fig

def create_domestic_chart():
    data = filtered_df.groupby('Year')['Domestic Passengers'].sum().reset_index()
    fig = px.line(data, x='Year', y='Domestic Passengers',
                  title="Domestic Passengers Per Year",
                  markers=True,
                  color_discrete_sequence=["#00CC96"],
                  template='plotly_dark')
    return fig

def create_international_chart():
    data = filtered_df.groupby('Year')[['Outbound International Passengers', 'Inbound International Passengers']].sum().reset_index()
    fig = px.line(data, x='Year',
                  y=['Outbound International Passengers', 'Inbound International Passengers'],
                  title="International Passengers Per Year",
                  markers=True,
                  color_discrete_sequence=["#EF553B", "#AB63FA"],
                  template='plotly_dark')
    return fig

def create_airport_map():
    data = filtered_df.groupby(['Origin Airport Code', 'Origin Airport Name', 'latitude', 'longitude'])['Total Passengers'].sum().reset_index()
    fig = px.scatter_geo(data, lat='latitude', lon='longitude',
                         size='Total Passengers',
                         hover_name='Origin Airport Code',
                         hover_data={'Origin Airport Name': True, 'Total Passengers': True, 'latitude': False, 'longitude': False},
                         projection="albers usa",
                         scope="usa",
                         title="Passenger Traffic by Airport",
                         color='Total Passengers',
                         color_continuous_scale='viridis',
                         template='plotly_dark')
    return fig

# Layout
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(create_total_passengers_chart(), use_container_width=True)

with col2:
    if passenger_type == 'Domestic Passengers':
        st.plotly_chart(create_domestic_chart(), use_container_width=True)
    else:
        st.plotly_chart(create_international_chart(), use_container_width=True)

col3, col4 = st.columns([2, 1])
with col3:
    st.plotly_chart(create_airport_map(), use_container_width=True)

with col4:
    st.subheader(f"Top {top_n} Airports by Passengers")
    top_airports = filtered_df.groupby(['Origin Airport Code', 'Origin City Name'])['Total Passengers'] \
                              .sum().nlargest(top_n).reset_index()
    top_airports['Rank'] = range(1, len(top_airports) + 1)
    st.dataframe(top_airports[['Rank', 'Origin Airport Code', 'Origin City Name', 'Total Passengers']].rename(
        columns={
            'Origin Airport Code': 'Airport',
            'Origin City Name': 'City',
            'Total Passengers': 'Passengers'
        }
    ), use_container_width=True)

# Optional: Add dark mode styling
st.markdown("""
    <style>
    body {
        background-color: #2d2d2d;
        color: white;
    }
    .css-1aumxhk {
        background-color: #3d3d3d;
    }
    </style>
""", unsafe_allow_html=True)
