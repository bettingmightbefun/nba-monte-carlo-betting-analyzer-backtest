"""
backtesting/cli_view.py
========================

Command-line utility to quickly view and compare backtest results.
Provides easy access to backtest summaries and live model comparisons.

Usage:
    python -m backtesting.cli_view
    python -m backtesting.cli_view --compare 8.5 53.2 0.045
    python -m backtesting.cli_view --latest
"""

from __future__ import annotations

import argparse
from typing import Optional

from backtesting.comparison import print_comparison_report
from backtesting.results_storage import (
    get_results_summary_text,
    load_latest_results,
    load_all_results
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NBA Backtesting Results Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backtesting.cli_view                    # Show latest results
  python -m backtesting.cli_view --latest          # Show latest results
  python -m backtesting.cli_view --all             # Show all historical results
  python -m backtesting.cli_view --compare 8.5 53.2 0.045  # Compare with live metrics
        """
    )

    parser.add_argument(
        '--latest', '-l',
        action='store_true',
        help='Show latest backtest results'
    )

    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Show all historical backtest results'
    )

    parser.add_argument(
        '--compare', '-c',
        nargs=3,
        metavar=('ROI', 'HIT_RATE', 'EV'),
        type=float,
        help='Compare live metrics (ROI%%, Hit Rate%%, EV per unit) with backtest'
    )

    parser.add_argument(
        '--run-id',
        help='Specific backtest run ID to compare against'
    )

    args = parser.parse_args()

    # Default action: show latest results
    if not any([args.latest, args.all, args.compare]):
        args.latest = True

    if args.all:
        show_all_results()
    elif args.compare:
        show_comparison(args.compare[0], args.compare[1], args.compare[2], args.run_id)
    else:
        show_latest_results()


def show_latest_results():
    """Show the latest backtest results."""
    print("🎯 NBA BACKTESTING RESULTS VIEWER")
    print("=" * 50)

    summary_text = get_results_summary_text()
    print(summary_text)

    # Show additional quick stats
    latest = load_latest_results()
    if latest:
        print("\n📊 QUICK STATS:")
        print("-" * 30)
        perf = latest['performance']
        config = latest['config']

        print(f"Run ID: {latest['run_id']}")
        print(f"Generated: {latest['timestamp'][:19].replace('T', ' ')}")
        print(f"Seasons: {', '.join(map(str, config['seasons']))}")
        print(f"Total Bets: {config['bets_placed']}")
        print(f"Bet Frequency: {(config['bets_placed'] / config['total_games'] * 100):.1f}%")
        print()
        print("Compare with your live model using:")
        print(f"python -m backtesting.cli_view --compare [ROI] [Hit Rate] [EV per unit]")


def show_all_results():
    """Show all historical backtest results."""
    print("📚 HISTORICAL BACKTEST RESULTS")
    print("=" * 50)

    all_results = load_all_results()

    if not all_results:
        print("No backtest results found. Run a backtest first!")
        return

    print(f"Found {len(all_results)} backtest runs:\n")

    for i, result in enumerate(all_results, 1):
        perf = result['performance']
        config = result['config']
        timestamp = result['timestamp'][:10]  # Just date

        status_indicator = "✅" if result.get('status') == 'completed' else "❌"

        print(f"{i}. {status_indicator} {result['run_id']} ({timestamp})")
        print(f"   Seasons: {', '.join(map(str, config['seasons']))}")
        print(f"   ROI: {perf['roi_pct']:+.1f}% | Hit Rate: {perf['hit_rate_pct']:.1f}% | Bets: {config['bets_placed']}")
        print()


def show_comparison(live_roi: float, live_hit_rate: float, live_ev: float, run_id: Optional[str]):
    """Show comparison between live metrics and backtest."""
    print("🔍 LIVE MODEL vs BACKTEST COMPARISON")
    print("=" * 50)

    live_metrics = {
        'roi_pct': live_roi,
        'hit_rate_pct': live_hit_rate,
        'expected_value_per_unit': live_ev
    }

    try:
        report = print_comparison_report(live_metrics, run_id)
        print(report)
    except Exception as e:
        print(f"❌ Error generating comparison: {e}")
        print("\nMake sure you've run at least one backtest first:")
        print("python -m backtesting.runner --seasons 2023 --dataset nba_2008-2025.xlsx")


if __name__ == "__main__":
    main()
