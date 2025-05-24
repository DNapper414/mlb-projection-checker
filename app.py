import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from utils import (
    fetch_boxscore,
    fetch_boxscore_nba,
    evaluate_projections,
    evaluate_projections_nba,
    get_nba_players
)

st.set_page_config(page_title="Bet Tracker by Apprentice Ent. Sports Picks", layout="centered")

st.title("🏀⚾ Bet Tracker by Apprentice Ent. Sports Picks")

# Choose sport and game date
sport = st.radio("Select Sport", ["MLB", "NBA"])
game_date = st.date_input("📅 Choose Game Date", value=datetime.today())

st.subheader(f"➕ Add {sport} Player Projection")

# Player and metric entry
if sport == "NBA":
    nba_players = get_nba_players()
    player = st.selectbox("Player Name", nba_players)
    metric = st.selectbox("Metric", ["points", "assists", "rebounds", "steals", "blocks", "3pts made", "PRA"])
else:
    player = st.text_input("Player Name")
    metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])

target = st.number_input("Target Value", min_value=0, value=1)

if st.button("➕ Add to Table"):
    if "projections" not in st.session_state:
        st.session_state.projections = []
    st.session_state.projections.append({
        "Sport": sport,
        "Date": game_date.strftime("%Y-%m-%d"),
        "Player": player,
        "Metric": metric,
        "Target": target
    })

# Show results if available
if "projections" in st.session_state and st.session_state.projections:
    all_proj_df = pd.DataFrame(st.session_state.projections)
    st.subheader("📊 Results")

    if sport == "MLB":
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date.strftime('%Y-%m-%d')}"
        resp = requests.get(schedule_url).json()
        game_ids = [
            str(game["gamePk"])
            for d in resp.get("dates", [])
            for game in d.get("games", [])
            if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
        ]
        boxscores = [fetch_boxscore(gid) for gid in game_ids]
        mlb_proj = [p for p in st.session_state.projections if p["Sport"] == "MLB"]
        mlb_df = pd.DataFrame(mlb_proj) if mlb_proj else pd.DataFrame(columns=["Player", "Metric", "Target"])
        results = evaluate_projections(mlb_df, boxscores)

    else:
        nba_proj = [p for p in st.session_state.projections if p["Sport"] == "NBA"]
        nba_df = pd.DataFrame(nba_proj) if nba_proj else pd.DataFrame(columns=["Player", "Metric", "Target"])
        results = evaluate_projections_nba(nba_df, game_date.strftime("%Y-%m-%d"))

    result_df = pd.DataFrame(results)
    st.dataframe(result_df, use_container_width=True)

    st.download_button("📥 Download Results CSV", result_df.to_csv(index=False), file_name="bet_results.csv")