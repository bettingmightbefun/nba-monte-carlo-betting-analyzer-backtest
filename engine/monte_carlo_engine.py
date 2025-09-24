"""
nba_monte_carlo_engine.py
==========================

This module orchestrates Monte Carlo simulations and betting analysis for NBA games.
It runs thousands of individual game simulations and aggregates the results to
provide comprehensive statistical analysis and betting edge calculations. The
engine supports both a fast 100k iteration mode and a high-precision 1M mode
used for deeper dives.

Functions
---------
run_monte_carlo_simulation(home_stats, away_stats, league_avg_ortg, spread, num_simulations=100000) -> SimulationResults
    Run Monte Carlo simulation of NBA game matchup with specified number of iterations

calculate_betting_edge(simulation_results, decimal_odds) -> Dict[str, float]
    Calculate betting edge and expected value based on simulation results

This module focuses on orchestration and statistical analysis, delegating
individual game physics to the game simulator module.
"""

from __future__ import annotations

import math
import random
from typing import Dict, Optional

from engine.statistical_models import TeamStats, SimulationResults
from engine.game_simulator import simulate_single_game


def run_monte_carlo_simulation(home_stats: TeamStats, away_stats: TeamStats,
                             league_avg_ortg: float, spread: float,
                             num_simulations: int = 100000,
                             seed: Optional[int] = None) -> SimulationResults:
    """
    Run Monte Carlo simulation of NBA game matchup.
    
    This function orchestrates thousands of individual game simulations to build
    a comprehensive picture of possible outcomes. Unlike deterministic models that
    give single point estimates, Monte Carlo simulation captures the full range
    of possibilities and their relative probabilities.
    
    The simulation tracks:
    - How often each team covers the spread
    - Average scores and margins
    - Statistical variance and confidence intervals
    - All data needed for betting analysis
    
    Args:
        home_stats: Home team statistical profile with variance parameters
        away_stats: Away team statistical profile with variance parameters  
        league_avg_ortg: League average offensive rating for normalization
        spread: Point spread (negative = home favored, positive = away favored)
        num_simulations: Number of games to simulate (default 100,000)
        
    Returns:
        SimulationResults with comprehensive outcome analysis including:
        - Coverage percentages and counts
        - Average scores and margins
        - Statistical measures (standard deviation, confidence intervals)
        
    Example:
        >>> home = TeamStats(pace=100, pace_std=4, ortg=115, ortg_std=6, drtg=108, drtg_std=5)
        >>> away = TeamStats(pace=98, pace_std=4, ortg=110, ortg_std=6, drtg=112, drtg_std=5)
        >>> results = run_monte_carlo_simulation(home, away, 110.0, -3.5, 50000)
        >>> print(f"Home covers {results.home_covers_percentage:.1f}% of the time")
    """
    if num_simulations <= 0:
        raise ValueError(
            "num_simulations must be a positive integer to run the Monte Carlo simulation"
        )

    # Set random seed for deterministic results in backtesting
    if seed is not None:
        random.seed(seed)

    print(f"🎲 Running {num_simulations:,} Monte Carlo simulations...")
    
    # Initialize tracking variables
    covers_count = 0
    push_count = 0
    home_wins = 0
    total_home_score = 0
    total_away_score = 0
    margin_count = 0
    margin_mean = 0.0
    margin_m2 = 0.0
    
    # Progress tracking for large simulations (user experience)
    milestone_percentages = (0.1, 0.25, 0.5, 0.75, 0.9)
    progress_milestones = sorted(
        {
            max(1, int(num_simulations * pct))
            for pct in milestone_percentages
            if 0 < int(num_simulations * pct) < num_simulations
        }
    )

    # Run the simulation loop
    for i in range(num_simulations):
        # Show progress for user feedback on long simulations
        if progress_milestones and (i + 1) == progress_milestones[0]:
            progress = ((i + 1) / num_simulations) * 100
            print(f"   Progress: {progress:.0f}% ({i + 1:,} games simulated)")
            progress_milestones.pop(0)
            
        # Simulate single game using the game simulator
        game = simulate_single_game(home_stats, away_stats, league_avg_ortg, spread)
        
        # Determine if the spread resulted in a push outcome
        # A push only occurs when the home team's margin exactly matches the
        # result that refunds the home spread ticket. With the convention used
        # throughout the project (negative spread = home favorite), that value
        # is always the negative of the posted spread. Checking both ±spread
        # mistakenly classified clear wins/losses as pushes for favorites and
        # underdogs.
        is_push = math.isclose(game.home_margin, -spread, abs_tol=1e-9)

        # Accumulate statistics (memory efficient - don't store individual games)
        if is_push:
            push_count += 1
        elif game.home_covers:
            covers_count += 1
        if game.home_margin > 0:
            home_wins += 1
        total_home_score += game.home_score
        total_away_score += game.away_score

        # Update running statistics for the margin using Welford's algorithm
        margin_count += 1
        delta = game.home_margin - margin_mean
        margin_mean += delta / margin_count
        delta2 = game.home_margin - margin_mean
        margin_m2 += delta * delta2

    # Calculate aggregated statistics
    covers_percentage = (covers_count / num_simulations) * 100.0
    push_percentage = (push_count / num_simulations) * 100.0
    home_win_percentage = (home_wins / num_simulations) * 100.0
    avg_home_score = total_home_score / num_simulations
    avg_away_score = total_away_score / num_simulations
    avg_margin = margin_mean

    # Calculate margin standard deviation and standard error for confidence interval
    margin_variance = margin_m2 / margin_count if margin_count else 0.0
    margin_std = math.sqrt(margin_variance)
    margin_standard_error = margin_std / math.sqrt(margin_count) if margin_count else 0.0

    # Calculate 95% confidence interval for the mean margin using standard error
    ci_lower = avg_margin - (1.96 * margin_standard_error)
    ci_upper = avg_margin + (1.96 * margin_standard_error)
    
    print(
        "✅ Simulation complete! Home team covers in "
        f"{covers_count:,} out of {num_simulations:,} games"
    )

    return SimulationResults(
        games_simulated=num_simulations,
        home_covers_count=covers_count,
        home_covers_percentage=covers_percentage,
        push_count=push_count,
        push_percentage=push_percentage,
        home_wins_count=home_wins,
        home_win_percentage=home_win_percentage,
        average_home_score=avg_home_score,
        average_away_score=avg_away_score,
        average_margin=avg_margin,
        margin_std=margin_std,
        confidence_interval_95=(ci_lower, ci_upper)
    )


