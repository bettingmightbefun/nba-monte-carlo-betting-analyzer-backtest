"""
nba_game_simulator.py
=====================

This module handles the core NBA game simulation logic with realistic
statistical variance. It models individual game outcomes by applying
random variations to team statistics based on NBA analytics research.

Functions
---------
simulate_single_game(home_stats, away_stats, league_avg_ortg, spread, home_court_advantage=2.0) -> GameResult
    Simulate a single NBA game with realistic statistical variance

This module focuses purely on the physics and mathematics of simulating
individual basketball games, including pace variations, shooting variance,
and home court advantage effects.
"""

from __future__ import annotations

import random
from typing import Tuple

from engine.statistical_models import TeamStats, GameResult


LEAGUE_AVG_FOUR_FACTORS = {
    "efg_pct": 0.540,
    "fta_rate": 0.250,
    "tov_pct": 0.140,
    "oreb_pct": 0.280,
}

LEAGUE_AVG_MISC = {
    "pts_off_tov": 15.0,
    "pts_2nd_chance": 12.0,
}

FOUR_FACTOR_WEIGHTS = {
    "efg_pct": 0.40,
    "fta_rate": 0.15,
    "tov_pct": 0.25,
    "oreb_pct": 0.20,
}

MISC_FACTOR_WEIGHTS = {
    "pts_off_tov": 0.10,
    "pts_2nd_chance": 0.10,
}

MULTIPLIER_BOUNDS: Tuple[float, float] = (0.85, 1.15)


def _sample_stat(value: float, deviation: float, lower: float, upper: float) -> float:
    """Sample a stat for the game while keeping values in realistic bounds."""
    sampled = random.normalvariate(value, deviation)
    return max(lower, min(upper, sampled))


def _normalized_diff(value: float, league_avg: float, higher_better: bool) -> float:
    """Return normalized difference from league average based on desired direction."""
    if higher_better:
        return (value - league_avg) / league_avg
    return (league_avg - value) / league_avg


def _factor_component(
    off_value: float,
    def_value: float,
    league_avg: float,
    weight: float,
    higher_better_off: bool,
    higher_better_def: bool,
) -> float:
    """Calculate a weighted contribution for a single Four Factor dimension."""
    off_dev = _normalized_diff(off_value, league_avg, higher_better_off)
    def_dev = _normalized_diff(def_value, league_avg, higher_better_def)
    return weight * (off_dev - def_dev) / 2.0


def _compute_efficiency_multiplier(off_team: TeamStats, def_team: TeamStats) -> float:
    """Derive offensive efficiency multiplier from Four Factors and misc stats."""
    offensive_stats = {
        "efg_pct": _sample_stat(off_team.efg_pct, off_team.efg_pct_std, 0.45, 0.65),
        "fta_rate": _sample_stat(off_team.fta_rate, off_team.fta_rate_std, 0.15, 0.35),
        "tov_pct": _sample_stat(off_team.tov_pct, off_team.tov_pct_std, 0.08, 0.22),
        "oreb_pct": _sample_stat(off_team.oreb_pct, off_team.oreb_pct_std, 0.18, 0.36),
        "pts_off_tov": _sample_stat(off_team.pts_off_tov, off_team.pts_off_tov_std, 8.0, 26.0),
        "pts_2nd_chance": _sample_stat(off_team.pts_2nd_chance, off_team.pts_2nd_chance_std, 6.0, 22.0),
    }

    defensive_stats = {
        "opp_efg_pct": _sample_stat(def_team.opp_efg_pct, def_team.opp_efg_pct_std, 0.45, 0.65),
        "opp_fta_rate": _sample_stat(def_team.opp_fta_rate, def_team.opp_fta_rate_std, 0.15, 0.35),
        "opp_tov_pct": _sample_stat(def_team.opp_tov_pct, def_team.opp_tov_pct_std, 0.08, 0.22),
        "opp_oreb_pct": _sample_stat(def_team.opp_oreb_pct, def_team.opp_oreb_pct_std, 0.18, 0.36),
        "opp_pts_off_tov": _sample_stat(def_team.opp_pts_off_tov, def_team.opp_pts_off_tov_std, 8.0, 26.0),
        "opp_pts_2nd_chance": _sample_stat(def_team.opp_pts_2nd_chance, def_team.opp_pts_2nd_chance_std, 6.0, 22.0),
    }

    multiplier = 1.0

    multiplier += _factor_component(
        offensive_stats["efg_pct"],
        defensive_stats["opp_efg_pct"],
        LEAGUE_AVG_FOUR_FACTORS["efg_pct"],
        FOUR_FACTOR_WEIGHTS["efg_pct"],
        True,
        False,
    )

    multiplier += _factor_component(
        offensive_stats["fta_rate"],
        defensive_stats["opp_fta_rate"],
        LEAGUE_AVG_FOUR_FACTORS["fta_rate"],
        FOUR_FACTOR_WEIGHTS["fta_rate"],
        True,
        False,
    )

    multiplier += _factor_component(
        offensive_stats["tov_pct"],
        defensive_stats["opp_tov_pct"],
        LEAGUE_AVG_FOUR_FACTORS["tov_pct"],
        FOUR_FACTOR_WEIGHTS["tov_pct"],
        False,
        True,
    )

    multiplier += _factor_component(
        offensive_stats["oreb_pct"],
        defensive_stats["opp_oreb_pct"],
        LEAGUE_AVG_FOUR_FACTORS["oreb_pct"],
        FOUR_FACTOR_WEIGHTS["oreb_pct"],
        True,
        False,
    )

    multiplier += _factor_component(
        offensive_stats["pts_off_tov"],
        defensive_stats["opp_pts_off_tov"],
        LEAGUE_AVG_MISC["pts_off_tov"],
        MISC_FACTOR_WEIGHTS["pts_off_tov"],
        True,
        False,
    )

    multiplier += _factor_component(
        offensive_stats["pts_2nd_chance"],
        defensive_stats["opp_pts_2nd_chance"],
        LEAGUE_AVG_MISC["pts_2nd_chance"],
        MISC_FACTOR_WEIGHTS["pts_2nd_chance"],
        True,
        False,
    )

    return max(MULTIPLIER_BOUNDS[0], min(MULTIPLIER_BOUNDS[1], multiplier))


