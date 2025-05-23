import streamlit as st

# Set page config first
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
st.image(logo, use_container_width=True)

# Title and instructions
st.title("⚾ MLB Player Projection Checker")
st.markdown("Enter player projections, choose a game date, and compare results to real MLB stats.")

# ✅ Session state for projections
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = []

# 📝 Manual projection form
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

# 📅 Select game date
recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date = st.selectbox("📅 Choose a game date", date_options)

# 🔄 Load game IDs
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
response = requests.get(schedule_url)
data = response.json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Loaded {len(game_ids)} game(s) for {selected_date}")

# 📊 Results logic
projections_df = pd.DataFrame(st.session_state.manual_projections)

if not projections_df.empty:
    st.subheader("📊 Results")

    # 🧹 Optional clear all button
    if st.button("🧹 Clear All Projections"):
        st.session_state.manual_projections.clear()
        st.rerun()

    # Fetch boxscores
    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]

    # Always re-evaluate (for duplicates to work)
    st.session_state.results = evaluate_projections(projections_df, boxscores)

    if st.session_state.results:
        # Column headers
        header = st.columns(6)
        header[0].markdown("**Player**")
        header[1].markdown("**Metric**")
        header[2].markdown("**Target**")
        header[3].markdown("**Actual**")
        header[4].markdown("**Met?**")
        header[5].markdown("**Remove Player**")

        player_to_remove = None

        for i, row in enumerate(st.session_state.results):
            cols = st.columns(6)
            cols[0].markdown(row["Player"])
            cols[1].markdown(row["Metric"])
            cols[2].markdown(f"🎯 {row['Target']}")
            cols[3].markdown(f"📊 {row['Actual']}")
            cols[4].markdown(row["✅ Met?"])
            if cols[5].button("❌", key=f"delete_{i}"):
                player_to_remove = i

        # Handle row deletion
        if player_to_remove is not None:
            del st.session_state.manual_projections[player_to_remove]
            st.rerun()

        # CSV download
        df_clean = pd.DataFrame(st.session_state.results)
        csv = df_clean.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results CSV", data=csv, file_name="results.csv", mime="text/csv")

    else:
        st.info("No results to show. Add projections above.")
else:
    st.warning("Please enter at least one player projection to begin.")