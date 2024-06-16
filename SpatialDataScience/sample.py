import streamlit as st
import folium
import geopandas as gpd
from streamlit_folium import folium_static

# Load the census tract data
@st.cache
def load_data():
    url = "https://opendata.arcgis.com/datasets/f4382ed86362467cac404fe7a77bf3a5_0.geojson"
    return gpd.read_file(url)

census_data = load_data()

# Create a Streamlit app
st.title('Interactive Map of Baltimore City with Census Tracts')

# Sidebar for selecting census tract
st.sidebar.title("Filter Census Tracts")
tracts = census_data['TRACTCE'].unique()
selected_tract = st.sidebar.selectbox("Select Census Tract", tracts)

# Define the center of the map
baltimore_coords = [39.2904, -76.6122]

# Create a Folium map centered on Baltimore City
map_baltimore = folium.Map(location=baltimore_coords, zoom_start=12)

# Add a choropleth layer to the map
folium.Choropleth(
    geo_data=census_data,
    name="choropleth",
    data=census_data,
    columns=["TRACTCE", "POPULATION"],
    key_on="feature.properties.TRACTCE",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Population"
).add_to(map_baltimore)

# Zoom to the selected census tract
selected_geom = census_data[census_data['TRACTCE'] == selected_tract]
if not selected_geom.empty:
    centroid = selected_geom.geometry.centroid.iloc[0]
    map_baltimore.location = [centroid.y, centroid.x]
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
