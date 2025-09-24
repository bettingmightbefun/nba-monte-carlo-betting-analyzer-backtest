/**
 * misc-stats-display.js
 * ======================
 * 
 * Miscellaneous stats analysis display and rendering
 */

// Create Miscellaneous Stats analysis section
export function createMiscStatsSection(data) {
  if (!data.home_misc_stats || !data.away_misc_stats) {
    return ''; // Return empty if Miscellaneous Stats data not available
  }
  
  const homeTeam = data.home_team;
  const awayTeam = data.away_team;
  const homeMiscStats = data.home_misc_stats;
  const awayMiscStats = data.away_misc_stats;
  
  return `
    <div class="calculation-section misc-stats-section">
      <h4><i class="fas fa-chart-bar"></i> 1.6. Miscellaneous Stats Analysis (Phase 1 Complete)</h4>
      <div class="misc-stats-explanation">
        <p>Phase 1 miscellaneous stats provide additional context beyond the Four Factors, capturing specific game situations that affect scoring:</p>
        <ul>
          <li><strong>Points off Turnovers:</strong> Shows defensive pressure + offensive execution efficiency</li>
          <li><strong>Second Chance Points:</strong> Complements OREB% with actual conversion efficiency</li>
        </ul>
      </div>
      
      <div class="calc-grid">
        <div class="calc-item">
          <h5>${homeTeam} Miscellaneous Stats</h5>
          <div class="misc-stats-stats">
            ${createTeamMiscStats(homeMiscStats)}
          </div>
        </div>
        
        <div class="calc-item">
          <h5>${awayTeam} Miscellaneous Stats</h5>
          <div class="misc-stats-stats">
            ${createTeamMiscStats(awayMiscStats)}
          </div>
        </div>
      </div>
      
      <div class="misc-stats-defensive">
        <h5>Defensive Miscellaneous Stats (What Teams Allow)</h5>
        <div class="calc-grid">
          <div class="calc-item">
            <h6>${homeTeam} Defense</h6>
            <div class="defensive-stats">
              ${createDefensiveMiscStats(homeMiscStats)}
            </div>
          </div>
          
          <div class="calc-item">
            <h6>${awayTeam} Defense</h6>
            <div class="defensive-stats">
              ${createDefensiveMiscStats(awayMiscStats)}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// Create team Miscellaneous Stats display
function createTeamMiscStats(miscStats) {
  return `
    <div class="stat-comparison">
      <div class="stat-row">
        <span class="stat-label">Season Pts off TO:</span>
        <span class="stat-value">${miscStats.season.pts_off_tov.toFixed(1)}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Last 10 Pts off TO:</span>
        <span class="stat-value">${miscStats.last_10.pts_off_tov.toFixed(1)}</span>
      </div>
      <div class="stat-row weighted">
        <span class="stat-label">Final Weighted:</span>
        <span class="stat-value">${miscStats.final_weighted.pts_off_tov.toFixed(1)}</span>
      </div>
    </div>
    
    <div class="stat-comparison">
      <div class="stat-row">
        <span class="stat-label">Season 2nd Chance:</span>
        <span class="stat-value">${miscStats.season.pts_2nd_chance.toFixed(1)}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Last 10 2nd Chance:</span>
        <span class="stat-value">${miscStats.last_10.pts_2nd_chance.toFixed(1)}</span>
      </div>
      <div class="stat-row weighted">
        <span class="stat-label">Final Weighted:</span>
        <span class="stat-value">${miscStats.final_weighted.pts_2nd_chance.toFixed(1)}</span>
      </div>
    </div>
  `;
}

// Create defensive Miscellaneous Stats display
function createDefensiveMiscStats(miscStats) {
  return `
    <div class="stat-row">
      <span class="stat-label">Opp Pts off TO:</span>
      <span class="stat-value">${miscStats.final_weighted.opp_pts_off_tov.toFixed(1)}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Opp 2nd Chance:</span>
      <span class="stat-value">${miscStats.final_weighted.opp_pts_2nd_chance.toFixed(1)}</span>
    </div>
  `;
}
