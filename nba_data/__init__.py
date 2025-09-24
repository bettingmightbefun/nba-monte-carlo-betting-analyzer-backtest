"""
NBA Data Package
================

NBA API integration and data fetching functionality.

This package contains all NBA data-related components:
- Team statistics fetching from NBA.com API
- Team name resolution and validation
- League-wide analytics and calculations
- Four Factors data integration
"""

__version__ = "1.0.0"
__author__ = "NBA Monte Carlo Betting Analyzer"

# Core data components
from .advanced_stats import get_season_team_stats, get_last_10_stats
from .four_factors import get_four_factors_team_stats
from .misc_stats import get_misc_team_stats
from .team_resolver import get_team_id, format_season
from .league_analytics import compute_league_average_ortg
from .schedule_fatigue import get_team_rest_profile
from .venue_splits import get_team_venue_splits
from .hustle_stats import get_team_hustle_profile
from .head_to_head import get_head_to_head_profile

__all__ = [
    'get_season_team_stats',
    'get_last_10_stats', 
    'get_four_factors_team_stats',
    'get_misc_team_stats',
    'get_team_id',
    'format_season',
    'compute_league_average_ortg',
    'get_team_rest_profile',
    'get_team_venue_splits',
    'get_team_hustle_profile',
    'get_head_to_head_profile'
]

