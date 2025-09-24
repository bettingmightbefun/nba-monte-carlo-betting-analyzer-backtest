/**
 * summary-display.js
 * ==================
 *
 * Renders the rich quick summary panel shown on successful analysis runs.
 */

export function createQuickSummary(data) {
  const monteCarloResults = data.monte_carlo_results;
  const bettingAnalysis = data.betting_analysis;
  const simulationSettings = data.simulation_settings || {};

  const coverPercentage = monteCarloResults.home_covers_percentage;
  const pushPercentage = monteCarloResults.push_percentage ?? 0;
  const edgePercentage = bettingAnalysis.edge_percentage;
  const gamesSimulated = monteCarloResults.games_simulated;
  const homeWins = monteCarloResults.home_wins_count;
  const homeWinPercentage = monteCarloResults.home_win_percentage;
  const pushCount = monteCarloResults.push_count ?? 0;

  const formatSignedPercent = (value, decimals = 2) =>
    `${value > 0 ? '+' : value < 0 ? '-' : ''}${Math.abs(value).toFixed(decimals)}%`;

  const formatSignedNumber = (value, decimals = 1) => {
    const fixed = Math.abs(value).toFixed(decimals);
    if (value > 0) return `+${fixed}`;
    if (value < 0) return `-${fixed}`;
    return `0.${'0'.repeat(decimals)}`;
  };

  const formatLine = (line) => {
    const formatted = Math.abs(line).toFixed(1);
    if (line > 0) return `+${formatted}`;
    if (line < 0) return `-${formatted}`;
    return '+0.0';
  };

  const formatSimulationCount = (count) => {
    if (count >= 1000) {
      const thousands = count / 1000;
      const formatted = thousands % 1 === 0
        ? thousands.toFixed(0)
        : thousands.toFixed(1);
      return `${formatted}k`;
    }
    return count.toLocaleString();
  };

  const simulationSubtitle = simulationSettings.description
    ? `${simulationSettings.description} • ${formatSimulationCount(gamesSimulated)} simulations`
    : `${formatSimulationCount(gamesSimulated)} Monte Carlo simulations`;

  const formatSignedWithSuffix = (value, decimals = 1, suffix = '') => {
    if (value == null || Number.isNaN(value)) {
      return 'n/a';
    }
    return `${formatSignedNumber(value, decimals)}${suffix}`;
  };

  const contextualFactors = data.contextual_factors || {};
  const homeTeamName = data.home_team || 'Home Team';
  const awayTeamName = data.away_team || 'Away Team';
  const restProfiles = contextualFactors.rest_profiles || {};
  const venueSplits = contextualFactors.venue_splits || {};
  const hustleProfiles = contextualFactors.hustle_profiles || {};
  const modelAdjustments = contextualFactors.model_adjustments || {};
  const homeAdjustments = modelAdjustments.home || {};
  const awayAdjustments = modelAdjustments.away || {};

  const getPrimaryNote = (adjustment) => {
    if (!adjustment || typeof adjustment !== 'object') {
      return 'No adjustment applied.';
    }

    const notes = Array.isArray(adjustment.notes)
      ? adjustment.notes.filter((note) => !!note)
      : [];

    if (notes.length > 0) {
      return notes[0];
    }

    return 'No adjustment applied.';
  };

  const formatRestDescriptor = (profile) => {
    if (!profile) {
      return 'Rest profile unavailable.';
    }

    const restDays = profile.rest_days_before_last_game;
    const fatigueFlag = profile.fatigue_flag_last_game || 'Fatigue status unavailable';

    if (restDays == null) {
      return `${fatigueFlag}`;
    }

    const label = restDays === 1 ? 'day' : 'days';
    return `${restDays} ${label} rest • ${fatigueFlag}`;
  };

  const formatRestSummary = (profile) => {
    if (!profile) {
      return '—';
    }

    const summaryBits = [];
    if (typeof profile.average_rest_days === 'number' && Number.isFinite(profile.average_rest_days)) {
      summaryBits.push(`${profile.average_rest_days.toFixed(1)}d avg rest`);
    }
    if (typeof profile.back_to_back_rate === 'number' && Number.isFinite(profile.back_to_back_rate)) {
      summaryBits.push(`${(profile.back_to_back_rate * 100).toFixed(1)}% back-to-backs`);
    }
    if (typeof profile.fatigue_score_mean === 'number' && Number.isFinite(profile.fatigue_score_mean)) {
      summaryBits.push(`fatigue score ${profile.fatigue_score_mean.toFixed(2)}`);
    }
    return summaryBits.join(' • ') || '—';
  };

  const renderRestItem = (teamLabel, profile, adjustment) => {
    const descriptor = formatRestDescriptor(profile);
    const summary = formatRestSummary(profile);
    const note = getPrimaryNote(adjustment);

    return `
      <li>
        <span class="context-team">${teamLabel}</span>
        <div class="context-detail">${descriptor}</div>
        <div class="context-detail">${summary}</div>
        <div class="context-note">${note}</div>
      </li>
    `;
  };

  const renderVenueItem = (
    teamLabel,
    performance,
    differentials,
    adjustment,
    locationLabel
  ) => {
    if (!performance) {
      return `
        <li>
          <span class="context-team">${teamLabel} (${locationLabel})</span>
          <div class="context-note">Venue performance unavailable.</div>
        </li>
      `;
    }

    const winPct = performance.win_pct != null && Number.isFinite(performance.win_pct)
      ? `${(performance.win_pct * 100).toFixed(1)}%`
      : 'n/a';
    const points = performance.points_per_game != null && Number.isFinite(performance.points_per_game)
      ? performance.points_per_game.toFixed(1)
      : 'n/a';
    const ortg = performance.offensive_rating != null && Number.isFinite(performance.offensive_rating)
      ? performance.offensive_rating.toFixed(1)
      : 'n/a';
    const drtg = performance.defensive_rating != null && Number.isFinite(performance.defensive_rating)
      ? performance.defensive_rating.toFixed(1)
      : 'n/a';

    const pointsGap = differentials && differentials.points_advantage != null
      ? formatSignedWithSuffix(differentials.points_advantage, 1, ' pts')
      : 'n/a';
    const winGap = differentials && differentials.win_pct_advantage != null
      ? formatSignedWithSuffix(differentials.win_pct_advantage * 100, 1, '%')
      : 'n/a';
    const ortgGap = differentials && differentials.ortg_advantage != null
      ? formatSignedWithSuffix(differentials.ortg_advantage, 2)
      : 'n/a';
    const note = getPrimaryNote(adjustment);

    return `
      <li>
        <span class="context-team">${teamLabel} (${locationLabel})</span>
        <div class="context-detail">Win% ${winPct} • ${points} PPG • ORtg ${ortg}${drtg !== 'n/a' ? ` • DRtg ${drtg}` : ''}</div>
        <div class="context-detail">Gap vs other venue: Points ${pointsGap}${winGap !== 'n/a' ? ` • Win% ${winGap}` : ''}${ortgGap !== 'n/a' ? ` • ORtg ${ortgGap}` : ''}</div>
        <div class="context-note">${note}</div>
      </li>
    `;
  };

  const renderHustleItem = (teamLabel, profile, adjustment) => {
    if (!profile) {
      return `
        <li>
          <span class="context-team">${teamLabel}</span>
          <div class="context-note">Hustle profile unavailable.</div>
        </li>
      `;
    }

    const effortScore = Number.isFinite(profile.team_effort_score)
      ? profile.team_effort_score.toFixed(2)
      : 'n/a';
    const percentile = Number.isFinite(profile.effort_percentile)
      ? `${(profile.effort_percentile * 100).toFixed(1)}%`
      : 'n/a';
    const leagueBaseline = Number.isFinite(profile.league_average_effort)
      ? profile.league_average_effort.toFixed(2)
      : 'n/a';
    const note = getPrimaryNote(adjustment);

    return `
      <li>
        <span class="context-team">${teamLabel}</span>
        <div class="context-detail">Effort score ${effortScore} • Percentile ${percentile}</div>
        <div class="context-detail">League baseline ${leagueBaseline}</div>
        <div class="context-note">${note}</div>
      </li>
    `;
  };

  const recommendationLevel = (() => {
    if (edgePercentage >= 3) return 'BET';
    if (edgePercentage >= 1) return 'LEAN';
    if (edgePercentage <= -3) return 'NO BET';
    return 'NO BET';
  })();

  const chipClass = {
    BET: 'chip--bet',
    LEAN: 'chip--lean',
    'NO BET': 'chip--no-bet'
  }[recommendationLevel];

  const edgeStateClass = edgePercentage > 3
    ? 'edge-bar--positive'
    : edgePercentage < -3
      ? 'edge-bar--negative'
      : 'edge-bar--neutral';

  const insightSentence = `Home team ${monteCarloResults.average_margin >= 0 ? 'won' : 'lost'} by ${Math.abs(monteCarloResults.average_margin).toFixed(1)} pts on average across simulations.`;

  const normalizedEdge = Math.max(-10, Math.min(10, edgePercentage));
  const edgeGaugeProgress = (Math.abs(normalizedEdge) / 10) * 50;
  const gaugeDirectionClass = normalizedEdge >= 0 ? 'positive' : 'negative';

  return `
    <div class="betting-recommendation-panel">
      <header class="recommendation-header">
        <div class="header-title-group">
          <div class="header-icon" aria-hidden="true">
            <i class="fas fa-bullseye"></i>
          </div>
          <div>
            <h3>Betting Recommendation</h3>
            <span class="subtitle">${simulationSubtitle}</span>
          </div>
        </div>
        <span class="recommendation-chip ${chipClass}">${recommendationLevel}</span>
      </header>

      <section class="insight-card">
        <p class="insight-text">${insightSentence}</p>
        <div class="edge-gauge">
          <div class="edge-gauge-header">
            <span>Edge vs Sportsbook</span>
            <span class="edge-gauge-value">${formatSignedPercent(edgePercentage)}</span>
          </div>
          <div class="edge-gauge-track">
            <div class="edge-gauge-fill ${gaugeDirectionClass}" style="--edge-progress: ${edgeGaugeProgress}"></div>
            <span class="edge-gauge-center"></span>
          </div>
        </div>
      </section>

      <section class="stat-tiles">
        <article class="stat-tile">
          <span class="stat-label">Home Win Rate</span>
          <span class="stat-value">${homeWinPercentage.toFixed(1)}%</span>
          <span class="stat-subtext">${homeWins.toLocaleString()} / ${gamesSimulated.toLocaleString()}</span>
        </article>
        <article class="stat-tile">
          <span class="stat-label">Cover Probability</span>
          <span class="stat-value">${coverPercentage.toFixed(1)}%</span>
          <span class="stat-subtext">${monteCarloResults.home_covers_count.toLocaleString()} / ${gamesSimulated.toLocaleString()}</span>
        </article>
        <article class="stat-tile">
          <span class="stat-label">Push Rate</span>
          <span class="stat-value">${pushPercentage.toFixed(1)}%</span>
          <span class="stat-subtext">${pushCount.toLocaleString()} / ${gamesSimulated.toLocaleString()}</span>
        </article>
        <article class="stat-tile">
          <span class="stat-label">Avg Final Scores</span>
          <span class="stat-value">${monteCarloResults.average_scores.home.toFixed(1)}–${monteCarloResults.average_scores.away.toFixed(1)}</span>
          <span class="stat-subtext">Margin ${formatSignedNumber(monteCarloResults.average_margin)}</span>
        </article>
        <article class="stat-tile">
          <span class="stat-label">Sportsbook Line</span>
          <span class="stat-value">${formatLine(bettingAnalysis.sportsbook_line)}</span>
          <span class="stat-subtext">Decimal odds ${bettingAnalysis.decimal_odds.toFixed(2)}</span>
        </article>
      </section>

      <section class="contextual-section insight-card">
        <header class="contextual-header">
          <h4>Contextual Factors Applied</h4>
          <span>Schedule, venue, and hustle adjustments derived from live NBA data</span>
        </header>
        <div class="context-grid">
          <article class="context-card">
            <div class="context-card-header">
              <i class="fas fa-bed" aria-hidden="true"></i>
              <div>
                <h5>Rest &amp; Fatigue</h5>
                <span>Latest recovery profiles before this matchup</span>
              </div>
            </div>
            <ul class="context-list">
              ${renderRestItem(homeTeamName, restProfiles.home, homeAdjustments.fatigue)}
              ${renderRestItem(awayTeamName, restProfiles.away, awayAdjustments.fatigue)}
            </ul>
          </article>
          <article class="context-card">
            <div class="context-card-header">
              <i class="fas fa-map-marker-alt" aria-hidden="true"></i>
              <div>
                <h5>Venue Performance</h5>
                <span>Home/Road form and model modifiers</span>
              </div>
            </div>
            <ul class="context-list">
              ${renderVenueItem(
                homeTeamName,
                venueSplits.home ? venueSplits.home.home_performance : null,
                venueSplits.home ? venueSplits.home.venue_differentials : null,
                homeAdjustments.venue,
                'Home'
              )}
              ${renderVenueItem(
                awayTeamName,
                venueSplits.away ? venueSplits.away.away_performance : null,
                venueSplits.away ? venueSplits.away.venue_differentials : null,
                awayAdjustments.venue,
                'Road'
              )}
            </ul>
          </article>
          <article class="context-card">
            <div class="context-card-header">
              <i class="fas fa-fire" aria-hidden="true"></i>
              <div>
                <h5>Hustle &amp; Effort</h5>
                <span>League-ranked activity signals</span>
              </div>
            </div>
            <ul class="context-list">
              ${renderHustleItem(homeTeamName, hustleProfiles.home, homeAdjustments.hustle)}
              ${renderHustleItem(awayTeamName, hustleProfiles.away, awayAdjustments.hustle)}
            </ul>
          </article>
        </div>
      </section>

      <footer class="edge-bar ${edgeStateClass}">
        <div class="edge-bar-main">
          <span class="edge-bar-label">Betting Edge</span>
          <span class="edge-bar-value">${formatSignedPercent(edgePercentage)}</span>
        </div>
        <div class="edge-bar-helper">
          <i class="fas fa-info-circle" aria-hidden="true"></i>
          <span>Edge is expected advantage vs the book; ~0% implies an efficient line.</span>
        </div>
      </footer>
    </div>
  `;
}
