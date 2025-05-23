import requests

# 🔄 Fetch boxscore data for a given game ID
def fetch_boxscore(game_id):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else None

# 📊 Get a specific stat for a given player
def get_stat_for_player(boxscore, player_name, stat_key):
    for team in ["home", "away"]:
        for player in boxscore["teams"][team]["players"].values():
            if player["person"]["fullName"].lower() == player_name.lower():
                batting_stats = player.get("stats", {}).get("batting", {})
                return batting_stats.get(stat_key, 0)
    return None

# ✅ Evaluate all projections against actual stats
def evaluate_projections(projections, boxscores):
    results = []
    for _, row in projections.iterrows():
        player = row["Player"]
        stat_key = row["Metric"]
        target = row["Target"]
        actual = None
        met = False

        # Look for player's stat in all boxscores
        for box in boxscores:
            actual = get_stat_for_player(box, player, stat_key)
            if actual is not None:
                met = actual >= target
                break

        results.append({
            "Player": player,
            "Metric": stat_key,
            "Target": target,
            "Actual": actual if actual is not None else "N/A",
            "✅ Met?": "✅" if met else "❌"
        })

    return results