import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# --- CONFIG ---
OSRM_CAR_URL = "http://router.project-osrm.org/route/v1/driving/"

TRANSPORT_API_ID = st.secrets["TRANSPORT_API_ID"]
TRANSPORT_API_KEY = st.secrets["TRANSPORT_API_KEY"]

# Known destinations
KNOWN_PLACES = {
    "Saint Pancras, London": (51.5319, -0.1263),
    "Manchester Piccadilly": (53.4773, -2.2304),
    "Birmingham New Street": (52.4778, -1.8983),
    "Edinburgh Waverley": (55.9520, -3.1880),
}

DEST_POSTCODES = {
    "Saint Pancras, London": "N1C 4QP",
    "Manchester Piccadilly": "M1 2WD",
    "Birmingham New Street": "B2 4QA",
    "Edinburgh Waverley": "EH1 1BB",
}

# --- FUNCTIONS ---
def reverse_geocode_postcode(lat, lon):
    """Convert lat/lon to nearest postcode using Nominatim"""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1
    }
    headers = {"User-Agent": "UK-Commute-App"}
    r = requests.get(url, params=params, headers=headers)
    if r.status_code == 200:
        data = r.json()
        return data.get("address", {}).get("postcode")
    return None

def get_car_distance_km(origin, dest):
    coords = f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
    r = requests.get(OSRM_CAR_URL + coords, params={"overview": "false"})
    if r.status_code == 200:
        data = r.json()
        meters = data["routes"][0]["distance"]
        return round(meters / 1000, 2)
    return None

def get_train_journey(origin_postcode, dest_postcode):
    url = f"https://transportapi.com/v3/uk/public/journey/from/{origin_postcode}/to/{dest_postcode}.json"
    params = {
        "app_id": TRANSPORT_API_ID,
        "app_key": TRANSPORT_API_KEY,
        "modes": "train"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        j = r.json()
        return j.get("duration"), j.get("fare", {}).get("total_cost")
    return None, None

# --- SIDEBAR ---
st.sidebar.header("Commute Layers")
show_train = st.sidebar.checkbox("Train journey time & cost", value=True)
show_car = st.sidebar.checkbox("Car distance", value=True)

destinations = st.sidebar.multiselect(
    "Select UK places to compare with:",
    options=list(KNOWN_PLACES.keys()),
    default=["Saint Pancras, London"]
)

# Origin postcode will be auto-filled after click
origin_postcode = None

# --- MAP SETUP (single map only) ---
st.write("Click on the map to select your potential home location.")
uk_center = [54.5, -3.5]
m = folium.Map(location=uk_center, zoom_start=6)

# First map render captures click
map_result = st_folium(m, width=900, height=650, returned_objects=["last_clicked"])

# --- PROCESS CLICK + GEOCODE ---
origin_point = None
if map_result and map_result.get("last_clicked"):
    lat = map_result["last_clicked"]["lat"]
    lon = map_result["last_clicked"]["lng"]
    origin_point = (lat, lon)

    # Get nearest postcode
    origin_postcode = reverse_geocode_postcode(lat, lon)
    origin_postcode = origin_postcode.replace(" ", "") if origin_postcode else None

    folium.Marker(origin_point, popup=f"Home ({origin_postcode or 'no postcode'})").add_to(m)

# --- FETCH + DRAW ROUTES ON SAME MAP ---
if origin_point and destinations and origin_postcode:
    for place in destinations:
        dest_coords = KNOWN_PLACES[place]
        folium.Marker(dest_coords, popup=place).add_to(m)

        if show_car:
            car_km = get_car_distance_km(origin_point, dest_coords)
            if car_km:
                folium.PolyLine(
                    [origin_point, dest_coords],
                    tooltip=f"🚗 {car_km} km to {place}"
                ).add_to(m)

        if show_train:
            duration, cost_p = get_train_journey(origin_postcode, DEST_POSTCODES[place])
            if duration:
                cost_str = f"£{cost_p/100:.2f}" if cost_p else "£?"
                folium.PolyLine(
                    [origin_point, dest_coords],
                    tooltip=f"🚆 {duration} min · {cost_str} to {place}"
                ).add_to(m)

# --- FINAL: render the same map (only once) ---
st_folium(m, width=900, height=650)

# --- DEBUG INFO BELOW MAP ---
if origin_point:
    st.write("📌 Click origin:", origin_point)
if origin_postcode:
    st.write("🏤 Nearest postcode:", origin_postcode)
