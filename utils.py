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
                        stats = pdata.get("stats", {})
                        batting = stats.get("batting", {})
                        if metric in batting:
                            actual = batting[metric]
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
# NBA Support
# -----------------------

def fetch_boxscore_nba(date_str):
    # Uses balldontlie.io API
    url = f"https://www.balldontlie.io/api/v1/stats?start_date={date_str}&end_date={date_str}&per_page=100"
    all_stats = []
    page = 1
    while True:
        paged_url = f"{url}&page={page}"
        resp = requests.get(paged_url).json()
        data = resp.get("data", [])
        all_stats.extend(data)
        if resp.get("meta", {}).get("next_page") is None:
            break
        page += 1
    return all_stats

def evaluate_projections_nba(projections_df, game_date):
    boxscores = fetch_boxscore_nba(game_date)
    results = []

    for _, row in projections_df.iterrows():
        name = row["Player"].strip().lower()
        metric = row["Metric"]
        target = row["Target"]
        actual = 0

        for stat in boxscores:
            full_name = f"{stat['player']['first_name']} {stat['player']['last_name']}".strip().lower()
            if full_name == name:
                if metric == "PRA":
                    actual = stat["pts"] + stat["reb"] + stat["ast"]
                elif metric == "3pts made":
                    actual = stat["fg3m"]
                else:
                    key_map = {
                        "points": "pts",
                        "assists": "ast",
                        "rebounds": "reb",
                        "steals": "stl",
                        "blocks": "blk"
                    }
                    actual = stat.get(key_map.get(metric, ""), 0)
                break

        results.append({
            "Player": row["Player"],
            "Metric": metric,
            "Target": target,
            "Actual": actual,
            "✅ Met?": actual >= target
        })

    return results