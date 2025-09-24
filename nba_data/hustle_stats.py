"""Hustle statistics helpers for quantifying team effort signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from nba_data.team_resolver import get_team_id, format_season

try:  # pragma: no cover - dependency optional for unit tests
    from nba_api.stats.endpoints import leaguehustlestatsteam
except ImportError:  # pragma: no cover - provide graceful fallback
    leaguehustlestatsteam = None  # type: ignore[assignment]


@dataclass(frozen=True)
class TeamHustleProfile:
    """Encapsulates core hustle metrics and derived effort signals."""

    deflections: float
    charges_drawn: float
    loose_balls_recovered: float
    screen_assists: float
    contested_shots: float
    box_outs: float
    minutes_played: float
    team_effort_score: float
    effort_percentile: Optional[float]
    league_average_effort: Optional[float]

    def as_dict(self) -> Dict[str, Optional[float]]:
        """Return serialisable representation."""

        return {
            "deflections": round(self.deflections, 2),
            "charges_drawn": round(self.charges_drawn, 2),
            "loose_balls_recovered": round(self.loose_balls_recovered, 2),
            "screen_assists": round(self.screen_assists, 2),
            "contested_shots": round(self.contested_shots, 2),
            "box_outs": round(self.box_outs, 2),
            "minutes_played": round(self.minutes_played, 1),
            "team_effort_score": round(self.team_effort_score, 2),
            "effort_percentile": round(self.effort_percentile, 3) if self.effort_percentile is not None else None,
            "league_average_effort": round(self.league_average_effort, 2) if self.league_average_effort is not None else None,
        }

def get_team_hustle_profile(team_name: str, season_end_year: int) -> TeamHustleProfile:
    """Fetch hustle metrics and derive effort score for a team."""

    if leaguehustlestatsteam is None:
        raise ImportError(
            "nba_api package is required for hustle statistics. "
            "Install it with `pip install nba_api`."
        )

    season = format_season(season_end_year)
    team_id = get_team_id(team_name)

    hustle = leaguehustlestatsteam.LeagueHustleStatsTeam(
        season=season,
        per_mode_time="PerGame",
    ).get_data_frames()[0]

    if hustle.empty:
        raise RuntimeError(
            f"No hustle statistics returned for season {season}."
        )

    team_row = hustle[hustle["TEAM_ID"] == team_id]
    if team_row.empty:
        raise RuntimeError(
            f"No hustle statistics found for team {team_name} in season {season}."
        )

    row = team_row.iloc[0]

    effort_score = (
        float(row.get("DEFLECTIONS", 0.0)) * 0.30
        + float(row.get("CHARGES_DRAWN", 0.0)) * 0.20
        + float(row.get("LOOSE_BALLS_RECOVERED", 0.0)) * 0.20
        + float(row.get("SCREEN_ASSISTS", 0.0)) * 0.15
        + float(row.get("CONTESTED_SHOTS", 0.0)) * 0.10
        + float(row.get("BOX_OUTS", 0.0)) * 0.05
    )

    league_effort_scores = (
        hustle["DEFLECTIONS"] * 0.30
        + hustle["CHARGES_DRAWN"] * 0.20
        + hustle["LOOSE_BALLS_RECOVERED"] * 0.20
        + hustle["SCREEN_ASSISTS"] * 0.15
        + hustle["CONTESTED_SHOTS"] * 0.10
        + hustle["BOX_OUTS"] * 0.05
    )

    league_avg_effort = float(league_effort_scores.mean()) if not league_effort_scores.empty else None

    effort_percentile = None
    if league_avg_effort is not None and len(league_effort_scores) > 1:
        rank = (league_effort_scores < effort_score).sum()
        effort_percentile = float(rank / (len(league_effort_scores) - 1))

    return TeamHustleProfile(
        deflections=float(row.get("DEFLECTIONS", 0.0)),
        charges_drawn=float(row.get("CHARGES_DRAWN", 0.0)),
        loose_balls_recovered=float(row.get("LOOSE_BALLS_RECOVERED", 0.0)),
        screen_assists=float(row.get("SCREEN_ASSISTS", 0.0)),
        contested_shots=float(row.get("CONTESTED_SHOTS", 0.0)),
        box_outs=float(row.get("BOX_OUTS", 0.0)),
        minutes_played=float(row.get("MIN", 0.0)),
        team_effort_score=effort_score,
        effort_percentile=effort_percentile,
        league_average_effort=league_avg_effort,
    )


__all__ = ["TeamHustleProfile", "get_team_hustle_profile"]
