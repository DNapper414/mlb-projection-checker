import streamlit as st

# Must be first Streamlit call
st.set_page_config(page_title="Bet Tracker by Apprentice Ent. Sports Picks", layout="centered")

from streamlit_autorefresh import st_autorefresh
import pandas as pd
import requests
import uuid
from datetime import datetime
from utils import (
    fetch_boxscore,
    evaluate_projections,
    evaluate_projections_nba_nbaapi,
    get_nba_players_today,
    get_mlb_players_today
)
from supabase_client import (
    add_projection,
    get_projections,
    remove_projection,
    clear_projections
)

# --- Auto-refresh every 20 seconds ---
st_autorefresh(interval=20000, key="auto_refresh")  # 20 seconds = 20000 ms

# --- Persistent session_id using query params ---
if "session_id" in st.query_params:
    session_id = st.query_params["session_id"]
else:
    session_id = str(uuid.uuid4())
    st.query_params["session_id"] = session_id
st.session_state.session_id = session_id

# --- Persistent sport selection using query params ---
default_sport = st.query_params.get("sport", "MLB")
sport = st.radio("Select Sport", ["MLB", "NBA"], index=0 if default_sport == "MLB" else 1)
if st.query_params.get("sport") != sport:
    st.query_params["sport"] = sport

# --- UI Layout ---
st.title("🏀⚾ Bet Tracker by Apprentice Ent. Sports Picks")
game_date = st.date_input("📅 Choose Game Date", value=datetime.today())
st.subheader(f"➕ Add {sport} Player Projection")

# --- Autocomplete Players ---
players = []
if sport == "NBA":
    try:
        players = get_nba_players_today(game_date.strftime("%Y-%m-%d"))
    except Exception:
        st.warning("⚠️ Could not load NBA player names. Use manual entry.")
elif sport == "MLB":
    try:
        players = get_mlb_players_today(game_date.strftime("%Y-%m-%d"))
    except Exception:
        st.warning("⚠️ Could not load MLB player names. Use manual entry.")

player = st.selectbox("Player Name", players) if players else st.text_input("Player Name")

metric = st.selectbox(
    "Metric",
    ["points", "assists", "rebounds", "steals", "blocks", "3pts made", "PRA"]
    if sport == "NBA"
    else ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"]
)
target = st.number_input("Target Value", min_value=0, value=1)

# --- Add Projection ---
if st.button("➕ Add to Table") and player:
    add_projection({
        "sport": sport,
        "date": game_date.strftime("%Y-%m-%d"),
        "player": player,
        "metric": metric,
        "target": target,
        "actual": None,
        "session_id": session_id
    })
    st.success(f"Projection added for {player}")

# --- Load & Evaluate Projections ---
response = get_projections(session_id)
projections = [p for p in response.data if p["sport"] == sport]

if projections:
    st.subheader("📊 Results")
    df = pd.DataFrame(projections)

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

    # --- Render Results Table ---
    header = st.columns(6)
    header[0].markdown("**Player**")
    header[1].markdown("**Metric**")
    header[2].markdown("**Target**")
    header[3].markdown("**Actual**")
    header[4].markdown("**Met?**")
    header[5].markdown("**🗑 Remove**")

    for i, row in results_df.iterrows():
        cols = st.columns(6)
        cols[0].markdown(row["Player"])
        cols[1].markdown(row["Metric"])
        cols[2].markdown(f"{row['Target']}")
        cols[3].markdown(f"{row['Actual']}")
        cols[4].markdown("✅" if row["✅ Met?"] else "❌")
        if cols[5].button("❌", key=f"remove_{i}"):
            remove_projection(df.iloc[i]["id"], session_id)
            st.rerun()

    # --- Download / Clear ---
    csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Results CSV", csv, file_name="bet_results.csv")

    if st.button("🧹 Clear All Projections"):
        clear_projections(session_id)
        st.rerun()
else:
    st.info("No projections yet. Add one above.")