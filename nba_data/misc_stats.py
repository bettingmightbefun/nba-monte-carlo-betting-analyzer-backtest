"""
misc_stats.py
=============

NBA Miscellaneous Statistics fetching for enhanced Monte Carlo modeling.
Fetches high-value stats that complement the Four Factors for better predictions.

Functions
---------
get_misc_team_stats(team_name: str, season_end_year: int, last_n_games: int = None) -> Dict[str, float]
    Get miscellaneous team statistics from NBA API.

High-Value Miscellaneous Stats:
- Points off Turnovers: Shows defensive pressure + offensive execution
- Second Chance Points: Shows offensive rebounding conversion efficiency
- Fast Break Points: Shows transition offense effectiveness (optional)

These stats provide additional context beyond the Four Factors and help
capture specific game situations that affect scoring.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

from nba_data.base_fetcher import fetch_team_data


def get_misc_team_stats(
    team_name: str,
    season_end_year: int,
    last_n_games: Optional[int] = None
) -> Dict[str, Optional[float]]:
    """
    Get miscellaneous team statistics from NBA API.
    
    Fetches miscellaneous stats that provide additional context for Monte Carlo modeling:
    - PTS_OFF_TOV: Points off turnovers (shows defensive pressure + offensive execution)
    - PTS_2ND_CHANCE: Second chance points (shows OREB conversion efficiency)
    - PTS_FB: Fast break points (shows transition offense)
    - PTS_PAINT: Points in the paint (shows interior offense)
    
    Also fetches opponent versions to understand defensive performance.
    
    Args:
        team_name: Team name, nickname, or abbreviation
        season_end_year: Year the season ends (e.g., 2024 for 2023-24 season)
        last_n_games: If provided, get stats for last N games only
        
    Returns:
        Dictionary with keys: 'pts_off_tov', 'pts_2nd_chance', 'pts_fb', 'pts_paint',
                             'opp_pts_off_tov', 'opp_pts_2nd_chance', 'opp_pts_fb', 'opp_pts_paint'.
        Values are Optional[float] where ``None`` indicates the statistic was not
        provided by the NBA API response for the requested period.
        
    Raises:
        RuntimeError: If NBA API fails or team data unavailable
        ValueError: If required statistics cannot be extracted
        
    Example:
        >>> stats = get_misc_team_stats("Los Angeles Lakers", 2024)
        >>> print(f"Points off TO: {stats['pts_off_tov']} | 2nd Chance: {stats['pts_2nd_chance']}")

        >>> recent = get_misc_team_stats("Lakers", 2024, last_n_games=10)
        >>> print(f"Recent Points off TO: {recent['pts_off_tov']}")
    """
    team_row = fetch_team_data(team_name, season_end_year, 'Misc', last_n_games)
    
    # Extract Miscellaneous Stats - check what's available
    available_cols = list(team_row.index)
    print(f"   Available Misc columns: {available_cols[:20]}...")  # Debug: show available columns
    
    # Try to extract the high-value miscellaneous stats
    misc_stats: Dict[str, Optional[float]] = {}
    
    def _extract_numeric(column_names, target_key):
        for col in column_names:
            if col in team_row:
                raw_value = team_row[col]
                try:
                    numeric_value = float(raw_value)
                except (TypeError, ValueError):
                    numeric_value = None
                if numeric_value is not None and math.isnan(numeric_value):
                    numeric_value = None
                misc_stats[target_key] = numeric_value
                if numeric_value is None:
                    print(
                        f"   Warning: {target_key} returned NaN/invalid value for {team_name}; treating as missing"
                    )
                return
        print(f"   Warning: {target_key} not found for {team_name}")
        misc_stats[target_key] = None

    # Points off Turnovers (high value)
    _extract_numeric(['PTS_OFF_TOV', 'POINTS_OFF_TURNOVERS', 'PTS_TURNOVERS'], 'pts_off_tov')

    # Second Chance Points (high value)
    _extract_numeric(['PTS_2ND_CHANCE', 'SECOND_CHANCE_PTS', 'PTS_SECOND_CHANCE'], 'pts_2nd_chance')

    # Fast Break Points (moderate value)
    _extract_numeric(['PTS_FB', 'FAST_BREAK_PTS', 'PTS_FASTBREAK'], 'pts_fb')

    # Points in Paint (moderate value, may overlap with EFG%)
    _extract_numeric(['PTS_PAINT', 'POINTS_IN_PAINT', 'PTS_IN_PAINT'], 'pts_paint')

    # Try to get opponent versions (defensive stats)
    _extract_numeric(['OPP_PTS_OFF_TOV', 'OPP_POINTS_OFF_TURNOVERS'], 'opp_pts_off_tov')
    _extract_numeric(['OPP_PTS_2ND_CHANCE', 'OPP_SECOND_CHANCE_PTS'], 'opp_pts_2nd_chance')
    _extract_numeric(['OPP_PTS_FB', 'OPP_FAST_BREAK_PTS'], 'opp_pts_fb')
    _extract_numeric(['OPP_PTS_PAINT', 'OPP_POINTS_IN_PAINT'], 'opp_pts_paint')

    # Log successful extraction
    period_desc = f"last {last_n_games} games" if last_n_games else "season"
    def _fmt(value: Optional[float]) -> str:
        return f"{value:.1f}" if value is not None else "N/A"

    print(
        "✅ Got Misc stats "
        f"{period_desc}: PtsOffTO={_fmt(misc_stats['pts_off_tov'])}, "
        f"2ndChance={_fmt(misc_stats['pts_2nd_chance'])}, "
        f"FastBreak={_fmt(misc_stats['pts_fb'])}"
    )
    
    return misc_stats


def analyze_misc_advantages(
    home_misc: Dict[str, Optional[float]],
    away_misc: Dict[str, Optional[float]],
) -> Dict[str, Dict[str, float]]:
    """
    Analyze miscellaneous stats advantages between two teams.
    
    Compares offensive miscellaneous stats of each team against the defensive
    miscellaneous stats allowed by their opponent to identify potential advantages.
    
    Args:
        home_misc: Home team's miscellaneous statistics
        away_misc: Away team's miscellaneous statistics
        
    Returns:
        Dictionary with 'home_advantages' and 'away_advantages' keys,
        each containing miscellaneous stats differential analysis
        
    Example:
        >>> home_misc = get_misc_team_stats("Lakers", 2024)
        >>> away_misc = get_misc_team_stats("Warriors", 2024) 
        >>> advantages = analyze_misc_advantages(home_misc, away_misc)
        >>> print(f"Home turnover points advantage: {advantages['home_advantages']['pts_off_tov_diff']:.1f}")
    """
    def _normalized_value(stats: Dict[str, Optional[float]], key: str) -> float:
        value = stats.get(key)
        if value is None:
            return 0.0
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if math.isnan(numeric):
            return 0.0
        return numeric

    # Calculate home team advantages (home offense vs away defense)
    home_advantages = {
        'pts_off_tov_diff': _normalized_value(home_misc, 'pts_off_tov')
        - _normalized_value(away_misc, 'opp_pts_off_tov'),
        'pts_2nd_chance_diff': _normalized_value(home_misc, 'pts_2nd_chance')
        - _normalized_value(away_misc, 'opp_pts_2nd_chance'),
        'pts_fb_diff': _normalized_value(home_misc, 'pts_fb')
        - _normalized_value(away_misc, 'opp_pts_fb'),
        'pts_paint_diff': _normalized_value(home_misc, 'pts_paint')
        - _normalized_value(away_misc, 'opp_pts_paint')
    }

    # Calculate away team advantages (away offense vs home defense)
    away_advantages = {
        'pts_off_tov_diff': _normalized_value(away_misc, 'pts_off_tov')
        - _normalized_value(home_misc, 'opp_pts_off_tov'),
        'pts_2nd_chance_diff': _normalized_value(away_misc, 'pts_2nd_chance')
        - _normalized_value(home_misc, 'opp_pts_2nd_chance'),
        'pts_fb_diff': _normalized_value(away_misc, 'pts_fb')
        - _normalized_value(home_misc, 'opp_pts_fb'),
        'pts_paint_diff': _normalized_value(away_misc, 'pts_paint')
        - _normalized_value(home_misc, 'opp_pts_paint')
    }
    
    return {
        'home_advantages': home_advantages,
        'away_advantages': away_advantages
    }


# Test function for this module
def test_misc_stats():
    """Test NBA miscellaneous statistics fetching functionality."""
    print("🔍 Testing NBA Miscellaneous Stats Fetcher...")
    
    test_teams = ["Los Angeles Lakers", "Golden State Warriors"]
    
    for team in test_teams:
        try:
            print(f"\n📊 Testing {team}:")
            
            # Test season miscellaneous stats
            season_misc = get_misc_team_stats(team, 2024)
            print(f"✅ Season Misc Stats: {season_misc}")
            
            # Test last 10 miscellaneous stats  
            recent_misc = get_misc_team_stats(team, 2024, last_n_games=10)
            print(f"✅ Last 10 Misc Stats: {recent_misc}")
            
        except Exception as e:
            print(f"❌ Error testing {team}: {e}")
    
    # Test matchup analysis
    try:
        print(f"\n🔬 Testing miscellaneous matchup analysis:")
        home_misc = get_misc_team_stats("Los Angeles Lakers", 2024)
        away_misc = get_misc_team_stats("Golden State Warriors", 2024)
        
        advantages = analyze_misc_advantages(home_misc, away_misc)
        print(f"✅ Misc matchup analysis: {advantages}")
        
    except Exception as e:
        print(f"❌ Error testing misc matchup analysis: {e}")
    
    print("\n✅ Miscellaneous stats tests complete!")


if __name__ == "__main__":
    test_misc_stats()
