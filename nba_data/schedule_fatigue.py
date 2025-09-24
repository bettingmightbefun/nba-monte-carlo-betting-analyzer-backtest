"""NBA schedule analysis utilities for rest days and fatigue factors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

from nba_data.team_resolver import get_team_id, format_season

try:  # pragma: no cover - import guarded for testing environments
    from nba_api.stats.endpoints import teamgamelogs
except ImportError:  # pragma: no cover - dependency optional for unit tests
    teamgamelogs = None  # type: ignore[assignment]


@dataclass(frozen=True)
class TeamRestProfile:
    """Represents recent rest dynamics for a specific team."""

    last_game_date: Optional[pd.Timestamp]
    rest_days_before_last_game: Optional[int]
    rest_days_until_next_game: Optional[int]
    fatigue_flag_last_game: str
    average_rest_days: float
    back_to_back_rate: float
    fatigue_score_mean: float

    def as_dict(self) -> Dict[str, Optional[float]]:
        """Return the profile as a serialisable dictionary."""

        return {
            "last_game_date": self.last_game_date.isoformat() if self.last_game_date else None,
            "rest_days_before_last_game": self.rest_days_before_last_game,
            "rest_days_until_next_game": self.rest_days_until_next_game,
            "fatigue_flag_last_game": self.fatigue_flag_last_game,
            "average_rest_days": round(self.average_rest_days, 2),
            "back_to_back_rate": round(self.back_to_back_rate, 3),
            "fatigue_score_mean": round(self.fatigue_score_mean, 3),
        }


def _compute_fatigue_score(rest_days: float) -> float:
    """Map rest days to a fatigue score (higher is more fatigue)."""

    if pd.isna(rest_days):
        return 0.7  # Neutral default when data is missing
    if rest_days <= 1:
        return 1.0
    if rest_days == 2:
        return 0.7
    if rest_days >= 4:
        return 0.3  # Very well rested boost
    return 0.5


def get_team_rest_profile(
    team_name: str,
    season_end_year: int,
    upcoming_game_date: Optional[pd.Timestamp | str] = None,
) -> TeamRestProfile:
    """Calculate recent rest and fatigue information for a team."""

    if teamgamelogs is None:
        raise ImportError(
            "nba_api package is required for schedule fatigue analysis. "
            "Install it with `pip install nba_api`."
        )

    team_id = get_team_id(team_name)
    season = format_season(season_end_year)

    game_logs = teamgamelogs.TeamGameLogs(
        team_id_nullable=team_id,
        season_nullable=season,
        season_type_nullable="Regular Season",
    ).get_data_frames()[0]

    if game_logs.empty:
        raise RuntimeError(
            f"No schedule data returned for {team_name} in season {season}."
        )

    df = game_logs.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values("GAME_DATE")
    df["LAST_GAME_DATE"] = df["GAME_DATE"].shift(1)
    df["REST_DAYS"] = (df["GAME_DATE"] - df["LAST_GAME_DATE"]).dt.days
    df["FATIGUE_SCORE"] = df["REST_DAYS"].apply(_compute_fatigue_score)
    df["BACK_TO_BACK"] = df["REST_DAYS"] <= 1

    last_row = df.tail(1).iloc[0]
    fatigue_flag = (
        "BACK_TO_BACK" if bool(last_row["BACK_TO_BACK"]) else "NORMAL REST"
    )
    if pd.isna(last_row["REST_DAYS"]):
        fatigue_flag = "SEASON OPENER"

    if upcoming_game_date is None:
        upcoming_game_ts = pd.Timestamp.today().normalize()
    else:
        upcoming_game_ts = pd.Timestamp(upcoming_game_date).normalize()

    rest_days_until_next_game: Optional[int]
    if pd.isna(last_row["GAME_DATE"]):
        rest_days_until_next_game = None
    else:
        last_game_date = last_row["GAME_DATE"].normalize()
        delta_days = int((upcoming_game_ts - last_game_date).days)
        if delta_days < 0:
            raise ValueError(
                "Upcoming game date "
                f"{upcoming_game_ts.date()} is before the last recorded game "
                f"on {last_game_date.date()} for {team_name}."
            )
        rest_days_until_next_game = delta_days

    avg_rest = float(df["REST_DAYS"].dropna().mean()) if df["REST_DAYS"].notna().any() else 0.0
    back_to_back_rate = (
        float(df["BACK_TO_BACK"].mean()) if df["BACK_TO_BACK"].notna().any() else 0.0
    )
    fatigue_score_mean = float(df["FATIGUE_SCORE"].mean())

    return TeamRestProfile(
        last_game_date=last_row["GAME_DATE"],
        rest_days_before_last_game=(
            int(last_row["REST_DAYS"]) if not pd.isna(last_row["REST_DAYS"]) else None
        ),
        rest_days_until_next_game=rest_days_until_next_game,
        fatigue_flag_last_game=fatigue_flag,
        average_rest_days=avg_rest,
        back_to_back_rate=back_to_back_rate,
        fatigue_score_mean=fatigue_score_mean,
    )


__all__ = ["TeamRestProfile", "get_team_rest_profile"]
