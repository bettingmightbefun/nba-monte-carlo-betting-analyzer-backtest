"""Monte Carlo simulation engine and betting analysis logic."""

from importlib import import_module
from typing import Any

__version__ = "1.0.0"
__author__ = "NBA Monte Carlo Betting Analyzer"

__all__ = [
    "run_monte_carlo_simulation",
    "calculate_betting_edge",
    "compute_model_report",
    "simulate_single_game",
    "TeamStats",
    "GameResult",
    "create_team_stats",
]

_LAZY_ATTRS = {
    "run_monte_carlo_simulation": ("engine.monte_carlo_engine", "run_monte_carlo_simulation"),
    "calculate_betting_edge": ("engine.monte_carlo_engine", "calculate_betting_edge"),
    "compute_model_report": ("engine.betting_analyzer", "compute_model_report"),
    "simulate_single_game": ("engine.game_simulator", "simulate_single_game"),
    "TeamStats": ("engine.statistical_models", "TeamStats"),
    "GameResult": ("engine.statistical_models", "GameResult"),
    "create_team_stats": ("engine.statistical_models", "create_team_stats"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover - thin wrapper
    if name in _LAZY_ATTRS:
        module_name, attr_name = _LAZY_ATTRS[name]
        module = import_module(module_name)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'engine' has no attribute '{name}'")
