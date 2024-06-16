import streamlit as st
import pydeck as pdk
import requests
import pandas as pd

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

# Create a Streamlit app
st.title("Interactive Map of Baltimore City")

# Sidebar for selecting community statistical area
st.sidebar.title("Filter Community Statistical Area")
tracts = ['All'] + list(data['CSA2020'].unique())
selected_tract = st.sidebar.selectbox("Select Community Statistical Area", tracts, index=0)

# Prepare the layers for PyDeck
layers = []

# Add a GeoJsonLayer for the choropleth
choropleth_layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_data,
    pickable=True,
    stroked=True,
    filled=True,
    extruded=False,
    wireframe=True,
    get_fill_color="[255, 255, properties.wrkout20 * 5]",
    get_line_color=[0, 0, 0],
    get_line_width=1,
)

layers.append(choropleth_layer)

# Highlight the selected community statistical area
if selected_tract != 'All':
    selected_geom = next((feature for feature in geojson_data['features'] if feature['properties']['CSA2020'] == selected_tract), None)
    if selected_geom:
        highlight_layer = pdk.Layer(
            "GeoJsonLayer",
            selected_geom,
            pickable=True,
            stroked=True,
            filled=True,
            extruded=False,
            wireframe=True,
            get_fill_color=[255, 175, 0, 160],
            get_line_color=[255, 175, 0],
            get_line_width=2,
        )
        layers.append(highlight_layer)

# Set the initial view state
view_state = pdk.ViewState(
    latitude=39.2904,  # Centered on Baltimore City
    longitude=-76.6122,
    zoom=11,
    pitch=0,
)

# Create the deck.gl map
deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    tooltip={"text": "{CSA2020}\n{wrkout20}% of residents work outside the city"},
)

# Display the map in the Streamlit app
st.pydeck_chart(deck)
