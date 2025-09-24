"""
backtesting/runner.py
====================

Main backtesting runner for NBA betting model evaluation.
Executes leakage-free backtests across multiple seasons with configurable parameters.

Functions
---------
main() -> None
    Main entry point for backtesting execution.

run_backtest(seasons, dataset_path, config_path, num_simulations, strict_before_tip) -> Dict
    Core backtesting logic with full result tracking.

This module orchestrates the entire backtesting workflow from data loading to results output.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from backtesting.data_loader import load_slim
from backtesting.metrics import calculate_backtest_metrics
from backtesting.results_storage import save_backtest_summary

try:
    from backtesting.plots import generate_backtest_plots
    PLOTS_AVAILABLE = True
except ImportError:
    PLOTS_AVAILABLE = False
    def generate_backtest_plots(*args, **kwargs):
        return []
from engine.betting_analyzer import compute_model_report
from nba_data.asof_fetchers import SimpleCache, get_team_stats_asof
from nba_data.team_alias import normalize_team_name
from nba_data.team_resolver import get_team_id


def load_config_file(config_path: str) -> Dict:
    """
    Load configuration file, with fallback to default config if yaml not available.
    """
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        print("Warning: PyYAML not installed, using default configuration")
        return get_default_config()
    except FileNotFoundError:
        print(f"Warning: Config file {config_path} not found, using default configuration")
        return get_default_config()


def get_default_config() -> Dict:
    """Get default backtesting configuration."""
    return {
        'entry': {
            'market': 'spread',
            'min_edge_pts': 0.1,  # Lower threshold for testing
            'max_bets_per_day': 10
        },
        'sizing': {
            'method': 'fixed_unit',
            'kelly_fraction': 0.25,
            'unit_stake': 1.0,
            'stake_cap_units': 2.0
        },
        'engine': {
            'sims': 5000,
            'cache_dir': '.cache/nba_api',
            'seed': 42
        },
        'outputs': {
            'dir': 'runs/',
            'per_game_format': 'parquet',
            'include_stress_tests': True
        }
    }


def main() -> None:
    """Main entry point for NBA backtesting."""
    parser = argparse.ArgumentParser(description="NBA Backtesting Runner")
    parser.add_argument(
        "--seasons",
        required=True,
        help="Comma-separated seasons to test (e.g., '2023,2024,2025')"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to slim dataset CSV file"
    )
    parser.add_argument(
        "--cfg",
        default="config/backtest.yaml",
        help="Path to backtest configuration YAML file (default: config/backtest.yaml)"
    )
    parser.add_argument(
        "--sims",
        type=int,
        default=None,
        help="Override number of simulations per game"
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Number of parallel workers (future enhancement)"
    )

    args = parser.parse_args()

    # Parse seasons
    seasons = [int(s.strip()) for s in args.seasons.split(",")]

    # Run the backtest
    results = run_backtest(
        seasons=seasons,
        dataset_path=args.dataset,
        config_path=args.cfg,
        num_simulations=args.sims
    )

    print("Backtesting completed successfully!")


def run_backtest(
    seasons: List[int],
    dataset_path: str,
    config_path: str,
    num_simulations: Optional[int] = None
) -> Dict:
    """
    Execute comprehensive NBA backtesting across specified seasons.

    Args:
        seasons: List of season end years to test (e.g., [2023, 2024, 2025])
        dataset_path: Path to slim odds/results dataset
        config_path: Path to YAML configuration file
        num_simulations: Override for simulations per game (uses config default if None)

    Returns:
        Dictionary with complete backtest results and metadata
    """
    start_time = time.time()

    # Load configuration
    config = load_config_file(config_path)

    # Override simulations if specified
    if num_simulations is not None:
        config['engine']['sims'] = num_simulations

    # Load and filter dataset
    print(f"[INIT] Loading dataset from {dataset_path}", flush=True)
    df = load_slim(dataset_path)
    df = df[df['season_end_year'].isin(seasons)].copy()

    if df.empty:
        raise ValueError(f"No games found for seasons {seasons}")

    print(f"[INIT] Loaded {len(df)} games across {len(seasons)} seasons", flush=True)

    # Initialize cache
    print(f"[INIT] Initializing API cache in {config['engine']['cache_dir']}", flush=True)
    cache = SimpleCache(config['engine']['cache_dir'])
    print(f"[INIT] Cache initialized, starting backtest processing...", flush=True)

    # Initialize results tracking
    per_game_results = []
    bet_counts = {season: 0 for season in seasons}
    daily_bet_counts = {}  # Track bets per date

    # Sort games chronologically for proper backtesting
    df = df.sort_values(['date', 'game_key']).reset_index(drop=True)

    # Cache max daily bet limit from config (defaults to 10 if unspecified)
    max_daily_bets = config['entry'].get('max_bets_per_day', 10)

    # Process each game
    for idx, game in df.iterrows():
        try:
            # Enforce per-day bet cap before running heavier processing
            game_date_str = game['date'].strftime('%Y-%m-%d')
            current_daily_bets = daily_bet_counts.get(game_date_str, 0)
            if current_daily_bets >= max_daily_bets:
                if current_daily_bets == max_daily_bets:
                    print(
                        f"[ENTRY] Daily bet limit reached for {game_date_str}; skipping remaining games on this date",
                        flush=True
                    )
                continue

            home_team = normalize_team_name(game['home'])
            away_team = normalize_team_name(game['away'])

            game_result = _process_single_game(
                game=game,
                config=config,
                cache=cache
            )

            if game_result:
                per_game_results.append(game_result)
                bet_counts[game['season_end_year']] += 1
                # Update daily bet count
                daily_bet_counts[game_date_str] = current_daily_bets + 1

                # Progress indicator with more detail
                if (idx + 1) % 50 == 0 or idx == 0:
                    progress_pct = ((idx + 1) / len(df)) * 100
                    print(f"[PROGRESS] {progress_pct:.1f}% - Processed {idx + 1}/{len(df)} games ({bet_counts[game['season_end_year']]} bets placed so far)", flush=True)
                    print(f"[STATUS] Currently processing: {home_team} vs {away_team} ({game['season_end_year']})", flush=True)

        except Exception as e:
            print(f"Error processing game {game['game_key']}: {e}", flush=True)
            continue

    # Generate aggregate results
    if not per_game_results:
        raise ValueError("No valid bets generated during backtesting")

    results_df = pd.DataFrame(per_game_results)

    # Calculate metrics and plots
    metrics = calculate_backtest_metrics(results_df, config)

    # Generate plots
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(config['outputs']['dir']) / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    plot_files = generate_backtest_plots(results_df, metrics, run_dir, config)

    # Save outputs
    _save_backtest_outputs(results_df, metrics, config, run_dir, timestamp)

    # Save user-friendly summary
    config['seasons_analyzed'] = seasons  # Add seasons to config for summary
    summary_file = save_backtest_summary(results_df, metrics, config, run_dir)
    print(f"Summary saved to: {summary_file}")

    # Summary
    elapsed = time.time() - start_time
    print("\nBacktest Summary:")
    print(f"Total games processed: {len(df)}")
    print(f"Total bets placed: {len(per_game_results)}")
    print(f"Bet frequency: {len(per_game_results)/len(df):.1%}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Results saved to: {run_dir}")

    print(f"[COMPLETE] Backtest finished! Processed {len(df)} games, placed {len(per_game_results)} bets", flush=True)

    # Season breakdown
    if bet_counts:
        print("\n[SUMMARY] Bets by Season:", flush=True)
        for season, count in sorted(bet_counts.items()):
            print(f"  {season}: {count} bets", flush=True)

    print(f"[COMPLETE] Results saved to: {run_dir}", flush=True)

    return {
        'per_game_results': results_df,
        'metrics': metrics,
        'config': config,
        'run_dir': str(run_dir),
        'timestamp': timestamp,
        'elapsed_seconds': elapsed,
        'bet_counts': bet_counts,  # Season-by-season bet counts
        'daily_bet_counts': daily_bet_counts  # Daily bet distribution
    }


def _process_single_game(
    game: pd.Series,
    config: Dict,
    cache: SimpleCache
) -> Optional[Dict]:
    """
    Process a single game for backtesting.

    Args:
        game: Game data row
        config: Backtest configuration
        cache: API cache instance

    Returns:
        Dictionary with game results, or None if no bet placed
    """
    game_key = game['game_key']
    game_date = game['date']
    home_team = normalize_team_name(game['home'])
    away_team = normalize_team_name(game['away'])

    # Determine as_of date (day before game for historical data)
    as_of = game_date - timedelta(days=1)

    try:
        print(f"[API] Fetching as-of stats for {home_team} vs {away_team} (as of {as_of.date()})", flush=True)

        # Get team IDs
        home_id = get_team_id(home_team)
        away_id = get_team_id(away_team)

        # Fetch as-of statistics for both teams
        home_stats = get_team_stats_asof(
            team_id=home_id,
            as_of=as_of,
            last_n_window=10,  # Use config value in future
            cache=cache
        )

        away_stats = get_team_stats_asof(
            team_id=away_id,
            as_of=as_of,
            last_n_window=10,
            cache=cache
        )

        print(f"[MODEL] Running simulation for {home_team} vs {away_team} ({config['engine']['sims']} sims)", flush=True)

        # Run model simulation in backtest mode with as-of data
        model_results, _ = compute_model_report(
            home_team=home_team,
            away_team=away_team,
            season_end_year=game['season_end_year'],
            recency_weight=0.7,  # Use config value in future
            sportsbook_line=game['spread_home_close_signed'],
            decimal_odds=2.0,  # Assume -110 = 1.909 decimal, but use 2.0 for now
            upcoming_game_date=game_date,
            num_simulations=config['engine']['sims'],
            backtest_mode=True,
            as_of=as_of,
            seed=config['engine'].get('seed')  # Use configured seed for reproducibility
        )

    except Exception as e:
        print(f"Error processing game {game_key}: {e}", flush=True)
        return None

    # Make betting decision based on config
    bet_decision = _make_bet_decision(
        model_results=model_results,
        game=game,
        config=config
    )

    if not bet_decision:
        print(f"[BET] No bet placed for {home_team} vs {away_team}", flush=True)
        return None  # No bet placed

    print(f"[BET] Placed {bet_decision['side']} bet on {home_team if bet_decision['side'] == 'home' else away_team} vs {away_team if bet_decision['side'] == 'home' else home_team} (edge: {bet_decision.get('edge_percentage', 'N/A')}%)", flush=True)

    # Calculate bet outcome and P&L
    outcome = _calculate_bet_outcome(
        bet_decision=bet_decision,
        game=game,
        model_results=model_results
    )

    # Return per-game result
    return {
        'game_key': game_key,
        'date': game_date,
        'season_end_year': game['season_end_year'],
        'home_team': home_team,
        'away_team': away_team,
        'market': bet_decision['market'],
        'side': bet_decision['side'],
        'close_line': bet_decision['close_line'],
        'edge_percentage': bet_decision['edge_percentage'],
        'cover_prob': bet_decision['cover_prob'],
        'stake': bet_decision['stake'],
        'pnl': outcome['pnl'],
        'ev_units': outcome['ev_units'],
        'sportsbook_line': bet_decision['sportsbook_line'],
        'final_margin_home': game['final_margin_home'],  # For stress testing
        'spread_home_close_signed': game['spread_home_close_signed'],  # Original spread
        'b2b': game.get('b2b', False),
        'three_in_four': game.get('three_in_four', False),
        'four_in_six': game.get('four_in_six', False),
        'covered': outcome['covered'],
        'is_push': outcome.get('is_push', False)
    }


def _make_bet_decision(
    model_results: Dict,
    game: pd.Series,
    config: Dict
) -> Optional[Dict]:
    """
    Decide whether to place a bet based on model results and config criteria.

    Args:
        model_results: Results from compute_model_report
        game: Game data row
        config: Backtest configuration

    Returns:
        Bet decision dict, or None if no bet
    """
    market = config['entry']['market']

    # For now, focus on spreads
    if market == 'spread':
        # Extract betting analysis from nested structure
        betting_analysis = model_results.get('betting_analysis', {})
        edge_percentage = betting_analysis.get('edge_percentage', 0.0)
        win_probability = betting_analysis.get('win_probability', 0.5)
        sportsbook_line = betting_analysis.get('sportsbook_line', game['spread_home_close_signed'])

        # Check minimum edge requirement (using edge percentage instead of point differential)
        if edge_percentage < config['entry']['min_edge_pts']:
            return None

        # Determine side based on edge (positive edge means bet on home)
        if edge_percentage > 0:
            side = 'home'
            close_line = game['spread_home_close_signed']
            cover_prob = win_probability
        else:
            # For away bets, we need to calculate the away win probability
            # Since edge_percentage is for home, negative means away has edge
            side = 'away'
            close_line = game['spread_home_close_signed']  # Keep original line for evaluation
            # For away bets, cover probability is 1 - home_cover_prob - push_prob
            push_prob = betting_analysis.get('push_probability', 0.0)
            cover_prob = 1.0 - win_probability - push_prob

        # Calculate stake (simplified for now)
        stake = config['sizing']['unit_stake']

        return {
            'market': market,
            'side': side,
            'close_line': close_line,
            'edge_percentage': edge_percentage,
            'cover_prob': cover_prob,
            'stake': stake,
            'sportsbook_line': sportsbook_line
        }

    return None


def _calculate_bet_outcome(
    bet_decision: Dict,
    game: pd.Series,
    model_results: Dict
) -> Dict:
    """
    Calculate bet outcome and profit/loss.

    Args:
        bet_decision: Bet decision from _make_bet_decision
        game: Game data row
        model_results: Model simulation results

    Returns:
        Dictionary with outcome details
    """
    actual_margin = game['final_margin_home']
    spread_line = game['spread_home_close_signed']

    # Get actual odds from model results instead of hardcoding
    betting_analysis = model_results.get('betting_analysis', {})
    decimal_odds = betting_analysis.get('decimal_odds', 1.909)  # fallback to -110

    if bet_decision['market'] == 'spread':
        # Check for push first (margin exactly equals the spread line)
        is_push = abs(actual_margin - spread_line) < 1e-9  # Account for floating point precision

        if is_push:
            covered = False  # Push means no cover, stake returned (but we treat as no win)
            pnl = 0.0  # Stake returned
        else:
            if bet_decision['side'] == 'home':
                # Home covers if actual margin beats the spread
                covered = actual_margin > spread_line
            else:  # away
                # Away covers if home margin is less than the spread (meaning away won by more than spread)
                covered = actual_margin < spread_line

            if covered:
                pnl = bet_decision['stake'] * (decimal_odds - 1)
            else:
                pnl = -bet_decision['stake']

        # Calculate expected value properly
        push_prob = betting_analysis.get('push_probability', 0.0)
        win_prob = bet_decision['cover_prob']
        loss_prob = 1.0 - win_prob - push_prob

        ev_units = (win_prob * (decimal_odds - 1)) + (push_prob * 0) - (loss_prob * 1)

    return {
        'covered': covered if not is_push else False,  # False for push since no winner
        'pnl': pnl,
        'ev_units': ev_units,
        'is_push': is_push
    }


def _save_backtest_outputs(
    results_df: pd.DataFrame,
    metrics: Dict,
    config: Dict,
    run_dir: Path,
    timestamp: str
) -> None:
    """
    Save all backtest outputs to disk.

    Args:
        results_df: Per-game results DataFrame
        metrics: Calculated metrics
        config: Configuration used
        run_dir: Output directory
        timestamp: Run timestamp
    """
    # Save per-game results
    if config['outputs']['per_game_format'] == 'parquet':
        results_df.to_parquet(run_dir / 'per_game.parquet')
    else:
        results_df.to_csv(run_dir / 'per_game.csv', index=False)

    # Save season summary
    season_summary = _calculate_season_summary(results_df)
    season_summary.to_csv(run_dir / 'season_summary.csv', index=False)

    # Save config and metadata
    with open(run_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2, default=str)

    with open(run_dir / 'run_metadata.json', 'w') as f:
        metadata = {
            'timestamp': timestamp,
            'total_games': len(results_df),
            'total_seasons': len(results_df['season_end_year'].unique()),
            'config_hash': hash(json.dumps(config, sort_keys=True, default=str)),
            'metrics': metrics
        }
        json.dump(metadata, f, indent=2, default=str)


def _calculate_season_summary(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate season-level summary statistics.

    Args:
        results_df: Per-game results DataFrame

    Returns:
        Season summary DataFrame
    """
    season_stats = []

    for season in results_df['season_end_year'].unique():
        season_data = results_df[results_df['season_end_year'] == season]

        total_bets = len(season_data)
        total_pnl = season_data['pnl'].sum()
        hit_rate = season_data['covered'].mean()
        avg_edge = season_data['edge_pts'].mean()

        season_stats.append({
            'season_end_year': season,
            'total_bets': total_bets,
            'total_pnl': total_pnl,
            'roi_pct': (total_pnl / season_data['stake'].sum()) * 100 if total_bets > 0 else 0,
            'hit_rate_pct': hit_rate * 100,
            'avg_edge_pts': avg_edge,
            'max_drawdown': _calculate_max_drawdown(season_data['pnl'].cumsum())
        })

    return pd.DataFrame(season_stats)


def _calculate_max_drawdown(cumulative_pnl: pd.Series) -> float:
    """
    Calculate maximum drawdown from cumulative P&L series.

    Args:
        cumulative_pnl: Cumulative profit/loss series

    Returns:
        Maximum drawdown amount
    """
    if cumulative_pnl.empty:
        return 0

    peak = cumulative_pnl.expanding().max()
    drawdown = cumulative_pnl - peak
    return drawdown.min()  # Most negative value


if __name__ == "__main__":
    main()
