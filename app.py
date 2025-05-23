import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import fetch_boxscore, evaluate_projections

st.set_page_config(page_title="MLB Projection Checker", layout="centered")

st.title("⚾ MLB Player Projection Checker")
st.markdown("Upload a CSV file or manually enter your player projections below.")

# 📁 Upload Option
uploaded_file = st.file_uploader("📁 Upload CSV with Projections", type=["csv"])

# 📝 Manual Entry
if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = []

with st.form("manual_input"):
    st.subheader("📝 Manual Projection Entry")
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

# 🧾 Merge CSV + Manual entries
if uploaded_file:
    projections_df = pd.read_csv(uploaded_file)
else:
    projections_df = pd.DataFrame(st.session_state.manual_projections)

# 🗓 Auto-fetch yesterday's final game IDs
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={yesterday}"
response = requests.get(schedule_url)
data = response.json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") == "Final"
]

st.info(f"🔁 Automatically loading {len(game_ids)} game(s) from {yesterday}")

# 📊 Run Comparison
if not projections_df.empty:
    st.subheader("📊 Results")
    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]  # filter out None

    results = evaluate_projections(projections_df, boxscores)
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results as CSV", data=csv, file_name="projection_results.csv", mime="text/csv")

else:
    st.warning("Please upload a projection CSV or enter a player manually.")