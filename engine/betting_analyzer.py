"""
nba_betting_analyzer.py
========================

This module implements a Monte Carlo simulation-based NBA betting model.
Instead of using deterministic calculations, it runs large batches of virtual
games with realistic statistical variance to determine true probabilities and
betting edges. The standard workflow simulates 100,000 games with an optional
high-precision mode that expands to 1,000,000 iterations for tighter confidence
intervals.

Key Features:
- Monte Carlo simulation with configurable 100k / 1M virtual games
- Realistic variance in team performance (pace, shooting, etc.)
- True probability distributions from actual game outcomes
- More accurate betting edge calculations than theoretical models

The Monte Carlo approach captures the natural randomness in basketball
that deterministic models miss, providing superior betting insights.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

import pandas as pd

from engine.adjustments import (
    apply_fatigue_adjustments,
    apply_head_to_head_adjustments,
    apply_hustle_adjustments,
    apply_venue_adjustments,
)
from engine.constants import LEAGUE_AVG_MISC_STATS as ENGINE_LEAGUE_AVG_MISC_STATS
from engine.data_pipeline import TeamDataBundle, collect_matchup_data
from engine.monte_carlo_engine import calculate_betting_edge, run_monte_carlo_simulation
from engine.report_builder import build_text_report
from engine.stat_processing import WeightedStats, compute_weighted_stats
from engine.statistical_models import SimulationResults, create_team_stats
from nba_data.advanced_stats import get_last_10_stats as nba_get_last_10_stats
from nba_data.advanced_stats import get_season_team_stats as nba_get_season_team_stats
from nba_data.four_factors import get_four_factors_team_stats as nba_get_four_factors_team_stats
from nba_data.head_to_head import get_head_to_head_profile as nba_get_head_to_head_profile
from nba_data.hustle_stats import (
    TeamHustleProfile,
    get_team_hustle_profile as nba_get_team_hustle_profile,
)
from nba_data.league_analytics import compute_league_average_ortg as nba_compute_league_average_ortg
from nba_data.misc_stats import get_misc_team_stats as nba_get_misc_team_stats
from nba_data.schedule_fatigue import get_team_rest_profile as nba_get_team_rest_profile
from nba_data.venue_splits import get_team_venue_splits as nba_get_team_venue_splits


@dataclass
class TeamPreparedData:
    """Container for a team's weighted and adjusted statistics."""

    data: TeamDataBundle
    weighted: WeightedStats
    adjusted_core: Dict[str, float]
    adjusted_misc: Dict[str, float]
    adjustments: Dict[str, Any]


# Exposed fetchers for backwards-compatible monkeypatching in tests
get_season_team_stats = nba_get_season_team_stats
get_last_10_stats = nba_get_last_10_stats
get_four_factors_team_stats = nba_get_four_factors_team_stats
get_misc_team_stats = nba_get_misc_team_stats
get_team_rest_profile = nba_get_team_rest_profile
get_team_venue_splits = nba_get_team_venue_splits
get_team_hustle_profile = nba_get_team_hustle_profile
compute_league_average_ortg = nba_compute_league_average_ortg
get_head_to_head_profile = nba_get_head_to_head_profile
LEAGUE_AVG_MISC_STATS = ENGINE_LEAGUE_AVG_MISC_STATS


def _validate_inputs(recency_weight: float, num_simulations: int) -> None:
    if not (0.0 <= recency_weight <= 1.0):
        raise ValueError("recency_weight must be between 0 and 1")
    if num_simulations <= 0:
        raise ValueError("num_simulations must be a positive integer")


def _resolve_game_date(upcoming_game_date: Optional[pd.Timestamp | str]) -> pd.Timestamp:
    if upcoming_game_date is None:
        return pd.Timestamp.today().normalize()
    return pd.Timestamp(upcoming_game_date).normalize()


