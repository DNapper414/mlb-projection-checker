import requests

def fetch_boxscore(game_id):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else None

def get_stat_for_player(boxscore, player_name, stat_key):
    for team in ["home", "away"]:
        for player in boxscore["teams"][team]["players"].values():
            if player["person"]["fullName"] == player_name:
                return player["stats"]["batting"].get(stat_key, 0)
    return None

def evaluate_projections(projections, boxscores):
    results = []
    for _, row in projections.iterrows():
        player = row["Player"]
        stat_key = row["Metric"]
        target = row["Target"]
        actual = None
        met = False

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
            "✅/❌": "✅" if met else "❌"
        })

    return results