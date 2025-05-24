import streamlit as st
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

# --- Page Setup ---
st.set_page_config(page_title="Bet Tracker by Apprentice Ent. Sports Picks", layout="centered")
st_autorefresh(interval=60000, key="auto_refresh")

# --- Session Handling ---
if "session_id" in st.query_params:
    session_id = st.query_params["session_id"]
else:
    session_id = str(uuid.uuid4())
    st.query_params["session_id"] = session_id
st.session_state.session_id = session_id

# --- Sport Selection ---
default_sport = st.query_params.get("sport", "MLB")
sport = st.radio("Select Sport", ["MLB", "NBA"], index=0 if default_sport == "MLB" else 1)
if st.query_params.get("sport") != sport:
    st.query_params["sport"] = sport

# --- Google Font & Global Styles ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    background-color: #0f0f0f;
    color: #f0f0f0;
}

h1, h2, h3 {
    color: #00ffd1;
}

input, select, textarea {
    background-color: #1e1e1e !important;
    color: #eee !important;
    border-radius: 6px;
}

button {
    border-radius: 50px !important;
    font-weight: 600;
    padding: 0.5rem 1rem;
    background: linear-gradient(to right, #00ffd1, #00c6ff);
    color: #000 !important;
}

table {
    width: 100%;
    border-collapse: collapse;
    background-color: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

th, td {
    padding: 12px 16px;
    border-bottom: 1px solid #333;
}

th {
    background-color: #111;
    color: #00ffd1;
}

tr:hover {
    background-color: rgba(255, 255, 255, 0.06);
}

.trash {
    font-size: 20px;
    text-align: center;
    cursor: default;
}

@media (max-width: 600px) {
    th, td {
        font-size: 12px;
        padding: 8px;
    }
}
</style>
""", unsafe_allow_html=True)

# --- UI Layout ---
st.title("📊 Bet Tracker — Apprentice Ent.")
game_date = st.date_input("📅 Game Date", value=datetime.today())
st.subheader(f"➕ Add {sport} Player Projection")

players = []
if sport == "NBA":
    try:
        players = get_nba_players_today(game_date.strftime("%Y-%m-%d"))
    except:
        st.warning("Could not load NBA players.")
elif sport == "MLB":
    try:
        players = get_mlb_players_today(game_date.strftime("%Y-%m-%d"))
    except:
        st.warning("Could not load MLB players.")

player = st.selectbox("Player Name", players) if players else st.text_input("Player Name")
metric = st.selectbox(
    "Metric",
    ["points", "assists", "rebounds", "steals", "blocks", "3pts made", "PRA"] if sport == "NBA"
    else ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"]
)
target = st.number_input("Target", min_value=0, value=1)

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

# --- Load & Filter Projections ---
response = get_projections(session_id)
projections = [p for p in response.data if p["sport"] == sport and p["date"] == game_date.strftime("%Y-%m-%d")]

if projections:
    df = pd.DataFrame(projections)

    # --- Evaluate ---
    if sport == "MLB":
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date.strftime('%Y-%m-%d')}"
        games = [
            str(game["gamePk"])
            for d in requests.get(schedule_url).json().get("dates", [])
            for game in d.get("games", [])
            if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
        ]
        boxscores = [fetch_boxscore(gid) for gid in games]
        results = evaluate_projections(df, boxscores)
    else:
        results = evaluate_projections_nba_nbaapi(df, game_date.strftime("%Y-%m-%d"))

    results_df = pd.DataFrame(results)

    # --- Table Render ---
    table_html = """
    <table>
        <thead>
            <tr>
                <th>Player</th>
                <th>Metric</th>
                <th>Target</th>
                <th>Actual</th>
                <th>Met?</th>
                <th>Remove</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in results_df.iterrows():
        met = "✅" if row["✅ Met?"] else "❌"
        table_html += f"""
        <tr>
            <td>{row['Player']}</td>
            <td>{row['Metric']}</td>
            <td>{row['Target']}</td>
            <td>{row['Actual']}</td>
            <td>{met}</td>
            <td class="trash">🗑️</td>
        </tr>
        """

    table_html += "</tbody></table>"
    html(table_html, height=520, scrolling=False)

    # --- Export / Clear Buttons ---
    st.markdown("### 📤 Export & Cleanup")
    csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, file_name="projections.csv")

    if st.button("🧹 Clear All Projections"):
        clear_projections(session_id)
        st.rerun()
else:
    st.info("No projections for this date yet.")