import streamlit as st

# Must be first
st.set_page_config(page_title="Bet Tracker by Apprentice Ent. Sports Picks", layout="centered")

from streamlit_autorefresh import st_autorefresh
from streamlit.components.v1 import html
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

# --- Auto-refresh every 20s ---
st_autorefresh(interval=20000, key="auto_refresh")

# --- Session ID persistence ---
if "session_id" in st.query_params:
    session_id = st.query_params["session_id"]
else:
    session_id = str(uuid.uuid4())
    st.query_params["session_id"] = session_id
st.session_state.session_id = session_id

# --- Sport switch ---
default_sport = st.query_params.get("sport", "MLB")
sport = st.radio("Select Sport", ["MLB", "NBA"], index=0 if default_sport == "MLB" else 1)
if st.query_params.get("sport") != sport:
    st.query_params["sport"] = sport

# --- UI Controls ---
st.title("🏀⚾ Bet Tracker by Apprentice Ent. Sports Picks")
game_date = st.date_input("📅 Choose Game Date", value=datetime.today())
st.subheader(f"➕ Add {sport} Player Projection")

# --- Autocomplete players ---
players = []
if sport == "NBA":
    try:
        players = get_nba_players_today(game_date.strftime("%Y-%m-%d"))
    except Exception:
        st.warning("⚠️ Could not load NBA players.")
elif sport == "MLB":
    try:
        players = get_mlb_players_today(game_date.strftime("%Y-%m-%d"))
    except Exception:
        st.warning("⚠️ Could not load MLB players.")

player = st.selectbox("Player Name", players) if players else st.text_input("Player Name")
metric = st.selectbox(
    "Metric",
    ["points", "assists", "rebounds", "steals", "blocks", "3pts made", "PRA"] if sport == "NBA" else
    ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"]
)
target = st.number_input("Target Value", min_value=0, value=1)

# --- Add projection ---
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
    st.success(f"Added projection for {player}")

# --- Get Projections ---
response = get_projections(session_id)
filtered = [p for p in response.data if p["sport"] == sport and p["date"] == game_date.strftime("%Y-%m-%d")]

if filtered:
    st.subheader("📊 Projections")
    df = pd.DataFrame(filtered)

    # --- Evaluate ---
    if sport == "MLB":
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date.strftime('%Y-%m-%d')}"
        game_ids = [
            str(game["gamePk"])
            for d in requests.get(schedule_url).json().get("dates", [])
            for game in d.get("games", [])
            if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
        ]
        boxscores = [fetch_boxscore(gid) for gid in game_ids]
        results = evaluate_projections(df, boxscores)
    else:
        results = evaluate_projections_nba_nbaapi(df, game_date.strftime("%Y-%m-%d"))

    results_df = pd.DataFrame(results)

    # --- Render HTML Table ---
    table_html = """
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        background-color: #222;
        color: #eee;
    }
    th, td {
        padding: 6px 8px;
        border: 1px solid #444;
        text-align: left;
    }
    th {
        background-color: #333;
        color: #fff;
    }
    .trash {
        font-size: 16px;
        text-align: center;
    }
    @media (max-width: 600px) {
        table {
            font-size: 12px;
        }
        th, td {
            padding: 4px 5px;
        }
        .trash {
            font-size: 14px;
        }
    }
    </style>
    <table>
        <thead>
            <tr>
                <th>Player</th>
                <th>Metric</th>
                <th>Target</th>
                <th>Actual</th>
                <th>Met?</th>
                <th>Remove Player</th>
            </tr>
        </thead>
        <tbody>
    """

    for i, row in results_df.iterrows():
        met_icon = "✅" if row["✅ Met?"] else "❌"
        table_html += f"""
        <tr>
            <td>{row["Player"]}</td>
            <td>{row["Metric"]}</td>
            <td>{row["Target"]}</td>
            <td>{row["Actual"]}</td>
            <td>{met_icon}</td>
            <td class="trash">[REMOVE_{i}]</td>
        </tr>
        """

    table_html += "</tbody></table>"

    # Render table with placeholders for buttons
    html_block = table_html
    html(html_block.replace("[REMOVE_", ""), height=500, scrolling=False)

    # --- Replace placeholders with working Streamlit buttons
    for i, row in results_df.iterrows():
        if st.button("❌", key=f"remove_{i}"):
            remove_projection(df.iloc[i]["id"], session_id)
            st.rerun()

    # --- Download and Clear
    st.markdown("### 📥 Export & Cleanup")
    csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, file_name="projections.csv")

    if st.button("🧹 Clear All Projections"):
        clear_projections(session_id)
        st.rerun()

else:
    st.info("No projections yet. Add one above.")