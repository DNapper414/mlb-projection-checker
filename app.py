import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from utils import (
    fetch_boxscore,
    fetch_boxscore_nba,
    evaluate_projections,
    evaluate_projections_nba,
    get_nba_players_from_games
)

st.set_page_config(page_title="Bet Tracker by Apprentice Ent. Sports Picks", layout="centered")
st.title("🏀⚾ Bet Tracker by Apprentice Ent. Sports Picks")

# --- UI: Sport and Date ---
sport = st.radio("Select Sport", ["MLB", "NBA"])
game_date = st.date_input("📅 Choose Game Date", value=datetime.today())

st.subheader(f"➕ Add {sport} Player Projection")

# --- Player Entry ---
nba_players = []
if sport == "NBA":
    try:
        nba_players = get_nba_players_from_games(game_date.strftime("%Y-%m-%d"))
    except Exception as e:
        st.warning("⚠️ Could not load NBA players from live data. You can still type the name manually.")
        nba_players = []

    if nba_players:
        player = st.selectbox("Player Name", nba_players)
    else:
        player = st.text_input("Player Name (manual entry)")
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

# --- Show Results ---
if "projections" in st.session_state and st.session_state.projections:
    st.subheader("📊 Results")

    # Filter projections by sport
    filtered = [p for p in st.session_state.projections if p["Sport"] == sport]
    df = pd.DataFrame(filtered)

    if df.empty:
        st.info(f"No {sport} projections yet.")
    else:
        # Clear All Button
        if st.button("🧹 Clear All Projections"):
            st.session_state.projections = [p for p in st.session_state.projections if p["Sport"] != sport]
            st.rerun()

        # Evaluate Actuals
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
            results = evaluate_projections_nba(df, game_date.strftime("%Y-%m-%d"))

        results_df = pd.DataFrame(results)

        # Render with trashcans
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

        # CSV download
        csv = results_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results CSV", csv, file_name="bet_results.csv")

else:
    st.info("Add at least one player to begin.")