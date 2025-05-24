import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from utils import (
    fetch_boxscore,
    evaluate_projections,
    evaluate_projections_nba_nbaapi,
    get_nba_players_today
)

st.set_page_config(page_title="Bet Tracker by Apprentice Ent. Sports Picks", layout="centered")
st.title("🏀⚾ Bet Tracker by Apprentice Ent. Sports Picks")

sport = st.radio("Select Sport", ["MLB", "NBA"])
game_date = st.date_input("📅 Choose Game Date", value=datetime.today())

st.subheader(f"➕ Add {sport} Player Projection")

# NBA Player Options
nba_players = []
if sport == "NBA":
    try:
        nba_players = get_nba_players_today(game_date.strftime("%Y-%m-%d"))
    except Exception:
        st.warning("⚠️ Could not load NBA player names. Use manual entry.")
        nba_players = []

# Player Input
if sport == "NBA":
    if nba_players:
        player = st.selectbox("Player Name", nba_players)
    else:
        player = st.text_input("Player Name")
    metric = st.selectbox("Metric", ["points", "assists", "rebounds", "steals", "blocks", "3pts made", "PRA"])
else:
    player = st.text_input("Player Name")
    metric = st.selectbox("Metric", ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"])

target = st.number_input("Target Value", min_value=0, value=1)

# Add to Table
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

# Show Results
if "projections" in st.session_state and st.session_state.projections:
    st.subheader("📊 Results")

    filtered = [p for p in st.session_state.projections if p["Sport"] == sport]
    df = pd.DataFrame(filtered)

    if df.empty:
        st.info("No projections added.")
    else:
        if st.button("🧹 Clear All Projections"):
            st.session_state.projections = [p for p in st.session_state.projections if p["Sport"] != sport]
            st.rerun()

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
            results = evaluate_projections(df, boxscores)
        else:
            results = evaluate_projections_nba_nbaapi(df, game_date.strftime("%Y-%m-%d"))

        results_df = pd.DataFrame(results)

        # Render table with delete buttons
        header = st.columns(6)
        header[0].markdown("**Player**")
        header[1].markdown("**Metric**")
        header[2].markdown("**Target**")
        header[3].markdown("**Actual**")
        header[4].markdown("**Met?**")
        header[5].markdown("**🗑 Remove Player**")

        for i, row in results_df.iterrows():
            cols = st.columns(6)
            cols[0].markdown(row["Player"])
            cols[1].markdown(row["Metric"])
            cols[2].markdown(f"{row['Target']}")
            cols[3].markdown(f"{row['Actual']}")
            cols[4].markdown("✅" if row["✅ Met?"] else "❌")
            if cols[5].button("❌", key=f"remove_{sport}_{i}"):
                index_in_session = df.index[i]
                del st.session_state.projections[index_in_session]
                st.rerun()

        # Download
        csv = results_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results CSV", csv, file_name="bet_results.csv")