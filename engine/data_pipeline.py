"""Data retrieval utilities for the betting analyzer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

import pandas as pd

from nba_data.advanced_stats import get_season_team_stats, get_last_10_stats
from nba_data.four_factors import get_four_factors_team_stats
from nba_data.misc_stats import get_misc_team_stats
from nba_data.league_analytics import compute_league_average_ortg
from nba_data.schedule_fatigue import get_team_rest_profile, TeamRestProfile
from nba_data.venue_splits import get_team_venue_splits
from nba_data.hustle_stats import get_team_hustle_profile, TeamHustleProfile
from nba_data.head_to_head import get_head_to_head_profile


@dataclass
class TeamDataBundle:
    """Collection of raw datasets for a single team."""

    team_name: str
    season: Dict[str, float]
    last_10: Dict[str, float]
    four_factors_season: Dict[str, float]
    four_factors_last10: Dict[str, float]
    misc_season: Dict[str, Optional[float]]
    misc_last10: Dict[str, Optional[float]]
    rest_profile: TeamRestProfile
    venue_splits: Dict[str, Dict[str, Optional[float]]]
    hustle_profile: TeamHustleProfile


Fetchers = Dict[str, Callable[..., Any]]


def _get_fetcher(name: str, fetchers: Optional[Fetchers], default: Callable[..., Any]) -> Callable[..., Any]:
    if fetchers and name in fetchers:
        return fetchers[name]
    return default


def _fetch_team_stat_splits(
    team_name: str,
    season_end_year: int,
    fetchers: Optional[Fetchers],
) -> Tuple[Dict[str, float], Dict[str, float]]:
    season_fetcher = _get_fetcher("get_season_team_stats", fetchers, get_season_team_stats)
    last10_fetcher = _get_fetcher("get_last_10_stats", fetchers, get_last_10_stats)
    season = season_fetcher(team_name=team_name, season_end_year=season_end_year)
    last10 = last10_fetcher(team_name=team_name, season_end_year=season_end_year)
    return season, last10


def _fetch_four_factors(
    team_name: str,
    season_end_year: int,
    fetchers: Optional[Fetchers],
) -> Tuple[Dict[str, float], Dict[str, float]]:
    factors_fetcher = _get_fetcher("get_four_factors_team_stats", fetchers, get_four_factors_team_stats)
    season = factors_fetcher(team_name=team_name, season_end_year=season_end_year)
    last10 = factors_fetcher(
        team_name=team_name,
        season_end_year=season_end_year,
        last_n_games=10,
    )
    return season, last10


def _fetch_misc_stats(
    team_name: str,
    season_end_year: int,
    fetchers: Optional[Fetchers],
) -> Tuple[Dict[str, Optional[float]], Dict[str, Optional[float]]]:
    misc_fetcher = _get_fetcher("get_misc_team_stats", fetchers, get_misc_team_stats)
    season = misc_fetcher(team_name=team_name, season_end_year=season_end_year)
    last10 = misc_fetcher(
        team_name=team_name,
        season_end_year=season_end_year,
        last_n_games=10,
    )
    return season, last10


def fetch_team_data(
    team_name: str,
    season_end_year: int,
    upcoming_game_ts: pd.Timestamp,
    fetchers: Optional[Fetchers] = None,
) -> TeamDataBundle:
    """Fetch all raw data required for a single team."""

    print(f"📊 Fetching data for {team_name}...")
    season, last10 = _fetch_team_stat_splits(team_name, season_end_year, fetchers)
    four_factors_season, four_factors_last10 = _fetch_four_factors(team_name, season_end_year, fetchers)
    misc_season, misc_last10 = _fetch_misc_stats(team_name, season_end_year, fetchers)

    rest_fetcher = _get_fetcher("get_team_rest_profile", fetchers, get_team_rest_profile)
    try:
        rest_profile = rest_fetcher(
            team_name=team_name,
            season_end_year=season_end_year,
            upcoming_game_date=upcoming_game_ts,
        )
    except ValueError as exc:  # pragma: no cover - defensive rewrap
        raise ValueError(f"Invalid upcoming_game_date for {team_name}: {exc}") from exc
    venue_fetcher = _get_fetcher("get_team_venue_splits", fetchers, get_team_venue_splits)
    hustle_fetcher = _get_fetcher("get_team_hustle_profile", fetchers, get_team_hustle_profile)
    venue_splits = venue_fetcher(team_name=team_name, season_end_year=season_end_year)
    hustle_profile = hustle_fetcher(team_name=team_name, season_end_year=season_end_year)

    return TeamDataBundle(
        team_name=team_name,
        season=season,
        last_10=last10,
        four_factors_season=four_factors_season,
        four_factors_last10=four_factors_last10,
        misc_season=misc_season,
        misc_last10=misc_last10,
        rest_profile=rest_profile,
        venue_splits=venue_splits,
        hustle_profile=hustle_profile,
    )


def collect_matchup_data(
    home_team: str,
    away_team: str,
    season_end_year: int,
    upcoming_game_ts: pd.Timestamp,
    fetchers: Optional[Fetchers] = None,
) -> Tuple[TeamDataBundle, TeamDataBundle, float, Dict[str, Any]]:
    """Collect all datasets required for a matchup."""

    print("🏀 Fetching REAL NBA data from official NBA.com API...")
    league_fetcher = _get_fetcher(
        "compute_league_average_ortg", fetchers, compute_league_average_ortg
    )
    league_avg_ortg = league_fetcher(season_end_year=season_end_year)

    print("📊 Fetching Four Factors data for enhanced analysis...")
    print("📈 Fetching Miscellaneous Stats data (Points off Turnovers, Second Chance Points)...")
    print("🛌 Evaluating schedule rest and fatigue context...")
    print("🏟️ Analyzing venue performance splits...")
    print("🔥 Capturing hustle and effort signals...")

    home_data = fetch_team_data(home_team, season_end_year, upcoming_game_ts, fetchers)
    away_data = fetch_team_data(away_team, season_end_year, upcoming_game_ts, fetchers)

    print("✅ Successfully retrieved REAL NBA data + Four Factors + Miscellaneous Stats from official API!")

    print("🤝 Assessing head-to-head history...")
    head_to_head_fetcher = _get_fetcher("get_head_to_head_profile", fetchers, get_head_to_head_profile)
    head_to_head_profile = head_to_head_fetcher(
        team_name=home_team,
        opponent_name=away_team,
        season_end_year=season_end_year,
    )

    return home_data, away_data, league_avg_ortg, head_to_head_profile
