import streamlit as st
import geopandas as gpd
from pathlib import Path

st.set_page_config(layout="wide")
st.title("🗺️ GridScoutAI Dashboard")

# Set data directory
DATA_DIR = Path(__file__).resolve().parent / "data"

# Find all scored GeoPackages
gpkg_files = sorted(DATA_DIR.glob("*_scored.gpkg"))
county_names = [f.stem.replace("_scored", "").capitalize() for f in gpkg_files]
county_map = dict(zip(county_names, gpkg_files))

# Sidebar selector
county = st.sidebar.selectbox("Select County", county_names)
selected_file = county_map[county]

# Load data
@st.cache_data
def load_data(path):
    return gpd.read_file(path)

gdf = load_data(selected_file)

# Show stats
st.subheader(f"🏞️ {county} County Parcels")
st.markdown(f"**Total parcels:** {len(gdf):,}")
st.markdown(f"**High scoring (≥12):** {(gdf['SCORE_TOTA'] >= 12).sum():,}")

# Show interactive table
st.dataframe(
    gdf[["SCORE_TOTA", "IS_VALID", "SCORE_ENV", "SCORE_GRID"]].sort_values("SCORE_TOTA", ascending=False),
    use_container_width=True
)

# Map
st.map(gdf[gdf["SCORE_TOTA"] >= 12], size=5)
