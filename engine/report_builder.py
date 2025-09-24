"""Text report construction utilities."""

from __future__ import annotations

from typing import Any, Dict, List

from engine.data_pipeline import TeamDataBundle
from engine.stat_processing import WeightedStats
from engine.statistical_models import SimulationResults


def _safe_format(value, default=0.0, fmt_str: str = "+.1f") -> str:
    """Safely format a value that might be ``None``."""

    return (value if value is not None else default).__format__(fmt_str)


def build_text_report(
    *,
    home_team: str,
    away_team: str,
    league_avg_ortg: float,
    recency_weight: float,
    home_data: TeamDataBundle,
    away_data: TeamDataBundle,
    home_weighted: WeightedStats,
    away_weighted: WeightedStats,
    home_adjustments: Dict[str, Any],
    away_adjustments: Dict[str, Any],
    head_to_head_profile: Dict[str, Any],
    simulation_results: SimulationResults,
    simulation_mode: str,
    sportsbook_line: float,
    decimal_odds: float,
    win_probability: float,
    push_probability: float,
    loss_probability: float,
    implied_probability: float,
    expected_value: float,
    edge_percent: float,
    decision: str,
) -> str:
    """Create the human-readable analysis report."""

    lines: List[str] = []
    lines.append("🏀 MONTE CARLO NBA BETTING ANALYSIS")
    lines.append("=" * 50)
    lines.append(f"Home Team: {home_team}")
    lines.append(f"Away Team: {away_team}")
    lines.append(f"League Average ORtg: {league_avg_ortg:.2f}")
    lines.append("")
    lines.append("📊 REAL NBA DATA from official NBA.com API")
    lines.append("")
    lines.append("Season-Long Statistics:")
    lines.append(
        f"  {home_team}: pace={home_data.season['pace']:.1f}, ORtg={home_data.season['ortg']:.1f}, DRtg={home_data.season['drtg']:.1f}"
    )
    lines.append(
        f"  {away_team}: pace={away_data.season['pace']:.1f}, ORtg={away_data.season['ortg']:.1f}, DRtg={away_data.season['drtg']:.1f}"
    )
    lines.append("")
    lines.append("Last 10 Games Statistics:")
    lines.append(
        f"  {home_team}: pace={home_data.last_10['pace']:.1f}, ORtg={home_data.last_10['ortg']:.1f}, DRtg={home_data.last_10['drtg']:.1f}"
    )
    lines.append(
        f"  {away_team}: pace={away_data.last_10['pace']:.1f}, ORtg={away_data.last_10['ortg']:.1f}, DRtg={away_data.last_10['drtg']:.1f}"
    )
    lines.append("")
    lines.append(f"Final Weighted Stats (Recency Weight: {recency_weight:.0%}):")
    lines.append(
        f"  {home_team}: pace={home_weighted.core['pace']:.1f}, ORtg={home_weighted.core['ortg']:.1f}, DRtg={home_weighted.core['drtg']:.1f}"
    )
    lines.append(
        f"  {away_team}: pace={away_weighted.core['pace']:.1f}, ORtg={away_weighted.core['ortg']:.1f}, DRtg={away_weighted.core['drtg']:.1f}"
    )
    lines.append("")
    lines.append("🎯 FOUR FACTORS ANALYSIS (Enhanced Model)")
    lines.append("")
    lines.append("Final Weighted Four Factors:")
    lines.append(f"  {home_team}:")
    lines.append(
        f"    EFG%: {home_weighted.four_factors['efg_pct']:.3f} | FTA Rate: {home_weighted.four_factors['fta_rate']:.3f}"
    )
    lines.append(
        f"    TOV%: {home_weighted.four_factors['tov_pct']:.3f} | OREB%: {home_weighted.four_factors['oreb_pct']:.3f}"
    )
    lines.append(f"  {away_team}:")
    lines.append(
        f"    EFG%: {away_weighted.four_factors['efg_pct']:.3f} | FTA Rate: {away_weighted.four_factors['fta_rate']:.3f}"
    )
    lines.append(
        f"    TOV%: {away_weighted.four_factors['tov_pct']:.3f} | OREB%: {away_weighted.four_factors['oreb_pct']:.3f}"
    )
    lines.append("")
    lines.append("Defensive Four Factors (What Teams Allow):")
    lines.append(f"  {home_team} Defense:")
    lines.append(
        f"    Opp EFG%: {home_weighted.four_factors['opp_efg_pct']:.3f} | Opp FTA Rate: {home_weighted.four_factors['opp_fta_rate']:.3f}"
    )
    lines.append(
        f"    Opp TOV%: {home_weighted.four_factors['opp_tov_pct']:.3f} | Opp OREB%: {home_weighted.four_factors['opp_oreb_pct']:.3f}"
    )
    lines.append(f"  {away_team} Defense:")
    lines.append(
        f"    Opp EFG%: {away_weighted.four_factors['opp_efg_pct']:.3f} | Opp FTA Rate: {away_weighted.four_factors['opp_fta_rate']:.3f}"
    )
    lines.append(
        f"    Opp TOV%: {away_weighted.four_factors['opp_tov_pct']:.3f} | Opp OREB%: {away_weighted.four_factors['opp_oreb_pct']:.3f}"
    )
    lines.append("")
    lines.append("📈 MISCELLANEOUS STATS ANALYSIS (Phase 1 Complete)")
    lines.append("")
    lines.append("Final Weighted Miscellaneous Stats:")
    lines.append(f"  {home_team}:")
    lines.append(
        f"    Points off Turnovers: {home_weighted.misc['pts_off_tov']:.1f} | Second Chance Points: {home_weighted.misc['pts_2nd_chance']:.1f}"
    )
    lines.append(f"  {away_team}:")
    lines.append(
        f"    Points off Turnovers: {away_weighted.misc['pts_off_tov']:.1f} | Second Chance Points: {away_weighted.misc['pts_2nd_chance']:.1f}"
    )
    lines.append("")
    lines.append("Defensive Miscellaneous Stats (What Teams Allow):")
    lines.append(f"  {home_team} Defense:")
    lines.append(
        f"    Opp Points off TO: {home_weighted.misc['opp_pts_off_tov']:.1f} | Opp Second Chance: {home_weighted.misc['opp_pts_2nd_chance']:.1f}"
    )
    lines.append(f"  {away_team} Defense:")
    lines.append(
        f"    Opp Points off TO: {away_weighted.misc['opp_pts_off_tov']:.1f} | Opp Second Chance: {away_weighted.misc['opp_pts_2nd_chance']:.1f}"
    )
    lines.append("")
    lines.append("🛌 SCHEDULE & FATIGUE CONTEXT")
    lines.append("")
    home_rest_days = home_data.rest_profile.rest_days_before_last_game
    away_rest_days = away_data.rest_profile.rest_days_before_last_game
    lines.append(
        f"  {home_team}: Rest {home_rest_days if home_rest_days is not None else 'N/A'} days, {home_data.rest_profile.fatigue_flag_last_game}"
    )
    for note in home_adjustments["fatigue"].get("notes", []):
        lines.append(f"    - {note}")
    lines.append(
        f"  {away_team}: Rest {away_rest_days if away_rest_days is not None else 'N/A'} days, {away_data.rest_profile.fatigue_flag_last_game}"
    )
    for note in away_adjustments["fatigue"].get("notes", []):
        lines.append(f"    - {note}")
    lines.append("")
    lines.append("🏟️ VENUE IMPACT")
    lines.append("")
    home_venue_diff = home_data.venue_splits.get("venue_differentials", {})
    away_venue_diff = away_data.venue_splits.get("venue_differentials", {})
    lines.append(
        f"  {home_team} Home Edge: Points {_safe_format(home_venue_diff.get('points_advantage'))}, Win% {_safe_format(home_venue_diff.get('win_pct_advantage'), fmt_str='+.3f')}, ORtg {_safe_format(home_venue_diff.get('ortg_advantage'), fmt_str='+.2f')}"
    )
    for note in home_adjustments["venue"].get("notes", []):
        lines.append(f"    - {note}")
    lines.append(
        f"  {away_team} Road Impact: Points {_safe_format(away_venue_diff.get('points_advantage'))}, Win% {_safe_format(away_venue_diff.get('win_pct_advantage'), fmt_str='+.3f')}, ORtg {_safe_format(away_venue_diff.get('ortg_advantage'), fmt_str='+.2f')}"
    )
    for note in away_adjustments["venue"].get("notes", []):
        lines.append(f"    - {note}")
    lines.append("")
    lines.append("🔥 HUSTLE & EFFORT SIGNALS")
    lines.append("")
    home_effort_pct = (
        f"{home_data.hustle_profile.effort_percentile * 100:.1f}%"
        if home_data.hustle_profile.effort_percentile is not None
        else "N/A"
    )
    away_effort_pct = (
        f"{away_data.hustle_profile.effort_percentile * 100:.1f}%"
        if away_data.hustle_profile.effort_percentile is not None
        else "N/A"
    )
    lines.append(
        f"  {home_team}: Effort Score {home_data.hustle_profile.team_effort_score:.2f} (Percentile {home_effort_pct})"
    )
    for note in home_adjustments["hustle"].get("notes", []):
        lines.append(f"    - {note}")
    lines.append(
        f"  {away_team}: Effort Score {away_data.hustle_profile.team_effort_score:.2f} (Percentile {away_effort_pct})"
    )
    for note in away_adjustments["hustle"].get("notes", []):
        lines.append(f"    - {note}")
    lines.append("")
    lines.append("🤝 HEAD-TO-HEAD HISTORY")
    lines.append("")
    seasons = head_to_head_profile.get("season_span", [])
    season_label = ", ".join(seasons) if seasons else "No seasons"
    lines.append(
        f"  Seasons Covered ({head_to_head_profile.get('season_type', 'Regular Season')}): {season_label}"
    )
    home_record = head_to_head_profile.get("team_records", {}).get(home_team, {})
    away_record = head_to_head_profile.get("team_records", {}).get(away_team, {})
    lines.append(
        f"  {home_team}: {home_record.get('team_wins', 0)}-{home_record.get('opponent_wins', 0)} ({home_record.get('win_pct', 0.0):.1%}), Avg Margin {home_record.get('avg_margin', 0.0):+.1f}"
    )
    lines.append(
        f"  {away_team}: {away_record.get('team_wins', 0)}-{away_record.get('opponent_wins', 0)} ({away_record.get('win_pct', 0.0):.1%}), Avg Margin {away_record.get('avg_margin', 0.0):+.1f}"
    )
    recent_games = head_to_head_profile.get("recent_games", [])
    if recent_games:
        lines.append("  Recent Meetings:")
        for game in recent_games:
            lines.append(
                "    "
                f"{game.get('game_date', 'N/A')}: "
                f"{home_team} {game.get('team_score', 0.0):.0f} - "
                f"{away_team} {game.get('opponent_score', 0.0):.0f} "
                f"({game.get('result', 'N/A')} {game.get('margin', 0.0):+.1f})"
            )
    for note in home_adjustments["head_to_head"].get("notes", []):
        lines.append(f"    - {home_team}: {note}")
    for note in away_adjustments["head_to_head"].get("notes", []):
        lines.append(f"    - {away_team}: {note}")
    lines.append("")
    lines.append("🎲 MONTE CARLO SIMULATION RESULTS")
    lines.append(
        "Simulation Mode: "
        + (
            "High Precision (1,000,000 sims)"
            if simulation_mode == "high_precision"
            else "Standard (100,000 sims)"
        )
    )
    lines.append(f"Games Simulated: {simulation_results.games_simulated:,}")
    lines.append(
        f"Home Team Covers Spread: {simulation_results.home_covers_count:,} times ({simulation_results.home_covers_percentage:.1f}%)"
    )
    push_count = getattr(simulation_results, "push_count", 0)
    push_percentage = getattr(simulation_results, "push_percentage", 0.0)
    lines.append(f"Push Outcomes: {push_count:,} times ({push_percentage:.1f}%)")
    lines.append(
        f"Average Final Scores: {home_team} {simulation_results.average_home_score:.1f}, {away_team} {simulation_results.average_away_score:.1f}"
    )
    lines.append(
        f"Average Margin: {simulation_results.average_margin:.1f} ± {simulation_results.margin_std:.1f} points"
    )
    lines.append(
        "95% Confidence Interval (Mean Margin): "
        f"{simulation_results.confidence_interval_95[0]:.1f} to "
        f"{simulation_results.confidence_interval_95[1]:.1f}"
    )
    lines.append("")
    lines.append("💰 BETTING ANALYSIS")
    lines.append(f"Sportsbook Line: {sportsbook_line:+.1f}")
    lines.append(f"Decimal Odds: {decimal_odds:.2f}")
    lines.append(f"Win Probability (from simulation): {win_probability:.1%}")
    lines.append(f"Push Probability: {push_probability:.1%}")
    lines.append(f"Loss Probability: {loss_probability:.1%}")
    lines.append(f"Implied Probability (from odds): {implied_probability:.1%}")
    lines.append(f"Expected Value: {expected_value:+.4f}")
    lines.append(f"Edge Percentage: {edge_percent:+.2f}%")
    lines.append("")
    lines.append(f"🎯 RECOMMENDATION: {decision}")

    return "\n".join(lines)