def _contextualize_team(
    *,
    team_data: TeamDataBundle,
    weighted: WeightedStats,
    head_to_head_profile: Dict[str, Any],
    location: str,
) -> TeamPreparedData:
    adjusted_core = dict(weighted.core)
    adjusted_misc = dict(weighted.misc)

    adjustments = {
        "fatigue": apply_fatigue_adjustments(adjusted_core, adjusted_misc, team_data.rest_profile),
        "venue": apply_venue_adjustments(adjusted_core, team_data.venue_splits, team_data.season, location),
        "hustle": apply_hustle_adjustments(adjusted_core, adjusted_misc, team_data.hustle_profile),
    }
    adjustments["head_to_head"] = apply_head_to_head_adjustments(
        adjusted_core, head_to_head_profile, team_data.team_name
    )

    return TeamPreparedData(
        data=team_data,
        weighted=weighted,
        adjusted_core=adjusted_core,
        adjusted_misc=adjusted_misc,
        adjustments=adjustments,
    )


def _create_team_stats(prepared: TeamPreparedData, league_avg_ortg: float):
    return create_team_stats(
        prepared.adjusted_core,
        league_avg_ortg,
        prepared.weighted.four_factors,
        prepared.adjusted_misc,
    )


def _build_team_output(prepared: TeamPreparedData) -> Dict[str, Any]:
    return {
        "season": prepared.data.season,
        "last_10": prepared.data.last_10,
        "final_weighted": prepared.weighted.core,
        "context_adjusted": prepared.adjusted_core,
    }


def _build_four_factors_output(prepared: TeamPreparedData) -> Dict[str, Any]:
    return {
        "season": prepared.data.four_factors_season,
        "last_10": prepared.data.four_factors_last10,
        "final_weighted": prepared.weighted.four_factors,
    }


def _build_misc_output(prepared: TeamPreparedData) -> Dict[str, Any]:
    return {
        "season": prepared.data.misc_season,
        "last_10": prepared.data.misc_last10,
        "final_weighted": prepared.weighted.misc,
        "context_adjusted": prepared.adjusted_misc,
    }


def _build_contextual_factors(
    home: TeamPreparedData,
    away: TeamPreparedData,
    head_to_head_profile: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "rest_profiles": {
            "home": home.data.rest_profile.as_dict(),
            "away": away.data.rest_profile.as_dict(),
        },
        "venue_splits": {
            "home": home.data.venue_splits,
            "away": away.data.venue_splits,
        },
        "hustle_profiles": {
            "home": home.data.hustle_profile.as_dict(),
            "away": away.data.hustle_profile.as_dict(),
        },
        "head_to_head": head_to_head_profile,
        "model_adjustments": {
            "home": home.adjustments,
            "away": away.adjustments,
        },
    }


def _build_neutral_hustle_profile() -> TeamHustleProfile:
    """Create a neutral hustle profile when as-of data lacks hustle metrics."""

    return TeamHustleProfile(
        deflections=0.0,
        charges_drawn=0.0,
        loose_balls_recovered=0.0,
        screen_assists=0.0,
        contested_shots=0.0,
        box_outs=0.0,
        minutes_played=0.0,
        team_effort_score=0.0,
        effort_percentile=None,
        league_average_effort=None,
    )


