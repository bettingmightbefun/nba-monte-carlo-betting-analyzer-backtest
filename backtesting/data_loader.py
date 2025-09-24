"""
backtesting/data_loader.py
==========================

Data loading and normalization for NBA backtesting slim datasets.
Supports CSV, CSV.GZ, and XLSX formats with automatic column normalization.

Functions
---------
load_slim(path: str) -> pd.DataFrame
    Load and normalize slim odds/results dataset.

normalize_columns(df: pd.DataFrame) -> pd.DataFrame
    Normalize column names to lowercase snake_case.

derive_game_features(df: pd.DataFrame) -> pd.DataFrame
    Add computed columns: game_key, season_end_year, spread_home_close_signed, final_margin_home.

This module handles the initial data ingestion and preprocessing for backtesting.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

import pandas as pd


def load_slim(path: str) -> pd.DataFrame:
    """
    Load slim odds/results dataset from CSV, CSV.GZ, or XLSX file.

    Automatically detects file format and normalizes column names to snake_case.
    Adds derived features for backtesting.

    Args:
        path: Path to data file (.csv, .csv.gz, .xlsx)

    Returns:
        DataFrame with normalized columns and derived features

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format not supported or required columns missing
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Slim dataset not found: {path}")

    file_path = Path(path)
    file_ext = file_path.suffix.lower()

    # Load based on file extension
    if file_ext == '.xlsx':
        df = pd.read_excel(path)
    elif file_ext == '.csv':
        # Handle both regular CSV and gzipped CSV
        if str(path).endswith('.gz'):
            df = pd.read_csv(path, compression='gzip')
        else:
            df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Use .csv, .csv.gz, or .xlsx")

    # Normalize column names and validate
    df = normalize_columns(df)
    df = validate_required_columns(df)

    # Add derived features
    df = derive_game_features(df)

    # Sort chronologically for backtesting
    df = df.sort_values(['date', 'game_key']).reset_index(drop=True)

    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to lowercase snake_case.

    Handles common variations in column naming conventions.

    Args:
        df: Raw DataFrame with potentially inconsistent column names

    Returns:
        DataFrame with normalized column names
    """
    # Create mapping for known column variations
    column_mapping = {
        # Date columns
        'Date': 'date',
        'DATE': 'date',

        # Team columns
        'Away': 'away',
        'AWAY': 'away',
        'Home': 'home',
        'HOME': 'home',

        # Score columns
        'Score_Away': 'score_away',
        'SCORE_AWAY': 'score_away',
        'Score_Home': 'score_home',
        'SCORE_HOME': 'score_home',
        'Away_Score': 'score_away',
        'Home_Score': 'score_home',

        # Spread/favored columns
        'Whos_Favored': 'whos_favored',
        'WHOS_FAVORED': 'whos_favored',
        'Favored': 'whos_favored',
        'FAVORED': 'whos_favored',

        # Spread value columns
        'Spread': 'spread',
        'SPREAD': 'spread',

        # Moneyline columns (optional)
        'Moneyline_Home': 'moneyline_home',
        'MONEYLINE_HOME': 'moneyline_home',
        'Moneyline_Away': 'moneyline_away',
        'MONEYLINE_AWAY': 'moneyline_away',
        'ML_Home': 'moneyline_home',
        'ML_Away': 'moneyline_away',

        # Total columns (optional)
        'Total': 'total',
        'TOTAL': 'total',
        'Over_Under': 'total',
        'OU': 'total',

        # Other columns
        'Season': 'season',
        'SEASON': 'season',
        'Regular': 'regular',
        'REGULAR': 'regular',
        'Playoffs': 'playoffs',
        'PLAYOFFS': 'playoffs',
        'OT_Away': 'ot_away',
        'OT_AWAY': 'ot_away',
    }

    # Apply mapping and convert to snake_case
    df = df.rename(columns=column_mapping)

    # Convert any remaining columns to snake_case
    df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]

    return df


def validate_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that required columns are present in the dataset.

    Args:
        df: DataFrame with normalized columns

    Returns:
        DataFrame (unchanged if valid)

    Raises:
        ValueError: If required columns are missing
    """
    required_columns = [
        'date', 'away', 'home', 'score_away', 'score_home',
        'whos_favored', 'spread'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        available = list(df.columns)
        raise ValueError(
            f"Missing required columns: {missing_columns}. "
            f"Available columns: {available}"
        )

    return df


def derive_game_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add computed columns needed for backtesting.

    Adds:
    - game_key: Unique identifier (YYYYMMDD_home_away)
    - season_end_year: NBA season end year (season column + 1)
    - spread_home_close_signed: Signed spread from home perspective
    - final_margin_home: Actual margin (home_score - away_score)

    Args:
        df: DataFrame with required columns

    Returns:
        DataFrame with additional derived columns
    """
    # Create game_key: YYYYMMDD_home_away (e.g., 20231030_lal_gsw)
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['date_str'] = df['date'].dt.strftime('%Y%m%d')
    df['game_key'] = df['date_str'] + '_' + df['home'] + '_' + df['away']
    df = df.drop('date_str', axis=1)

    # Derive season_end_year (NBA seasons are Oct-Jun, so season 2023 = 2023-24 season)
    df['season_end_year'] = df['season'] + 1

    # Calculate signed spread from home perspective
    # If home is favored, spread is positive (home gives points)
    # If away is favored, spread is negative (home receives points)
    df['spread_home_close_signed'] = df.apply(
        lambda row: row['spread'] if row['whos_favored'] == 'home' else -row['spread'],
        axis=1
    )

    # Calculate final margin from home perspective
    df['final_margin_home'] = df['score_home'] - df['score_away']

    # Add rest flags (will be computed later with as-of data)
    df['b2b'] = False  # Back-to-back
    df['three_in_four'] = False  # Three games in four days
    df['four_in_six'] = False  # Four games in six days

    return df
