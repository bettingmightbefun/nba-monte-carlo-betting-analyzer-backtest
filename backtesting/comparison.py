"""
backtesting/comparison.py
=========================

Compare live model performance against backtest benchmarks.
Provides easy assessment of how current model stacks up vs historical testing.

Functions
---------
compare_live_vs_backtest(live_metrics, backtest_id=None) -> Dict
    Compare current live performance against a backtest benchmark.

get_performance_assessment(live_metrics, benchmark) -> Dict
    Assess current model performance relative to backtest expectations.

print_comparison_report(live_metrics, backtest_id=None) -> str
    Generate human-readable comparison report.

This module helps you quickly see if your live model's performance
is in line with backtesting expectations.
"""

from __future__ import annotations

from typing import Dict, Optional

from backtesting.results_storage import get_comparison_benchmark, save_model_comparison


def compare_live_vs_backtest(live_metrics: Dict, backtest_id: Optional[str] = None) -> Dict:
    """
    Compare current live performance against a backtest benchmark.

    Args:
        live_metrics: Current live model metrics (roi_pct, hit_rate, etc.)
        backtest_id: Specific backtest ID to compare against (uses latest if None)

    Returns:
        Comparison dictionary with differences and assessments
    """
    # Get benchmark data
    if backtest_id:
        # Would need to load specific backtest - for now use latest
        benchmark = get_comparison_benchmark()
    else:
        benchmark = get_comparison_benchmark()

    if not benchmark:
        return {
            'error': 'No backtest benchmark available. Run a backtest first.',
            'comparison': None
        }

    # Extract key metrics
    live_roi = live_metrics.get('roi_pct', 0)
    live_hit_rate = live_metrics.get('hit_rate_pct', 0)
    live_ev = live_metrics.get('expected_value_per_unit', 0)

    backtest_roi = benchmark.get('roi_benchmark', 0)
    backtest_hit_rate = benchmark.get('hit_rate_benchmark', 0)
    backtest_ev = benchmark.get('ev_per_unit_benchmark', 0)

    # Calculate differences
    roi_diff = live_roi - backtest_roi
    hit_rate_diff = live_hit_rate - backtest_hit_rate
    ev_diff = live_ev - backtest_ev

    # Performance assessment
    assessment = get_performance_assessment(live_metrics, benchmark)

    comparison = {
        'live_metrics': {
            'roi_pct': live_roi,
            'hit_rate_pct': live_hit_rate,
            'expected_value_per_unit': live_ev
        },
        'benchmark_metrics': {
            'roi_pct': backtest_roi,
            'hit_rate_pct': backtest_hit_rate,
            'expected_value_per_unit': backtest_ev
        },
        'differences': {
            'roi_pct_diff': roi_diff,
            'hit_rate_pct_diff': hit_rate_diff,
            'ev_per_unit_diff': ev_diff
        },
        'assessment': assessment,
        'backtest_id': benchmark.get('backtest_id'),
        'comparison_timestamp': __import__('datetime').datetime.now().isoformat()
    }

    # Save comparison for historical tracking
    save_model_comparison(live_metrics, benchmark.get('backtest_id'))

    return comparison