def calculate_betting_edge(simulation_results: SimulationResults,
                          decimal_odds: float) -> Dict[str, float]:
    """
    Calculate betting edge based on Monte Carlo simulation results.
    
    This function performs the crucial conversion from simulation statistics
    to actionable betting information. It compares the "true" probability
    (derived from simulations) to the "implied" probability (derived from
    sportsbook odds) to determine if there's a profitable betting opportunity.
    
    The calculation is much more accurate than theoretical probability models
    because it's based on actual simulated game outcomes that account for
    realistic variance and randomness.
    
    Args:
        simulation_results: Results from Monte Carlo simulation
        decimal_odds: Decimal odds from sportsbook (e.g., 1.91 for -110)
        
    Returns:
        Dictionary containing:
        - expected_value: Expected profit/loss per $1 bet
        - edge_percentage: Edge as percentage (positive = profitable)
        - win_probability: Probability the bet wins (home covers)
        - push_probability: Probability the bet pushes (stake returned)
        - loss_probability: Probability the bet loses
        - implied_probability: Probability implied by odds
        - breakeven_probability: Push-aware break-even probability
        - probability_difference: Win - Break-even probability
        
    Mathematical Foundation:
        Expected Value = (True_Prob × Profit_If_Win) - (Loss_Prob × Stake)
        Where:
        - Profit_If_Win = decimal_odds - 1.0
        - Loss_Prob = 1.0 - True_Prob - Push_Prob
        - Stake = 1.0 (per dollar bet)
        
    Example:
        >>> results = SimulationResults(...)  # From simulation
        >>> edge_data = calculate_betting_edge(results, 1.91)
        >>> if edge_data["edge_percentage"] > 2.0:
        ...     print("Profitable bet detected!")
    """
    if decimal_odds <= 1.0:
        raise ValueError(
            "decimal_odds must be greater than 1.0 to calculate a betting edge"
        )

    # Convert simulation percentages to probabilities (0.0 to 1.0)
    win_prob = simulation_results.home_covers_percentage / 100.0
    push_prob = simulation_results.push_percentage / 100.0
    loss_prob = max(0.0, 1.0 - win_prob - push_prob)

    # Calculate expected value using standard betting mathematics
    # EV = (Probability of Win × Profit) - (Probability of Loss × Stake)
    profit_if_win = decimal_odds - 1.0  # Profit per $1 bet if we win
    expected_value = (win_prob * profit_if_win) - (loss_prob * 1.0)

    # Convert to percentage for easier interpretation
    edge_percentage = expected_value * 100.0
    
    # Calculate implied probability from sportsbook odds for comparison
    # This is what the sportsbook thinks the probability is
    implied_probability = 1.0 / decimal_odds
    breakeven_probability = (1.0 - push_prob) / decimal_odds

    return {
        "expected_value": expected_value,
        "edge_percentage": edge_percentage,
        "win_probability": win_prob,
        "push_probability": push_prob,
        "loss_probability": loss_prob,
        "true_probability": win_prob,
        "implied_probability": implied_probability,
        "probability_difference": win_prob - breakeven_probability,
        "breakeven_probability": breakeven_probability
    }


