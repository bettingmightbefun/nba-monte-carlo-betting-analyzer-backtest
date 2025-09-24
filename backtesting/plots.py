"""
backtesting/plots.py
====================

Matplotlib-based plotting functions for NBA backtesting visualization.
Creates equity curves, drawdown charts, calibration plots, and edge bucket analysis.

Functions
---------
generate_backtest_plots(results_df, metrics, run_dir, config) -> List[str]
    Generate all backtest plots and save to disk.

plot_equity_curve(results_df, run_dir) -> str
    Plot cumulative P&L over time.

plot_drawdown(results_df, run_dir) -> str
    Plot drawdown chart with max drawdown highlighted.

plot_calibration_curve(metrics, run_dir) -> str
    Plot predicted vs actual probabilities.

plot_roi_by_edge_bucket(metrics, run_dir) -> str
    Plot ROI by edge magnitude buckets.

This module provides comprehensive visualization of backtesting results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

import pandas as pd

# Set up plotting style (only if matplotlib available)
if MATPLOTLIB_AVAILABLE:
    plt.style.use('default')
    sns.set_palette("husl")


def generate_backtest_plots(
    results_df: pd.DataFrame,
    metrics: Dict,
    run_dir: Path,
    config: Dict
) -> List[str]:
    """
    Generate all backtest plots and save to disk.

    Args:
        results_df: Per-game results DataFrame
        metrics: Calculated metrics dictionary
        run_dir: Directory to save plots
        config: Backtest configuration

    Returns:
        List of generated plot file paths
    """
    plot_files = []

    if not MATPLOTLIB_AVAILABLE:
        print("Warning: matplotlib not available, skipping plot generation")
        return plot_files

    if results_df.empty:
        return plot_files

    try:
        # Equity curve
        equity_file = plot_equity_curve(results_df, run_dir)
        plot_files.append(equity_file)

        # Drawdown chart
        drawdown_file = plot_drawdown(results_df, run_dir)
        plot_files.append(drawdown_file)

        # Calibration curve (if probabilistic data available)
        if 'calibration_curve' in metrics:
            calibration_file = plot_calibration_curve(metrics, run_dir)
            plot_files.append(calibration_file)

        # ROI by edge bucket
        if 'edge_buckets' in metrics:
            edge_file = plot_roi_by_edge_bucket(metrics, run_dir)
            plot_files.append(edge_file)

    except Exception as e:
        print(f"Error generating plots: {e}")
        # Continue without plots if there's an error

    return plot_files


def plot_equity_curve(results_df: pd.DataFrame, run_dir: Path) -> str:
    """
    Plot cumulative P&L (equity curve) over time.

    Args:
        results_df: Per-game results DataFrame
        run_dir: Directory to save plot

    Returns:
        Path to saved plot file
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Calculate cumulative P&L
    cumulative_pnl = results_df['pnl'].cumsum()

    # Plot equity curve
    ax.plot(results_df['date'], cumulative_pnl, linewidth=2, label='Cumulative P&L')

    # Add zero line
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)

    # Format plot
    ax.set_title('Backtest Equity Curve', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative P&L ($)')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Rotate x-axis labels for readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    # Save plot
    plot_path = run_dir / 'equity_curve.png'
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(plot_path)


def plot_drawdown(results_df: pd.DataFrame, run_dir: Path) -> str:
    """
    Plot drawdown chart highlighting maximum drawdown.

    Args:
        results_df: Per-game results DataFrame
        run_dir: Directory to save plot

    Returns:
        Path to saved plot file
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Calculate cumulative P&L and drawdown
    cumulative_pnl = results_df['pnl'].cumsum()
    running_max = cumulative_pnl.expanding().max()
    drawdown = cumulative_pnl - running_max

    # Plot drawdown
    ax.fill_between(results_df['date'], 0, drawdown, color='red', alpha=0.3, label='Drawdown')
    ax.plot(results_df['date'], drawdown, color='red', linewidth=1)

    # Highlight maximum drawdown
    max_dd = drawdown.min()
    max_dd_date = results_df.loc[drawdown.idxmin(), 'date']

    ax.axhline(y=max_dd, color='darkred', linestyle='--', alpha=0.7,
               label=f'Max DD: ${max_dd:.2f}')

    # Format plot
    ax.set_title('Drawdown Chart', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown ($)')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    # Save plot
    plot_path = run_dir / 'drawdown.png'
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(plot_path)


def plot_calibration_curve(metrics: Dict, run_dir: Path) -> str:
    """
    Plot calibration curve showing predicted vs actual probabilities.

    Args:
        metrics: Metrics dictionary with calibration data
        run_dir: Directory to save plot

    Returns:
        Path to saved plot file
    """
    calibration_data = metrics.get('calibration_curve', [])
    if not calibration_data:
        return ""

    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract data for plotting
    predicted_probs = [point['avg_predicted_prob'] for point in calibration_data]
    actual_rates = [point['actual_cover_rate'] for point in calibration_data]
    counts = [point['count'] for point in calibration_data]

    # Scatter plot with point sizes based on count
    scatter = ax.scatter(predicted_probs, actual_rates, s=[c/2 for c in counts],
                        alpha=0.6, c=counts, cmap='viridis')

    # Perfect calibration line
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.7, label='Perfect Calibration')

    # Add colorbar for sample sizes
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Sample Size')

    # Format plot
    ax.set_title('Calibration Curve', fontsize=14, fontweight='bold')
    ax.set_xlabel('Predicted Probability')
    ax.set_ylabel('Actual Cover Rate')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Add metrics text
    brier = metrics.get('brier_score', 0)
    log_loss = metrics.get('log_loss', 0)
    ax.text(0.05, 0.95, '.3f'
            '.3f',
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Save plot
    plot_path = run_dir / 'calibration_curve.png'
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(plot_path)


def plot_roi_by_edge_bucket(metrics: Dict, run_dir: Path) -> str:
    """
    Plot ROI by edge magnitude buckets.

    Args:
        metrics: Metrics dictionary with edge bucket data
        run_dir: Directory to save plot

    Returns:
        Path to saved plot file
    """
    edge_buckets = metrics.get('edge_buckets', [])
    if not edge_buckets:
        return ""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Extract data
    edge_ranges = [bucket['edge_range'] for bucket in edge_buckets]
    roi_values = [bucket['roi_pct'] for bucket in edge_buckets]
    hit_rates = [bucket['hit_rate'] * 100 for bucket in edge_buckets]  # Convert to percentage
    counts = [bucket['count'] for bucket in edge_buckets]

    # ROI by edge bucket
    bars1 = ax1.bar(edge_ranges, roi_values, color='skyblue', alpha=0.7)
    ax1.set_title('ROI by Edge Magnitude', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Edge Range (points)')
    ax1.set_ylabel('ROI (%)')
    ax1.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar, roi in zip(bars1, roi_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                '.1f', ha='center', va='bottom', fontsize=9)

    # Hit rate by edge bucket
    bars2 = ax2.bar(edge_ranges, hit_rates, color='lightcoral', alpha=0.7)
    ax2.set_title('Hit Rate by Edge Magnitude', fontsize=12)
    ax2.set_xlabel('Edge Range (points)')
    ax2.set_ylabel('Hit Rate (%)')
    ax2.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar, hit_rate in zip(bars2, hit_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                '.1f', ha='center', va='bottom', fontsize=9)

    # Add sample size annotation
    total_bets = sum(counts)
    ax1.text(0.02, 0.98, f'Total Bets: {total_bets}',
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Check for monotonic improvement
    monotonic = metrics.get('monotonic_improvement', False)
    color = 'green' if monotonic else 'red'
    status = '✓ Monotonic' if monotonic else '✗ Non-monotonic'
    ax1.text(0.98, 0.98, status, transform=ax1.transAxes,
             verticalalignment='top', horizontalalignment='right',
             color=color, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plot_path = run_dir / 'roi_by_edge_bucket.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(plot_path)
