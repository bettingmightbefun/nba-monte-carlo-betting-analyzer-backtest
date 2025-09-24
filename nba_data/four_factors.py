"""
four_factors.py
===============

NBA Four Factors statistics fetching and analysis.
The Four Factors are the key basketball metrics that research shows 
are most predictive of wins and losses.

Functions
---------
get_four_factors_team_stats(team_name: str, season_end_year: int, last_n_games: int = None) -> Dict[str, float]
    Get Four Factors team statistics from NBA API.

The Four Factors are:
- EFG% (Effective Field Goal %): Shooting efficiency accounting for 3-point value
- FTA Rate: Free throw attempt rate (aggression getting to the line)  
- TOV% (Turnover %): Ball security and possession management
- OREB% (Offensive Rebounding %): Second-chance opportunities

This module focuses on these advanced basketball analytics that provide
better predictive power than traditional team ratings alone.
"""

from __future__ import annotations

from typing import Dict, Optional

from nba_data.base_fetcher import fetch_team_data


def get_four_factors_team_stats(
    team_name: str, 
    season_end_year: int, 
    last_n_games: Optional[int] = None
) -> Dict[str, float]:
    """
    Get Four Factors team statistics from NBA API.
    
    Fetches the Four Factors that research shows are most predictive of wins:
    - EFG_PCT: Effective Field Goal Percentage
    - FTA_RATE: Free Throw Attempt Rate  
    - TM_TOV_PCT: Team Turnover Percentage
    - OREB_PCT: Offensive Rebound Percentage
    
    Also fetches opponent Four Factors (what the team allows defensively):
    - OPP_EFG_PCT: Opponent Effective Field Goal Percentage
    - OPP_FTA_RATE: Opponent Free Throw Attempt Rate
    - OPP_TOV_PCT: Opponent Turnover Percentage  
    - OPP_OREB_PCT: Opponent Offensive Rebound Percentage
    
    Args:
        team_name: Team name, nickname, or abbreviation
        season_end_year: Year the season ends (e.g., 2024 for 2023-24 season)
        last_n_games: If provided, get stats for last N games only
        
    Returns:
        Dictionary with keys: 'efg_pct', 'fta_rate', 'tov_pct', 'oreb_pct',
                             'opp_efg_pct', 'opp_fta_rate', 'opp_tov_pct', 'opp_oreb_pct'
        
    Raises:
        RuntimeError: If NBA API fails or team data unavailable
        ValueError: If required statistics cannot be extracted
        
    Example:
        >>> stats = get_four_factors_team_stats("Los Angeles Lakers", 2024)
        >>> print(f"EFG%: {stats['efg_pct']:.3f}, TOV%: {stats['tov_pct']:.3f}")
        
        >>> recent = get_four_factors_team_stats("Lakers", 2024, last_n_games=10)
        >>> print(f"Recent EFG%: {recent['efg_pct']:.3f}")
    """
    team_row = fetch_team_data(team_name, season_end_year, 'Four Factors', last_n_games)
    
    # Extract Four Factors - these should always be available with this measure type
    required_cols = [
        'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 
        'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT'
    ]
    
    # Validate all required columns are present
    missing_cols = [col for col in required_cols if col not in team_row]
    if missing_cols:
        available_cols = list(team_row.index)
        raise ValueError(
            f"Missing required Four Factors columns for {team_name}: {missing_cols}. "
            f"Available columns: {available_cols[:15]}..."
        )
    
    # Extract all Four Factors data
    four_factors = {
        "efg_pct": float(team_row['EFG_PCT']),
        "fta_rate": float(team_row['FTA_RATE']),
        "tov_pct": float(team_row['TM_TOV_PCT']),
        "oreb_pct": float(team_row['OREB_PCT']),
        "opp_efg_pct": float(team_row['OPP_EFG_PCT']),
        "opp_fta_rate": float(team_row['OPP_FTA_RATE']),
        "opp_tov_pct": float(team_row['OPP_TOV_PCT']),
        "opp_oreb_pct": float(team_row['OPP_OREB_PCT'])
    }
    
    # Log successful extraction
    period_desc = f"last {last_n_games} games" if last_n_games else "season"
    print(f"✅ Got Four Factors {period_desc}: EFG%={four_factors['efg_pct']:.3f}, "
          f"TOV%={four_factors['tov_pct']:.3f}, OREB%={four_factors['oreb_pct']:.3f}, "
          f"FTA_Rate={four_factors['fta_rate']:.3f}")
    
    return four_factors


