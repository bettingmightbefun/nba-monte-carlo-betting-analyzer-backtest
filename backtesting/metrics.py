"""
backtesting/metrics.py
======================

Comprehensive metrics calculation for NBA backtesting results.
Includes ROI, hit rate, drawdown, calibration, and edge-bucket analysis.

Functions
---------
calculate_backtest_metrics(results_df, config) -> Dict
    Calculate all backtest metrics from results DataFrame.

calculate_roi_metrics(results_df) -> Dict
    Calculate ROI, hit rate, and basic performance metrics.

calculate_risk_metrics(results_df) -> Dict
    Calculate drawdown, Sharpe ratio, and risk-adjusted metrics.

calculate_calibration_metrics(results_df) -> Dict
    Calculate calibration curve data and Brier/log-loss scores.

calculate_edge_bucket_analysis(results_df) -> Dict
    Analyze ROI by edge magnitude buckets.

This module provides comprehensive statistical analysis of backtesting performance.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def calculate_backtest_metrics(results_df: pd.DataFrame, config: Dict) -> Dict:
    """
    Calculate comprehensive backtest metrics.

    Args:
        results_df: DataFrame with per-game results
        config: Backtest configuration

    Returns:
        Dictionary with all calculated metrics
    """
    if results_df.empty:
        return {}

    metrics = {}

    # Basic ROI and performance metrics
    metrics.update(calculate_roi_metrics(results_df))

    # Risk and drawdown metrics
    metrics.update(calculate_risk_metrics(results_df))

    # Calibration and probabilistic metrics
    metrics.update(calculate_calibration_metrics(results_df))

    # Edge bucket analysis
    metrics.update(calculate_edge_bucket_analysis(results_df))

    # Stress testing (if enabled)
    if config.get('outputs', {}).get('include_stress_tests', False):
        metrics.update(calculate_stress_test_metrics(results_df, config))

    return metrics


def calculate_roi_metrics(results_df: pd.DataFrame) -> Dict:
    """
    Calculate basic ROI and performance metrics.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        Dictionary with ROI metrics
    """
    total_bets = len(results_df)
    total_stake = results_df['stake'].sum()
    total_pnl = results_df['pnl'].sum()
    hit_rate = results_df['covered'].mean()

    roi_pct = (total_pnl / total_stake * 100) if total_stake > 0 else 0

    # Average metrics
    avg_stake = results_df['stake'].mean()
    avg_win = results_df[results_df['covered']]['pnl'].mean()
    avg_loss = results_df[~results_df['covered']]['pnl'].mean()

    return {
        'total_bets': total_bets,
        'total_stake': total_stake,
        'total_pnl': total_pnl,
        'roi_pct': roi_pct,
        'hit_rate': hit_rate,
        'avg_stake': avg_stake,
        'avg_win_amount': avg_win if not pd.isna(avg_win) else 0,
        'avg_loss_amount': avg_loss if not pd.isna(avg_loss) else 0,
        'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 and not pd.isna(avg_win) and not pd.isna(avg_loss) else float('inf')
    }


def calculate_risk_metrics(results_df: pd.DataFrame) -> Dict:
    """
    Calculate risk-adjusted metrics including drawdown and Sharpe ratio.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        Dictionary with risk metrics
    """
    if results_df.empty:
        return {}

    # Calculate cumulative P&L
    cumulative_pnl = results_df['pnl'].cumsum()

    # Maximum drawdown
    running_max = cumulative_pnl.expanding().max()
    drawdown = cumulative_pnl - running_max
    max_drawdown = drawdown.min()  # Most negative value

    # Sharpe ratio (assuming daily returns, risk-free rate = 0)
    if len(results_df) > 1:
        returns = results_df['pnl'] / results_df['stake']
        sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
    else:
        sharpe_ratio = 0

    # Win streak analysis
    win_streaks = _calculate_streaks(results_df['covered'])
    loss_streaks = _calculate_streaks(~results_df['covered'])
    max_win_streak = max(win_streaks) if win_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0

    return {
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'calmar_ratio': abs(results_df['pnl'].sum() / max_drawdown) if max_drawdown < 0 else float('inf')
    }


def calculate_calibration_metrics(results_df: pd.DataFrame) -> Dict:
    """
    Calculate calibration curve data and probabilistic metrics.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        Dictionary with calibration metrics
    """
    if results_df.empty or 'cover_prob' not in results_df.columns:
        return {}

    # Brier score (mean squared difference between predicted prob and outcome)
    brier_score = ((results_df['cover_prob'] - results_df['covered']) ** 2).mean()

    # Log loss (cross-entropy)
    eps = 1e-15  # Avoid log(0)
    cover_prob_clipped = np.clip(results_df['cover_prob'], eps, 1 - eps)
    log_loss = -(results_df['covered'] * np.log(cover_prob_clipped) +
                 (1 - results_df['covered']) * np.log(1 - cover_prob_clipped)).mean()

    # Calibration curve data (predicted prob buckets)
    calibration_data = _calculate_calibration_curve(results_df)

    return {
        'brier_score': brier_score,
        'log_loss': log_loss,
        'calibration_curve': calibration_data,
        'expected_value_per_unit': results_df['ev_units'].mean()
    }


def calculate_edge_bucket_analysis(results_df: pd.DataFrame) -> Dict:
    """
    Analyze ROI by edge magnitude buckets.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        Dictionary with edge bucket analysis
    """
    # Check for edge_percentage column (new format) or fallback to edge_pts
    edge_col = 'edge_percentage' if 'edge_percentage' in results_df.columns else 'edge_pts'

    if results_df.empty or edge_col not in results_df.columns:
        return {}

    # Filter to only positive edges for meaningful analysis
    positive_edges = results_df[results_df[edge_col] > 0].copy()

    if positive_edges.empty:
        return {'edge_buckets': [], 'message': 'No positive edges found for bucket analysis'}

    # Create edge buckets (percentage increments for edge_percentage, point increments for edge_pts)
    max_edge = positive_edges[edge_col].max()
    if edge_col == 'edge_percentage':
        # For percentages, use 1% increments
        bucket_size = 1.0
        edge_bins = np.arange(0, max_edge + bucket_size, bucket_size)
    else:
        # For points, use 0.5 point increments
        bucket_size = 0.5
        edge_bins = np.arange(0, max_edge + bucket_size, bucket_size)

    # Ensure we have at least 2 bins
    if len(edge_bins) < 2:
        edge_bins = np.array([0, max(1.0, max_edge)])

    positive_edges['edge_bucket'] = pd.cut(positive_edges[edge_col], bins=edge_bins, right=False)

    bucket_analysis = []

    for bucket in positive_edges['edge_bucket'].cat.categories:
        bucket_data = positive_edges[positive_edges['edge_bucket'] == bucket]

        if len(bucket_data) == 0:
            continue

        roi = (bucket_data['pnl'].sum() / bucket_data['stake'].sum() * 100) if bucket_data['stake'].sum() > 0 else 0
        hit_rate = bucket_data['covered'].mean()
        count = len(bucket_data)

        bucket_analysis.append({
            'edge_range': f"{bucket.left:.1f}-{bucket.right:.1f}",
            'count': count,
            'roi_pct': roi,
            'hit_rate': hit_rate,
            'avg_pnl': bucket_data['pnl'].mean()
        })

    return {
        'edge_buckets': bucket_analysis,
        'monotonic_improvement': _check_monotonic_improvement(bucket_analysis)
    }


def calculate_stress_test_metrics(results_df: pd.DataFrame, config: Dict) -> Dict:
    """
    Calculate stress test metrics with re-pricing scenarios.

    Args:
        results_df: Per-game results DataFrame
        config: Backtest configuration

    Returns:
        Dictionary with stress test results
    """
    # Check if required columns exist for stress testing
    required_cols = ['close_line', 'final_margin_home', 'stake']
    if not all(col in results_df.columns for col in required_cols):
        return {'stress_tests': {'error': f'Missing required columns: {required_cols}'}}

    stress_results = {}

    if config['entry']['market'] == 'spread':
        # Test re-pricing at close ±0.5 spreads using close_line from results
        for offset in [-0.5, 0.5]:
            stress_results[f'spread_{offset:+.1f}'] = _calculate_stress_roi(
                results_df, 'close_line', offset
            )

    # Test robustness to market movement
    stress_results['market_stress'] = _calculate_market_stress(results_df)

    return {'stress_tests': stress_results}


def _calculate_calibration_curve(results_df: pd.DataFrame) -> List[Dict]:
    """
    Calculate calibration curve data points.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        List of calibration data points
    """
    # Create probability bins
    prob_bins = np.arange(0, 1.1, 0.1)
    calibration_points = []

    for i in range(len(prob_bins) - 1):
        bin_start = prob_bins[i]
        bin_end = prob_bins[i + 1]

        # Filter to predictions in this bin
        bin_data = results_df[
            (results_df['cover_prob'] >= bin_start) &
            (results_df['cover_prob'] < bin_end)
        ]

        if len(bin_data) == 0:
            continue

        avg_predicted = bin_data['cover_prob'].mean()
        actual_rate = bin_data['covered'].mean()
        count = len(bin_data)

        calibration_points.append({
            'prob_bin_start': bin_start,
            'prob_bin_end': bin_end,
            'avg_predicted_prob': avg_predicted,
            'actual_cover_rate': actual_rate,
            'count': count,
            'calibration_error': abs(avg_predicted - actual_rate)
        })

    return calibration_points


def _calculate_streaks(bool_series: pd.Series) -> List[int]:
    """
    Calculate streak lengths for a boolean series.

    Args:
        bool_series: Series of boolean values

    Returns:
        List of streak lengths
    """
    streaks = []
    current_streak = 0

    for value in bool_series:
        if value:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 0

    if current_streak > 0:
        streaks.append(current_streak)

    return streaks


def _check_monotonic_improvement(bucket_analysis: List[Dict]) -> bool:
    """
    Check if ROI improves monotonically with edge magnitude.

    Args:
        bucket_analysis: List of edge bucket results

    Returns:
        True if ROI increases with edge (good calibration)
    """
    if len(bucket_analysis) < 2:
        return False

    # Sort by edge range and check if ROI is non-decreasing
    sorted_buckets = sorted(bucket_analysis, key=lambda x: float(x['edge_range'].split('-')[0]))

    for i in range(1, len(sorted_buckets)):
        if sorted_buckets[i]['roi_pct'] < sorted_buckets[i-1]['roi_pct']:
            return False

    return True


def _calculate_stress_roi(results_df: pd.DataFrame, line_column: str, offset: float) -> Dict:
    """
    Calculate ROI under stress test with line offset.

    Args:
        results_df: Per-game results DataFrame
        line_column: Column name for the line
        offset: Amount to offset the line

    Returns:
        Dictionary with stress test ROI metrics
    """
    stressed_df = results_df.copy()
    stressed_df[line_column] = stressed_df[line_column] + offset

    # Recalculate outcomes with stressed lines
    stressed_df['stressed_covered'] = stressed_df.apply(
        lambda row: _recalculate_cover(row, line_column), axis=1
    )

    stressed_df['stressed_pnl'] = stressed_df.apply(
        lambda row: row['stake'] * 0.909 if row['stressed_covered'] else -row['stake'],
        axis=1
    )

    total_stake = stressed_df['stake'].sum()
    total_pnl = stressed_df['stressed_pnl'].sum()

    return {
        'offset': offset,
        'total_pnl': total_pnl,
        'roi_pct': (total_pnl / total_stake * 100) if total_stake > 0 else 0,
        'hit_rate': stressed_df['stressed_covered'].mean()
    }


def _recalculate_cover(row: pd.Series, line_column: str) -> bool:
    """
    Recalculate cover outcome with stressed line.

    Args:
        row: Single game result row
        line_column: Column name for the line

    Returns:
        True if covered under stressed conditions
    """
    actual_margin = row['final_margin_home']  # Assuming home perspective

    if row['side'] == 'home':
        return actual_margin > row[line_column]
    else:  # away
        return actual_margin < row[line_column]


def _calculate_market_stress(results_df: pd.DataFrame) -> Dict:
    """
    Calculate robustness to general market movement.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        Dictionary with market stress metrics
    """
    # Test sensitivity to 0.5 point line movement in both directions
    stress_up = _calculate_stress_roi(results_df, 'close_line', 0.5)
    stress_down = _calculate_stress_roi(results_df, 'close_line', -0.5)

    return {
        'line_up_0_5': stress_up,
        'line_down_0_5': stress_down,
        'avg_stress_impact': (stress_up['roi_pct'] + stress_down['roi_pct']) / 2
    }
