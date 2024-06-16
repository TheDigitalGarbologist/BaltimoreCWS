import streamlit as st
import folium
import requests
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd

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

# Convert GeoJSON to GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

# Calculate the centroid of the entire GeoDataFrame
centroid = gdf.geometry.centroid.unary_union.centroid

# Create a Folium map centered on Baltimore City
map_baltimore = folium.Map(location=(centroid.y, centroid.x), zoom_start=11)

# Add a choropleth layer to the map
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=data,
    columns=["CSA2020", "wrkout20"],
    key_on="feature.properties.CSA2020",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Percent of Employed Residents who Work Outside the City"
).add_to(map_baltimore)

# Apply zoom and highlight only if a specific community statistical area is selected
if selected_tract != 'All':
    selected_geom = next((feature for feature in geojson_data['features'] if feature['properties']['CSA2020'] == selected_tract), None)
    if selected_geom:
        # Calculate the centroid for zooming
        selected_gdf = gpd.GeoDataFrame.from_features([selected_geom])
        selected_centroid = selected_gdf.geometry.centroid.unary_union.centroid
        
        map_baltimore.location = [selected_centroid.y, selected_centroid.x]
        map_baltimore.zoom_start = 14

        # Highlight the selected community statistical area
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
