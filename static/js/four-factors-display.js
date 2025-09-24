/**
 * four-factors-display.js
 * =======================
 * 
 * Four Factors analysis display and rendering
 */

// Create Four Factors analysis section
export function createFourFactorsSection(data) {
  if (!data.home_four_factors || !data.away_four_factors) {
    return ''; // Return empty if Four Factors data not available
  }
  
  const homeTeam = data.home_team;
  const awayTeam = data.away_team;
  const homeFourFactors = data.home_four_factors;
  const awayFourFactors = data.away_four_factors;
  
  return `
    <div class="calculation-section four-factors-section">
      <h4><i class="fas fa-chart-pie"></i> 1.5. Four Factors Analysis (Enhanced Model)</h4>
      <div class="four-factors-explanation">
        <p>The Four Factors are the key basketball metrics that research shows are most predictive of wins. Our enhanced model now incorporates these critical statistics:</p>
        <ul>
          <li><strong>EFG% (Effective Field Goal %):</strong> Shooting efficiency accounting for 3-point value</li>
          <li><strong>FTA Rate:</strong> Free throw attempt rate (aggression getting to the line)</li>
          <li><strong>TOV%:</strong> Turnover percentage (ball security)</li>
          <li><strong>OREB%:</strong> Offensive rebounding percentage (second chances)</li>
        </ul>
      </div>
      
      <div class="calc-grid">
        <div class="calc-item">
          <h5>${homeTeam} Four Factors</h5>
          <div class="four-factors-stats">
            ${createTeamFourFactorsStats(homeFourFactors)}
          </div>
        </div>
        
        <div class="calc-item">
          <h5>${awayTeam} Four Factors</h5>
          <div class="four-factors-stats">
            ${createTeamFourFactorsStats(awayFourFactors)}
          </div>
        </div>
      </div>
      
      <div class="four-factors-defensive">
        <h5>Defensive Four Factors (What Teams Allow)</h5>
        <div class="calc-grid">
          <div class="calc-item">
            <h6>${homeTeam} Defense</h6>
            <div class="defensive-stats">
              ${createDefensiveFourFactors(homeFourFactors)}
            </div>
          </div>
          
          <div class="calc-item">
            <h6>${awayTeam} Defense</h6>
            <div class="defensive-stats">
              ${createDefensiveFourFactors(awayFourFactors)}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// Create team Four Factors statistics display
function createTeamFourFactorsStats(fourFactors) {
  return `
    <div class="stat-comparison">
      <div class="stat-row">
        <span class="stat-label">Season EFG%:</span>
        <span class="stat-value">${(fourFactors.season.efg_pct * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Last 10 EFG%:</span>
        <span class="stat-value">${(fourFactors.last_10.efg_pct * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row weighted">
        <span class="stat-label">Final Weighted:</span>
        <span class="stat-value">${(fourFactors.final_weighted.efg_pct * 100).toFixed(1)}%</span>
      </div>
    </div>
    
    <div class="stat-comparison">
      <div class="stat-row">
        <span class="stat-label">Season FTA Rate:</span>
        <span class="stat-value">${(fourFactors.season.fta_rate * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Last 10 FTA Rate:</span>
        <span class="stat-value">${(fourFactors.last_10.fta_rate * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row weighted">
        <span class="stat-label">Final Weighted:</span>
        <span class="stat-value">${(fourFactors.final_weighted.fta_rate * 100).toFixed(1)}%</span>
      </div>
    </div>
    
    <div class="stat-comparison">
      <div class="stat-row">
        <span class="stat-label">Season TOV%:</span>
        <span class="stat-value">${(fourFactors.season.tov_pct * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Last 10 TOV%:</span>
        <span class="stat-value">${(fourFactors.last_10.tov_pct * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row weighted">
        <span class="stat-label">Final Weighted:</span>
        <span class="stat-value">${(fourFactors.final_weighted.tov_pct * 100).toFixed(1)}%</span>
      </div>
    </div>
    
    <div class="stat-comparison">
      <div class="stat-row">
        <span class="stat-label">Season OREB%:</span>
        <span class="stat-value">${(fourFactors.season.oreb_pct * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Last 10 OREB%:</span>
        <span class="stat-value">${(fourFactors.last_10.oreb_pct * 100).toFixed(1)}%</span>
      </div>
      <div class="stat-row weighted">
        <span class="stat-label">Final Weighted:</span>
        <span class="stat-value">${(fourFactors.final_weighted.oreb_pct * 100).toFixed(1)}%</span>
      </div>
    </div>
  `;
}

// Create defensive Four Factors display
function createDefensiveFourFactors(fourFactors) {
  return `
    <div class="stat-row">
      <span class="stat-label">Opp EFG%:</span>
      <span class="stat-value">${(fourFactors.final_weighted.opp_efg_pct * 100).toFixed(1)}%</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Opp FTA Rate:</span>
      <span class="stat-value">${(fourFactors.final_weighted.opp_fta_rate * 100).toFixed(1)}%</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Opp TOV%:</span>
      <span class="stat-value">${(fourFactors.final_weighted.opp_tov_pct * 100).toFixed(1)}%</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Opp OREB%:</span>
      <span class="stat-value">${(fourFactors.final_weighted.opp_oreb_pct * 100).toFixed(1)}%</span>
    </div>
  `;
}
