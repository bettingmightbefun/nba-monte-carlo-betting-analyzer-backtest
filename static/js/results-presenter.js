/**
 * results-presenter.js
 * =====================
 *
 * Handles rendering of success and error states for the analysis view.
 */

import { createQuickSummary } from './summary-display.js';
import { createCalculationBreakdown } from './calculation-display.js';

export function displayResults(result, elements) {
  const {
    quickSummary,
    summaryContent,
    detailedResults,
    reportEl,
    jsonEl
  } = elements;

  const data = result.data;
  const report = result.text_report;

  quickSummary.classList.remove('hidden');
  detailedResults.classList.remove('hidden');

  summaryContent.innerHTML = createQuickSummary(data);

  const calculationDetails = document.getElementById('calculationDetails');
  calculationDetails.textContent = createCalculationBreakdown(data);

  reportEl.textContent = report;
  jsonEl.textContent = JSON.stringify(data, null, 2);
}

export function displayError(error, traceback, elements) {
  const { errorSection, errorEl } = elements;
  errorSection.classList.remove('hidden');

  let errorHtml = `<h3>❌ Analysis Error</h3><p><strong>Error:</strong> ${error}</p>`;

  if (traceback) {
    errorHtml += `
      <details>
        <summary>Technical Details</summary>
        <pre>${traceback}</pre>
      </details>
    `;
  }

  errorEl.innerHTML = errorHtml;
}
