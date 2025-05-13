import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
from pathlib import Path
from datetime import datetime

# ----------------------------------------------------------------------------
# Resolve paths (works locally & on Streamlit Cloud)
# ----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / "data" / "GridScout_Final.gpkg"
LOG_PATH = SCRIPT_DIR / "data" / "outreach_log.csv"

# ----------------------------------------------------------------------------
# Streamlit config
# ----------------------------------------------------------------------------
st.set_page_config(page_title="GridScoutAI Dashboard", layout="wide")

# ----------------------------------------------------------------------------
# Load data (cached)
# ----------------------------------------------------------------------------
@st.cache_data
def load_parcels(path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path)

gdf = load_parcels(DATA_PATH)

# ----------------------------------------------------------------------------
# Sidebar – logo & filters
# ----------------------------------------------------------------------------
st.sidebar.image("https://i.imgur.com/3ZQ3Z6N.png", width=180)
st.sidebar.title("GridScout AI")
st.sidebar.write("Camden County demo – score & filter parcels for clean‑energy siting.")

score_min, score_max = int(gdf.SCORE_TOTA.min()), int(gdf.SCORE_TOTA.max())
score_range = st.sidebar.slider("Score range", score_min, score_max, (score_min, score_max))
only_buildable = st.sidebar.checkbox("Buildable only (IS_VALID = 1)", value=True)

# ----------------------------------------------------------------------------
# Filter dataframe
# ----------------------------------------------------------------------------
filtered = gdf.query("@score_range[0] <= SCORE_TOTA <= @score_range[1]")
if only_buildable:
    filtered = filtered[filtered.IS_VALID == 1]

# ----------------------------------------------------------------------------
# Main title
# ----------------------------------------------------------------------------
st.title("📍 GridScoutAI – Camden Parcel Dashboard")

# ----------------------------------------------------------------------------
# Map view
# ----------------------------------------------------------------------------
st.subheader("🗺️ Candidate parcels map")
if filtered.empty:
    st.warning("No parcels match current filters.")
else:
    filtered4326 = filtered.to_crs(epsg=4326)
    filtered4326["lon"] = filtered4326.geometry.centroid.x
    filtered4326["lat"] = filtered4326.geometry.centroid.y

    # Dynamic zoom: closer if few features
    zoom_lvl = 11 if len(filtered4326) < 200 else 10

    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=filtered4326.lat.mean(),
                longitude=filtered4326.lon.mean(),
                zoom=zoom_lvl,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=filtered4326,
                    get_position="[lon, lat]",
                    # Score‑based color ramp (red low → green high)
                    get_color="""
                        [
                          (255 - (SCORE_TOTA * 12)) > 0 ? (255 - (SCORE_TOTA * 12)) : 0,
                          (SCORE_TOTA * 12) < 255 ? (SCORE_TOTA * 12) : 255,
                          60,
                          160
                        ]
                    """,
                    get_radius=120,
                    pickable=True,
                )
            ],
            tooltip={"text": "PIN: {PAMS_PIN}\nScore: {SCORE_TOTA}\nLand Use: {lu23catn}"},
        )
    )

# ----------------------------------------------------------------------------
# Parcel table + CSV download
# ----------------------------------------------------------------------------
st.subheader("📋 Parcel table")
show_cols = (
    filtered[["PAMS_PIN", "SCORE_TOTA", "lu23catn", "IS_VALID"]]
    .rename(columns={"SCORE_TOTA": "Score", "lu23catn": "Land Use", "IS_VALID": "Buildable"})
    .sort_values("Score", ascending=False)
)
st.dataframe(show_cols, use_container_width=True)

csv_bytes = show_cols.to_csv(index=False).encode()
st.download_button("Download filtered CSV", csv_bytes, "gridscout_filtered.csv", mime="text/csv")

# ----------------------------------------------------------------------------
# Outreach form
# ----------------------------------------------------------------------------
st.subheader("📞 Outreach notes")
if filtered.empty:
    st.info("Filter some parcels first to add notes.")
else:
    with st.form("outreach_form"):
        pin = st.selectbox("Parcel PIN", filtered.PAMS_PIN.unique())
        contacted = st.radio("Contacted?", ["Yes", "No"], horizontal=True)
        note = st.text_area("Notes")
        if st.form_submit_button("Save"):
            entry = pd.DataFrame([
                {
                    "PAMS_PIN": pin,
                    "Contacted": contacted,
                    "Notes": note,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ])
            if LOG_PATH.exists():
                existing = pd.read_csv(LOG_PATH)
                log = pd.concat([existing, entry], ignore_index=True)
            else:
                LOG_PATH.parent.mkdir(exist_ok=True)
                log = entry
            log.to_csv(LOG_PATH, index=False)
            st.success("Note saved ✅")

# ----------------------------------------------------------------------------
# Outreach log display
# ----------------------------------------------------------------------------
st.subheader("📂 Outreach log")
if LOG_PATH.exists():
    st.dataframe(pd.read_csv(LOG_PATH), use_container_width=True)
else:
    st.info("No outreach notes yet.")
