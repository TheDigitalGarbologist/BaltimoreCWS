import streamlit as st
import folium
from streamlit_folium import folium_static
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

# Prepare color ramp (blue chromatic scale)
color_ramp = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c']

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

# Create a folium map with Esri hybrid imagery tiles
m = folium.Map(location=[39.2904, -76.6122], zoom_start=11, scrollWheelZoom=False)

# Add Esri Imagery tile layer
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Tiles © Esri',
    name='Esri Imagery',
    overlay=False,
    control=True
).add_to(m)

# Add choropleth layer
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=data,
    columns=["CSA2020", "wrkout20"],
    key_on="feature.properties.CSA2020",
    fill_color="Blues",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Percent of Employed Residents who Work Outside the City"
).add_to(m)

# Highlight the selected community statistical area
if st.session_state.selected_tract != 'All':
    selected_geom = next((feature for feature in geojson_data['features'] if feature['properties']['CSA2020'] == st.session_state.selected_tract), None)
    if selected_geom:
        folium.GeoJson(
            selected_geom,
            name="highlight",
            style_function=lambda x: {
                "fillColor": "#ffaf00",
                "color": "#ffaf00",
                "weight": 2,
                "fillOpacity": 0.6,
            },
        ).add_to(m)

# Add Esri World Imagery Labels tile layer last to appear above the choropleth
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    attr='Labels © Esri',
    name='Esri World Imagery Labels',
    overlay=True,
    control=True
).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Display the map
folium_static(m)

# Create a map legend
st.markdown("""
<div style="position: fixed; 
     bottom: 50px; left: 50px; width: 200px; 
     background: white; z-index: 1000; padding: 10px; 
     border: 2px solid grey; border-radius: 5px;">
    <h4>Legend</h4>
    <i style="background: #f7fbff; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 0 - 10%<br>
    <i style="background: #deebf7; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 10 - 20%<br>
    <i style="background: #c6dbef; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 20 - 30%<br>
    <i style="background: #9ecae1; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 30 - 40%<br>
    <i style="background: #6baed6; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 40 - 50%<br>
    <i style="background: #3182bd; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 50 - 60%<br>
    <i style="background: #08519c; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 60 - 70%<br>
</div>
""", unsafe_allow_html=True)