def _convert_asof_stats_to_team_data(
    asof_stats: Dict[str, float],
    team_name: str,
    season_end_year: int
) -> TeamDataBundle:
    """
    Convert as-of statistics to TeamDataBundle format for compatibility.

    This creates a minimal TeamDataBundle from backtest as-of stats
    to maintain compatibility with existing processing pipeline.
    """
    # Create minimal season stats
    season_stats = {
        'pace': asof_stats.get('pace_season', 100),
        'ortg': asof_stats.get('ortg_season', 110),
        'drtg': asof_stats.get('drtg_season', 110),
        'efg_pct': asof_stats.get('efg_pct_season', 0.5),
        'tov_pct': asof_stats.get('tov_pct_season', 15),
        'orb_pct': asof_stats.get('orb_pct_season', 25),
        'ft_fga': asof_stats.get('ft_fga_season', 0.2),
    }

    # Create minimal last-10 stats
    last10_stats = {
        'pace': asof_stats.get('pace_last10', season_stats['pace']),
        'ortg': asof_stats.get('ortg_last10', season_stats['ortg']),
        'drtg': asof_stats.get('drtg_last10', season_stats['drtg']),
    }

    # Create proper TeamRestProfile object for compatibility
    from nba_data.schedule_fatigue import TeamRestProfile
    rest_profile = TeamRestProfile(
        last_game_date=None,  # Not available in as-of stats
        rest_days_before_last_game=None,  # Not available in as-of stats
        rest_days_until_next_game=None,  # Not available in as-of stats
        fatigue_flag_last_game="normal",  # Default
        average_rest_days=2.0,  # Default
        back_to_back_rate=0.0,  # Default
        fatigue_score_mean=0.5,  # Default
    )

    return TeamDataBundle(
        team_name=team_name,
        season=season_stats,
        last_10=last10_stats,
        four_factors_season={
            'efg_pct': season_stats['efg_pct'],
            'tov_pct': season_stats['tov_pct'],
            'orb_pct': season_stats['orb_pct'],
            'ft_fga': season_stats['ft_fga'],
        },
        four_factors_last10={
            'efg_pct': last10_stats.get('efg_pct', season_stats['efg_pct']),
            'tov_pct': last10_stats.get('tov_pct', season_stats['tov_pct']),
            'orb_pct': last10_stats.get('orb_pct', season_stats['orb_pct']),
            'ft_fga': last10_stats.get('ft_fga', season_stats['ft_fga']),
        },
        misc_season={
            'pts_off_tov': asof_stats.get('pts_off_tov_season', 0),
            'pts_2nd_chance': asof_stats.get('pts_2nd_chance_season', 0),
            'pts_fb': asof_stats.get('pts_fb_season', 0),
            'pts_paint': asof_stats.get('pts_paint_season', 0),
        },
        misc_last10={},  # Not available from as-of stats
        rest_profile=rest_profile,
        venue_splits={},  # Not available from as-of stats
        hustle_profile=_build_neutral_hustle_profile(),
    )


def _run_simulation(
    home_stats,
    away_stats,
    league_avg_ortg: float,
    sportsbook_line: float,
    num_simulations: int,
    seed: Optional[int] = None,
) -> Tuple[SimulationResults, str]:
    simulation_mode = "high_precision" if num_simulations >= 1_000_000 else "standard"
    print(
        "\n🎲 MONTE CARLO SIMULATION - Running "
        f"{num_simulations:,} virtual games ({simulation_mode.replace('_', ' ').title()} mode)..."
    )
    results = run_monte_carlo_simulation(
        home_stats=home_stats,
        away_stats=away_stats,
        league_avg_ortg=league_avg_ortg,
        spread=sportsbook_line,
        num_simulations=num_simulations,
    )
    return results, simulation_mode


def _evaluate_betting_edge(
    simulation_results: SimulationResults,
    decimal_odds: float,
    home_team: str,
) -> Tuple[Dict[str, float], str, float, float, float, float, float]:
    edge_analysis = calculate_betting_edge(simulation_results, decimal_odds)
    edge_percent = edge_analysis.get("edge_percentage", 0.0)
    decision = (
        f"POSITIVE EV BET on {home_team} spread" if edge_percent > 2.0 else "NO BET - LINE IS EFFICIENT."
    )

    win_probability = edge_analysis.get("win_probability", edge_analysis.get("true_probability", 0.0))
    push_probability = edge_analysis.get("push_probability", 0.0)
    loss_probability = edge_analysis.get(
        "loss_probability", max(0.0, 1.0 - win_probability - push_probability)
    )
    implied_probability = edge_analysis.get("implied_probability", 0.0)
    expected_value = edge_analysis.get("expected_value", 0.0)

    return (
        edge_analysis,
        decision,
        win_probability,
        push_probability,
        loss_probability,
        implied_probability,
        expected_value,
    )


