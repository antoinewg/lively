import streamlit as st
import folium
from streamlit_folium import st_folium

st.write(f"Hello world {st.secrets['DB_USERNAME']}")

# Create a folium map centered on the UK
uk_center = [54.5, -3.5]
m = folium.Map(location=uk_center, zoom_start=6)

# Example marker
folium.Marker([51.5074, -0.1278], popup="London").add_to(m)

# Display using streamlit-folium
st_folium(m, width=800, height=600)
