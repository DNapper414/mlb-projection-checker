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

# --- Page setup ---
st.set_page_config(page_title="Bet Tracker | Apprentice Ent.", layout="centered")
st_autorefresh(interval=60000, key="auto_refresh")

# --- Session handling ---
if "session_id" in st.query_params:
    session_id = st.query_params["session_id"]
else:
    session_id = str(uuid.uuid4())
    st.query_params["session_id"] = session_id
st.session_state.session_id = session_id

# --- Sport selector ---
default_sport = st.query_params.get("sport", "MLB")
sport = st.radio("Select Sport", ["MLB", "NBA"], index=0 if default_sport == "MLB" else 1)
if st.query_params.get("sport") != sport:
    st.query_params["sport"] = sport

# --- Inject Modern Styling ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #f8f8f8;
}

h1, h2, h3 {
    color: #00ffe1;
    text-shadow: 0 0 6px #00ffe1;
}

.reportview-container {
    background-color: transparent;
}

.card {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

button {
    border-radius: 25px !important;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
    background: linear-gradient(to right, #00ffe1, #00c3ff);
    color: #000 !important;
    border: none;
    box-shadow: 0 0 10px #00ffe1;
    transition: all 0.3s ease-in-out;
}

button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 16px #00ffe1;
}

table {
    width: 100%;
    border-collapse: collapse;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    overflow: hidden;
    color: #fff;
    font-size: 14px;
}

th, td {
    padding: 12px;
    border: 1px solid #333;
    text-align: left;
}

th {
    background-color: rgba(0,0,0,0.6);
    color: #00ffe1;
}

tr:hover {
    background-color: rgba(255,255,255,0.06);
}

.trash {
    text-align: center;
    font-size: 20px;
    cursor: not-allowed;
}

@media (max-width: 600px) {
    table {
        font-size: 12px;
    }
    th, td {
        padding: 8px;
    }
}
</style>
""", unsafe_allow_html=True)

# --- UI layout ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.title("🏆 Bet Tracker by Apprentice Ent.")
game_date = st.date_input("📅 Game Date", value=datetime.today())
st.subheader(f"➕ Add {sport} Player Projection")

players = []
if sport == "NBA":
    try:
        players = get_nba_players_today(game_date.strftime("%Y-%m-%d"))
    except:
        st.warning("NBA players not loaded.")
elif sport == "MLB":
    try:
        players = get_mlb_players_today(game_date.strftime("%Y-%m-%d"))
    except:
        st.warning("MLB players not loaded.")

player = st.selectbox("Player Name", players) if players else st.text_input("Player Name")
metric = st.selectbox(
    "Metric",
    ["points", "assists", "rebounds", "steals", "blocks", "3pts made", "PRA"] if sport == "NBA" else
    ["hits", "homeRuns", "totalBases", "rbi", "baseOnBalls", "runs", "stolenBases"]
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
    st.success(f"Projection for {player} added.")
st.markdown('</div>', unsafe_allow_html=True)

# --- Load projections ---
response = get_projections(session_id)
projections = [p for p in response.data if p["sport"] == sport and p["date"] == game_date.strftime("%Y-%m-%d")]

if projections:
    df = pd.DataFrame(projections)

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

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Projection Results")

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
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Export + Cleanup ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📥 Export & Cleanup")
    csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", csv, file_name="projections.csv")

    if st.button("🧹 Clear All Projections"):
        clear_projections(session_id)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No projections added yet.")