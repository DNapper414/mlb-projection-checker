import streamlit as st
import pandas as pd
from utils import fetch_boxscore, evaluate_projections

st.set_page_config(page_title="MLB Projection Checker", layout="centered")

st.title("⚾ MLB Player Projection Checker")

st.markdown("Upload a CSV file or manually enter your player projections below.")

uploaded_file = st.file_uploader("📁 Upload CSV with Projections", type=["csv"])

if uploaded_file:
    projections_df = pd.read_csv(uploaded_file)
else:
    with st.form("manual_input"):
        st.subheader("📝 Manual Projection Entry")
        player = st.text_input("Player Name (e.g. Aaron Judge)")
        metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])
        target = st.number_input("Target Value", value=1)
        submitted = st.form_submit_button("Add to Table")

        if submitted:
            projections_df = pd.DataFrame([{
                "Player": player,
                "Metric": metric,
                "Target": target
            }])
        else:
            projections_df = pd.DataFrame(columns=["Player", "Metric", "Target"])

from datetime import datetime, timedelta
import requests

# Automatically fetch game IDs from yesterday
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={yesterday}"
response = requests.get(schedule_url)
data = response.json()

game_ids = []
for date_info in data.get("dates", []):
    for game in date_info.get("games", []):
        if game.get("status", {}).get("abstractGameState") == "Final":
            game_ids.append(str(game["gamePk"]))

st.info(f"🔁 Automatically loading {len(game_ids)} game(s) from {yesterday}")

if not projections_df.empty:
    st.subheader("📊 Results")

    # Auto-fetch all final games from yesterday
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={yesterday}"
    schedule_resp = requests.get(schedule_url).json()
    game_ids = [
        str(game["gamePk"])
        for d in schedule_resp.get("dates", [])
        for game in d.get("games", [])
        if game.get("status", {}).get("abstractGameState") == "Final"
    ]

    # Load all box scores
    boxscores = []
    for gid in game_ids:
        box = fetch_boxscore(gid)
        if box:
            boxscores.append(box)

    # Evaluate projections across all games
    results = evaluate_projections(projections_df, boxscores)
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results as CSV", data=csv, file_name="projection_results.csv", mime="text/csv")
file_name="projection_results.csv", mime="text/csv")

elif projections_df.empty:
    st.warning("Please upload a projection CSV or enter a player manually.")
elif not game_ids:
    st.info("Enter game IDs to fetch live data.")