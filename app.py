import streamlit as st

# First Streamlit command
st.set_page_config(page_title="MLB Projection Checker", layout="centered")

import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from PIL import Image
from utils import fetch_boxscore, evaluate_projections

# Logo
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
logo = Image.open(logo_path)
st.image(logo, width=300)

# Title
st.title("⚾ MLB Player Projection Checker")
st.markdown("Enter player projections, choose a date, and view live or final results.")

# Initialize projections state
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = []

# Form to add projection
with st.form("manual_input"):
    st.subheader("📝 Add Player Projection")
    player = st.text_input("Player Name")
    metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])
    target = st.number_input("Target", value=1)
    add = st.form_submit_button("Add")

    if add and player and metric:
        st.session_state.manual_projections.append({
            "Player": player,
            "Metric": metric,
            "Target": target
        })

# Display projections with delete buttons inline
st.subheader("📋 Current Projections")
if st.session_state.manual_projections:
    for i, row in enumerate(st.session_state.manual_projections):
        cols = st.columns([4, 3, 2, 1])
        cols[0].markdown(f"**{row['Player']}**")
        cols[1].markdown(row["Metric"])
        cols[2].markdown(str(row["Target"]))
        if cols[3].button("❌", key=f"del_{i}_{row['Player']}"):
            del st.session_state.manual_projections[i]
            st.experimental_set_query_params()  # triggers re-render safely
            break  # Exit loop to avoid index mismatch
else:
    st.markdown("_No players added._")

# Turn into DataFrame for processing
projections_df = pd.DataFrame(st.session_state.manual_projections)

# Date dropdown (last 7 days including today)
recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date = st.selectbox("📅 Choose a game date", date_options)

# Fetch schedule and game IDs
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
response = requests.get(schedule_url)
data = response.json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Loaded {len(game_ids)} game(s) from {selected_date}")

# Results
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
    st.warning("Add at least one player projection to begin.")