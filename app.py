"""
app.py
======

This module defines a minimal Flask application that serves a single
page and exposes an endpoint for running the betting analysis.

Routes
------
GET /            Render the index.html template with no caching.
GET /favicon.ico Return an empty 204 response (browser nicety).
POST /run        Execute the analysis and return JSON with the
                 structured data and text report, or an error and
                 traceback on failure.

The application is intentionally slim: all business logic lives in
``nba_betting_analyzer`` and related modules.  Any exceptions raised
during data retrieval or computation are caught and returned as part
of the JSON payload so the frontend can display a traceback.
"""

from __future__ import annotations

import subprocess
import traceback
from flask import Flask, render_template, jsonify, make_response, request

from engine import betting_analyzer

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the main page with cache‑busting headers."""
    response = make_response(render_template("index.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/favicon.ico")
def favicon():
    """Return a 204 No Content for favicon requests."""
    return "", 204


@app.route("/run", methods=["POST"])
def run():
    """Handle analysis requests."""
    try:
        # Get form data from request
        form_data = request.get_json() or {}
        
        # Extract parameters with defaults
        home_team = form_data.get('homeTeam', 'LOS ANGELES LAKERS')
        away_team = form_data.get('awayTeam', 'GOLDEN STATE WARRIORS')
        season_year = form_data.get('seasonYear', 2025)
        recency_weight = form_data.get('recencyWeight', 0.4)
        simulation_mode = (form_data.get('simulationMode') or 'standard').lower()
        requested_num_simulations = form_data.get('numSimulations', 100000)
        try:
            requested_num_simulations = int(requested_num_simulations)
        except (TypeError, ValueError):
            requested_num_simulations = 100000

        precision_presets = {
            'standard': 100000,
            'high': 1000000,
            'high_precision': 1000000,
        }
        num_simulations = precision_presets.get(
            simulation_mode, requested_num_simulations
        )
        if num_simulations <= 0:
            num_simulations = 100000

        # Handle new betting format
        home_spread = form_data.get('homeSpread', -3.5)
        away_spread = form_data.get('awaySpread', 3.5)
        home_odds = form_data.get('homeOdds', 1.91)
        away_odds = form_data.get('awayOdds', 1.91)
        
        # For now, we'll analyze the home team bet (can be expanded later)
        spread_line = home_spread
        decimal_odds = home_odds
        
        game_date = form_data.get('gameDate')

        # Run analysis with custom parameters
        data, report = betting_analyzer.compute_model_report(
            home_team=home_team,
            away_team=away_team,
            season_end_year=season_year,
            recency_weight=recency_weight,
            sportsbook_line=spread_line,
            decimal_odds=decimal_odds,
            upcoming_game_date=game_date,
            num_simulations=num_simulations,
        )

        # Add the betting lines to the response data for frontend display
        data['sportsbook_line'] = spread_line
        data['home_spread'] = home_spread
        data['away_spread'] = away_spread
        data['home_odds'] = home_odds
        data['away_odds'] = away_odds
        data.setdefault('simulation_settings', {})
        data['simulation_settings'].update({
            'mode': 'high_precision' if num_simulations >= 1000000 else 'standard',
            'num_simulations': num_simulations
        })

        return jsonify({"ok": True, "text_report": report, "data": data})
    except Exception as exc:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": tb})


@app.route("/backtesting")
def backtesting():
    """Serve the backtesting page."""
    response = make_response(render_template("backtesting.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/api/backtesting/run", methods=["POST"])
def run_backtest():
    """Handle backtest execution requests."""
    try:
        form_data = request.get_json() or {}

        # Extract backtest parameters
        seasons = form_data.get('seasons', '2023')
        dataset = form_data.get('dataset', 'nba_2008-2025.csv')
        simulations = form_data.get('simulations', 1000)  # Smaller default for web
        min_edge = form_data.get('minEdge', 1.0)

        # Build command
        cmd = [
            'python', '-m', 'backtesting.runner',
            '--seasons', seasons,
            '--dataset', dataset,
            '--cfg', 'config/backtest.yaml',
            '--sims', str(simulations),
            '--strict-before-tip'
        ]

        # Run the backtest (this might take time)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='.',
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            return jsonify({
                "ok": True,
                "output": result.stdout,
                "run_completed": True
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.stderr,
                "command": ' '.join(cmd)
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            "ok": False,
            "error": "Backtest timed out after 5 minutes"
        })
    except Exception as exc:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": tb})


@app.route("/api/backtesting/results")
def get_backtest_results():
    """Get backtest results summary."""
    try:
        from backtesting.results_storage import (
            load_latest_results,
            load_all_results,
            get_results_summary_text
        )

        latest = load_latest_results()
        all_results = load_all_results()

        return jsonify({
            "ok": True,
            "latest": latest,
            "all_results": all_results[:10],  # Last 10 runs
            "summary_text": get_results_summary_text()
        })

    except Exception as exc:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": tb})


@app.route("/api/backtesting/compare", methods=["POST"])
def compare_models():
    """Compare live model performance against backtest."""
    try:
        from backtesting.comparison import compare_live_vs_backtest, print_comparison_report

        form_data = request.get_json() or {}

        # Get live metrics from request
        live_metrics = {
            'roi_pct': float(form_data.get('liveRoi', 0)),
            'hit_rate_pct': float(form_data.get('liveHitRate', 0)),
            'expected_value_per_unit': float(form_data.get('liveEv', 0))
        }

        backtest_id = form_data.get('backtestId')

        comparison = compare_live_vs_backtest(live_metrics, backtest_id)
        report = print_comparison_report(live_metrics, backtest_id)

        return jsonify({
            "ok": True,
            "comparison": comparison,
            "report": report
        })

    except Exception as exc:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": tb})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
