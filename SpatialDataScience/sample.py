import streamlit as st
import folium
from streamlit_folium import folium_static

# Create a Streamlit app
st.title('Interactive Map of Baltimore City')

# Define the center of the map
baltimore_coords = [39.2904, -76.6122]

# Create a Folium map centered on Baltimore City
map_baltimore = folium.Map(location=baltimore_coords, zoom_start=12)

# Add a marker for the center of Baltimore City
folium.Marker(baltimore_coords, popup='Baltimore City Center').add_to(map_baltimore)

# Display the map in the Streamlit app
folium_static(map_baltimore)

# Add additional interactive elements if needed
st.sidebar.title("Interactive Elements")
st.sidebar.markdown("Use the sidebar to add more features to the map.")


