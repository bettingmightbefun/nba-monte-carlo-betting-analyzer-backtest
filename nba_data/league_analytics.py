"""
nba_league_analytics.py
========================

This module handles league-wide NBA analytics and API connectivity testing.
Provides functions to calculate league averages and verify NBA API access.

Functions
---------
compute_league_average_ortg(season_end_year: int) -> float
    Compute league-wide average offensive rating for a season.

test_api_connection() -> bool
    Test if NBA API is working and accessible.

This module focuses on league-wide calculations and system diagnostics,
separate from individual team statistics.
"""

from __future__ import annotations

import time

from nba_data.team_resolver import format_season

try:
    from nba_api.stats.endpoints import leaguedashteamstats
except ImportError as exc:
    raise ImportError(
        "nba_api package is required but not installed. Run: pip install nba_api"
    ) from exc


def compute_league_average_ortg(season_end_year: int) -> float:
    """
    Compute league-wide average offensive rating.
    
    Calculates the average offensive rating across all NBA teams for a given season.
    This value is used as a baseline for normalizing team performance metrics
    in the Monte Carlo simulation.
    
    Args:
        season_end_year: Year the season ends (e.g., 2024 for 2023-24 season)
        
    Returns:
        League average offensive rating as float
        
    Raises:
        RuntimeError: If NBA API fails or data unavailable
        ValueError: If required statistics cannot be calculated
        
    Example:
        >>> league_avg = compute_league_average_ortg(2024)
        >>> print(f"League average ORtg: {league_avg:.2f}")
    """
    print(f"📊 Computing league average ORtg for {season_end_year}")
    
    season = format_season(season_end_year)
    
    try:
        # Get all team ADVANCED stats for league average
        league_stats = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            season_type_all_star='Regular Season',
            measure_type_detailed_defense='Advanced',  # Correct parameter for advanced stats
            per_mode_detailed='PerGame'
        )
        
        time.sleep(0.5)
        
        df = league_stats.get_data_frames()[0]
        
        # Calculate league average offensive rating - FAIL if not available
        if 'OFF_RATING' in df.columns:
            avg_ortg = df['OFF_RATING'].mean()
        elif 'E_OFF_RATING' in df.columns:
            avg_ortg = df['E_OFF_RATING'].mean()
        elif 'OFFRTG' in df.columns:
            avg_ortg = df['OFFRTG'].mean()
        else:
            # Calculate from basic stats if advanced not available
            required_cols = ['PTS', 'FGA', 'FTA', 'OREB', 'TOV']
            if all(col in df.columns for col in required_cols):
                # Calculate average offensive rating from basic stats
                total_pts = df['PTS'].sum()
                total_fga = df['FGA'].sum()
                total_fta = df['FTA'].sum()
                total_oreb = df['OREB'].sum()
                total_tov = df['TOV'].sum()
                
                total_possessions = total_fga + 0.44 * total_fta - total_oreb + total_tov
                if total_possessions <= 0:
                    raise ValueError(f"Invalid total possessions calculation: {total_possessions}")
                
                avg_ortg = 100.0 * total_pts / total_possessions
            else:
                missing_cols = [col for col in required_cols if col not in df.columns]
                raise ValueError(f"Missing required columns for league average calculation: {missing_cols}. Available: {list(df.columns)}")
        
        # Validate result
        if avg_ortg <= 0:
            raise ValueError(f"Invalid league average offensive rating: {avg_ortg}")
        
        print(f"✅ League average ORtg: {avg_ortg:.2f}")
        
        return float(avg_ortg)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to get league average ORtg: {e}")
        raise RuntimeError(f"Cannot proceed without real NBA league average data. Error: {e}") from e


def test_api_connection() -> bool:
    """
    Test if NBA API is working and accessible.
    
    Performs a simple API call to verify connectivity and data availability.
    This function is useful for diagnostics and setup verification.
    
    Returns:
        True if API is working, False otherwise
        
    Example:
        >>> if test_api_connection():
        ...     print("NBA API is ready!")
        ... else:
        ...     print("NBA API connection failed")
    """
    try:
        print("🔍 Testing NBA API connection...")
        
        # Try to get current season team stats
        current_season = "2023-24"  # Most recent completed season
        
        team_stats = leaguedashteamstats.LeagueDashTeamStats(
            season=current_season,
            season_type_all_star='Regular Season',
            measure_type_detailed_defense='Base',
            per_mode_detailed='PerGame'
        )
        
        df = team_stats.get_data_frames()[0]
        
        if not df.empty:
            print(f"✅ NBA API working! Found {len(df)} teams for {current_season}")
            sample_team = df.iloc[0]
            print(f"   Sample team: {sample_team['TEAM_NAME']}")
            print(f"   Available columns: {list(sample_team.index)[:15]}...")
            return True
        else:
            print("❌ NBA API returned empty data")
            return False
            
    except Exception as e:
        print(f"❌ NBA API test failed: {e}")
        return False


# Test function for this module
def test_league_analytics():
    """Test NBA league analytics functionality."""
    print("🔍 Testing NBA League Analytics...")
    
    # Test API connection
    if test_api_connection():
        print("\n📊 Testing league average calculation...")
        try:
            league_avg = compute_league_average_ortg(2024)
            print(f"✅ League average ORtg: {league_avg:.2f}")
            
            # Validate result is reasonable (NBA league average is typically 110-115)
            if 105.0 <= league_avg <= 120.0:
                print("✅ League average is within expected range")
            else:
                print(f"⚠️  League average {league_avg:.2f} seems outside typical range (105-120)")
                
        except Exception as e:
            print(f"❌ Error calculating league average: {e}")
    else:
        print("❌ Cannot test league analytics - API connection failed")
    
    print("\n✅ League analytics tests complete!")


if __name__ == "__main__":
    test_league_analytics()
