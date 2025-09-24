"""
nba_data/team_alias.py
======================

Team name aliasing for handling differences between CSV data and NBA API conventions.
Provides mapping between various team name formats to ensure consistent team identification.

Functions
---------
normalize_team_name(team_name: str) -> str
    Normalize team name/abbreviation to NBA API compatible format.

TEAM_ALIASES: Dict[str, str]
    Mapping of alternative team names to canonical NBA API abbreviations.
"""

from __future__ import annotations

from typing import Dict

# Mapping of alternative team names/abbreviations to canonical NBA API format
TEAM_ALIASES: Dict[str, str] = {
    # Standard 3-letter codes that should work with nba_api
    # These are included for completeness - most should work directly

    # Historical team changes
    'sea': 'okc',  # Seattle SuperSonics -> Oklahoma City Thunder
    'van': 'mem',  # Vancouver Grizzlies -> Memphis Grizzlies
    'no': 'nop',   # New Orleans Hornets -> New Orleans Pelicans (2013)

    # Alternative abbreviations sometimes found in data
    'brk': 'bkn',  # Brooklyn Nets
    'cho': 'cha',  # Charlotte Hornets
    'pho': 'phx',  # Phoenix Suns
    'wsh': 'was',  # Washington Wizards
    'ny': 'nyk',   # New York Knicks

    # Full team names to abbreviations (if needed)
    'los angeles lakers': 'lal',
    'los angeles clippers': 'lac',
    'golden state warriors': 'gsw',
    'san antonio spurs': 'sas',
    'brooklyn nets': 'brk',
    'new york knicks': 'nyk',
    'boston celtics': 'bos',
    'philadelphia 76ers': 'phi',
    'miami heat': 'mia',
    'milwaukee bucks': 'mil',
    'chicago bulls': 'chi',
    'cleveland cavaliers': 'cle',
    'detroit pistons': 'det',
    'indiana pacers': 'ind',
    'atlanta hawks': 'atl',
    'charlotte hornets': 'cho',
    'washington wizards': 'was',
    'orlando magic': 'orl',
    'portland trail blazers': 'por',
    'utah jazz': 'uta',
    'denver nuggets': 'den',
    'minnesota timberwolves': 'min',
    'oklahoma city thunder': 'okc',
    'dallas mavericks': 'dal',
    'houston rockets': 'hou',
    'memphis grizzlies': 'mem',
    'new orleans pelicans': 'nop',
    'sacramento kings': 'sac',
    'phoenix suns': 'phx',
    'toronto raptors': 'tor',
}


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name/abbreviation to NBA API compatible format.

    Handles case conversion, common abbreviations, and historical team changes.

    Args:
        team_name: Team name or abbreviation from data source

    Returns:
        Canonical team abbreviation compatible with nba_api

    Examples:
        >>> normalize_team_name('GSW')
        'gsw'
        >>> normalize_team_name('Golden State Warriors')
        'gsw'
        >>> normalize_team_name('sea')  # SuperSonics
        'okc'
    """
    if not team_name:
        raise ValueError("Team name cannot be empty")

    # Convert to lowercase for consistent matching
    normalized = team_name.lower().strip()

    # Check direct alias mapping
    if normalized in TEAM_ALIASES:
        return TEAM_ALIASES[normalized]

    # If it's already a standard 3-letter code, return as-is
    if len(normalized) == 3 and normalized.isalpha():
        return normalized

    # If no alias found, return the original (assume it's already correct)
    return normalized