# Test function for this module
def test_monte_carlo_engine():
    """Test NBA Monte Carlo engine functionality."""
    print("🔍 Testing NBA Monte Carlo Engine...")
    
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
    
    print(f"\n🎲 Running test simulation:")
    print(f"Home: Pace={home_team.pace}, ORtg={home_team.ortg}, DRtg={home_team.drtg}")
    print(f"Away: Pace={away_team.pace}, ORtg={away_team.ortg}, DRtg={away_team.drtg}")
    
    # Run smaller simulation for testing
    results = run_monte_carlo_simulation(
        home_team, away_team, 
        league_avg_ortg=110.0, 
        spread=-3.5,
        num_simulations=10000  # Smaller for testing
    )
    
    print(f"\n📊 Simulation Results:")
    print(f"Games simulated: {results.games_simulated:,}")
    print(f"Home covers: {results.home_covers_percentage:.1f}%")
    print(f"Average scores: {results.average_home_score:.1f} - {results.average_away_score:.1f}")
    print(f"Average margin: {results.average_margin:.1f} ± {results.margin_std:.1f}")
    print(f"95% CI: ({results.confidence_interval_95[0]:.1f}, {results.confidence_interval_95[1]:.1f})")
    
    # Test betting edge calculation
    print(f"\n💰 Testing betting analysis:")
    edge_data = calculate_betting_edge(results, decimal_odds=1.91)
    print(f"Win probability: {edge_data['win_probability']:.3f}")
    print(f"Push probability: {edge_data['push_probability']:.3f}")
    print(f"Loss probability: {edge_data['loss_probability']:.3f}")
    print(f"Break-even probability: {edge_data['breakeven_probability']:.3f}")
    print(f"Expected value: {edge_data['expected_value']:.4f}")
    print(f"Edge percentage: {edge_data['edge_percentage']:.2f}%")
    
    # Test different odds
    print(f"\n🧪 Testing different odds scenarios:")
    for odds in [1.50, 1.91, 2.00, 2.50]:
        edge = calculate_betting_edge(results, odds)
        print(f"Odds {odds}: EV={edge['expected_value']:.4f}, Edge={edge['edge_percentage']:.1f}%")
    
    print("\n✅ Monte Carlo engine tests complete!")


if __name__ == "__main__":
    test_monte_carlo_engine()