def simulate_single_game(home_stats: TeamStats, away_stats: TeamStats, 
                        league_avg_ortg: float, spread: float, home_court_advantage: float = 2.0) -> GameResult:
    """
    Simulate a single NBA game with realistic statistical variance.
    
    This function models the natural randomness in basketball that makes games
    unpredictable even when we know team statistics. It accounts for:
    - Hot/cold shooting nights (offensive rating variance)
    - Defensive intensity variations (defensive rating variance)
    - Game flow and pace changes (pace variance)
    - Home court advantage effects
    - Random game events (referee calls, injuries, etc.)
    
    The simulation uses normal distributions to model realistic variance
    based on NBA analytics research showing how much teams typically
    deviate from their season averages in individual games.
    
    Args:
        home_stats: Home team statistical profile with variance parameters
        away_stats: Away team statistical profile with variance parameters
        league_avg_ortg: League average offensive rating for normalization
        spread: Point spread (negative = home favored, positive = away favored)
        home_court_advantage: Points added to home team (default 2.0)
        
    Returns:
        GameResult with final scores, margin, spread coverage, and total points
        
    Example:
        >>> home = TeamStats(pace=100, pace_std=4, ortg=115, ortg_std=6, drtg=108, drtg_std=5)
        >>> away = TeamStats(pace=98, pace_std=4, ortg=110, ortg_std=6, drtg=112, drtg_std=5)
        >>> game = simulate_single_game(home, away, 110.0, -3.5, 2.0)
        >>> print(f"Final: {game.home_score}-{game.away_score}")
    """
    # Generate random variations for this specific game
    # Use normal distribution to model realistic variance based on NBA research
    home_game_pace = max(85.0, random.normalvariate(home_stats.pace, home_stats.pace_std))
    away_game_pace = max(85.0, random.normalvariate(away_stats.pace, away_stats.pace_std))
    
    home_game_ortg = max(90.0, random.normalvariate(home_stats.ortg, home_stats.ortg_std))
    away_game_ortg = max(90.0, random.normalvariate(away_stats.ortg, away_stats.ortg_std))
    
    home_game_drtg = max(95.0, random.normalvariate(home_stats.drtg, home_stats.drtg_std))
    away_game_drtg = max(95.0, random.normalvariate(away_stats.drtg, away_stats.drtg_std))
    
    # Calculate game pace (average of both teams with additional randomness)
    # This models how game flow affects pace beyond individual team tendencies
    game_pace = (home_game_pace + away_game_pace) / 2.0
    game_pace += random.normalvariate(0, 2.0)  # Additional game-specific variance
    game_pace = max(85.0, min(110.0, game_pace))  # Realistic NBA pace bounds
    
    # Calculate Four Factors-based efficiency multipliers
    home_efficiency_multiplier = _compute_efficiency_multiplier(home_stats, away_stats)
    away_efficiency_multiplier = _compute_efficiency_multiplier(away_stats, home_stats)

    # Calculate adjusted points per possession for each team
    # This is where team offense meets opponent defense, normalized by league average
    # Higher opponent defensive rating makes it harder to score while Four Factors tune the result
    home_adj_ppp = (
        (home_game_ortg / 100.0)
        * (away_game_drtg / league_avg_ortg)
        * home_efficiency_multiplier
    )
    away_adj_ppp = (
        (away_game_ortg / 100.0)
        * (home_game_drtg / league_avg_ortg)
        * away_efficiency_multiplier
    )
    
    # Calculate base expected scores
    # Pace × Points per possession + home court advantage
    home_expected = game_pace * home_adj_ppp + home_court_advantage
    away_expected = game_pace * away_adj_ppp
    
    # Add final layer of game-specific randomness
    # This captures unpredictable events: hot shooting nights, foul trouble,
    # referee calls, key player injuries, clutch performances, etc.
    game_variance = 8.0  # Points of additional random variance
    home_score = home_expected + random.normalvariate(0, game_variance)
    away_score = away_expected + random.normalvariate(0, game_variance)
    
    # Round to integer scores and ensure realistic minimums
    # NBA teams rarely score below 70 points in modern basketball
    home_score = max(70, round(home_score))
    away_score = max(70, round(away_score))
    
    # Calculate game results
    home_margin = home_score - away_score
    total_points = home_score + away_score
    
    # Calculate if home team covers the spread
    # Spread convention: negative = home favored, positive = away favored
    if spread < 0:
        # Home team is favored (e.g., spread = -3.5)
        # They must win by MORE than the absolute spread value to cover
        home_covers = home_margin > abs(spread)
    else:
        # Away team is favored (e.g., spread = +3.5) 
        # Home can lose by less than spread and still cover
        home_covers = home_margin > -spread
    
    return GameResult(
        home_score=home_score,
        away_score=away_score, 
        home_margin=home_margin,
        home_covers=home_covers,
        total_points=total_points
    )


