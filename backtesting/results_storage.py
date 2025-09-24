"""
backtesting/results_storage.py
==============================

User-friendly results storage and retrieval for backtesting.
Provides easy access to backtest summaries and comparison data.

Functions
---------
save_backtest_summary(results_df, metrics, config, run_dir) -> str
    Save a condensed summary of backtest results.

load_latest_results() -> Dict
    Load the most recent backtest summary.

load_all_results() -> List[Dict]
    Load summaries of all backtest runs.

get_comparison_benchmark() -> Dict
    Get a benchmark for comparing live model performance.

save_model_comparison(live_metrics, backtest_id) -> None
    Save comparison between live model and backtest results.

This module provides simple storage for backtest results that can be easily
accessed by both CLI and web interfaces.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


def save_backtest_summary(
    results_df: pd.DataFrame,
    metrics: Dict,
    config: Dict,
    run_dir: Path
) -> str:
    """
    Save a condensed, user-friendly summary of backtest results.

    Args:
        results_df: Per-game results DataFrame
        metrics: Calculated metrics dictionary
        config: Backtest configuration used
        run_dir: Directory where full results are stored

    Returns:
        Path to the summary file
    """
    # Create summary data
    summary = {
        'run_id': run_dir.name,
        'timestamp': datetime.now().isoformat(),
        'config': {
            'seasons': config.get('seasons_analyzed', []),
            'market': config['entry']['market'],
            'min_edge_pts': config['entry']['min_edge_pts'],
            'simulations': config['engine']['sims'],
            'total_games': len(results_df) if not results_df.empty else 0,
            'bets_placed': metrics.get('total_bets', 0)
        },
        'performance': {
            'roi_pct': round(metrics.get('roi_pct', 0), 2),
            'hit_rate_pct': round(metrics.get('hit_rate', 0) * 100, 1),
            'total_pnl': round(metrics.get('total_pnl', 2), 2),
            'max_drawdown_pct': round(metrics.get('max_drawdown', 0) * -100, 1),  # Convert to positive percentage
            'sharpe_ratio': round(metrics.get('sharpe_ratio', 0), 2),
            'brier_score': round(metrics.get('brier_score', 0), 3),
            'expected_value_per_unit': round(metrics.get('expected_value_per_unit', 0), 3)
        },
        'season_breakdown': _create_season_breakdown(results_df),
        'edge_analysis': _create_edge_analysis(metrics),
        'run_directory': str(run_dir),
        'status': 'completed'
    }

    # Save summary
    summary_file = run_dir / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Also save as "latest" for easy access
    latest_file = Path('results') / 'latest_summary.json'
    latest_file.parent.mkdir(exist_ok=True)
    with open(latest_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Save to historical results
    history_file = Path('results') / 'backtest_history.json'
    history = load_all_results()
    history.append(summary)

    # Keep only last 50 runs to prevent file from growing too large
    if len(history) > 50:
        history = history[-50:]

    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2, default=str)

    return str(summary_file)


def _create_season_breakdown(results_df: pd.DataFrame) -> List[Dict]:
    """Create per-season performance breakdown."""
    if results_df.empty:
        return []

    season_stats = []
    for season in results_df['season_end_year'].unique():
        season_data = results_df[results_df['season_end_year'] == season]
        total_bets = len(season_data)

        if total_bets > 0:
            roi = (season_data['pnl'].sum() / season_data['stake'].sum()) * 100
            hit_rate = season_data['covered'].mean() * 100
        else:
            roi = 0
            hit_rate = 0

        season_stats.append({
            'season': int(season),
            'bets': total_bets,
            'roi_pct': round(roi, 1),
            'hit_rate_pct': round(hit_rate, 1)
        })

    return sorted(season_stats, key=lambda x: x['season'], reverse=True)


def _create_edge_analysis(metrics: Dict) -> Dict:
    """Extract edge bucket analysis for summary."""
    buckets = metrics.get('edge_buckets', [])

    if not buckets:
        return {'buckets': []}

    # Find best and worst performing edge buckets
    sorted_buckets = sorted(buckets, key=lambda x: x['roi_pct'], reverse=True)

    return {
        'buckets': sorted_buckets[:5],  # Top 5 buckets
        'best_edge_range': sorted_buckets[0]['edge_range'] if sorted_buckets else None,
        'best_roi_pct': sorted_buckets[0]['roi_pct'] if sorted_buckets else 0,
        'monotonic_improvement': metrics.get('monotonic_improvement', False)
    }


def load_latest_results() -> Optional[Dict]:
    """
    Load the most recent backtest summary.

    Returns:
        Latest backtest summary, or None if no results exist
    """
    latest_file = Path('results') / 'latest_summary.json'

    if latest_file.exists():
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    return None


def load_all_results() -> List[Dict]:
    """
    Load summaries of all backtest runs.

    Returns:
        List of all backtest summaries (most recent first)
    """
    history_file = Path('results') / 'backtest_history.json'

    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
                # Sort by timestamp, most recent first
                return sorted(history, key=lambda x: x['timestamp'], reverse=True)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    return []


def get_comparison_benchmark() -> Optional[Dict]:
    """
    Get a benchmark for comparing live model performance.

    Returns the most recent successful backtest as a comparison baseline.
    """
    latest = load_latest_results()

    if latest and latest.get('status') == 'completed':
        return {
            'backtest_id': latest['run_id'],
            'roi_benchmark': latest['performance']['roi_pct'],
            'hit_rate_benchmark': latest['performance']['hit_rate_pct'],
            'ev_per_unit_benchmark': latest['performance']['expected_value_per_unit'],
            'config': latest['config']
        }

    return None


def save_model_comparison(live_metrics: Dict, backtest_id: Optional[str] = None) -> None:
    """
    Save comparison between live model performance and backtest results.

    Args:
        live_metrics: Current live model metrics
        backtest_id: ID of backtest to compare against (uses latest if None)
    """
    if backtest_id is None:
        benchmark = get_comparison_benchmark()
        if benchmark:
            backtest_id = benchmark['backtest_id']
        else:
            return

    comparison = {
        'timestamp': datetime.now().isoformat(),
        'backtest_id': backtest_id,
        'live_performance': live_metrics,
        'benchmark': get_comparison_benchmark()
    }

    # Save to comparisons directory
    comparison_dir = Path('results') / 'comparisons'
    comparison_dir.mkdir(exist_ok=True, parents=True)

    comparison_file = comparison_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2, default=str)


def get_results_summary_text() -> str:
    """
    Get a human-readable summary of the latest backtest results.

    Returns:
        Formatted text summary suitable for display
    """
    latest = load_latest_results()

    if not latest:
        return "No backtest results available. Run a backtest first."

    perf = latest['performance']
    config = latest['config']

    summary = f"""
🎯 LATEST BACKTEST RESULTS
══════════════════════════════════════════════

📊 Configuration:
   • Seasons: {', '.join(map(str, config['seasons']))}
   • Market: {config['market']}
   • Min Edge: {config['min_edge_pts']} pts
   • Simulations: {config['simulations']:,}
   • Games Processed: {config['total_games']:,}
   • Bets Placed: {config['bets_placed']:,}

💰 Performance:
   • ROI: {perf['roi_pct']:+.1f}%
   • Hit Rate: {perf['hit_rate_pct']:.1f}%
   • Total P&L: ${perf['total_pnl']:,.0f}
   • Max Drawdown: {perf['max_drawdown_pct']:.1f}%
   • Sharpe Ratio: {perf['sharpe_ratio']:.2f}
   • Brier Score: {perf['brier_score']:.3f}
   • EV per Unit: {perf['expected_value_per_unit']:+.3f}

📈 Run ID: {latest['run_id']}
🕒 Completed: {latest['timestamp'][:19].replace('T', ' ')}

Compare this against your live model's current performance!
"""

    return summary.strip()
