"""
statistical_models.py
======================

This module defines the core data models and structures used throughout
the NBA Monte Carlo simulation system. Contains team statistics containers,
game result structures, and simulation result aggregations.

Classes
-------
TeamStats: Container for team statistical data with variance parameters
GameResult: Result of a single simulated NBA game
SimulationResults: Aggregated results from Monte Carlo simulation

Functions
---------
create_team_stats(base_stats: Dict[str, float], league_avg_ortg: float) -> TeamStats
    Factory function to create TeamStats with realistic NBA variance parameters

This module has zero dependencies on simulation logic or betting calculations,
making it lightweight and easily testable in isolation.
"""

from __future__ import annotations

from typing import Dict, Tuple, NamedTuple
from dataclasses import dataclass


@dataclass
class TeamStats:
    """
    Container for team statistical data with variance parameters.
    
    This class holds both the base statistical values (pace, offensive rating,
    defensive rating) and their associated standard deviations for realistic
    game-to-game variance modeling. Now includes the Four Factors that research
    shows are most predictive of wins.
    
    Attributes:
        pace: Team's average possessions per 48 minutes
        pace_std: Standard deviation for pace variation (typically ±4)
        ortg: Team's offensive rating (points per 100 possessions)
        ortg_std: Standard deviation for offensive rating (typically ±6)
        drtg: Team's defensive rating (points allowed per 100 possessions)
        drtg_std: Standard deviation for defensive rating (typically ±5)
        
        Four Factors (Team):
        efg_pct: Effective Field Goal Percentage (accounts for 3-point value)
        efg_pct_std: Standard deviation for EFG% variation (typically ±0.04)
        fta_rate: Free Throw Attempt Rate (FTA/FGA)
        fta_rate_std: Standard deviation for FTA rate variation (typically ±0.03)
        tov_pct: Team Turnover Percentage
        tov_pct_std: Standard deviation for turnover rate variation (typically ±0.02)
        oreb_pct: Offensive Rebound Percentage
        oreb_pct_std: Standard deviation for OREB% variation (typically ±0.03)
        
        Four Factors (Opponent):
        opp_efg_pct: Opponent Effective Field Goal Percentage allowed
        opp_efg_pct_std: Standard deviation for opponent EFG% variation
        opp_fta_rate: Opponent Free Throw Attempt Rate allowed
        opp_fta_rate_std: Standard deviation for opponent FTA rate variation
        opp_tov_pct: Opponent Turnover Percentage forced
        opp_tov_pct_std: Standard deviation for opponent turnover rate variation
        opp_oreb_pct: Opponent Offensive Rebound Percentage allowed
        opp_oreb_pct_std: Standard deviation for opponent OREB% variation
    """
    pace: float
    pace_std: float  # Standard deviation for pace variation
    ortg: float
    ortg_std: float  # Standard deviation for offensive rating variation
    drtg: float
    drtg_std: float  # Standard deviation for defensive rating variation
    
    # Four Factors - Team Offense
    efg_pct: float
    efg_pct_std: float  # Standard deviation for EFG% variation
    fta_rate: float
    fta_rate_std: float  # Standard deviation for FTA rate variation
    tov_pct: float
    tov_pct_std: float  # Standard deviation for turnover rate variation
    oreb_pct: float
    oreb_pct_std: float  # Standard deviation for OREB% variation
    
    # Four Factors - Opponent Defense (what team allows)
    opp_efg_pct: float
    opp_efg_pct_std: float  # Standard deviation for opponent EFG% variation
    opp_fta_rate: float
    opp_fta_rate_std: float  # Standard deviation for opponent FTA rate variation
    opp_tov_pct: float
    opp_tov_pct_std: float  # Standard deviation for opponent turnover rate variation
    opp_oreb_pct: float
    opp_oreb_pct_std: float  # Standard deviation for opponent OREB% variation
    
    # Miscellaneous Stats - High Value Additions
    pts_off_tov: float  # Points off turnovers (shows defensive pressure + offensive execution)
    pts_off_tov_std: float  # Standard deviation for points off turnovers variation
    pts_2nd_chance: float  # Second chance points (shows OREB conversion efficiency)
    pts_2nd_chance_std: float  # Standard deviation for second chance points variation
    
    # Opponent Miscellaneous Stats (what team allows)
    opp_pts_off_tov: float  # Opponent points off turnovers allowed
    opp_pts_off_tov_std: float  # Standard deviation for opponent points off turnovers
    opp_pts_2nd_chance: float  # Opponent second chance points allowed
    opp_pts_2nd_chance_std: float  # Standard deviation for opponent second chance points


