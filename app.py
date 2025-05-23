import streamlit as st

# Streamlit must begin with this
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
st.markdown("Enter projections and check results from live or recent MLB games.")

# 🧠 Manual projection state
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = []

# 📝 Form to add new projection
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

# 📅 Dropdown for recent game dates
recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date = st.selectbox("📅 Choose a game date", date_options)

# 🔄 Fetch MLB game IDs for the selected date
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
response = requests.get(schedule_url)
data = response.json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Loaded {len(game_ids)} game(s) on {selected_date}")

# 🧾 Create projections DataFrame
projections_df = pd.DataFrame(st.session_state.manual_projections)

# 📊 Generate results if there are projections
if not projections_df.empty:
    st.subheader("📊 Results")

    # Fetch all boxscores once
    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]

    # Evaluate if not already cached
    if "results" not in st.session_state:
        st.session_state.results = evaluate_projections(projections_df, boxscores)

    # Display each row manually with delete button
    if st.session_state.results:
        for i, row in enumerate(st.session_state.results):
            cols = st.columns([3, 2, 2, 2, 2, 1])
            cols[0].markdown(f"**{row['Player']}**")
            cols[1].markdown(row["Metric"])
            cols[2].markdown(f"🎯 {row['Target']}")
            cols[3].markdown(f"📊 {row['Actual']}")
            cols[4].markdown(row["✅ Met?"])
            if cols[5].button("❌", key=f"delete_{i}"):
                del st.session_state.results[i]
                st.experimental_set_query_params()
                break  # important to avoid index errors after deletion

        # CSV export
        if st.session_state.results:
            df_clean = pd.DataFrame(st.session_state.results)
            csv = df_clean.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Results CSV", data=csv, file_name="results.csv", mime="text/csv")
    else:
        st.info("No results to show. Try adding more projections.")
else:
    st.warning("Enter at least one projection above to begin.")