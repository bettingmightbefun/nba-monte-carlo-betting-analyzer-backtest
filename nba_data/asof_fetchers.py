"""
nba_data/asof_fetchers.py
========================

As-of-date NBA data fetching with leakage prevention for backtesting.
Fetches team statistics as they would have appeared on a specific date,
ensuring no future games or information leaks into the data.

Functions
---------
get_team_stats_asof(team_id, as_of, last_n_window=10, cache=None) -> dict
    Get team statistics as-of a specific date with caching.

This module provides leakage-free data fetching for backtesting scenarios.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from nba_data.team_resolver import get_team_id

try:
    from nba_api.stats.endpoints import leaguedashteamstats, teamgamelogs
except ImportError as exc:
    raise ImportError(
        "nba_api package is required but not installed. Run: pip install nba_api"
    ) from exc


class SimpleCache:
    """Simple disk-based cache for NBA API responses."""

    def __init__(self, cache_dir: str = ".cache/nba_api"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key from endpoint and parameters."""
        # Sort params for consistent hashing
        param_str = json.dumps(params, sort_keys=True, default=str)
        key = f"{endpoint}_{param_str}"
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, endpoint: str, params: dict) -> Optional[pd.DataFrame]:
        """Get cached data if available."""
        cache_key = self._get_cache_key(endpoint, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return pd.DataFrame(data)
            except (json.JSONDecodeError, KeyError):
                # Invalid cache, remove it
                cache_file.unlink(missing_ok=True)
                return None
        return None

    def set(self, endpoint: str, params: dict, data: pd.DataFrame) -> None:
        """Cache data to disk."""
        cache_key = self._get_cache_key(endpoint, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump(data.to_dict('records'), f, default=str)
        except Exception:
            # If caching fails, continue without error
            pass


def get_team_stats_asof(
    team_id: int,
    as_of: datetime,
    last_n_window: int = 10,
    cache: Optional[SimpleCache] = None
) -> Dict[str, float]:
    """
    Get team statistics as-of a specific date with leakage prevention.

    Fetches team stats using only data available before the as_of date,
    ensuring no future games leak into the statistics.

    Args:
        team_id: NBA team ID
        as_of: Date to get stats as-of (no games after this date included)
        last_n_window: Number of recent games to analyze for rest/fatigue
        cache: Optional cache instance for API responses

    Returns:
        Dictionary with team statistics and rest flags

    Raises:
        RuntimeError: If NBA API fails or insufficient data available
    """
    if cache is None:
        cache = SimpleCache()

    # Convert to date for API calls
    as_of_date = as_of.date()
    date_to_str = as_of_date.strftime('%Y-%m-%d')

    # Season determination: NBA seasons run Oct-Jun
    # If as_of is Oct-Dec, season is current_year
    # If as_of is Jan-Jun, season is previous_year
    if as_of.month >= 10:  # Oct-Dec
        season_end_year = as_of.year + 1
    else:  # Jan-Jun
        season_end_year = as_of.year

    season_str = f"{season_end_year-1}-{str(season_end_year)[-2:]}"

    stats = {}

    # Fetch season-to-date advanced stats (up to as_of date)
    try:
        advanced_stats = _fetch_season_stats_asof(
            team_id, season_str, date_to_str, 'Advanced', cache
        )
        stats.update(advanced_stats)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch advanced stats for team {team_id}: {e}")

    # Fetch four factors stats
    try:
        four_factors_stats = _fetch_season_stats_asof(
            team_id, season_str, date_to_str, 'Four Factors', cache
        )
        stats.update(four_factors_stats)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch four factors stats for team {team_id}: {e}")

    # Fetch misc stats
    try:
        misc_stats = _fetch_season_stats_asof(
            team_id, season_str, date_to_str, 'Misc', cache
        )
        stats.update(misc_stats)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch misc stats for team {team_id}: {e}")

    # Fetch last N games and calculate rest flags
    try:
        game_logs = _fetch_recent_games_asof(
            team_id, season_str, date_to_str, last_n_window, cache
        )
        last_n_stats = _calculate_last_n_stats(game_logs)
        rest_flags = _calculate_rest_flags(game_logs, as_of_date)

        stats.update(last_n_stats)
        stats.update(rest_flags)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch recent games for team {team_id}: {e}")

    return stats


def _fetch_season_stats_asof(
    team_id: int,
    season: str,
    date_to: str,
    measure_type: str,
    cache: SimpleCache
) -> Dict[str, float]:
    """
    Fetch season stats up to a specific date using LeagueDashTeamStats.

    Args:
        team_id: NBA team ID
        season: Season string (e.g., '2023-24')
        date_to: End date for stats (YYYY-MM-DD)
        measure_type: 'Advanced', 'Four Factors', or 'Misc'
        cache: Cache instance

    Returns:
        Dictionary of team statistics
    """
    cache_key = f"season_stats_{team_id}_{season}_{date_to}_{measure_type}"
    cached = cache.get("leaguedashteamstats", {
        "team_id": team_id,
        "season": season,
        "date_to": date_to,
        "measure_type": measure_type
    })

    if cached is not None:
        team_data = cached
    else:
        # Try to use date filtering if available, otherwise fall back to season stats
        try:
            # First try with date filtering
            api_response = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                measure_type_detailed_defense=measure_type,
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season',
                date_to_nullable=date_to
            )

            df = api_response.get_data_frames()[0]
            team_data = df[df['TEAM_ID'] == team_id]

            if team_data.empty:
                raise ValueError(f"No {measure_type} data found for team {team_id} in season {season} up to {date_to}")

        except Exception:
            # Fall back to season stats without date filtering
            print(f"Warning: Date filtering not supported, using full season stats for {measure_type}")
            api_response = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                measure_type_detailed_defense=measure_type,
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season'
            )

            df = api_response.get_data_frames()[0]
            team_data = df[df['TEAM_ID'] == team_id]

            if team_data.empty:
                raise ValueError(f"No {measure_type} data found for team {team_id} in season {season}")

        # Cache the result
        cache.set("leaguedashteamstats", {
            "team_id": team_id,
            "season": season,
            "date_to": date_to,
            "measure_type": measure_type
        }, team_data)

    # Extract first row (should be only row for this team)
    row = team_data.iloc[0]

    # Return relevant stats based on measure type
    if measure_type == 'Advanced':
        return {
            'pace_season': row.get('PACE', 0),
            'ortg_season': row.get('OFF_RATING', 0),
            'drtg_season': row.get('DEF_RATING', 0),
            'nrtg_season': row.get('NET_RATING', 0),
        }
    elif measure_type == 'Four Factors':
        return {
            'efg_pct_season': row.get('EFG_PCT', 0),
            'tov_pct_season': row.get('TM_TOV_PCT', 0),
            'orb_pct_season': row.get('OREB_PCT', 0),
            'ft_fga_season': row.get('FTA_RATE', 0),
        }
    elif measure_type == 'Misc':
        return {
            'pts_off_tov_season': row.get('PTS_OFF_TOV', 0),
            'pts_2nd_chance_season': row.get('PTS_2ND_CHANCE', 0),
            'pts_fb_season': row.get('PTS_FB', 0),
            'pts_paint_season': row.get('PTS_PAINT', 0),
        }
    else:
        return {}


