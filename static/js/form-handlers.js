/**
 * ui-handlers.js
 * ==============
 * 
 * UI event handlers, form validation, and interface controls
 */

import { CSS_CLASSES, CONFIG } from './constants.js';

// Initialize UI handlers
export function initializeUIHandlers() {
  setupRecencySlider();
  setupSpreadInputSync();
  setupTabSwitching();
}

// Update recency weight display
function setupRecencySlider() {
  const recencySlider = document.getElementById('recencyWeight');
  const recencyValue = document.getElementById('recencyValue');
  
  recencySlider.addEventListener('input', (e) => {
    const value = Math.round(e.target.value * 100);
    recencyValue.textContent = `${value}%`;
  });
}

// Auto-sync spread inputs (when home spread changes, update away spread to opposite)
function setupSpreadInputSync() {
  const homeSpreadInput = document.getElementById('homeSpread');
  const awaySpreadInput = document.getElementById('awaySpread');
  
  homeSpreadInput.addEventListener('input', (e) => {
    const homeValue = parseFloat(e.target.value);
    if (!isNaN(homeValue)) {
      awaySpreadInput.value = (-homeValue).toFixed(1);
    }
  });
  
  awaySpreadInput.addEventListener('input', (e) => {
    const awayValue = parseFloat(e.target.value);
    if (!isNaN(awayValue)) {
      homeSpreadInput.value = (-awayValue).toFixed(1);
    }
  });
}

// Tab switching functionality
function setupTabSwitching() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const targetTab = button.dataset.tab;
      
      // Update active tab button
      tabButtons.forEach(btn => btn.classList.remove(CSS_CLASSES.ACTIVE));
      button.classList.add(CSS_CLASSES.ACTIVE);
      
      // Update active tab pane
      tabPanes.forEach(pane => pane.classList.remove(CSS_CLASSES.ACTIVE));
      document.getElementById(`${targetTab}Tab`).classList.add(CSS_CLASSES.ACTIVE);
    });
  });
}

// Form validation
export function validateForm() {
  const homeTeam = document.getElementById('homeTeam').value.trim();
  const awayTeam = document.getElementById('awayTeam').value.trim();
  const homeSpread = document.getElementById('homeSpread').value;
  const awaySpread = document.getElementById('awaySpread').value;
  const homeOdds = document.getElementById('homeOdds').value;
  const awayOdds = document.getElementById('awayOdds').value;
  
  if (!homeTeam || !awayTeam) {
    alert('Please enter both team names');
    return false;
  }
  
  if (homeTeam.toLowerCase() === awayTeam.toLowerCase()) {
    alert('Home and away teams cannot be the same');
    return false;
  }
  
  if (!homeSpread || !awaySpread) {
    alert('Please enter spread lines for both teams');
    return false;
  }
  
  if (!homeOdds || !awayOdds) {
    alert('Please enter decimal odds for both teams');
    return false;
  }
  
  if (parseFloat(homeOdds) < 1 || parseFloat(awayOdds) < 1) {
    alert('Decimal odds must be 1.00 or higher');
    return false;
  }
  
  // Check that spreads are opposite (home -3.5 should match away +3.5)
  const homeSpreadNum = parseFloat(homeSpread);
  const awaySpreadNum = parseFloat(awaySpread);
  if (Math.abs(homeSpreadNum + awaySpreadNum) > 0.1) {
    alert('Spreads should be opposite (e.g., Home: -3.5, Away: +3.5)');
    return false;
  }
  
  return true;
}

// Get form data
export function getFormData() {
  // Get team values from either select elements or search inputs
  const homeTeamElement = document.getElementById('homeTeam');
  const awayTeamElement = document.getElementById('awayTeam');
  
  // Check if we have search inputs (enhanced dropdowns) or regular selects
  const homeTeamInput = homeTeamElement.parentElement.querySelector('.team-search-input');
  const awayTeamInput = awayTeamElement.parentElement.querySelector('.team-search-input');

  const selectedSimulation = document.querySelector('input[name="simulationMode"]:checked');
  const numSimulations = selectedSimulation
    ? parseInt(selectedSimulation.dataset.simulations, 10)
    : CONFIG.DEFAULT_NUM_SIMULATIONS;
  const simulationMode = selectedSimulation ? selectedSimulation.value : 'standard';

  return {
    homeTeam: (homeTeamInput ? homeTeamInput.value : homeTeamElement.value).trim(),
    awayTeam: (awayTeamInput ? awayTeamInput.value : awayTeamElement.value).trim(),
    homeSpread: parseFloat(document.getElementById('homeSpread').value),
    awaySpread: parseFloat(document.getElementById('awaySpread').value),
    homeOdds: parseFloat(document.getElementById('homeOdds').value),
    awayOdds: parseFloat(document.getElementById('awayOdds').value),
    recencyWeight: parseFloat(document.getElementById('recencyWeight').value),
    seasonYear: parseInt(document.getElementById('seasonYear').value),
    simulationMode,
    numSimulations
  };
}

// Show loading state
export function showLoading() {
  const runButton = document.getElementById('run');
  runButton.disabled = true;
  const span = runButton.querySelector('span');
  const loader = runButton.querySelector('.loader');
  if (span) span.textContent = 'Analyzing...';
  if (loader) loader.classList.remove('hidden');
}

// Hide loading state
export function hideLoading() {
  const runButton = document.getElementById('run');
  runButton.disabled = false;
  const span = runButton.querySelector('span');
  const loader = runButton.querySelector('.loader');
  if (span) span.textContent = 'Analyze Betting Edge';
  if (loader) loader.classList.add('hidden');
}

// Hide all result sections
export function hideAllResults() {
  const quickSummary = document.getElementById('quickSummary');
  const detailedResults = document.getElementById('detailedResults');
  const errorSection = document.getElementById('errorSection');
  
  [quickSummary, detailedResults, errorSection].forEach(section => {
    if (section) section.classList.add(CSS_CLASSES.HIDDEN);
  });
}