class GameResult(NamedTuple):
    """
    Result of a single simulated NBA game.
    
    This immutable structure captures all relevant outcomes from a single
    game simulation, including scores, margin, spread coverage, and totals.
    
    Attributes:
        home_score: Final score of home team
        away_score: Final score of away team
        home_margin: Point differential (positive if home wins)
        home_covers: Whether home team covered the spread
        total_points: Combined points scored by both teams
    """
    home_score: int
    away_score: int
    home_margin: int  # Positive if home wins
    home_covers: bool  # True if home team covers the spread
    total_points: int


class SimulationResults(NamedTuple):
    """
    Aggregated results from running Monte Carlo simulation.

    This structure contains comprehensive statistics and analysis from
    running thousands of game simulations, including coverage probabilities,
    average outcomes, and statistical confidence measures.

    Attributes:
        games_simulated: Number of games simulated
        home_covers_count: Number of games where home team covered spread
        home_covers_percentage: Percentage of games home team covered
        push_count: Number of simulations that resulted in a push
        push_percentage: Percentage of simulations that resulted in a push
        home_wins_count: Number of games the home team won outright
        home_win_percentage: Percentage of games the home team won outright
        average_home_score: Mean home team score across all simulations
        average_away_score: Mean away team score across all simulations
        average_margin: Mean point differential across all simulations
        margin_std: Standard deviation of point differentials
        confidence_interval_95: 95% confidence interval for the mean margin
    """
    games_simulated: int
    home_covers_count: int
    home_covers_percentage: float
    push_count: int
    push_percentage: float
    home_wins_count: int
    home_win_percentage: float
    average_home_score: float
    average_away_score: float
    average_margin: float
    margin_std: float
    confidence_interval_95: Tuple[float, float]


def create_team_stats(base_stats: Dict[str, float], league_avg_ortg: float, four_factors_stats: Dict[str, float] = None, misc_stats: Dict[str, float] = None) -> TeamStats:
    """
    Create TeamStats with realistic variance based on NBA historical data.
    
    This factory function takes raw team statistics and creates a TeamStats
    object with appropriate variance parameters based on NBA analytics research.
    The variance values are derived from historical analysis of NBA team
    performance fluctuations.
    
    Args:
        base_stats: Dictionary with keys 'pace', 'ortg', 'drtg'
        league_avg_ortg: League average offensive rating (currently unused but
                        kept for potential future normalization features)
        four_factors_stats: Dictionary with Four Factors keys (optional)
        misc_stats: Dictionary with miscellaneous stats keys (optional)
    
    Returns:
        TeamStats object with realistic variance parameters
    
    Variance Research Notes:
        - Pace varies ~±4 possessions per game based on opponent and game flow
        - Offensive rating varies ~±6 points per 100 possessions (hot/cold shooting)
        - Defensive rating varies ~±5 points per 100 possessions (effort/matchups)
        - EFG% varies ~±0.04 (4 percentage points) based on shot selection/defense
        - FTA Rate varies ~±0.03 (3 percentage points) based on aggression/fouls
        - Turnover% varies ~±0.02 (2 percentage points) based on pressure/pace
        - OREB% varies ~±0.03 (3 percentage points) based on effort/matchups
    
    Example:
        >>> stats_dict = {"pace": 100.0, "ortg": 110.0, "drtg": 108.0}
        >>> ff_dict = {"efg_pct": 0.54, "fta_rate": 0.25, "tov_pct": 0.14, "oreb_pct": 0.28, ...}
        >>> team_stats = create_team_stats(stats_dict, 110.5, ff_dict)
        >>> print(f"Pace: {team_stats.pace} ± {team_stats.pace_std}")
    """
    # If Four Factors not provided, use league average defaults
    if four_factors_stats is None:
        four_factors_stats = {
            "efg_pct": 0.540,  # League average EFG%
            "fta_rate": 0.250,  # League average FTA rate
            "tov_pct": 0.140,  # League average turnover%
            "oreb_pct": 0.280,  # League average OREB%
            "opp_efg_pct": 0.540,  # League average opponent EFG%
            "opp_fta_rate": 0.250,  # League average opponent FTA rate
            "opp_tov_pct": 0.140,  # League average opponent turnover%
            "opp_oreb_pct": 0.280,  # League average opponent OREB%
        }
    
    # If miscellaneous stats not provided, use league average defaults
    if misc_stats is None:
        misc_stats = {
            "pts_off_tov": 15.0,  # League average points off turnovers per game
            "pts_2nd_chance": 12.0,  # League average second chance points per game
            "opp_pts_off_tov": 15.0,  # League average opponent points off turnovers allowed
            "opp_pts_2nd_chance": 12.0,  # League average opponent second chance points allowed
        }
    
    return TeamStats(
        pace=base_stats["pace"],
        pace_std=4.0,  # NBA teams typically vary ±4 possessions from their average
        ortg=base_stats["ortg"], 
        ortg_std=6.0,  # Offensive rating varies ±6 points per 100 possessions
        drtg=base_stats["drtg"],
        drtg_std=5.0,  # Defensive rating varies ±5 points per 100 possessions
        
        # Four Factors - Team Offense
        efg_pct=four_factors_stats["efg_pct"],
        efg_pct_std=0.04,  # EFG% varies ±4 percentage points per game
        fta_rate=four_factors_stats["fta_rate"],
        fta_rate_std=0.03,  # FTA rate varies ±3 percentage points per game
        tov_pct=four_factors_stats["tov_pct"],
        tov_pct_std=0.02,  # Turnover% varies ±2 percentage points per game
        oreb_pct=four_factors_stats["oreb_pct"],
        oreb_pct_std=0.03,  # OREB% varies ±3 percentage points per game
        
        # Four Factors - Opponent Defense
        opp_efg_pct=four_factors_stats["opp_efg_pct"],
        opp_efg_pct_std=0.04,  # Opponent EFG% varies ±4 percentage points per game
        opp_fta_rate=four_factors_stats["opp_fta_rate"],
        opp_fta_rate_std=0.03,  # Opponent FTA rate varies ±3 percentage points per game
        opp_tov_pct=four_factors_stats["opp_tov_pct"],
        opp_tov_pct_std=0.02,  # Opponent turnover% varies ±2 percentage points per game
        opp_oreb_pct=four_factors_stats["opp_oreb_pct"],
        opp_oreb_pct_std=0.03,  # Opponent OREB% varies ±3 percentage points per game
        
        # Miscellaneous Stats - High Value Additions
        pts_off_tov=misc_stats["pts_off_tov"],
        pts_off_tov_std=3.0,  # Points off turnovers varies ±3 points per game
        pts_2nd_chance=misc_stats["pts_2nd_chance"],
        pts_2nd_chance_std=2.5,  # Second chance points varies ±2.5 points per game
        
        # Opponent Miscellaneous Stats
        opp_pts_off_tov=misc_stats["opp_pts_off_tov"],
        opp_pts_off_tov_std=3.0,  # Opponent points off turnovers varies ±3 points per game
        opp_pts_2nd_chance=misc_stats["opp_pts_2nd_chance"],
        opp_pts_2nd_chance_std=2.5,  # Opponent second chance points varies ±2.5 points per game
    )