def analyze_four_factors_advantage(home_four_factors: Dict[str, float], away_four_factors: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Analyze Four Factors matchup advantages between two teams.
    
    Compares offensive Four Factors of each team against the defensive
    Four Factors allowed by their opponent to identify potential advantages.
    
    Args:
        home_four_factors: Home team's Four Factors statistics
        away_four_factors: Away team's Four Factors statistics
        
    Returns:
        Dictionary with 'home_advantages' and 'away_advantages' keys,
        each containing Four Factors differential analysis
        
    Example:
        >>> home_ff = get_four_factors_team_stats("Lakers", 2024)
        >>> away_ff = get_four_factors_team_stats("Warriors", 2024) 
        >>> advantages = analyze_four_factors_advantage(home_ff, away_ff)
        >>> print(f"Home EFG advantage: {advantages['home_advantages']['efg_diff']:.3f}")
    """
    # Calculate home team advantages (home offense vs away defense)
    home_advantages = {
        'efg_diff': home_four_factors['efg_pct'] - away_four_factors['opp_efg_pct'],
        'fta_diff': home_four_factors['fta_rate'] - away_four_factors['opp_fta_rate'],
        'tov_diff': away_four_factors['opp_tov_pct'] - home_four_factors['tov_pct'],  # Lower TOV% is better
        'oreb_diff': home_four_factors['oreb_pct'] - away_four_factors['opp_oreb_pct']
    }
    
    # Calculate away team advantages (away offense vs home defense)
    away_advantages = {
        'efg_diff': away_four_factors['efg_pct'] - home_four_factors['opp_efg_pct'],
        'fta_diff': away_four_factors['fta_rate'] - home_four_factors['opp_fta_rate'],
        'tov_diff': home_four_factors['opp_tov_pct'] - away_four_factors['tov_pct'],  # Lower TOV% is better
        'oreb_diff': away_four_factors['oreb_pct'] - home_four_factors['opp_oreb_pct']
    }
    
    return {
        'home_advantages': home_advantages,
        'away_advantages': away_advantages
    }


# Test function for this module
def test_four_factors():
    """Test NBA Four Factors fetching functionality."""
    print("🔍 Testing NBA Four Factors Fetcher...")
    
    test_teams = ["Los Angeles Lakers", "Golden State Warriors"]
    
    for team in test_teams:
        try:
            print(f"\n📊 Testing {team}:")
            
            # Test season Four Factors
            season_ff = get_four_factors_team_stats(team, 2024)
            print(f"✅ Season Four Factors: {season_ff}")
            
            # Test last 10 Four Factors  
            recent_ff = get_four_factors_team_stats(team, 2024, last_n_games=10)
            print(f"✅ Last 10 Four Factors: {recent_ff}")
            
        except Exception as e:
            print(f"❌ Error testing {team}: {e}")
    
    # Test matchup analysis
    try:
        print(f"\n🔬 Testing matchup analysis:")
        home_ff = get_four_factors_team_stats("Los Angeles Lakers", 2024)
        away_ff = get_four_factors_team_stats("Golden State Warriors", 2024)
        
        advantages = analyze_four_factors_advantage(home_ff, away_ff)
        print(f"✅ Matchup analysis: {advantages}")
        
    except Exception as e:
        print(f"❌ Error testing matchup analysis: {e}")
    
    print("\n✅ Four Factors tests complete!")


if __name__ == "__main__":
    test_four_factors()
