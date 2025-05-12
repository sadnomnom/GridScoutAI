import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import os
from datetime import datetime

# Set up page layout
st.set_page_config(page_title="GridScoutAI Dashboard", layout="wide")

# Load parcels
@st.cache_data
def load_parcels(path):
    return gpd.read_file(path)

DATA_PATH = "data/GridScout_Final.gpkg"
gdf = load_parcels(DATA_PATH)

# Sidebar
st.sidebar.image("https://i.imgur.com/3ZQ3Z6N.png", width=200)  # Replace with your logo URL if desired
st.sidebar.title("GridScoutAI")
st.sidebar.markdown("Explore and manage high-potential parcels for energy storage or development.")

st.title("📍 GridScoutAI: Camden Parcel Dashboard")

# Sidebar filters
st.sidebar.header("Parcel Filters")
score_min, score_max = int(gdf.SCORE_TOTA.min()), int(gdf.SCORE_TOTA.max())
score_range = st.sidebar.slider("Score Range", score_min, score_max, (score_min, score_max))

valid_only = st.sidebar.checkbox("Only show buildable parcels", value=True)

# Apply filters
filtered = gdf[(gdf.SCORE_TOTA >= score_range[0]) & (gdf.SCORE_TOTA <= score_range[1])]
if valid_only:
    filtered = filtered[filtered["IS_VALID"] == 1]

# Map
st.subheader("🗺️ Map of Candidate Parcels")
if not filtered.empty:
    filtered = filtered.to_crs(epsg=4326)
    filtered["lon"] = filtered.centroid.x
    filtered["lat"] = filtered.centroid.y

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=filtered["lat"].mean(),
            longitude=filtered["lon"].mean(),
            zoom=10,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=filtered,
                get_position='[lon, lat]',
                get_color='[30, 144, 255, 160]',  # Dodger Blue
                get_radius=100,
                pickable=True,
            )
        ],
        tooltip={"text": "Score: {SCORE_TOTA}\nLand Use: {lu23catn}"}
    ))
else:
    st.warning("No parcels match the selected criteria.")

# Table
st.subheader("📋 Parcel Table")
display_cols = filtered[["PAMS_PIN", "SCORE_TOTA", "lu23catn", "IS_VALID"]].copy()
display_cols.rename(columns={"SCORE_TOTA": "Score", "lu23catn": "Land Use", "IS_VALID": "Buildable"}, inplace=True)
display_cols["Score"] = display_cols["Score"].round(0).astype(int)
st.dataframe(display_cols.sort_values("Score", ascending=False))

# Outreach section
st.subheader("📞 Outreach Notes")
with st.form("outreach_form"):
    selected_pin = st.selectbox("Choose Parcel PIN", filtered["PAMS_PIN"].unique())
    contacted = st.radio("Contacted?", ["Yes", "No"])
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Save Outreach Note")
    if submitted:
        st.success(f"✅ Outreach note saved for {selected_pin}!")

        # Save outreach note to CSV
        log_path = "data/outreach_log.csv"
        new_entry = pd.DataFrame([{
            "PAMS_PIN": selected_pin,
            "Contacted": contacted,
            "Notes": notes,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])

        try:
            existing = pd.read_csv(log_path)
            updated = pd.concat([existing, new_entry], ignore_index=True)
        except FileNotFoundError:
            updated = new_entry

        updated.to_csv(log_path, index=False)

# Show existing outreach notes
st.subheader("📂 Outreach Log")
try:
    log_df = pd.read_csv("data/outreach_log.csv")
    st.dataframe(log_df)
except FileNotFoundError:
    st.info("No outreach notes saved yet.")