def get_performance_assessment(live_metrics: Dict, benchmark: Dict) -> Dict:
    """
    Assess current model performance relative to backtest expectations.

    Args:
        live_metrics: Current live model metrics
        benchmark: Backtest benchmark data

    Returns:
        Assessment dictionary with status and recommendations
    """
    live_roi = live_metrics.get('roi_pct', 0)
    live_hit_rate = live_metrics.get('hit_rate_pct', 0)
    live_ev = live_metrics.get('expected_value_per_unit', 0)

    backtest_roi = benchmark.get('roi_benchmark', 0)
    backtest_hit_rate = benchmark.get('hit_rate_benchmark', 0)
    backtest_ev = benchmark.get('ev_per_unit_benchmark', 0)

    # Define acceptable ranges (within 20% of backtest)
    roi_range = abs(backtest_roi) * 0.20 if backtest_roi != 0 else 2.0
    hit_rate_range = 5.0  # 5 percentage points
    ev_range = abs(backtest_ev) * 0.30 if backtest_ev != 0 else 0.01

    # Assess each metric
    assessments = {}

    # ROI assessment
    roi_diff = live_roi - backtest_roi
    if abs(roi_diff) <= roi_range:
        assessments['roi'] = 'aligned'
    elif roi_diff > roi_range:
        assessments['roi'] = 'better'
    else:
        assessments['roi'] = 'worse'

    # Hit rate assessment
    hit_rate_diff = live_hit_rate - backtest_hit_rate
    if abs(hit_rate_diff) <= hit_rate_range:
        assessments['hit_rate'] = 'aligned'
    elif hit_rate_diff > hit_rate_range:
        assessments['hit_rate'] = 'better'
    else:
        assessments['hit_rate'] = 'worse'

    # EV assessment
    ev_diff = live_ev - backtest_ev
    if abs(ev_diff) <= ev_range:
        assessments['expected_value'] = 'aligned'
    elif ev_diff > ev_range:
        assessments['expected_value'] = 'better'
    else:
        assessments['expected_value'] = 'worse'

    # Overall assessment
    good_metrics = sum(1 for status in assessments.values() if status in ['aligned', 'better'])

    if good_metrics == 3:
        overall = 'excellent'
        status = '✅ Live performance matches or exceeds backtest expectations'
    elif good_metrics >= 2:
        overall = 'good'
        status = '👍 Live performance is generally aligned with backtest'
    elif good_metrics == 1:
        overall = 'concerning'
        status = '⚠️ Live performance shows some deviation from backtest'
    else:
        overall = 'poor'
        status = '❌ Live performance significantly underperforms backtest'

    return {
        'overall_status': overall,
        'status_message': status,
        'metric_assessments': assessments,
        'recommendations': _get_recommendations(assessments, benchmark)
    }


def _get_recommendations(assessments: Dict, benchmark: Dict) -> List[str]:
    """Generate recommendations based on performance assessment."""
    recommendations = []

    if assessments.get('roi') == 'worse':
        recommendations.append("ROI is lower than backtest - consider adjusting edge thresholds or bet sizing")

    if assessments.get('hit_rate') == 'worse':
        recommendations.append("Hit rate is lower - model may be over-aggressive or market conditions changed")

    if assessments.get('expected_value') == 'worse':
        recommendations.append("Expected value is negative - review model calibration and market efficiency")

    if assessments.get('roi') == 'better' and assessments.get('hit_rate') == 'better':
        recommendations.append("Strong live performance - consider if backtest sample was representative")

    if not recommendations:
        recommendations.append("Live performance is well-aligned with backtest expectations")

    return recommendations


def print_comparison_report(live_metrics: Dict, backtest_id: Optional[str] = None) -> str:
    """
    Generate human-readable comparison report.

    Args:
        live_metrics: Current live model metrics
        backtest_id: Specific backtest ID to compare against

    Returns:
        Formatted comparison report
    """
    comparison = compare_live_vs_backtest(live_metrics, backtest_id)

    if 'error' in comparison:
        return f"❌ Comparison Error: {comparison['error']}"

    live = comparison['live_metrics']
    bench = comparison['benchmark_metrics']
    diff = comparison['differences']
    assess = comparison['assessment']

    report = f"""
🔍 LIVE MODEL vs BACKTEST COMPARISON
══════════════════════════════════════════════════════════

📊 Current Live Performance:
   • ROI: {live['roi_pct']:+.1f}%
   • Hit Rate: {live['hit_rate_pct']:.1f}%
   • EV per Unit: {live['expected_value_per_unit']:+.3f}

🎯 Backtest Benchmark (ID: {comparison['backtest_id']}):
   • ROI: {bench['roi_pct']:+.1f}%
   • Hit Rate: {bench['hit_rate_pct']:.1f}%
   • EV per Unit: {bench['expected_value_per_unit']:+.3f}

📈 Differences (Live - Backtest):
   • ROI: {diff['roi_pct_diff']:+.1f} pts
   • Hit Rate: {diff['hit_rate_pct_diff']:+.1f} pts
   • EV per Unit: {diff['ev_per_unit_diff']:+.3f}

{assess['status_message']}

💡 Recommendations:
"""

    for rec in assess['recommendations']:
        report += f"   • {rec}\n"

    report += f"\n🕒 Comparison generated: {comparison['comparison_timestamp'][:19].replace('T', ' ')}"

    return report.strip()


# Example usage for testing
def example_live_metrics() -> Dict:
    """Example live metrics for testing."""
    return {
        'roi_pct': 8.5,
        'hit_rate_pct': 53.2,
        'expected_value_per_unit': 0.045,
        'total_bets': 150,
        'total_pnl': 1275.00
    }


if __name__ == "__main__":
    # Example usage
    live = example_live_metrics()
    print(print_comparison_report(live))
