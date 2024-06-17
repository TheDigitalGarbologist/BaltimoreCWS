import streamlit as st
import pydeck as pdk
import pandas as pd
import requests
import jinja2
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

# Sidebar for selecting community statistical area and color ramp
st.sidebar.title("Map Settings")
tracts = ['All'] + list(data['CSA2020'].unique())
selected_tract = st.sidebar.selectbox("Select Community Statistical Area", tracts, index=0)
st.session_state.selected_tract = selected_tract

# Color ramp options
color_ramps = {
    'Blues': 'Blues',
    'Viridis': 'Viridis',
    'Cividis': 'Cividis',
    'Inferno': 'Inferno',
    'Magma': 'Magma',
    'Plasma': 'Plasma'
}
selected_color_ramp = st.sidebar.selectbox("Select Color Ramp", list(color_ramps.keys()), index=0)

# Define opacity settings
fill_opacity = 0.75
marker_line_opacity = 1.0

# Generate color map for pydeck layer
color_maps = {
    'Blues': [[240, 249, 232], [204, 235, 197], [168, 221, 181], [123, 204, 196], [78, 179, 211], [43, 140, 190], [8, 88, 158]],
    'Viridis': [[253, 231, 37], [94, 201, 98], [33, 145, 140], [59, 82, 139], [68, 1, 84]],
    'Cividis': [[255, 233, 0], [204, 189, 0], [158, 148, 0], [112, 107, 0], [79, 56, 60]],
    'Inferno': [[0, 0, 4], [31, 12, 72], [85, 15, 109], [136, 34, 106], [186, 54, 85], [227, 89, 51], [249, 140, 10], [252, 208, 62], [252, 255, 164]],
    'Magma': [[0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129], [181, 54, 122], [229, 80, 100], [255, 124, 67], [253, 184, 99], [252, 253, 191]],
    'Plasma': [[12, 7, 134], [126, 3, 167], [197, 27, 138], [239, 60, 77], [250, 136, 20], [247, 233, 33]]
}

def get_color(value, min_val, max_val, color_map):
    color_idx = int((value - min_val) / (max_val - min_val) * (len(color_map) - 1))
    return color_map[color_idx]

data['color'] = data['wrkout20'].apply(get_color, args=(data['wrkout20'].min(), data['wrkout20'].max(), color_maps[selected_color_ramp]))

# Create pydeck layer
layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_data,
    pickable=True,
    stroked=True,
    filled=True,
    get_fill_color="color",
    get_line_color=[0, 0, 0],
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

# Display the map in the Streamlit app
st.pydeck_chart(r)

# Function to create HTML legend
def create_legend(labels: list) -> str:
    """Creates an HTML legend from a list dictionary of the format {'text': str, 'color': [r, g, b]}"""
    labels = list(labels)
    for label in labels:
        assert label['color'] and label['text']
        assert len(label['color']) in (3, 4)
        label['color'] = ', '.join([str(c) for c in label['color']])
    legend_template = jinja2.Template('''
    <style>
      .legend {
        width: 150px;
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
      }
      .legend .square {
        height: 10px;
        width: 10px;
        border: 1px solid grey;
      }
      .legend .left {
        float: left;
        margin-right: 10px;
      }
      .legend .right {
        float: right;
      }
      .legend .clear {
        clear: both;
      }
    </style>
    <div class='legend'>
      <h4>Legend</h4>
      {% for label in labels %}
      <div>
        <div class="square left" style="background:rgba({{ label['color'] }})"></div>
        <span class="right">{{label['text']}}</span>
        <div class="clear"></div>
      </div>
      {% endfor %}
    </div>
    ''')
    html_str = legend_template.render(labels=labels)
    return html_str

# Create the legend labels
min_val = data['wrkout20'].min()
max_val = data['wrkout20'].max()
steps = len(color_maps[selected_color_ramp])
legend_labels = []
for i in range(steps):
    value = min_val + (max_val - min_val) * (i / steps)
    color = get_color(value, min_val, max_val, color_maps[selected_color_ramp])
    legend_labels.append({'text': f'{value:.1f}', 'color': color})

# Create and display the legend
legend_html = create_legend(legend_labels)
html(legend_html)
