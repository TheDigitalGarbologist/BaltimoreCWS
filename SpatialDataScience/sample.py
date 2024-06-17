import streamlit as st
import pydeck as pdk
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
from streamlit.components.v1 import html

# Function to get GeoJSON data from ArcGIS REST service
@st.cache_data
def get_geojson():
    url = "https://services1.arcgis.com/mVFRs7NF4iFitgbY/ArcGIS/rest/services/Wrkout/FeatureServer/0/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

geojson_data = get_geojson()

# Extracting the relevant data for the choropleth layer
data = pd.json_normalize(geojson_data['features'])
data['CSA2020'] = data['properties.CSA2020']
data['wrkout20'] = data['properties.wrkout20']

# Initialize session state for selected tract
if 'selected_tract' not in st.session_state:
    st.session_state.selected_tract = 'All'

# Create a Streamlit app
st.title("Interactive Map of Baltimore City")

# Sidebar for selecting community statistical area
st.sidebar.title("Filter Community Statistical Area")
tracts = ['All'] + list(data['CSA2020'].unique())
selected_tract = st.sidebar.selectbox("Select Community Statistical Area", tracts, index=0)
st.session_state.selected_tract = selected_tract

# Define opacity settings
fill_opacity = 0.75
marker_line_opacity = 1.0

# Inferno color ramp
color_ramp = plt.cm.inferno

def get_color(value, min_val, max_val):
    normalized_value = (value - min_val) / (max_val - min_val)
    color = color_ramp(normalized_value)
    return [int(c * 255) for c in color[:3]]

# Apply colors to data
min_val = data['wrkout20'].min()
max_val = data['wrkout20'].max()
data['fill_color'] = data['wrkout20'].apply(lambda x: get_color(x, min_val, max_val))

# Convert fill_color to the appropriate format for pydeck
data['fill_color'] = data['fill_color'].apply(lambda x: [x[0], x[1], x[2]])

# Create pydeck layer
layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_data,
    pickable=True,
    stroked=True,
    filled=True,
    get_fill_color="properties.fill_color",
    get_line_color=[0, 0, 0, int(marker_line_opacity * 255)],
    get_line_width=1,
)

# Set the initial view state
view_state = pdk.ViewState(
    latitude=39.2904,
    longitude=-76.6122,
    zoom=10,
    bearing=0,
    pitch=0
)

# Create the deck.gl map
r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/dark-v10",
    tooltip={"text": "{CSA2020}\n{wrkout20}% of residents work outside the city"},
)

# Create the legend with Matplotlib
fig, ax = plt.subplots(figsize=(6, 1))
fig.subplots_adjust(bottom=0.5)

norm = plt.Normalize(vmin=min_val, vmax=max_val)
cb = fig.colorbar(
    plt.cm.ScalarMappable(cmap=color_ramp, norm=norm),
    cax=ax,
    orientation='horizontal',
    label='% of residents work outside the city'
)

# Save the legend as an image
fig.savefig("legend.png")

# Layout with columns for legend and map
col1, col2 = st.columns([1, 4])

with col1:
    st.image("legend.png")

with col2:
    st.pydeck_chart(r)
