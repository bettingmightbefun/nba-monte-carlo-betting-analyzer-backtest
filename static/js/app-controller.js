/**
 * main.js
 * =======
 *
 * Main application entry point - coordinates all modules
 */

import { CONFIG } from './constants.js';
import { initializeUIHandlers, validateForm, getFormData, showLoading, hideLoading, hideAllResults } from './form-handlers.js';
import { initializeSearchableDropdowns } from './team-selector.js';
import { displayResults, displayError } from './results-presenter.js';

const elements = {};

document.addEventListener('DOMContentLoaded', () => {
  initializeDOMElements();
  initializeUIHandlers();
  initializeSearchableDropdowns();
  setupMainEventListeners();
});

function initializeDOMElements() {
  elements.runButton = document.getElementById('run');
  elements.reportEl = document.getElementById('report');
  elements.jsonEl = document.getElementById('json');
  elements.errorEl = document.getElementById('error');

  elements.quickSummary = document.getElementById('quickSummary');
  elements.summaryContent = document.getElementById('summaryContent');
  elements.detailedResults = document.getElementById('detailedResults');
  elements.errorSection = document.getElementById('errorSection');
}

function setupMainEventListeners() {
  elements.runButton.addEventListener('click', async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    await runAnalysis();
  });
}

async function runAnalysis() {
  try {
    showLoading();
    hideAllResults();

    const formData = getFormData();

    const response = await fetch(CONFIG.API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    });

    const result = await response.json();

    if (result.ok) {
      displayResults(result, elements);
    } else {
      displayError(result.error, result.traceback, elements);
    }

  } catch (error) {
    console.error('Analysis failed:', error);
    displayError(`Network error: ${error.message}`, null, elements);
  } finally {
    hideLoading();
  }
}
