"""
advanced_stats.py
=================

NBA Advanced Statistics fetching (Pace, Offensive Rating, Defensive Rating).
Handles both season-long and recent form statistics with robust error handling.

Functions
---------
get_season_team_stats(team_name: str, season_end_year: int) -> Dict[str, float]
    Get season-long pace, offensive rating and defensive rating for a team.

get_last_10_stats(team_name: str, season_end_year: int) -> Dict[str, float]  
    Get last 10 games pace, offensive rating and defensive rating for a team.

This module focuses on advanced basketball analytics that form the core
of Monte Carlo simulation inputs.
"""

from __future__ import annotations

from typing import Dict

from nba_data.base_fetcher import (
    fetch_team_data, 
    extract_column_value, 
    calculate_pace_from_basic_stats
)


def get_season_team_stats(team_name: str, season_end_year: int) -> Dict[str, float]:
    """
    Get season-long team statistics from NBA API.
    
    Fetches comprehensive team statistics for the entire season including
    pace (possessions per 48 minutes), offensive rating (points per 100 possessions),
    and defensive rating (points allowed per 100 possessions).
    
    Args:
        team_name: Team name, nickname, or abbreviation
        season_end_year: Year the season ends (e.g., 2024 for 2023-24 season)
        
    Returns:
        Dictionary with keys: 'pace', 'ortg', 'drtg'
        
    Raises:
        RuntimeError: If NBA API fails or team data unavailable
        ValueError: If required statistics cannot be extracted or calculated
        
    Example:
        >>> stats = get_season_team_stats("Los Angeles Lakers", 2024)
        >>> print(f"Pace: {stats['pace']:.1f}, ORtg: {stats['ortg']:.1f}")
    """
    team_row = fetch_team_data(team_name, season_end_year, 'Advanced')
    
    # Extract pace with fallback calculation
    pace = _extract_pace_stat(team_row, team_name, "")
    
    # Extract offensive and defensive ratings
    ortg = extract_column_value(
        team_row, 
        ['OFF_RATING', 'E_OFF_RATING', 'OFFRTG'], 
        team_name, 
        'offensive rating'
    )
    
    drtg = extract_column_value(
        team_row, 
        ['DEF_RATING', 'E_DEF_RATING', 'DEFRTG'], 
        team_name, 
        'defensive rating'
    )
    
    print(f"✅ Got season stats: Pace={pace:.1f}, ORtg={ortg:.1f}, DRtg={drtg:.1f}")
    
    return {
        "pace": pace,
        "ortg": ortg,
        "drtg": drtg
    }


def get_last_10_stats(team_name: str, season_end_year: int) -> Dict[str, float]:
    """
    Get last 10 games statistics from NBA API.
    
    Fetches recent team performance data to capture current form and momentum.
    Uses the same statistical categories as season stats but limited to the
    most recent 10 games played.
    
    Args:
        team_name: Team name, nickname, or abbreviation
        season_end_year: Year the season ends (e.g., 2024 for 2023-24 season)
        
    Returns:
        Dictionary with keys: 'pace', 'ortg', 'drtg'
        
    Raises:
        RuntimeError: If NBA API fails or team data unavailable
        ValueError: If required statistics cannot be extracted or calculated
        
    Example:
        >>> recent_stats = get_last_10_stats("Golden State Warriors", 2024)
        >>> print(f"Recent pace: {recent_stats['pace']:.1f}")
    """
    team_row = fetch_team_data(team_name, season_end_year, 'Advanced', last_n_games=10)
    
    # Extract pace with fallback calculation
    pace = _extract_pace_stat(team_row, team_name, "last 10")
    
    # Extract offensive and defensive ratings
    ortg = extract_column_value(
        team_row, 
        ['OFF_RATING', 'E_OFF_RATING', 'OFFRTG'], 
        team_name, 
        'offensive rating (last 10)'
    )
    
    drtg = extract_column_value(
        team_row, 
        ['DEF_RATING', 'E_DEF_RATING', 'DEFRTG'], 
        team_name, 
        'defensive rating (last 10)'
    )
    
    print(f"✅ Got last 10 stats: Pace={pace:.1f}, ORtg={ortg:.1f}, DRtg={drtg:.1f}")
    
    return {
        "pace": pace,
        "ortg": ortg,
        "drtg": drtg
    }


def _extract_pace_stat(team_row, team_name: str, period_desc: str) -> float:
    """
    Extract pace statistic with fallback to calculation from basic stats.
    
    Args:
        team_row: Pandas Series containing team statistics
        team_name: Team name for error messages
        period_desc: Description of the period (e.g., "last 10") for error messages
        
    Returns:
        Pace value (possessions per 48 minutes)
        
    Raises:
        ValueError: If pace cannot be extracted or calculated
    """
    # Try to extract pace from advanced stats columns
    pace_columns = ['PACE', 'E_PACE', 'Pace']
    
    for col_name in pace_columns:
        if col_name in team_row and team_row[col_name] is not None:
            try:
                return float(team_row[col_name])
            except (ValueError, TypeError):
                continue
    
    # Fallback to calculating pace from basic stats
    try:
        return calculate_pace_from_basic_stats(team_row, team_name, period_desc)
    except ValueError as e:
        # Show available columns for debugging
        available_cols = list(team_row.index)
        print(f"   Available columns: {available_cols[:15]}...")  # Show first 15 columns
        raise ValueError(f"Could not extract or calculate pace for {team_name} {period_desc}: {e}") from e


# Test function for this module
def test_advanced_stats():
    """Test NBA advanced statistics fetching functionality."""
    print("🔍 Testing NBA Advanced Stats Fetcher...")
    
    test_teams = ["Los Angeles Lakers", "Golden State Warriors"]
    
    for team in test_teams:
        try:
            print(f"\n📊 Testing {team}:")
            
            # Test season stats
            season_stats = get_season_team_stats(team, 2024)
            print(f"✅ Season stats: {season_stats}")
            
            # Test last 10 stats  
            recent_stats = get_last_10_stats(team, 2024)
            print(f"✅ Last 10 stats: {recent_stats}")
            
        except Exception as e:
            print(f"❌ Error testing {team}: {e}")
    
    print("\n✅ Advanced stats tests complete!")


if __name__ == "__main__":
    test_advanced_stats()
