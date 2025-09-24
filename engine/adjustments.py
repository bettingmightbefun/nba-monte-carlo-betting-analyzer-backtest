"""Contextual adjustment helpers for team statistics."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from nba_data.hustle_stats import TeamHustleProfile
from nba_data.schedule_fatigue import TeamRestProfile


def apply_hustle_adjustments(
    stats: Dict[str, float],
    misc_stats: Dict[str, float],
    hustle_profile: TeamHustleProfile,
) -> Dict[str, Any]:
    """Adjust team metrics based on hustle data."""

    adjustments: Dict[str, Any] = {"notes": []}
    league_avg = hustle_profile.league_average_effort
    team_effort = hustle_profile.team_effort_score

    if league_avg is None or league_avg == 0:
        adjustments["notes"].append("No league hustle baseline – skipping effort adjustment.")
        return adjustments

    if math.isnan(league_avg) or math.isnan(team_effort):
        adjustments["notes"].append("Invalid hustle metrics – skipping effort adjustment.")
        return adjustments

    relative = (team_effort - league_avg) / league_avg
    if math.isnan(relative):
        adjustments["notes"].append("Invalid hustle differential – skipping effort adjustment.")
        return adjustments

    relative = max(min(relative, 0.2), -0.2)

    if abs(relative) < 0.02:
        adjustments["notes"].append("Effort score near league average – no adjustment applied.")
        return adjustments

    multipliers: Dict[str, float] = {}

    defensive_shift = max(min(relative * 0.5, 0.03), -0.03)
    if abs(defensive_shift) > 1e-6:
        drtg_multiplier = 1.0 - defensive_shift
        stats["drtg"] *= drtg_multiplier
        multipliers["drtg"] = round(drtg_multiplier, 4)

    turnover_shift = max(min(relative * 0.6, 0.08), -0.08)
    if abs(turnover_shift) > 1e-6:
        if "pts_off_tov" in misc_stats:
            misc_stats["pts_off_tov"] *= 1.0 + turnover_shift
            multipliers["pts_off_tov"] = round(1.0 + turnover_shift, 4)
        if "pts_2nd_chance" in misc_stats:
            misc_stats["pts_2nd_chance"] *= 1.0 + (turnover_shift * 0.4)
            multipliers["pts_2nd_chance"] = round(1.0 + (turnover_shift * 0.4), 4)
        if "opp_pts_off_tov" in misc_stats:
            misc_stats["opp_pts_off_tov"] *= 1.0 - (turnover_shift * 0.6)
            multipliers["opp_pts_off_tov"] = round(1.0 - (turnover_shift * 0.6), 4)
        if "opp_pts_2nd_chance" in misc_stats:
            misc_stats["opp_pts_2nd_chance"] *= 1.0 - (turnover_shift * 0.4)
            multipliers["opp_pts_2nd_chance"] = round(1.0 - (turnover_shift * 0.4), 4)

    adjustments["notes"].append(
        f"Hustle differential ({relative * 100:+.1f}%) applied to defense and extra-chance stats."
    )
    if multipliers:
        adjustments["multipliers"] = multipliers
    return adjustments


def apply_fatigue_adjustments(
    stats: Dict[str, float],
    misc_stats: Dict[str, float],
    rest_profile: TeamRestProfile,
) -> Dict[str, Any]:
    """Modify statistics based on rest and fatigue context."""

    adjustments: Dict[str, Any] = {"notes": []}
    rest_days_upcoming = rest_profile.rest_days_until_next_game

    if rest_days_upcoming is None:
        adjustments["notes"].append(
            "Upcoming game date unavailable – skipping fatigue adjustment."
        )
        adjustments["rest_days_until_next_game"] = None
        adjustments["rest_days_before_last_game"] = rest_profile.rest_days_before_last_game
        return adjustments

    if rest_days_upcoming <= 1:
        pace_mult = 0.97
        ortg_mult = 0.98
        drtg_mult = 1.015
        stats["pace"] *= pace_mult
        stats["ortg"] *= ortg_mult
        stats["drtg"] *= drtg_mult
        if "pts_off_tov" in misc_stats:
            misc_stats["pts_off_tov"] *= 0.97
        if "pts_2nd_chance" in misc_stats:
            misc_stats["pts_2nd_chance"] *= 0.97
        adjustments["notes"].append(
            "Back-to-back fatigue penalty applied (-3% pace, -2% ORtg, +1.5% DRtg)."
        )
        adjustments["multipliers"] = {
            "pace": round(pace_mult, 3),
            "ortg": round(ortg_mult, 3),
            "drtg": round(drtg_mult, 3),
        }
    elif rest_days_upcoming == 2:
        pace_mult = 0.99
        ortg_mult = 0.99
        stats["pace"] *= pace_mult
        stats["ortg"] *= ortg_mult
        adjustments["notes"].append(
            "Two days rest – slight normalization (-1% pace/ORtg)."
        )
        adjustments["multipliers"] = {
            "pace": round(pace_mult, 3),
            "ortg": round(ortg_mult, 3),
        }
    elif rest_days_upcoming >= 4:
        pace_mult = 1.01
        ortg_mult = 1.015
        drtg_mult = 0.985
        stats["pace"] *= pace_mult
        stats["ortg"] *= ortg_mult
        stats["drtg"] *= drtg_mult
        if "pts_off_tov" in misc_stats:
            misc_stats["pts_off_tov"] *= 1.03
        if "pts_2nd_chance" in misc_stats:
            misc_stats["pts_2nd_chance"] *= 1.02
        adjustments["notes"].append(
            "Extended rest boost applied (+1% pace, +1.5% ORtg, -1.5% DRtg)."
        )
        adjustments["multipliers"] = {
            "pace": round(pace_mult, 3),
            "ortg": round(ortg_mult, 3),
            "drtg": round(drtg_mult, 3),
        }
    else:
        adjustments["notes"].append("Standard rest window – no fatigue adjustment required.")

    adjustments["rest_days"] = rest_days_upcoming
    adjustments["rest_days_until_next_game"] = rest_days_upcoming
    adjustments["rest_days_before_last_game"] = rest_profile.rest_days_before_last_game
    return adjustments


def apply_venue_adjustments(
    stats: Dict[str, float],
    venue_splits: Dict[str, Dict[str, Optional[float]]],
    season_baseline: Dict[str, float],
    location: str,
) -> Dict[str, Any]:
    """Alter ratings based on venue performance."""

    adjustments: Dict[str, Any] = {"notes": []}
    key = "home_performance" if location == "home" else "away_performance"
    performance = venue_splits.get(key, {})

    if not performance:
        adjustments["notes"].append("Venue splits unavailable – no adjustment applied.")
        return adjustments

    rating_deltas: Dict[str, float] = {}

    offensive_rating = performance.get("offensive_rating")
    if offensive_rating is not None and season_baseline.get("ortg") is not None:
        raw_delta = offensive_rating - season_baseline["ortg"]
        weighted_delta = raw_delta * 0.5
        stats["ortg"] += weighted_delta
        rating_deltas["ortg"] = round(weighted_delta, 2)
        adjustments["notes"].append(
            f"Venue offensive tilt adds {weighted_delta:+.2f} ORtg (50% of {raw_delta:+.2f})."
        )

    defensive_rating = performance.get("defensive_rating")
    if defensive_rating is not None and season_baseline.get("drtg") is not None:
        raw_delta = defensive_rating - season_baseline["drtg"]
        weighted_delta = raw_delta * 0.5
        stats["drtg"] += weighted_delta
        rating_deltas["drtg"] = round(weighted_delta, 2)
        adjustments["notes"].append(
            f"Venue defensive tilt adds {weighted_delta:+.2f} DRtg (50% of {raw_delta:+.2f})."
        )

    if rating_deltas:
        adjustments["rating_deltas"] = rating_deltas
    else:
        adjustments["notes"].append("Venue ratings aligned with season averages – no shift applied.")

    return adjustments


def apply_head_to_head_adjustments(
    stats: Dict[str, float],
    profile: Dict[str, Any],
    team_key: str,
) -> Dict[str, Any]:
    """Incorporate head-to-head performance into team ratings."""

    adjustments: Dict[str, Any] = {"notes": []}
    team_record = profile.get("team_records", {}).get(team_key)

    if not team_record:
        adjustments["notes"].append("Head-to-head data unavailable.")
        return adjustments

    total_games = team_record.get("total_games", 0)
    if not total_games:
        adjustments["notes"].append("No recent meetings to inform adjustments.")
        return adjustments

    avg_margin = float(team_record.get("avg_margin", 0.0) or 0.0)
    margin_shift = max(min(avg_margin * 0.1, 1.5), -1.5)

    if abs(margin_shift) < 0.05:
        adjustments["notes"].append(
            "Historical results balanced – no rating shift applied."
        )
        return adjustments

    stats["ortg"] += margin_shift
    adjustments["notes"].append(
        f"Head-to-head margin ({avg_margin:+.2f}) nudges ORtg by {margin_shift:+.2f}."
    )
    adjustments["ortg_shift"] = round(margin_shift, 2)

    return adjustments
