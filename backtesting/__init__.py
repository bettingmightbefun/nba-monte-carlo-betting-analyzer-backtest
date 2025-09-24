"""
NBA Backtesting System
======================

A comprehensive, leakage-free backtesting framework for NBA betting models.
Provides tools for evaluating betting strategies across multiple seasons with
proper as-of-date data fetching and statistical analysis.

Modules
-------
data_loader: Data loading and normalization for slim datasets
runner: Main backtesting execution engine
metrics: Comprehensive performance metrics calculation
plots: Visualization and plotting utilities
results_storage: User-friendly results storage and retrieval
comparison: Live model vs backtest benchmark comparisons
cli_view: Command-line results viewer

Usage
-----
# Run a backtest
python -m backtesting.runner --seasons 2023,2024 --dataset nba_2008-2025.xlsx

# View results
python -m backtesting.cli_view

# Compare live model with backtest
python -m backtesting.cli_view --compare 8.5 53.2 0.045

# Web interface at /backtesting

This package implements the backtesting system described in the original requirements.
"""

from __future__ import annotations

__version__ = "1.0.0"
__description__ = "NBA Backtesting System for leakage-free model evaluation"
