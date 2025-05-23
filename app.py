import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
from PIL import Image
from utils import fetch_boxscore, evaluate_projections

# Set Streamlit page config
st.set_page_config(page_title="MLB Projection Checker", layout="centered")

# Path to the temporary file
PROJECTION_FILE = "projections.json"

# -----------------------------
# Helpers to read/write storage
# -----------------------------

def load_projections():
    if os.path.exists(PROJECTION_FILE):
        with open(PROJECTION_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_projections(projections):
    with open(PROJECTION_FILE, "w") as f:
        json.dump(projections, f)

# -------------------------------
# Restore state from local file
# -------------------------------

if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = load_projections()

# -----------------
# Logo and Title
# -----------------

logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
logo = Image.open(logo_path)
st.image(logo, use_container_width=True)

st.title("⚾ MLB Player Projection Checker")
st.markdown("Enter player projections, choose a game date, and compare results with real MLB stats.")

# -------------------------
# Projection Entry Form
# -------------------------

with st.form("manual_input"):
    st.subheader("📝 Add Player Projection")
    player = st.text_input("Player Name (e.g. Aaron Judge)")
    metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])
    target = st.number_input("Target", value=1)
    submitted = st.form_submit_button("Add")

    if submitted and player and metric:
        st.session_state.manual_projections.append({
            "Player": player,
            "Metric": metric,
            "Target": target
        })
        save_projections(st.session_state.manual_projections)
        st.rerun()

# -------------------------
# Game Date Dropdown
# -------------------------

recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date = st.selectbox("📅 Choose a game date", date_options)

# -------------------------
# Load Game IDs
# -------------------------

schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
data = requests.get(schedule_url).json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Loaded {len(game_ids)} game(s) for {selected_date}")

# -------------------------
# Results
# -------------------------

projections_df = pd.DataFrame(st.session_state.manual_projections)

if not projections_df.empty:
    st.subheader("📊 Results")

    if st.button("🧹 Clear All Projections"):
        st.session_state.manual_projections = []
        save_projections([])
        st.rerun()

    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]

    results = evaluate_projections(projections_df, boxscores)

    if results:
        header = st.columns(6)
        header[0].markdown("**Player**")
        header[1].markdown("**Metric**")
        header[2].markdown("**Target**")
        header[3].markdown("**Actual**")
        header[4].markdown("**Met?**")
        header[5].markdown("**Remove Player**")

        for i, row in enumerate(results):
            cols = st.columns(6)
            cols[0].markdown(row["Player"])
            cols[1].markdown(row["Metric"])
            cols[2].markdown(f"🎯 {row['Target']}")
            cols[3].markdown(f"📊 {row['Actual']}")
            cols[4].markdown(row["✅ Met?"])
            if cols[5].button("❌", key=f"delete_{i}"):
                st.session_state.manual_projections.pop(i)
                save_projections(st.session_state.manual_projections)
                st.rerun()

        df_clean = pd.DataFrame(results)
        csv = df_clean.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results CSV", data=csv, file_name="results.csv", mime="text/csv")

    else:
        st.info("No results available.")
else:
    st.warning("Please enter at least one projection to begin.")