def _build_fetchers() -> Dict[str, Callable[..., Any]]:
    return {
        "get_season_team_stats": get_season_team_stats,
        "get_last_10_stats": get_last_10_stats,
        "get_four_factors_team_stats": get_four_factors_team_stats,
        "get_misc_team_stats": get_misc_team_stats,
        "get_team_rest_profile": get_team_rest_profile,
        "get_team_venue_splits": get_team_venue_splits,
        "get_team_hustle_profile": get_team_hustle_profile,
        "compute_league_average_ortg": compute_league_average_ortg,
        "get_head_to_head_profile": get_head_to_head_profile,
    }


def compute_model_report(
    home_team: str,
    away_team: str,
    season_end_year: int,
    recency_weight: float,
    sportsbook_line: float,
    decimal_odds: float,
    upcoming_game_date: Optional[pd.Timestamp | str] = None,
    num_simulations: int = 100_000,
    as_of: Optional[datetime] = None,
    last_n_window: int = 10,
    backtest_mode: bool = False,
    seed: Optional[int] = None,
) -> Tuple[Dict[str, Any], str]:
    """Compute Monte Carlo simulation-based betting model report."""

    _validate_inputs(recency_weight, num_simulations)
    upcoming_game_ts = _resolve_game_date(upcoming_game_date)

    # Handle backtest mode with as-of data fetching
    if backtest_mode and as_of is not None:
        from nba_data.asof_fetchers import SimpleCache, get_team_stats_asof
        from nba_data.team_resolver import get_team_id

        # Use as-of fetching for backtesting
        cache = SimpleCache()
        try:
            home_id = get_team_id(home_team)
            away_id = get_team_id(away_team)

            home_asof_stats = get_team_stats_asof(home_id, as_of, last_n_window, cache)
            away_asof_stats = get_team_stats_asof(away_id, as_of, last_n_window, cache)

            # Convert as-of stats to TeamDataBundle format for compatibility
            home_data = _convert_asof_stats_to_team_data(home_asof_stats, home_team, season_end_year)
            away_data = _convert_asof_stats_to_team_data(away_asof_stats, away_team, season_end_year)

            # Use a simple league average for backtesting
            league_avg_ortg = 110.0  # Could be made more sophisticated

            # Skip head-to-head for now in backtest mode (could be added later)
            head_to_head_profile = {}

        except Exception as e:
            raise RuntimeError(f"Failed to fetch as-of data for backtesting: {e}")

    else:
        # Standard live mode fetching
        fetchers = _build_fetchers()

        home_data, away_data, league_avg_ortg, head_to_head_profile = collect_matchup_data(
            home_team=home_team,
            away_team=away_team,
            season_end_year=season_end_year,
            upcoming_game_ts=upcoming_game_ts,
            fetchers=fetchers,
        )

    home_weighted = compute_weighted_stats(home_data, recency_weight)
    away_weighted = compute_weighted_stats(away_data, recency_weight)

    home_prepared = _contextualize_team(
        team_data=home_data,
        weighted=home_weighted,
        head_to_head_profile=head_to_head_profile,
        location="home",
    )
    away_prepared = _contextualize_team(
        team_data=away_data,
        weighted=away_weighted,
        head_to_head_profile=head_to_head_profile,
        location="away",
    )

    home_team_stats = _create_team_stats(home_prepared, league_avg_ortg)
    away_team_stats = _create_team_stats(away_prepared, league_avg_ortg)

    simulation_results, simulation_mode = _run_simulation(
        home_team_stats,
        away_team_stats,
        league_avg_ortg,
        sportsbook_line,
        num_simulations,
        seed=seed if backtest_mode else None,
    )

    (
        edge_analysis,
        decision,
        win_probability,
        push_probability,
        loss_probability,
        implied_probability,
        expected_value,
    ) = _evaluate_betting_edge(simulation_results, decimal_odds, home_team)
    edge_percent = edge_analysis.get("edge_percentage", 0.0)

    data = {
        "home_team": home_team,
        "away_team": away_team,
        "league_avg_ortg": league_avg_ortg,
        "home_team_stats": _build_team_output(home_prepared),
        "away_team_stats": _build_team_output(away_prepared),
        "home_four_factors": _build_four_factors_output(home_prepared),
        "away_four_factors": _build_four_factors_output(away_prepared),
        "home_misc_stats": _build_misc_output(home_prepared),
        "away_misc_stats": _build_misc_output(away_prepared),
        "contextual_factors": _build_contextual_factors(home_prepared, away_prepared, head_to_head_profile),
        "simulation_settings": {
            "mode": simulation_mode,
            "num_simulations": num_simulations,
            "description": (
                "High Precision (1M simulations)" if simulation_mode == "high_precision" else "Standard Precision (100k simulations)"
            ),
        },
        "monte_carlo_results": {
            "games_simulated": simulation_results.games_simulated,
            "home_covers_count": simulation_results.home_covers_count,
            "home_covers_percentage": simulation_results.home_covers_percentage,
            "push_count": getattr(simulation_results, "push_count", 0),
            "push_percentage": getattr(simulation_results, "push_percentage", 0.0),
            "home_wins_count": simulation_results.home_wins_count,
            "home_win_percentage": simulation_results.home_win_percentage,
            "average_scores": {
                "home": simulation_results.average_home_score,
                "away": simulation_results.average_away_score,
            },
            "average_margin": simulation_results.average_margin,
            "margin_std_dev": simulation_results.margin_std,
            "confidence_interval_95": simulation_results.confidence_interval_95,
        },
        "betting_analysis": {
            "sportsbook_line": sportsbook_line,
            "decimal_odds": decimal_odds,
            "win_probability": win_probability,
            "true_probability": win_probability,
            "push_probability": push_probability,
            "loss_probability": loss_probability,
            "implied_probability": implied_probability,
            "expected_value": expected_value,
            "edge_percentage": edge_percent,
            "decision": decision,
        },
    }

    text_report = build_text_report(
        home_team=home_team,
        away_team=away_team,
        league_avg_ortg=league_avg_ortg,
        recency_weight=recency_weight,
        home_data=home_data,
        away_data=away_data,
        home_weighted=home_weighted,
        away_weighted=away_weighted,
        home_adjustments=home_prepared.adjustments,
        away_adjustments=away_prepared.adjustments,
        head_to_head_profile=head_to_head_profile,
        simulation_results=simulation_results,
        simulation_mode=simulation_mode,
        sportsbook_line=sportsbook_line,
        decimal_odds=decimal_odds,
        win_probability=win_probability,
        push_probability=push_probability,
        loss_probability=loss_probability,
        implied_probability=implied_probability,
        expected_value=expected_value,
        edge_percent=edge_percent,
        decision=decision,
    )

    return data, text_report


def run_analysis() -> Tuple[Dict[str, Any], str]:
    """Run the betting analysis with default parameters."""

    HOME_TEAM = "LOS ANGELES LAKERS"
    AWAY_TEAM = "GOLDEN STATE WARRIORS"
    SEASON_END_YEAR = 2025
    RECENCY_WEIGHT = 0.4
    SPORTSBOOK_LINE = -3.5
    DECIMAL_ODDS = 1.91
    return compute_model_report(
        home_team=HOME_TEAM,
        away_team=AWAY_TEAM,
        season_end_year=SEASON_END_YEAR,
        recency_weight=RECENCY_WEIGHT,
        sportsbook_line=SPORTSBOOK_LINE,
        decimal_odds=DECIMAL_ODDS,
        num_simulations=100_000,
    )
