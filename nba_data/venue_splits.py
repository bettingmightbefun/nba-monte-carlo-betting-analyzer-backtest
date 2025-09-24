"""Home/away venue split utilities for NBA teams."""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from nba_data.team_resolver import get_team_id, format_season

try:  # pragma: no cover - dependency optional for tests
    from nba_api.stats.endpoints import teamdashboardbygeneralsplits, teamgamelogs
except ImportError:  # pragma: no cover - provide graceful fallback
    teamdashboardbygeneralsplits = None  # type: ignore[assignment]
    teamgamelogs = None  # type: ignore[assignment]


def _safe_float(value: Optional[float]) -> Optional[float]:
    return float(value) if value is not None and not pd.isna(value) else None


def get_team_venue_splits(team_name: str, season_end_year: int) -> Dict[str, Dict[str, Optional[float]]]:
    """Return key venue performance metrics for a team."""

    if teamdashboardbygeneralsplits is None:
        raise ImportError(
            "nba_api package is required for venue split analysis. "
            "Install it with `pip install nba_api`."
        )

    team_id = get_team_id(team_name)
    season = format_season(season_end_year)

    dashboard = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
        team_id=team_id,
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
    ).get_data_frames()

    location_data: Optional[pd.DataFrame] = None
    for df in dashboard:
        if "TEAM_GAME_LOCATION" in df.columns:
            location_data = df
            break

    if location_data is not None and not location_data.empty:
        return _extract_dashboard_splits(location_data)

    return _calculate_manual_splits(team_id, season)


def _extract_dashboard_splits(location_data: pd.DataFrame) -> Dict[str, Dict[str, Optional[float]]]:
    home_stats = location_data[location_data["TEAM_GAME_LOCATION"] == "Home"]
    away_stats = location_data[location_data["TEAM_GAME_LOCATION"] == "Road"]

    if home_stats.empty or away_stats.empty:
        team_id = int(location_data["TEAM_ID"].iloc[0])
        season = str(location_data["SEASON_ID"].iloc[0])
        return _calculate_manual_splits(team_id, season)

    home_row = home_stats.iloc[0]
    away_row = away_stats.iloc[0]

    home_performance = {
        "games_played": int(home_row.get("GP", 0)),
        "wins": int(home_row.get("W", 0)),
        "losses": int(home_row.get("L", 0)),
        "win_pct": _safe_float(home_row.get("W_PCT")),
        "points_per_game": _safe_float(home_row.get("PTS")),
        "offensive_rating": _safe_float(home_row.get("E_OFF_RATING", home_row.get("OFF_RATING"))),
        "defensive_rating": _safe_float(home_row.get("E_DEF_RATING", home_row.get("DEF_RATING"))),
        "net_rating": _safe_float(home_row.get("E_NET_RATING", home_row.get("NET_RATING"))),
    }

    away_performance = {
        "games_played": int(away_row.get("GP", 0)),
        "wins": int(away_row.get("W", 0)),
        "losses": int(away_row.get("L", 0)),
        "win_pct": _safe_float(away_row.get("W_PCT")),
        "points_per_game": _safe_float(away_row.get("PTS")),
        "offensive_rating": _safe_float(away_row.get("E_OFF_RATING", away_row.get("OFF_RATING"))),
        "defensive_rating": _safe_float(away_row.get("E_DEF_RATING", away_row.get("DEF_RATING"))),
        "net_rating": _safe_float(away_row.get("E_NET_RATING", away_row.get("NET_RATING"))),
    }

    venue_differentials = {
        "points_advantage": _diff(home_performance["points_per_game"], away_performance["points_per_game"]),
        "win_pct_advantage": _diff(home_performance["win_pct"], away_performance["win_pct"]),
        "ortg_advantage": _diff(home_performance["offensive_rating"], away_performance["offensive_rating"]),
        "drtg_advantage": _diff(away_performance["defensive_rating"], home_performance["defensive_rating"]),
    }

    return {
        "home_performance": home_performance,
        "away_performance": away_performance,
        "venue_differentials": venue_differentials,
    }


def _calculate_manual_splits(team_id: int, season: str) -> Dict[str, Dict[str, Optional[float]]]:
    if teamgamelogs is None:
        raise ImportError(
            "nba_api package is required for venue split analysis. "
            "Install it with `pip install nba_api`."
        )

    logs = teamgamelogs.TeamGameLogs(
        team_id_nullable=team_id,
        season_nullable=season,
        season_type_nullable="Regular Season",
    ).get_data_frames()[0]

    if logs.empty:
        raise RuntimeError(
            f"No game log data available for team {team_id} in season {season}."
        )

    logs["IS_AWAY"] = logs["MATCHUP"].str.contains("@")

    def _calc_split(df: pd.DataFrame) -> Dict[str, Optional[float]]:
        if df.empty:
            return {"games_played": 0, "wins": 0, "losses": 0, "win_pct": 0.0, "points_per_game": 0.0}
        wins = int((df["WL"] == "W").sum())
        games = int(len(df))
        return {
            "games_played": games,
            "wins": wins,
            "losses": games - wins,
            "win_pct": wins / games if games > 0 else 0.0,
            "points_per_game": float(df["PTS"].mean()),
        }

    home_games = logs[~logs["IS_AWAY"]]
    away_games = logs[logs["IS_AWAY"]]

    home_perf = _calc_split(home_games)
    away_perf = _calc_split(away_games)

    venue_differentials = {
        "points_advantage": _diff(home_perf.get("points_per_game"), away_perf.get("points_per_game")),
        "win_pct_advantage": _diff(home_perf.get("win_pct"), away_perf.get("win_pct")),
        "ortg_advantage": None,  # Not available in manual calculation
        "drtg_advantage": None,  # Not available in manual calculation
    }

    return {
        "home_performance": home_perf,
        "away_performance": away_perf,
        "venue_differentials": venue_differentials,
    }


def _diff(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    if pd.isna(a) or pd.isna(b):
        return None
    return float(a) - float(b)


__all__ = ["get_team_venue_splits"]