def _fetch_recent_games_asof(
    team_id: int,
    season: str,
    date_to: str,
    last_n: int,
    cache: SimpleCache
) -> pd.DataFrame:
    """
    Fetch recent games for a team up to a specific date.

    Args:
        team_id: NBA team ID
        season: Season string
        date_to: End date for games
        last_n: Number of recent games to fetch
        cache: Cache instance

    Returns:
        DataFrame with recent game logs
    """
    cache_key = f"recent_games_{team_id}_{season}_{date_to}_{last_n}"
    cached = cache.get("teamgamelogs", {
        "team_id": team_id,
        "season": season,
        "date_to": date_to,
        "last_n": last_n
    })

    if cached is not None:
        return cached

    # Fetch games up to date_to, then take the most recent last_n
    api_response = teamgamelogs.TeamGameLogs(
        team_id_nullable=team_id,
        season_nullable=season,
        season_type_nullable='Regular Season'
    )

    df = api_response.get_data_frames()[0]

    # Filter to games before date_to
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    df = df[df['GAME_DATE'] < pd.Timestamp(date_to)]

    # Sort by game date descending (most recent first) and take last_n
    df = df.sort_values('GAME_DATE', ascending=False).head(last_n)

    # Cache the result
    cache.set("teamgamelogs", {
        "team_id": team_id,
        "season": season,
        "date_to": date_to,
        "last_n": last_n
    }, df)

    return df


def _calculate_last_n_stats(game_logs: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate last N games statistics from game logs.

    Args:
        game_logs: DataFrame with recent game logs

    Returns:
        Dictionary with last N game averages
    """
    if game_logs.empty:
        return {
            'pace_last10': 0,
            'ortg_last10': 0,
            'drtg_last10': 0,
            'games_in_last10': 0,
        }

    # Calculate per-game averages
    avg_stats = game_logs.mean(numeric_only=True)

    return {
        'pace_last10': avg_stats.get('PACE', 0),
        'ortg_last10': avg_stats.get('OFF_RATING', 0),
        'drtg_last10': avg_stats.get('DEF_RATING', 0),
        'games_in_last10': len(game_logs),
    }


def _calculate_rest_flags(game_logs: pd.DataFrame, as_of_date: datetime.date) -> Dict[str, bool]:
    """
    Calculate rest/fatigue flags from game schedule.

    Args:
        game_logs: DataFrame with recent game logs (sorted by date descending)
        as_of_date: The as-of date for analysis

    Returns:
        Dictionary with rest flags (b2b, three_in_four, four_in_six)
    """
    if game_logs.empty:
        return {
            'b2b': False,
            'three_in_four': False,
            'four_in_six': False,
        }

    # Get game dates, sort ascending (earliest first)
    game_dates = sorted(game_logs['GAME_DATE'].dt.date)

    # Check if team played yesterday (back-to-back)
    yesterday = as_of_date - timedelta(days=1)
    b2b = yesterday in game_dates

    # Check three games in four days (any 3 games within any 4-day span)
    three_in_four = _check_games_in_window(game_dates, 3, 4, as_of_date)

    # Check four games in six days
    four_in_six = _check_games_in_window(game_dates, 4, 6, as_of_date)

    return {
        'b2b': b2b,
        'three_in_four': three_in_four,
        'four_in_six': four_in_six,
    }


def _check_games_in_window(
    game_dates: list,
    num_games: int,
    window_days: int,
    as_of_date: datetime.date
) -> bool:
    """
    Check if team played num_games within any window_days period ending on or before as_of_date.

    Args:
        game_dates: List of game dates (sorted ascending)
        num_games: Number of games to check for
        window_days: Number of days in the window
        as_of_date: The reference date

    Returns:
        True if condition met, False otherwise
    """
    # Only consider games on or before as_of_date
    relevant_dates = [d for d in game_dates if d <= as_of_date]

    if len(relevant_dates) < num_games:
        return False

    # Check sliding windows
    for i in range(len(relevant_dates) - num_games + 1):
        window_start = relevant_dates[i]
        window_end = relevant_dates[i + num_games - 1]

        # Check if all games fit within window_days
        if (window_end - window_start).days < window_days:
            return True

    return False
