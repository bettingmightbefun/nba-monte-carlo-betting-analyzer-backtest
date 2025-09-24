"""NBA head-to-head matchup helper utilities."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import pandas as pd

from nba_data.team_resolver import get_team_id, format_season

try:  # pragma: no cover - import guarded for environments without nba_api
    from nba_api.stats.endpoints import leaguegamefinder
except ImportError as exc:  # pragma: no cover - handled during runtime initialisation
    raise ImportError(
        "nba_api package is required but not installed. Run: pip install nba_api"
    ) from exc


def get_head_to_head_profile(
    team_name: str,
    opponent_name: str,
    season_end_year: int,
    last_n_seasons: int = 3,
    season_type: str = "Regular Season",
    request_delay: float = 0.4,
) -> Dict[str, object]:
    """Return a summarized head-to-head profile between two teams.

    The helper aggregates recent matchup data (default last three seasons)
    and surfaces high level metrics such as win/loss record, scoring
    differentials, and a log of the most recent meetings.
    """

    if last_n_seasons < 1:
        raise ValueError("last_n_seasons must be at least 1")

    team_id = get_team_id(team_name)
    opponent_id = get_team_id(opponent_name)

    seasons_considered = [
        season_end_year - offset for offset in range(last_n_seasons - 1, -1, -1)
    ]

    frames: List[pd.DataFrame] = []

    for year in seasons_considered:
        season = format_season(year)
        try:
            finder = leaguegamefinder.LeagueGameFinder(
                team_id_nullable=team_id,
                vs_team_id_nullable=opponent_id,
                season_nullable=season,
                season_type_nullable=season_type,
                outcome_nullable=None,
            )
            if request_delay:
                time.sleep(request_delay)
            season_frame = finder.get_data_frames()[0]
        except Exception as exc:  # pragma: no cover - defensive guard for live API
            raise RuntimeError(
                f"Failed to fetch head-to-head games for {team_name} vs {opponent_name}: {exc}"
            ) from exc

        if not season_frame.empty:
            frames.append(season_frame)

    if frames:
        games_df = pd.concat(frames, ignore_index=True)
    else:
        games_df = pd.DataFrame()

    return _build_profile(
        games_df=games_df,
        team_name=team_name,
        opponent_name=opponent_name,
        seasons_considered=seasons_considered,
        season_type=season_type,
    )


def _build_profile(
    *,
    games_df: pd.DataFrame,
    team_name: str,
    opponent_name: str,
    seasons_considered: List[int],
    season_type: str,
) -> Dict[str, object]:
    """Assemble a serialisable matchup profile from the raw dataframe."""

    total_games = int(len(games_df.index)) if not games_df.empty else 0

    team_summary = _summarise_team_view(games_df, team_name, opponent_name)
    opponent_summary = _summarise_opponent_view(games_df, team_name, opponent_name)
    recent_games = _recent_games(games_df)

    profile: Dict[str, object] = {
        "season_span": [format_season(year) for year in seasons_considered],
        "season_type": season_type,
        "total_games": total_games,
        "team_records": {
            team_name: team_summary,
            opponent_name: opponent_summary,
        },
        "recent_games": recent_games,
    }

    return profile


def _summarise_team_view(
    games_df: pd.DataFrame, team_name: str, opponent_name: str
) -> Dict[str, object]:
    """Create a summary dictionary from the primary team perspective."""

    if games_df.empty:
        return {
            "team": team_name,
            "opponent": opponent_name,
            "total_games": 0,
            "team_wins": 0,
            "opponent_wins": 0,
            "win_pct": 0.0,
            "avg_margin": 0.0,
            "avg_points_scored": 0.0,
            "avg_points_allowed": 0.0,
            "last_meeting": None,
        }

    wins = int((games_df.get("WL") == "W").sum())
    losses = int((games_df.get("WL") == "L").sum())
    total_games = int(len(games_df.index))

    margin_series = games_df["PLUS_MINUS"] if "PLUS_MINUS" in games_df else None
    points_series = games_df["PTS"] if "PTS" in games_df else None
    # Calculate opponent points from team points and margin
    opp_points_series = points_series - margin_series if points_series is not None and margin_series is not None else None

    avg_margin = _mean_or_zero(margin_series)
    avg_points = _mean_or_zero(points_series)
    avg_allowed = _mean_or_zero(opp_points_series)

    last_meeting = _last_meeting_snapshot(games_df, perspective="team")

    win_pct = wins / total_games if total_games else 0.0

    return {
        "team": team_name,
        "opponent": opponent_name,
        "total_games": total_games,
        "team_wins": wins,
        "opponent_wins": losses,
        "win_pct": win_pct,
        "avg_margin": avg_margin,
        "avg_points_scored": avg_points,
        "avg_points_allowed": avg_allowed,
        "last_meeting": last_meeting,
    }


def _summarise_opponent_view(
    games_df: pd.DataFrame, team_name: str, opponent_name: str
) -> Dict[str, object]:
    """Return the complementary view for the opponent team."""

    team_summary = _summarise_team_view(games_df, team_name, opponent_name)

    total_games = team_summary["total_games"]
    avg_margin = float(team_summary["avg_margin"])
    avg_points_scored = float(team_summary["avg_points_allowed"])
    avg_points_allowed = float(team_summary["avg_points_scored"])
    wins = int(team_summary["opponent_wins"])
    losses = int(team_summary["team_wins"])
    win_pct = wins / total_games if total_games else 0.0

    last_meeting = _last_meeting_snapshot(games_df, perspective="opponent")

    return {
        "team": opponent_name,
        "opponent": team_name,
        "total_games": total_games,
        "team_wins": wins,
        "opponent_wins": losses,
        "win_pct": win_pct,
        "avg_margin": -avg_margin,
        "avg_points_scored": avg_points_scored,
        "avg_points_allowed": avg_points_allowed,
        "last_meeting": last_meeting,
    }


def _recent_games(games_df: pd.DataFrame, limit: int = 5) -> List[Dict[str, object]]:
    """Return the last ``limit`` games from the primary team perspective."""

    if games_df.empty:
        return []

    if "GAME_DATE" not in games_df.columns:
        ordered = games_df.tail(limit)
    else:
        ordered = games_df.assign(
            _parsed_date=pd.to_datetime(games_df["GAME_DATE"], errors="coerce")
        ).sort_values("_parsed_date")
        ordered = ordered.tail(limit)

    results: List[Dict[str, object]] = []

    for _, row in ordered.iterrows():
        game_date = None
        if "GAME_DATE" in row and pd.notna(row["GAME_DATE"]):
            try:
                game_date = pd.to_datetime(row["GAME_DATE"]).date().isoformat()
            except Exception:  # pragma: no cover - robust fallback
                game_date = str(row["GAME_DATE"])

        team_score = _coerce_float(row.get("PTS"))
        margin = _coerce_float(row.get("PLUS_MINUS"))
        # Calculate opponent score from team score and margin
        # If team has +10 margin, opponent scored 10 less
        opp_score = team_score - margin

        results.append(
            {
                "game_date": game_date,
                "team_score": team_score,
                "opponent_score": opp_score,
                "margin": margin,
                "result": row.get("WL"),
                "matchup": row.get("MATCHUP"),
            }
        )

    return results


def _last_meeting_snapshot(
    games_df: pd.DataFrame, *, perspective: str
) -> Optional[Dict[str, object]]:
    """Produce a light-weight summary of the most recent meeting."""

    if games_df.empty:
        return None

    sorted_games = _recent_games(games_df, limit=1)
    if not sorted_games:
        return None

    entry = sorted_games[-1]

    if perspective == "team":
        return entry

    # mirror for opponent perspective
    mirrored = dict(entry)
    mirrored["team_score"], mirrored["opponent_score"] = (
        entry["opponent_score"],
        entry["team_score"],
    )
    mirrored["margin"] = -_coerce_float(entry.get("margin"))
    result = entry.get("result")
    mirrored["result"] = {"W": "L", "L": "W"}.get(result, result)
    return mirrored


def _mean_or_zero(series: Optional[pd.Series]) -> float:
    """Safely return the mean of a series or zero if unavailable."""

    if series is None or series.empty:
        return 0.0

    value = series.mean()
    if pd.isna(value):
        return 0.0
    return float(value)


def _coerce_float(value: Optional[object]) -> float:
    """Convert a potentially ``None``/NaN value to ``float`` safely."""

    if value is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        return 0.0
    if pd.isna(numeric):
        return 0.0
    return numeric


__all__ = ["get_head_to_head_profile"]

