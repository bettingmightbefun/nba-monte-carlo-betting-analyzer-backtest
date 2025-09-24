"""Utilities for weighting and cleaning statistical inputs."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict

from engine.constants import LEAGUE_AVG_MISC_STATS
from engine.data_pipeline import TeamDataBundle


@dataclass
class WeightedStats:
    """Weighted statistical profiles for a team."""

    core: Dict[str, float]
    four_factors: Dict[str, float]
    misc: Dict[str, float]


def _weighted_average(season_value: float, last10_value: float, weight: float) -> float:
    return season_value * (1.0 - weight) + last10_value * weight


def _clean_misc_value(raw_value) -> float:
    if raw_value is None:
        return math.nan
    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        return math.nan
    if math.isnan(numeric_value) or math.isinf(numeric_value):
        return math.nan
    return numeric_value


def _blend_misc_stat(key: str, team_data: TeamDataBundle, weight: float) -> float:
    season_value = _clean_misc_value(team_data.misc_season.get(key))
    last10_value = _clean_misc_value(team_data.misc_last10.get(key))

    if math.isnan(season_value) and math.isnan(last10_value):
        return LEAGUE_AVG_MISC_STATS[key]
    if math.isnan(last10_value):
        return season_value if not math.isnan(season_value) else LEAGUE_AVG_MISC_STATS[key]
    if math.isnan(season_value):
        return last10_value
    return _weighted_average(season_value, last10_value, weight)


def compute_weighted_stats(team_data: TeamDataBundle, recency_weight: float) -> WeightedStats:
    """Blend season and last-10 data into a weighted profile."""

    core_stats = {
        "pace": _weighted_average(team_data.season["pace"], team_data.last_10["pace"], recency_weight),
        "ortg": _weighted_average(team_data.season["ortg"], team_data.last_10["ortg"], recency_weight),
        "drtg": _weighted_average(team_data.season["drtg"], team_data.last_10["drtg"], recency_weight),
    }

    four_factors = {
        key: _weighted_average(
            team_data.four_factors_season[key],
            team_data.four_factors_last10[key],
            recency_weight,
        )
        for key in team_data.four_factors_season
    }

    misc_stats = {
        key: _blend_misc_stat(key, team_data, recency_weight)
        for key in LEAGUE_AVG_MISC_STATS
    }

    return WeightedStats(core=core_stats, four_factors=four_factors, misc=misc_stats)
