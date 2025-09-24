"""
base_fetcher.py
===============

Common NBA API utilities and error handling for all stat fetching operations.
Provides base functionality that other fetchers can inherit and reuse.

Functions
---------
fetch_team_data(team_name, season_end_year, measure_type, last_n_games=None) -> pandas.DataFrame
    Core NBA API fetching logic with error handling and rate limiting.

validate_team_data(team_data, team_name, stat_type) -> None
    Validates that team data was successfully retrieved.

This module centralizes common API logic to reduce duplication across fetchers.
"""

from __future__ import annotations

import time
from typing import Dict, Optional
import pandas as pd

from nba_data.team_resolver import get_team_id, format_season

try:
    from nba_api.stats.endpoints import leaguedashteamstats
except ImportError as exc:
    raise ImportError(
        "nba_api package is required but not installed. Run: pip install nba_api"
    ) from exc


def fetch_team_data(
    team_name: str, 
    season_end_year: int, 
    measure_type: str,
    last_n_games: Optional[int] = None
) -> pd.DataFrame:
    """
    Core NBA API fetching logic with error handling and rate limiting.
    
    Args:
        team_name: Team name, nickname, or abbreviation
        season_end_year: Year the season ends (e.g., 2024 for 2023-24 season)
        measure_type: NBA API measure type ('Advanced', 'Four Factors', etc.)
        last_n_games: If provided, get stats for last N games only
        
    Returns:
        DataFrame containing team statistics
        
    Raises:
        RuntimeError: If NBA API fails or team data unavailable
        ValueError: If invalid parameters provided
    """
    team_id = get_team_id(team_name)
    season = format_season(season_end_year)
    
    period_desc = f"last {last_n_games} games" if last_n_games else "season"
    print(f"📊 Fetching {measure_type} {period_desc} stats for {team_name}")
    
    try:
        # Build API parameters
        kwargs = {
            'season': season,
            'season_type_all_star': 'Regular Season',
            'measure_type_detailed_defense': measure_type,
            'per_mode_detailed': 'PerGame'
        }
        
        # Add last_n_games parameter if specified
        if last_n_games is not None:
            kwargs['last_n_games'] = last_n_games
            
        # Make API call
        team_stats = leaguedashteamstats.LeagueDashTeamStats(**kwargs)
        
        # Add small delay to be respectful to NBA API
        time.sleep(0.5)
        
        # Get the data
        df = team_stats.get_data_frames()[0]
        
        # Find our team
        team_data = df[df['TEAM_ID'] == team_id]
        validate_team_data(team_data, team_name, f"{measure_type} {period_desc}")
        
        return team_data.iloc[0]
        
    except Exception as e:
        error_msg = f"Failed to get {measure_type} {period_desc} stats for {team_name}: {e}"
        print(f"❌ CRITICAL ERROR: {error_msg}")
        raise RuntimeError(f"Cannot proceed without real NBA {measure_type} data for {team_name}. Error: {e}") from e


def validate_team_data(team_data: pd.DataFrame, team_name: str, stat_type: str) -> None:
    """
    Validates that team data was successfully retrieved.
    
    Args:
        team_data: DataFrame containing team data
        team_name: Name of the team for error messages
        stat_type: Type of stats being fetched for error messages
        
    Raises:
        RuntimeError: If no data found for the team
    """
    if team_data.empty:
        raise RuntimeError(f"No {stat_type} data found for team {team_name}")


def extract_column_value(team_row: pd.Series, column_names: list, team_name: str, stat_name: str) -> float:
    """
    Extract a statistic value from team data, trying multiple possible column names.
    
    Args:
        team_row: Pandas Series containing team statistics
        column_names: List of possible column names to try (in order of preference)
        team_name: Team name for error messages
        stat_name: Human-readable name of the statistic for error messages
        
    Returns:
        Float value of the statistic
        
    Raises:
        ValueError: If none of the column names are found
    """
    for col_name in column_names:
        if col_name in team_row and pd.notna(team_row[col_name]):
            return float(team_row[col_name])
    
    available_cols = list(team_row.index)
    raise ValueError(
        f"No {stat_name} data available for {team_name}. "
        f"Tried columns: {column_names}. "
        f"Available columns: {available_cols[:10]}..."
    )


def calculate_pace_from_basic_stats(team_row: pd.Series, team_name: str, period_desc: str = "") -> float:
    """
    Calculate pace from basic team statistics when advanced pace isn't available.
    
    Formula: Pace = 48 * Possessions / (Minutes / 5)
    Where Possessions = FGA + 0.44 * FTA - OREB + TOV
    
    Args:
        team_row: Pandas Series containing team statistics
        team_name: Team name for error messages
        period_desc: Description of the period (e.g., "last 10") for error messages
        
    Returns:
        Calculated pace value
        
    Raises:
        ValueError: If required columns are missing or invalid
    """
    required_cols = ['FGA', 'FTA', 'TOV', 'OREB', 'MIN']
    
    # Check if all required columns are available
    missing_cols = [col for col in required_cols if col not in team_row]
    if missing_cols:
        raise ValueError(
            f"Missing required columns for {team_name} {period_desc} pace calculation: {missing_cols}"
        )
    
    # Extract values
    fga = float(team_row['FGA'])
    fta = float(team_row['FTA']) 
    tov = float(team_row['TOV'])
    oreb = float(team_row['OREB'])
    min_played = float(team_row['MIN'])
    
    # Validate values
    if min_played <= 0:
        raise ValueError(f"Invalid minutes played for {team_name} {period_desc}: {min_played}")
    
    # Calculate possessions
    possessions = fga + 0.44 * fta - oreb + tov
    if possessions <= 0:
        raise ValueError(f"Invalid possessions calculation for {team_name} {period_desc}: {possessions}")
    
    # Convert to per-48 minute pace
    pace = 48.0 * possessions / (min_played / 5.0)
    
    return pace