# Test function for this module
def test_statistical_models():
    """Test NBA game models functionality."""
    print("🔍 Testing NBA Game Models...")
    
    # Test TeamStats creation
    print("\n📊 Testing TeamStats creation:")
    base_stats = {
        "pace": 100.0,
        "ortg": 115.0,
        "drtg": 108.0
    }
    
    team_stats = create_team_stats(base_stats, 110.5)
    print(f"✅ TeamStats created: Pace={team_stats.pace}±{team_stats.pace_std}")
    print(f"   ORtg={team_stats.ortg}±{team_stats.ortg_std}")
    print(f"   DRtg={team_stats.drtg}±{team_stats.drtg_std}")
    
    # Test GameResult creation
    print("\n🏀 Testing GameResult:")
    game_result = GameResult(
        home_score=108,
        away_score=105,
        home_margin=3,
        home_covers=False,  # Assuming spread was -3.5
        total_points=213
    )
    print(f"✅ GameResult: {game_result.home_score}-{game_result.away_score}")
    print(f"   Margin: {game_result.home_margin}, Covers: {game_result.home_covers}")
    
    # Test SimulationResults creation
    print("\n📈 Testing SimulationResults:")
    sim_results = SimulationResults(
        games_simulated=10000,
        home_covers_count=4500,
        home_covers_percentage=45.0,
        push_count=200,
        push_percentage=2.0,
        home_wins_count=5200,
        home_win_percentage=52.0,
        average_home_score=110.5,
        average_away_score=108.2,
        average_margin=2.3,
        margin_std=12.5,
        confidence_interval_95=(-22.2, 26.8)
    )
    print(f"✅ SimulationResults: {sim_results.games_simulated} games")
    print(f"   Coverage: {sim_results.home_covers_percentage}%")
    print(f"   Home wins: {sim_results.home_win_percentage}%")
    print(f"   Avg scores: {sim_results.average_home_score}-{sim_results.average_away_score}")
    
    print("\n✅ Game models tests complete!")


if __name__ == "__main__":
    test_statistical_models()
