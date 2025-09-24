"""
stats_fetcher.py
================

NBA Statistics fetching unified interface.
This module provides a convenient single import point for NBA data fetching functionality.

Purpose:
- Unified testing interface for all NBA data modules
- Convenient single import for common NBA statistics functions  
- Stable API facade that abstracts internal module organization

Architecture:
- Re-exports functions from specialized modules (advanced_stats, four_factors, base_fetcher)
- Provides aggregated testing functionality
- Maintains clean separation between internal organization and external API

Functions
---------
All functions are re-exported from their respective specialized modules.
Use this module for convenience, or import directly from specific modules for clarity.
"""

from __future__ import annotations

# Import everything from the modularized components
from nba_data.advanced_stats import (
    get_season_team_stats,
    get_last_10_stats,
    test_advanced_stats
)

from nba_data.four_factors import (
    get_four_factors_team_stats,
    analyze_four_factors_advantage,
    test_four_factors
)

from nba_data.base_fetcher import (
    fetch_team_data,
    validate_team_data,
    extract_column_value,
    calculate_pace_from_basic_stats
)

# Re-export all functions for backward compatibility
__all__ = [
    # Advanced stats functions
    'get_season_team_stats',
    'get_last_10_stats', 
    'test_advanced_stats',
    
    # Four Factors functions
    'get_four_factors_team_stats',
    'analyze_four_factors_advantage',
    'test_four_factors',
    
    # Base fetcher utilities
    'fetch_team_data',
    'validate_team_data',
    'extract_column_value',
    'calculate_pace_from_basic_stats'
]


def test_stats_fetcher():
    """Test all NBA stats fetching functionality."""
    print("🔍 Testing NBA Stats Fetcher (Modularized)...")
    
    # Test advanced stats
    test_advanced_stats()
    
    print("\n" + "="*50)
    
    # Test Four Factors
    test_four_factors()
    
    print("\n✅ All stats fetcher tests complete!")


if __name__ == "__main__":
    test_stats_fetcher()
