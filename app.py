import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
from PIL import Image
from utils import (
    fetch_boxscore,
    evaluate_projections,
    fetch_boxscore_nba,
    evaluate_projections_nba,
)

# --- Page Setup ---
st.set_page_config(page_title="Bet Tracker", layout="centered")

# --- File Storage ---
PROJECTION_FILE = "projections.json"

def load_projections():
    if os.path.exists(PROJECTION_FILE):
        with open(PROJECTION_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_projections(data):
    with open(PROJECTION_FILE, "w") as f:
        json.dump(data, f)

# --- Session State Initialization ---
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = load_projections()

# --- Lock date selection on rerun ---
recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date_options[0]
selected_date = st.selectbox("📅 Choose a Game Date", date_options, index=date_options.index(st.session_state.selected_date))
st.session_state.selected_date = selected_date

# --- Branding ---
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=True)

st.title("Bet Tracker by Apprentice Ent. Sports Picks")
st.markdown("Track your player projections for MLB and NBA in one place.")

# --- Sport Selector ---
sport = st.selectbox("Choose a Sport", ["MLB", "NBA"])

# --- Metric Options ---
if sport == "MLB":
    metric_options = ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"]
else:
    metric_options = ["points", "assists", "rebounds", "3pts made", "steals", "blocks", "PRA"]

# --- Add Projection Form ---
with st.form("manual_input"):
    st.subheader(f"📝 Add {sport} Player Projection")
    player = st.text_input("Player Name (e.g. LeBron James or Aaron Judge)")
    metric = st.selectbox("Metric", metric_options)
    target = st.number_input("Target", value=1)
    submitted = st.form_submit_button("Add")

    if submitted and player and metric:
        st.session_state.manual_projections.append({
            "Sport": sport,
            "Player": player,
            "Metric": metric,
            "Target": target
        })
        save_projections(st.session_state.manual_projections)
        st.rerun()

# --- Filter Projections by Sport ---
projections_df = pd.DataFrame([p for p in st.session_state.manual_projections if p["Sport"] == sport])

# --- Show Results ---
if not projections_df.empty:
    st.subheader(f"📊 {sport} Results")

    if st.button("🧹 Clear All Projections"):
        st.session_state.manual_projections = [p for p in st.session_state.manual_projections if p["Sport"] != sport]
        save_projections(st.session_state.manual_projections)
        st.rerun()

    # --- Load Boxscores and Evaluate ---
    if sport == "MLB":
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
        data = requests.get(url).json()
        game_ids = [
            str(g["gamePk"])
            for d in data.get("dates", [])
            for g in d.get("games", [])
            if g.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
        ]
        boxscores = [fetch_boxscore(gid) for gid in game_ids]
        boxscores = [b for b in boxscores if b]
        results = evaluate_projections(projections_df, boxscores)
    else:
        results = evaluate_projections_nba(projections_df, selected_date)

    # --- Render Table ---
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
            cols[2].markdown(f"{row['Target']}")
            cols[3].markdown(f"{row['Actual']}")
            cols[4].markdown("✅" if row["✅ Met?"] else "❌")
            if cols[5].button("❌", key=f"delete_{sport}_{i}"):
                global_index = projections_df.index[i]
                st.session_state.manual_projections.pop(global_index)
                save_projections(st.session_state.manual_projections)
                st.rerun()

        # --- CSV Download ---
        df_clean = pd.DataFrame(results)
        csv = df_clean.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results CSV", data=csv, file_name=f"{sport.lower()}_results.csv", mime="text/csv")
    else:
        st.info("No results available.")
else:
    st.warning(f"No {sport} projections added. Enter at least one to begin.")