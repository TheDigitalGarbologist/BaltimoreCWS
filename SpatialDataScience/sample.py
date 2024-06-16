import streamlit as st
import pydeck as pdk
import requests
import pandas as pd
import colorbrewer

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

# Layer toggles
show_choropleth = st.sidebar.checkbox("Show Choropleth Layer", value=True)
show_highlight = st.sidebar.checkbox("Show Highlight Layer", value=True)

# Prepare color ramp (blue chromatic scale)
color_ramp = colorbrewer.Blues[7]  # Using a 7-class Blues color ramp

# Function to map values to color ramp
def map_to_color(value, min_val, max_val, color_ramp):
    color_index = int((value - min_val) / (max_val - min_val) * (len(color_ramp) - 1))
    return color_ramp[color_index]

# Calculate min and max values for the color mapping
min_val = data['wrkout20'].min()
max_val = data['wrkout20'].max()

# Add color to each feature in the geojson data
for feature in geojson_data['features']:
    value = feature['properties']['wrkout20']
    feature['properties']['fill_color'] = map_to_color(value, min_val, max_val, color_ramp)

# Prepare the layers for PyDeck
layers = []

# Add a GeoJsonLayer for the choropleth
if show_choropleth:
    choropleth_layer = pdk.Layer(
        "GeoJsonLayer",
        geojson_data,
        pickable=True,
        stroked=True,
        filled=True,
        extruded=False,
        wireframe=True,
        get_fill_color="[properties.fill_color[0], properties.fill_color[1], properties.fill_color[2], 200]",  # 33% transparency
        get_line_color=[0, 0, 0],
        get_line_width=1,
    )
    layers.append(choropleth_layer)

# Highlight the selected community statistical area
if selected_tract != 'All' and show_highlight:
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
    zoom=10,
    pitch=30,
)

# Create the deck.gl map with satellite basemap and labels
deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style='mapbox://styles/mapbox/satellite-streets-v11',
    tooltip={"text": "{CSA2020}\n{wrkout20}% of residents work outside the city"},
)

# Display the map in the Streamlit app
st.pydeck_chart(deck)

# Create a map legend
st.markdown("""
<style>
.map-legend {
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 1000;
    background: white;
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
}
.map-legend h4 {
    margin: 0;
    font-size: 14px;
    font-weight: bold;
}
.map-legend div {
    display: flex;
    align-items: center;
    margin-top: 5px;
}
.map-legend span {
    width: 20px;
    height: 20px;
    display: block;
    margin-right: 5px;
    border: 1px solid #000;
}
</style>
<div class="map-legend">
    <h4>Legend</h4>
    <div><span style="background-color: #f7fbff"></span>0 - 10%</div>
    <div><span style="background-color: #deebf7"></span>10 - 20%</div>
    <div><span style="background-color: #c6dbef"></span>20 - 30%</div>
    <div><span style="background-color: #9ecae1"></span>30 - 40%</div>
    <div><span style="background-color: #6baed6"></span>40 - 50%</div>
    <div><span style="background-color: #3182bd"></span>50 - 60%</div>
    <div><span style="background-color: #08519c"></span>60 - 70%</div>
</div>
""", unsafe_allow_html=True)
