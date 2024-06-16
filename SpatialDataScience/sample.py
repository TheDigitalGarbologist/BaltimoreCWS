import streamlit as st
import folium
import requests
from streamlit_folium import folium_static
import pandas as pd

# Function to get GeoJSON data from ArcGIS REST service
@st.cache_data
def get_geojson():
    url = "https://services1.arcgis.com/mVFRs7NF4iFitgbY/ArcGIS/rest/services/Popchg/FeatureServer/0/query"
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
data['CSA2010'] = data['properties.CSA2010']
data['popchg20'] = data['properties.popchg20']

# Create a Streamlit app
st.title('Interactive Map of Baltimore City")

# Sidebar for selecting census tract
st.sidebar.title("Filter Census Tracts")
tracts = data['CSA2010'].unique()
selected_tract = st.sidebar.selectbox("Select Census Tract", tracts)

# Define the center of the map
baltimore_coords = [39.2904, -76.6122]

# Create a Folium map centered on Baltimore City
map_baltimore = folium.Map(location=baltimore_coords, zoom_start=10)

# Add a choropleth layer to the map
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=data,
    columns=["CSA2010", "popchg20"],
    key_on="feature.properties.CSA2010",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Population Change (2020)"
).add_to(map_baltimore)

# Zoom to the selected census tract
selected_geom = next((feature for feature in geojson_data['features'] if feature['properties']['CSA2010'] == selected_tract), None)
if selected_geom:
    centroid = selected_geom['geometry']['coordinates'][0][0]  # Correctly extract the centroid
    map_baltimore.location = [centroid[1], centroid[0]]
    map_baltimore.zoom_start = 14

    # Highlight the selected census tract
    folium.GeoJson(
        selected_geom,
        style_function=lambda x: {
            "fillColor": "#ffaf00",
            "color": "#ffaf00",
            "weight": 2,
            "fillOpacity": 0.6,
        },
    ).add_to(map_baltimore)

# Display the map in the Streamlit app
folium_static(map_baltimore)
