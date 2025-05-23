import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta
from PIL import Image
from utils import fetch_boxscore, evaluate_projections

# Set page config
st.set_page_config(page_title="MLB Projection Checker", layout="centered")

# ---------------------------
# LocalStorage JS Integration
# ---------------------------

local_storage_key = "mlb_projections"

# Hidden text input to exchange with localStorage
projections_json = st.text_area("Projections (stored in browser)", "", key="projections_store", label_visibility="collapsed")

# JavaScript to sync with localStorage
st.markdown(f"""
<script>
const key = "{local_storage_key}";

// Sync from localStorage on load
const saved = localStorage.getItem(key);
if (saved && !window._synced) {{
    const textarea = window.parent.document.querySelector('textarea[data-testid="stTextArea"]');
    textarea.value = saved;
    textarea.dispatchEvent(new Event("input", {{ bubbles: true }}));
    window._synced = true;
}}

// Watch for changes to store in localStorage
const textarea = window.parent.document.querySelector('textarea[data-testid="stTextArea"]');
const observer = new MutationObserver(() => {{
    localStorage.setItem(key, textarea.value);
}});
observer.observe(textarea, {{ attributes: true, childList: true, subtree: true }});
</script>
""", unsafe_allow_html=True)

# --------------------------------------
# Restore session_state from localStorage
# --------------------------------------

try:
    stored_projections = json.loads(projections_json) if projections_json else []
except:
    stored_projections = []

if "manual_projections" not in st.session_state:
    st.session_state.manual_projections = stored_projections

# -----------------
# Load logo + title
# -----------------

logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
logo = Image.open(logo_path)
st.image(logo, use_container_width=True)

st.title("⚾ MLB Player Projection Checker")
st.markdown("Enter player projections, select a game date, and compare to real MLB stats.")

# ---------------------
# Projection entry form
# ---------------------

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
        st.rerun()

# -------------------------
# Game date selection + API
# -------------------------

recent_days = [datetime.now().date() - timedelta(days=i) for i in range(7)]
date_options = [d.strftime("%Y-%m-%d") for d in recent_days]
selected_date = st.selectbox("📅 Choose a game date", date_options)

schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={selected_date}"
data = requests.get(schedule_url).json()

game_ids = [
    str(game["gamePk"])
    for d in data.get("dates", [])
    for game in d.get("games", [])
    if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress"]
]

st.info(f"🔁 Loaded {len(game_ids)} game(s) for {selected_date}")

# ---------------------------
# Evaluate and render results
# ---------------------------

projections_df = pd.DataFrame(st.session_state.manual_projections)

if not projections_df.empty:
    st.subheader("📊 Results")

    if st.button("🧹 Clear All Projections"):
        st.session_state.manual_projections = []
        st.rerun()

    boxscores = [fetch_boxscore(gid) for gid in game_ids]
    boxscores = [b for b in boxscores if b]

    results = evaluate_projections(projections_df, boxscores)

    if results:
        header = st.columns(6)
        header[0].markdown("**Player**")
        header[1].markdown("**Metric**")
        header[2].markdown("**Target**")
        header[3].markdown("**Actual**")
        header[4].markdown("**Met?**")
        header[5].markdown("**Remove Player**")

        for i, row in enumerate(results):
            cols = st.columns(6)
            cols[0].markdown(row["Player"])
            cols[1].markdown(row["Metric"])
            cols[2].markdown(f"🎯 {row['Target']}")
            cols[3].markdown(f"📊 {row['Actual']}")
            cols[4].markdown(row["✅ Met?"])
            if cols[5].button("❌", key=f"delete_{i}"):
                st.session_state.manual_projections.pop(i)
                st.rerun()

        df_clean = pd.DataFrame(results)
        csv = df_clean.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results CSV", data=csv, file_name="results.csv", mime="text/csv")
    else:
        st.info("No results to display.")
else:
    st.warning("Please enter at least one player projection to begin.")