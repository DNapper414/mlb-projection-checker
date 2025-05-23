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

game_ids_input = st.text_input("📅 Enter Game IDs (comma-separated)", placeholder="e.g. 777818,777816")
game_ids = [g.strip() for g in game_ids_input.split(",") if g.strip().isdigit()]

if not projections_df.empty and game_ids:
    st.subheader("📊 Results")
    boxscores = []
    for gid in game_ids:
        boxscore = fetch_boxscore(gid)
        if boxscore:
            boxscores.append(boxscore)

    results = evaluate_projections(projections_df, boxscores)
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results as CSV", data=csv, file_name="projection_results.csv", mime="text/csv")

elif projections_df.empty:
    st.warning("Please upload a projection CSV or enter a player manually.")
elif not game_ids:
    st.info("Enter game IDs to fetch live data.")