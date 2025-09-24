/**
 * calculation-display.js
 * =======================
 *
 * Builds the JSON calculation breakdown shown in the technical details panel.
 */

export function createCalculationBreakdown(data) {
  const recencyWeightInput = document.getElementById('recencyWeight');
  const recencyWeightValue = recencyWeightInput ? parseFloat(recencyWeightInput.value) : undefined;
  const recencyWeight = Number.isFinite(recencyWeightValue) ? recencyWeightValue : 0.4;

  const roundNumericValues = (value, decimals = 4) => {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return Number(value.toFixed(decimals));
    }

    if (Array.isArray(value)) {
      return value.map((item) => roundNumericValues(item, decimals));
    }

    if (value && typeof value === 'object') {
      return Object.fromEntries(
        Object.entries(value).map(([key, val]) => [key, roundNumericValues(val, decimals)])
      );
    }

    return value ?? null;
  };

  const buildCoreStats = (stats) => {
    if (!stats) {
      return null;
    }

    const normalizeSection = (section) => {
      if (!section) {
        return null;
      }

      return {
        pace: roundNumericValues(section.pace, 2),
        offensive_rating: roundNumericValues(section.ortg, 2),
        defensive_rating: roundNumericValues(section.drtg, 2)
      };
    };

    return {
      season: normalizeSection(stats.season),
      last_10: normalizeSection(stats.last_10),
      final_weighted: normalizeSection(stats.final_weighted)
    };
  };

  const buildFourFactors = (fourFactors) => {
    if (!fourFactors) {
      return null;
    }

    const normalize = (section) => (section ? roundNumericValues(section, 3) : null);

    return {
      season: normalize(fourFactors.season),
      last_10: normalize(fourFactors.last_10),
      final_weighted: normalize(fourFactors.final_weighted)
    };
  };

  const buildMiscStats = (miscStats) => {
    if (!miscStats) {
      return null;
    }

    return roundNumericValues(miscStats, 3);
  };

  const buildRestProfiles = (profiles) => {
    if (!profiles) {
      return null;
    }

    const normalize = (profile) => (profile ? roundNumericValues(profile, 3) : null);

    return {
      home: normalize(profiles.home),
      away: normalize(profiles.away)
    };
  };

  const buildVenueSplits = (splits) => {
    if (!splits) {
      return null;
    }

    return roundNumericValues(splits, 3);
  };

  const buildHustleProfiles = (profiles) => {
    if (!profiles) {
      return null;
    }

    const normalize = (profile) => (profile ? roundNumericValues(profile, 3) : null);

    return {
      home: normalize(profiles.home),
      away: normalize(profiles.away)
    };
  };

  const buildModelAdjustments = (adjustments) => {
    if (!adjustments) {
      return null;
    }

    const normalizeSide = (side) => {
      if (!side) {
        return null;
      }

      return {
        fatigue: side.fatigue ? roundNumericValues(side.fatigue, 3) : null,
        venue: side.venue ? roundNumericValues(side.venue, 3) : null,
        hustle: side.hustle ? roundNumericValues(side.hustle, 3) : null
      };
    };

    return {
      home: normalizeSide(adjustments.home),
      away: normalizeSide(adjustments.away)
    };
  };

  const monteCarloResults = data.monte_carlo_results || {};
  const bettingAnalysis = data.betting_analysis || {};
  const winProbabilityValue = bettingAnalysis.win_probability ?? bettingAnalysis.true_probability ?? null;
  const pushProbabilityValue = bettingAnalysis.push_probability ?? null;
  const lossProbabilityValue = bettingAnalysis.loss_probability ?? null;

  const calculationSummary = {
    calculation_steps: {
      data_collection_and_weighting: {
        weighting_formula: 'Final Stat = Season × (1 - weight) + Last10 × weight',
        recency_weight_applied: roundNumericValues(recencyWeight, 2),
        home_team: buildCoreStats(data.home_team_stats),
        away_team: buildCoreStats(data.away_team_stats)
      },
      four_factors_analysis: data.home_four_factors && data.away_four_factors
        ? {
            home_team: buildFourFactors(data.home_four_factors),
            away_team: buildFourFactors(data.away_four_factors)
          }
        : 'Not available for this matchup',
      miscellaneous_adjustments: data.home_misc_stats && data.away_misc_stats
        ? {
            home_team: buildMiscStats(data.home_misc_stats),
            away_team: buildMiscStats(data.away_misc_stats)
          }
        : 'Not available for this matchup',
      contextual_adjustments: data.contextual_factors
        ? {
            rest_profiles: buildRestProfiles(data.contextual_factors.rest_profiles),
            venue_performance: buildVenueSplits(data.contextual_factors.venue_splits),
            hustle_profiles: buildHustleProfiles(data.contextual_factors.hustle_profiles),
            model_adjustments: buildModelAdjustments(data.contextual_factors.model_adjustments)
          }
        : 'Not available for this matchup',
      monte_carlo_simulation: {
        games_simulated: monteCarloResults.games_simulated ?? null,
        home_covers: {
          count: monteCarloResults.home_covers_count ?? null,
          percentage: roundNumericValues(monteCarloResults.home_covers_percentage, 2)
        },
        pushes: {
          count: monteCarloResults.push_count ?? null,
          percentage: roundNumericValues(monteCarloResults.push_percentage, 2)
        },
        home_wins: {
          count: monteCarloResults.home_wins_count ?? null,
          percentage: roundNumericValues(monteCarloResults.home_win_percentage, 2)
        },
        average_scores: roundNumericValues(monteCarloResults.average_scores, 2),
        average_margin: roundNumericValues(monteCarloResults.average_margin, 2),
        margin_std_dev: roundNumericValues(monteCarloResults.margin_std_dev, 2),
        confidence_interval_95: roundNumericValues(monteCarloResults.confidence_interval_95, 2)
      },
      betting_edge_analysis: {
        sportsbook_line: bettingAnalysis.sportsbook_line ?? data.sportsbook_line ?? null,
        decimal_odds: bettingAnalysis.decimal_odds ?? null,
        win_probability_percent: winProbabilityValue != null
          ? roundNumericValues(winProbabilityValue * 100, 2)
          : null,
        true_probability_percent: winProbabilityValue != null
          ? roundNumericValues(winProbabilityValue * 100, 2)
          : null,
        push_probability_percent: pushProbabilityValue != null
          ? roundNumericValues(pushProbabilityValue * 100, 2)
          : null,
        loss_probability_percent: lossProbabilityValue != null
          ? roundNumericValues(lossProbabilityValue * 100, 2)
          : null,
        implied_probability_percent: bettingAnalysis.implied_probability != null
          ? roundNumericValues(bettingAnalysis.implied_probability * 100, 2)
          : null,
        expected_value_per_unit: roundNumericValues(bettingAnalysis.expected_value, 4),
        edge_percentage: roundNumericValues(bettingAnalysis.edge_percentage, 2),
        recommendation: bettingAnalysis.decision ?? null
      }
    }
  };

  return JSON.stringify(calculationSummary, null, 2);
}
