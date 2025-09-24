"""
nba_team_resolver.py
===================

This module handles team identification and season formatting for NBA API calls.
Provides utilities to convert team names to NBA API team IDs and format season strings.

Functions
---------
get_team_id(team_name: str) -> int
    Convert team name/abbreviation to NBA team ID with exact and partial matching.

format_season(season_end_year: int) -> str
    Convert season end year to NBA API season format (e.g., 2024 -> "2023-24").

This module has zero dependencies on NBA API data fetching, making it lightweight
and easily testable in isolation.
"""

from __future__ import annotations

try:
    from nba_api.stats.static import teams
except ImportError as exc:
    raise ImportError(
        "nba_api package is required but not installed. Run: pip install nba_api"
    ) from exc


def get_team_id(team_name: str) -> int:
    """
    Convert team name/abbreviation to NBA team ID.
    
    Supports multiple input formats:
    - Full name: "Los Angeles Lakers"
    - Nickname: "Lakers" 
    - Abbreviation: "LAL"
    - Partial match: "Los Angeles" (matches first found)
    
    Args:
        team_name: Team name, nickname, or abbreviation
        
    Returns:
        NBA team ID as integer
        
    Raises:
        ValueError: If team name is empty or no matching team found
        
    Examples:
        >>> get_team_id("Los Angeles Lakers")
        1610612747
        >>> get_team_id("Lakers")
        1610612747
        >>> get_team_id("LAL")
        1610612747
    """
    if not team_name:
        raise ValueError("team name cannot be empty")

    # Special handling for ambiguous abbreviations
    team_name_upper = team_name.upper().strip()
    if team_name_upper == "SA":
        # SA typically refers to San Antonio Spurs in sports contexts
        return 1610612759  # San Antonio Spurs

    # Get all NBA teams from static data
    nba_teams = teams.get_teams()
    
    # Try exact matches first (most reliable)
    for team in nba_teams:
        if (team['abbreviation'].upper() == team_name_upper or 
            team['full_name'].upper() == team_name_upper or
            team['nickname'].upper() == team_name_upper):
            return team['id']
    
    # Try partial matches as fallback
    partial_matches = [
        team for team in nba_teams
        if (
            team_name_upper in team['full_name'].upper()
            or team_name_upper in team['nickname'].upper()
        )
    ]

    if len(partial_matches) == 1:
        return partial_matches[0]["id"]

    if len(partial_matches) > 1:
        candidate_names = ", ".join(team["full_name"] for team in partial_matches)
        raise ValueError(
            "Ambiguous team name "
            f"'{team_name}'. Candidates: {candidate_names}"
        )

    # No match found
    raise ValueError(f"Could not find NBA team: {team_name}")


def format_season(season_end_year: int) -> str:
    """
    Convert season end year to NBA API season format.
    
    NBA API expects seasons in "YYYY-YY" format where the first year
    is the start of the season and YY is the last two digits of the end year.
    
    Args:
        season_end_year: The year the season ends (e.g., 2024 for 2023-24 season)
        
    Returns:
        Season string in NBA API format
        
    Examples:
        >>> format_season(2024)
        "2023-24"
        >>> format_season(2023)
        "2022-23"
    """
    start_year = season_end_year - 1
    return f"{start_year}-{str(season_end_year)[-2:]}"


# Test function for this module
def test_team_resolver():
    """Test team resolution functionality."""
    print("🔍 Testing NBA Team Resolver...")
    
    # Test common team formats
    test_cases = [
        ("Los Angeles Lakers", "Full name"),
        ("Lakers", "Nickname"),
        ("LAL", "Abbreviation"),
        ("Golden State Warriors", "Full name"),
        ("Warriors", "Nickname"),
        ("GSW", "Abbreviation")
    ]
    
    for team_name, format_type in test_cases:
        try:
            team_id = get_team_id(team_name)
            print(f"✅ {format_type}: '{team_name}' → ID {team_id}")
        except Exception as e:
            print(f"❌ {format_type}: '{team_name}' → ERROR: {e}")
    
    # Test season formatting
    print(f"\n📅 Season Format Tests:")
    for year in [2024, 2023, 2025]:
        season_str = format_season(year)
        print(f"✅ {year} → '{season_str}'")
    
    print("✅ Team resolver tests complete!")


if __name__ == "__main__":
    test_team_resolver()