# Test function for this module
def test_game_simulator():
    """Test NBA game simulator functionality."""
    print("🔍 Testing NBA Game Simulator...")
    
    # Create test team stats
    home_team = TeamStats(
        pace=100.0, pace_std=4.0,
        ortg=115.0, ortg_std=6.0, 
        drtg=108.0, drtg_std=5.0
    )
    
    away_team = TeamStats(
        pace=98.0, pace_std=4.0,
        ortg=110.0, ortg_std=6.0,
        drtg=112.0, drtg_std=5.0
    )
    
    print(f"\n🏀 Simulating games:")
    print(f"Home: Pace={home_team.pace}, ORtg={home_team.ortg}, DRtg={home_team.drtg}")
    print(f"Away: Pace={away_team.pace}, ORtg={away_team.ortg}, DRtg={away_team.drtg}")
    
    # Test multiple games to show variance
    spread = -3.5
    league_avg = 110.0
    
    for i in range(5):
        game = simulate_single_game(home_team, away_team, league_avg, spread)
        print(f"Game {i+1}: {game.home_score}-{game.away_score} "
              f"(margin: {game.home_margin:+}, covers: {game.home_covers})")
    
    # Test edge cases
    print(f"\n🧪 Testing edge cases:")
    
    # Test with extreme stats
    extreme_home = TeamStats(pace=120, pace_std=10, ortg=130, ortg_std=15, drtg=90, drtg_std=10)
    extreme_away = TeamStats(pace=80, pace_std=2, ortg=95, ortg_std=3, drtg=125, drtg_std=8)
    
    extreme_game = simulate_single_game(extreme_home, extreme_away, league_avg, 0.0)
    print(f"Extreme teams: {extreme_game.home_score}-{extreme_game.away_score}")
    
    # Test different spreads
    for test_spread in [-10.5, -3.5, 0.0, +5.5]:
        test_game = simulate_single_game(home_team, away_team, league_avg, test_spread)
        print(f"Spread {test_spread:+}: covers={test_game.home_covers} (margin: {test_game.home_margin:+})")
    
    print("\n✅ Game simulator tests complete!")


if __name__ == "__main__":
    test_game_simulator()
