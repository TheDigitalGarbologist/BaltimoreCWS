import streamlit as st
import folium
import requests
from streamlit_folium import folium_static

# Function to get GeoJSON data from ArcGIS REST service
@st.cache
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

# Create a Streamlit app
st.title('Interactive Map of Baltimore City with Census Tracts')

# Sidebar for selecting census tract
st.sidebar.title("Filter Census Tracts")
tracts = [feature['properties']['CSA2010'] for feature in geojson_data['features']]
selected_tract = st.sidebar.selectbox("Select Census Tract", tracts)

# Define the center of the map
baltimore_coords = [39.2904, -76.6122]

# Create a Folium map centered on Baltimore City
map_baltimore = folium.Map(location=baltimore_coords, zoom_start=12)

# Add a choropleth layer to the map
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=geojson_data,
    columns=["properties.CSA2010", "properties.popchg20"],
    key_on="feature.properties.CSA2010",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Population Change (2020)"
).add_to(map_baltimore)

# Zoom to the selected census tract
selected_geom = next((feature for feature in geojson_data['features'] if feature['properties']['CSA2010'] == selected_tract), None)
if selected_geom:
    centroid = [selected_geom['geometry']['coordinates'][1], selected_geom['geometry']['coordinates'][0]]
    map_baltimore.location = centroid
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
