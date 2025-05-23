import streamlit as st

# ✅ Must be the first Streamlit command
st.set_page_config(page_title="MLB Projection Checker", layout="centered")

import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from PIL import Image
from utils import fetch_boxscore, evaluate_projections

# 🖼️ Load and display logo
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
logo = Image.open(logo_path)
st.image(logo, width=300)

# 🏷️ Title
st.title("⚾ MLB Player Projection Checker")
st.markdown("Enter player prop projections and select a date to check results (live or completed games).")

# 📝 Manual Projections
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = []

with st.form("manual_input"):
    st.subheader("📝 Add Player Projection")
    player = st.text_input("Player Name (e.g. Aaron Judge)")
    metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])
    target = st.number_input("Target Value", value=1)
    submitted = st.form_submit_button("Add to Table")

    if submitted and player and metric:
        st.session_state.manual_projections.append({
            "Player": player,
            "Metric": metric,
            "Target": target
        })

# 🚮 Show and manage current projections
st.subheader("📋 Current Projections")

for i, row in enumerate(st.session_state.manual_projections):
    col1, col2, col3, col4, col5 = st.columns([4, 3, 2, 1, 1])
    col1.write(row["Player"])
    col2.write(row["Metric"])
    col3.write(str(row["Target"]))
    if col4.button("❌", key=f"delete_{i}"):
        st.session_state.manual_projections.pop(i)
        st.experimental_rerun()

projections_df = pd.DataFrame(st.session_state.manual_projections)

# 📅 Select a game date (today + past 6 days)
recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date_str = st.selectbox("📅 Choose a game date", date_options)

# 🔄 Fetch all game IDs (Final OR In Progress)
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date_str}"
response = requests.get(schedule_url)
data = response.json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Loading {len(game_ids)} game(s) from {selected_date_str}")

# 📊 Stat comparison and results
if not projections_df.empty:
    st.subheader("📊 Results")
    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]

    results = evaluate_projections(projections_df, boxscores)
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results as CSV", data=csv, file_name="projection_results.csv", mime="text/csv")
else:
    st.warning("Enter at least one player projection to begin.")