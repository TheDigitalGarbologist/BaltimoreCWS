import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests

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

# Create customized color scale with defined opacity
color_ramp = [
    [0, f'rgba(247, 251, 255, {fill_opacity})'],
    [0.1, f'rgba(222, 235, 247, {fill_opacity})'],
    [0.2, f'rgba(198, 219, 239, {fill_opacity})'],
    [0.3, f'rgba(158, 202, 225, {fill_opacity})'],
    [0.4, f'rgba(107, 174, 214, {fill_opacity})'],
    [0.5, f'rgba(66, 146, 198, {fill_opacity})'],
    [0.6, f'rgba(33, 113, 181, {fill_opacity})'],
    [0.7, f'rgba(8, 81, 156, {fill_opacity})'],
    [0.8, f'rgba(8, 48, 107, {fill_opacity})'],
    [1, f'rgba(3, 19, 43, {fill_opacity})']
]

# Create Plotly map
fig = go.Figure(
    go.Choroplethmapbox(
        geojson=geojson_data,
        featureidkey='properties.CSA2020',
        locations=data['CSA2020'],
        z=data['wrkout20'],
        colorscale=color_ramp,
        zauto=True,
        showscale=True,
        marker_line_width=0.5,
        marker_line_color=f'rgba(0, 0, 0, {marker_line_opacity})'
    )
)

# Highlight the selected community statistical area
if st.session_state.selected_tract != 'All':
    try:
        selected_geom = next((feature for feature in geojson_data['features'] if feature['properties']['CSA2020'] == st.session_state.selected_tract), None)
        if selected_geom:
            selected_layer = go.Choroplethmapbox(
                geojson=geojson_data,
                locations=[st.session_state.selected_tract],
                z=[selected_geom['properties']['wrkout20']],
                colorscale=[[0, f'rgba(255, 175, 0, {fill_opacity})'], [1, f'rgba(255, 175, 0, {fill_opacity})']],
                showscale=False,
                marker_line_width=3,
                marker_line_color=f'rgba(255, 175, 0, {marker_line_opacity})',
                featureidkey='properties.CSA2020'
            )
            fig.add_trace(selected_layer)
    except Exception as e:
        st.error(f"Error highlighting selected tract: {e}")

# Update layout for the map
fig.update_layout(
    mapbox_style="carto-darkmatter",
    mapbox_zoom=10,
    mapbox_center={"lat": 39.2904, "lon": -76.6122},
    margin={"r":0,"t":0,"l":0,"b":0},
    coloraxis_colorbar={
        'title': {'text': 'Percent of Employed<br>Residents who Work<br>Outside the City', 'side': 'right'},
        'tickvals': [0, 10, 20, 30, 40, 50, 60, 70],
        'ticktext': ['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%']
    }
)

# Display the map in the Streamlit app
st.plotly_chart(fig, use_container_width=True)
