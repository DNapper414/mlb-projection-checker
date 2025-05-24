import requests
from datetime import datetime
import time
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2

# -------------------------------
# MLB FUNCTIONS
# -------------------------------

def fetch_boxscore(game_id):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def evaluate_projections(projections_df, boxscores):
    results = []
    for _, row in projections_df.iterrows():
        # Handle both capitalized and lowercase keys
        player_name = row.get("Player", row.get("player", "")).strip().lower()
        metric = row.get("Metric", row.get("metric", ""))
        target = row.get("Target", row.get("target", 0))
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
            "Player": row.get("Player", row.get("player", "")),
            "Metric": metric,
            "Target": target,
            "Actual": actual,
            "✅ Met?": actual >= target
        })
    return results

def get_mlb_players_today(date_str):
    """Return all player names from MLB games on a given date."""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
    resp = requests.get(url).json()
    game_ids = [
        str(game["gamePk"])
        for d in resp.get("dates", [])
        for game in d.get("games", [])
        if game.get("status", {}).get("abstractGameState") in ["Final", "Live", "In Progress", "Preview"]
    ]

    player_names = set()
    for gid in game_ids:
        boxscore = fetch_boxscore(gid)
        if not boxscore:
            continue
        for team in ["home", "away"]:
            players = boxscore["teams"][team]["players"]
            for pdata in players.values():
                name = pdata["person"]["fullName"]
                player_names.add(name)

    return sorted(player_names)

# -------------------------------
# NBA FUNCTIONS (nba_api)
# -------------------------------

def get_nba_players_today(date_str):
    """Return all player names from all games played on a given date."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date_obj.strftime("%m/%d/%Y"), league_id="00")
    game_ids = scoreboard.game_header.get_data_frame()["GAME_ID"].tolist()
    all_players = set()

    for gid in game_ids:
        time.sleep(0.6)
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gid)
        df = box.player_stats.get_data_frame()
        for name in df["PLAYER_NAME"]:
            all_players.add(name)

    return sorted(all_players)

def evaluate_projections_nba_nbaapi(projections_df, date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date_obj.strftime("%m/%d/%Y"), league_id="00")
    game_ids = scoreboard.game_header.get_data_frame()["GAME_ID"].tolist()
    results = []

    for _, row in projections_df.iterrows():
        input_name = row.get("Player", row.get("player", "")).strip().lower()
        metric = row.get("Metric", row.get("metric", ""))
        target = row.get("Target", row.get("target", 0))
        actual = 0
        found = False

        for gid in game_ids:
            time.sleep(0.6)
            box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gid)
            df = box.player_stats.get_data_frame()
            for _, player_row in df.iterrows():
                player_name = player_row["PLAYER_NAME"].strip().lower()
                if input_name in player_name or player_name in input_name:
                    found = True
                    if metric == "PRA":
                        actual = player_row["PTS"] + player_row["REB"] + player_row["AST"]
                    elif metric == "3pts made":
                        actual = player_row["FG3M"]
                    elif metric == "points":
                        actual = player_row["PTS"]
                    elif metric == "rebounds":
                        actual = player_row["REB"]
                    elif metric == "assists":
                        actual = player_row["AST"]
                    elif metric == "steals":
                        actual = player_row["STL"]
                    elif metric == "blocks":
                        actual = player_row["BLK"]
                    break
            if found:
                break

        results.append({
            "Player": row.get("Player", row.get("player", "")),
            "Metric": metric,
            "Target": target,
            "Actual": actual if found else "N/A",
            "✅ Met?": actual >= target if found else False
        })

    return results