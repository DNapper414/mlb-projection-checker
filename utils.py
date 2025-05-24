import requests

# -----------------------
# MLB Support
# -----------------------

def fetch_boxscore(game_id):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def evaluate_projections(projections_df, boxscores):
    results = []
    for _, row in projections_df.iterrows():
        player_name = row["Player"].strip().lower()
        metric = row["Metric"]
        target = row["Target"]
        actual = 0
        found = False
        for box in boxscores:
            for team in ["home", "away"]:
                players = box["teams"][team]["players"]
                for pdata in players.values():
                    full_name = pdata["person"]["fullName"].strip().lower()
                    if full_name == player_name:
                        stats = pdata.get("stats", {}).get("batting", {})
                        if metric in stats:
                            actual = stats[metric]
                            found = True
                            break
                if found:
                    break
            if found:
                break
        results.append({
            "Player": row["Player"],
            "Metric": metric,
            "Target": target,
            "Actual": actual,
            "✅ Met?": actual >= target
        })
    return results

# -----------------------
# NBA Support via RapidAPI (Box Score-Based)
# -----------------------

RAPIDAPI_KEY = "47945fd24fmsh2539580c53289bdp119b7bjsne5525ec5acdf"
RAPIDAPI_HOST = "api-nba-v1.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
}

def get_nba_players_from_games(date_str):
    games_url = f"https://api-nba-v1.p.rapidapi.com/games?date={date_str}"
    games_resp = requests.get(games_url, headers=HEADERS)
    games_data = games_resp.json().get("response", [])
    all_players = set()

    for game in games_data:
        game_id = game.get("id")
        stats_url = f"https://api-nba-v1.p.rapidapi.com/players/statistics?game={game_id}"
        stats_resp = requests.get(stats_url, headers=HEADERS)
        stats_data = stats_resp.json().get("response", [])
        for s in stats_data:
            name = f"{s['player']['firstname']} {s['player']['lastname']}".strip()
            all_players.add(name)

    return sorted(all_players)

def fetch_boxscore_nba(date_str):
    games_url = f"https://api-nba-v1.p.rapidapi.com/games?date={date_str}"
    games_resp = requests.get(games_url, headers=HEADERS)
    games_data = games_resp.json().get("response", [])
    all_stats = []
    for game in games_data:
        game_id = game.get("id")
        stats_url = f"https://api-nba-v1.p.rapidapi.com/players/statistics?game={game_id}"
        stats_resp = requests.get(stats_url, headers=HEADERS)
        stats_data = stats_resp.json().get("response", [])
        all_stats.extend(stats_data)
    return all_stats

def evaluate_projections_nba(projections_df, game_date):
    boxscores = fetch_boxscore_nba(game_date)
    results = []
    for _, row in projections_df.iterrows():
        input_name = row["Player"].strip().lower()
        metric = row["Metric"]
        target = row["Target"]
        actual = 0
        found = False
        for stat in boxscores:
            player = stat.get("player", {})
            stats = stat.get("statistics", {})
            full_name = f"{player.get('firstname', '')} {player.get('lastname', '')}".strip().lower()
            if input_name == full_name or input_name in full_name:
                found = True
                if metric == "PRA":
                    actual = stats.get("points", 0) + stats.get("assists", 0) + stats.get("rebounds", 0)
                elif metric == "3pts made":
                    actual = stats.get("tpm", 0)
                else:
                    actual = stats.get(metric, 0)
                break
        results.append({
            "Player": row["Player"],
            "Metric": metric,
            "Target": target,
            "Actual": actual if found else "N/A",
            "✅ Met?": actual >= target if found else False
        })
    return results