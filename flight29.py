import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Initialize the app with a Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

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

df = df.merge(
    airport_coords, 
    left_on='Origin Airport Code', 
    right_on='code', 
    how='left'
).dropna(subset=['latitude', 'longitude'])

# Visualization functions
def create_total_passengers_chart(selected_years=None):
    if selected_years is None:
        selected_years = df['Year'].unique()
    data = df[df['Year'].isin(selected_years)].groupby('Year')['Total Passengers'].sum().reset_index()
    return px.bar(
        data,
        x='Year', y='Total Passengers',
        title="Total Passengers Per Year",
        color='Total Passengers',
        color_continuous_scale='viridis',
        template='plotly_dark'
    )

def create_domestic_chart(selected_years=None):
    if selected_years is None:
        selected_years = df['Year'].unique()
    data = df[df['Year'].isin(selected_years)].groupby('Year')['Domestic Passengers'].sum().reset_index()
    return px.line(
        data,
        x='Year', y='Domestic Passengers',
        title="Domestic Passengers Per Year",
        markers=True,
        color_discrete_sequence=["#00CC96"],
        template='plotly_dark'
    )

def create_international_chart(selected_years=None):
    if selected_years is None:
        selected_years = df['Year'].unique()
    data = df[df['Year'].isin(selected_years)].groupby('Year')[['Outbound International Passengers', 'Inbound International Passengers']].sum().reset_index()
    return px.line(
        data,
        x='Year', y=['Outbound International Passengers', 'Inbound International Passengers'],
        title="International Passengers Per Year",
        markers=True,
        color_discrete_sequence=["#EF553B", "#AB63FA"],
        template='plotly_dark'
    )

def create_airport_map(selected_years=None):
    if selected_years is None:
        selected_years = df['Year'].unique()
    data = df[df['Year'].isin(selected_years)].groupby(['Origin Airport Code','Origin Airport Name','latitude', 'longitude'])['Total Passengers'].sum().reset_index()
    return px.scatter_geo(
        data,
        lat='latitude',
        lon='longitude',
        size='Total Passengers',
        hover_name='Origin Airport Code',
        hover_data={'Origin Airport Name': True, 'Total Passengers': True, 'latitude': False, 'longitude': False},
        projection="albers usa",
        scope="usa",
        title="Passenger Traffic by Airport",
        color='Total Passengers',
        color_continuous_scale='viridis',
        template='plotly_dark'
    )



# Create the app layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("US Flight Analytics Dashboard", 
                      className="text-center my-4",
                      style={'color': 'white'}), 
              width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Year Range Selector", style={'color': 'white'}),
                dbc.CardBody([
                    dcc.RangeSlider(
                        id='year-slider',
                        min=df['Year'].min(),
                        max=df['Year'].max(),
                        value=[df['Year'].min(), df['Year'].max()],
                        marks={str(year): str(year) for year in df['Year'].unique()},
                        step=None,
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ], className="mb-4", style={'backgroundColor': '#3d3d3d'})
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Total Passengers", style={'color': 'white'}),
                dbc.CardBody([
                    dcc.Graph(id='total-passengers-chart', figure=create_total_passengers_chart())
                ])
            ], style={'backgroundColor': '#3d3d3d', 'height': '100%'})
        ], md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Domestic vs International", style={'color': 'white'}),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='passenger-type-dropdown',
                        options=[
                            {'label': 'Domestic Passengers', 'value': 'Domestic Passengers'},
                            {'label': 'International Passengers', 'value': 'International Passengers'}
                        ],
                        value='Domestic Passengers',
                        clearable=False,
                        style={'color': 'black'}
                    ),
                    dcc.Graph(id='passenger-type-chart')
                ])
            ], style={'backgroundColor': '#3d3d3d', 'height': '100%'})
        ], md=6)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Airport Traffic Map", style={'color': 'white'}),
                dbc.CardBody([
                    dcc.Graph(id='airport-map', figure=create_airport_map())
                ])
            ], style={'backgroundColor': '#3d3d3d'})
        ], md=8),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Top Airports", style={'color': 'white'}),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='top-airports-dropdown',
                        options=[
                            {'label': 'Top 5', 'value': 5},
                            {'label': 'Top 10', 'value': 10},
                            {'label': 'Top 20', 'value': 20}
                        ],
                        value=5,
                        clearable=False,
                        style={'color': 'black'}
                    ),
                    html.Div(id='top-airports-table')
                ])
            ], style={'backgroundColor': '#3d3d3d', 'height': '100%'})
        ], md=4)
    ], className="mb-4"),
    

], fluid=True, style={'backgroundColor': '#2d2d2d', 'minHeight': '100vh'})

# Callbacks for interactivity
@app.callback(
    [Output('total-passengers-chart', 'figure'),
     Output('passenger-type-chart', 'figure'),
     Output('airport-map', 'figure')],
    [Input('year-slider', 'value'),
     Input('passenger-type-dropdown', 'value')]
)
def update_charts(selected_years, passenger_type):
    start_year, end_year = selected_years
    years = list(range(start_year, end_year + 1))
    
    # Update charts
    total_passengers = create_total_passengers_chart(years)
    
    if passenger_type == 'domestic':
        passenger_chart = create_domestic_chart(years)
    else:
        passenger_chart = create_international_chart(years)
    
    airport_map = create_airport_map(years)
    
    
    return total_passengers, passenger_chart, airport_map

@app.callback(
    Output('top-airports-table', 'children'),
    [Input('year-slider', 'value'),
     Input('top-airports-dropdown', 'value')]
)
def update_top_airports(selected_years, top_n):
    start_year, end_year = selected_years
    years = list(range(start_year, end_year + 1))
    
    top_airports = df[df['Year'].isin(years)].groupby(['Origin Airport Code', 'Origin City Name'])['Total Passengers'].sum().nlargest(top_n).reset_index()
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Rank"), html.Th("Airport"), html.Th("City"), html.Th("Passengers")])),
        html.Tbody([
            html.Tr([
                html.Td(i+1),
                html.Td(row['Origin Airport Code']),
                html.Td(row['Origin City Name']),
                html.Td(f"{row['Total Passengers']:,.0f}")
            ]) for i, row in top_airports.iterrows()
        ])
    ], bordered=True, hover=True, responsive=True, striped=True, style={'color': 'white'})

if __name__ == '__main__':
    app.run(debug=True)