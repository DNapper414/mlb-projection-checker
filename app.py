import streamlit as st

# Must be first
st.set_page_config(page_title="MLB Projection Checker", layout="centered")

import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from PIL import Image
from utils import fetch_boxscore, evaluate_projections

# 🖼️ Logo
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
logo = Image.open(logo_path)
st.image(logo, width=300)

# 🏷️ Title
st.title("⚾ MLB Player Projection Checker")
st.markdown("Enter your projections, select a date, and view results from live or recent MLB games.")

# Initialize state
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = []

# 📝 Projection Form
with st.form("manual_input"):
    st.subheader("📝 Add Player Projection")
    player = st.text_input("Player Name (e.g. Aaron Judge)")
    metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])
    target = st.number_input("Target", value=1)
    submitted = st.form_submit_button("Add to Table")

    if submitted and player and metric:
        st.session_state.manual_projections.append({
            "Player": player,
            "Metric": metric,
            "Target": target
        })

# 📋 Show entered projections
st.subheader("📋 Current Projections")
if st.session_state.manual_projections:
    projections_df = pd.DataFrame(st.session_state.manual_projections)
    st.dataframe(projections_df)
else:
    st.markdown("_No player projections added yet._")
    projections_df = pd.DataFrame()

# 📅 Game date selector (dropdown)
recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date = st.selectbox("📅 Choose a game date", date_options)

# 🔁 Fetch game data for selected date
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
response = requests.get(schedule_url)
data = response.json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Found {len(game_ids)} game(s) for {selected_date}")

# 📊 Results table
if not projections_df.empty:
    st.subheader("📊 Results")
    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]

    results = evaluate_projections(projections_df, boxscores)
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv, file_name="results.csv", mime="text/csv")
else:
    st.warning("Please add at least one projection to view results.")