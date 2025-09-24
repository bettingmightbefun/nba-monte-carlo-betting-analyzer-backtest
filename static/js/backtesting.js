/**
 * backtesting.js - Frontend JavaScript for NBA backtesting dashboard
 */

// Global state
let currentResults = null;
let equityChart = null;
let calibrationChart = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadBacktestResults();
});

// Set up event listeners
function initializeEventListeners() {
    // Backtest form submission
    document.getElementById('backtestForm').addEventListener('submit', handleBacktestSubmit);

    // Comparison form submission
    document.getElementById('comparisonForm').addEventListener('submit', handleComparisonSubmit);

    // Refresh results button
    document.getElementById('refreshResults').addEventListener('click', loadBacktestResults);

    // Console controls
    document.getElementById('clearConsole').addEventListener('click', clearConsole);
    document.getElementById('scrollToBottom').addEventListener('click', scrollConsoleToBottom);
}

// Handle backtest form submission
async function handleBacktestSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        seasons: document.getElementById('seasons').value,
        dataset: document.getElementById('dataset').value,
        simulations: document.getElementById('simulations').value,
        minEdge: document.getElementById('minEdge').value
    };

    // Update UI for running state
    setRunningState(true);

    try {
        const response = await fetch('/api/backtesting/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.ok) {
            // Parse and display the console output
            if (result.output) {
                parseAndDisplayConsoleOutput(result.output);
            }

            showSuccessMessage('Backtest completed successfully!');
            // Reload results after a short delay
            setTimeout(() => {
                loadBacktestResults();
            }, 1000);
        } else {
            addConsoleLine(`ERROR: ${result.error}`, 'error');
            showErrorMessage(`Backtest failed: ${result.error}`);
        }
    } catch (error) {
        showErrorMessage(`Error running backtest: ${error.message}`);
    } finally {
        setRunningState(false);
    }
}

// Handle comparison form submission
async function handleComparisonSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        liveRoi: document.getElementById('liveRoi').value,
        liveHitRate: document.getElementById('liveHitRate').value,
        liveEv: document.getElementById('liveEv').value
    };

    try {
        const response = await fetch('/api/backtesting/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.ok) {
            displayComparisonResults(result.comparison, result.report);
        } else {
            showErrorMessage(`Comparison failed: ${result.error}`);
        }
    } catch (error) {
        showErrorMessage(`Error running comparison: ${error.message}`);
    }
}

// Load backtest results from server
async function loadBacktestResults() {
    try {
        const response = await fetch('/api/backtesting/results');
        const result = await response.json();

        if (result.ok) {
            currentResults = result;
            displayLatestResults(result.latest, result.summary_text);
            displayHistoricalRuns(result.all_results);
            displayPerformanceMetrics(result.latest);
        } else {
            showErrorMessage(`Failed to load results: ${result.error}`);
        }
    } catch (error) {
        showErrorMessage(`Error loading results: ${error.message}`);
    }
}

// Display latest results summary
function displayLatestResults(latest, summaryText) {
    const summaryContent = document.getElementById('summaryContent');

    if (!latest) {
        summaryContent.innerHTML = '<p>No backtest results available. Run a backtest first!</p>';
        return;
    }

    summaryContent.innerHTML = `<pre>${summaryText}</pre>`;
}

// Display performance metrics
function displayPerformanceMetrics(latest) {
    const metricsContainer = document.getElementById('performanceMetrics');

    if (!latest) {
        metricsContainer.classList.add('hidden');
        return;
    }

    const perf = latest.performance;

    document.getElementById('roiValue').textContent = `${perf.roi_pct.toFixed(1)}%`;
    document.getElementById('hitRateValue').textContent = `${perf.hit_rate_pct.toFixed(1)}%`;
    document.getElementById('pnlValue').textContent = `$${perf.total_pnl.toLocaleString()}`;
    document.getElementById('betsValue').textContent = perf.total_bets || 0;

    metricsContainer.classList.remove('hidden');
}

// Display historical runs
function displayHistoricalRuns(allResults) {
    const runsList = document.getElementById('runsList');

    if (!allResults || allResults.length === 0) {
        runsList.innerHTML = '<p>No historical backtests found.</p>';
        return;
    }

    const runsHtml = allResults.map(run => {
        const perf = run.performance;
        const config = run.config;
        const timestamp = new Date(run.timestamp).toLocaleString();

        return `
            <div class="run-item" data-run-id="${run.run_id}">
                <div class="run-id">${run.run_id}</div>
                <div class="run-metrics">
                    <div class="metric">
                        <div class="metric-label">ROI</div>
                        <div class="metric-value">${perf.roi_pct.toFixed(1)}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Hit Rate</div>
                        <div class="metric-value">${perf.hit_rate_pct.toFixed(1)}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Bets</div>
                        <div class="metric-value">${config.bets_placed || 0}</div>
                    </div>
                </div>
                <small style="color: #666;">${timestamp}</small>
            </div>
        `;
    }).join('');

    runsList.innerHTML = runsHtml;

    // Add click handlers for run items
    document.querySelectorAll('.run-item').forEach(item => {
        item.addEventListener('click', () => {
            // Remove selected class from all items
            document.querySelectorAll('.run-item').forEach(i => i.classList.remove('selected'));
            // Add selected class to clicked item
            item.classList.add('selected');
        });
    });
}

// Display comparison results
function displayComparisonResults(comparison, report) {
    const resultsContainer = document.getElementById('comparisonResults');
    const content = document.getElementById('comparisonContent');
    const textElement = document.getElementById('comparisonText');

    textElement.textContent = report;
    resultsContainer.classList.remove('hidden');

    // Scroll to comparison results
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

// Set UI running state
function setRunningState(isRunning) {
    const runButton = document.getElementById('runButton');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const consoleContainer = document.getElementById('consoleContainer');

    if (isRunning) {
        runButton.disabled = true;
        runButton.textContent = 'Running...';
        progressContainer.classList.remove('hidden');
        consoleContainer.classList.remove('hidden');
        progressFill.style.width = '0%';
        progressText.textContent = 'Running backtest...';

        // Clear and initialize console
        clearConsole();
        addConsoleLine('Starting backtest execution...', 'status');

        // Simulate progress (since we don't have real progress updates)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 5;
            if (progress > 85) progress = 85; // Leave room for final completion
            progressFill.style.width = `${progress}%`;

            if (!isRunning) {
                clearInterval(progressInterval);
            }
        }, 1000);

        // Store interval for cleanup
        window.progressInterval = progressInterval;
    } else {
        runButton.disabled = false;
        runButton.textContent = '🚀 Run Backtest';
        progressFill.style.width = '100%';
        progressText.textContent = 'Completed!';

        // Hide progress and console after a delay
        setTimeout(() => {
            progressContainer.classList.add('hidden');
            consoleContainer.classList.add('hidden');
        }, 3000);

        // Clear progress interval
        if (window.progressInterval) {
            clearInterval(window.progressInterval);
        }
    }
}

// Show error message
function showErrorMessage(message) {
    showMessage(message, 'error');
}

// Show success message
function showSuccessMessage(message) {
    showMessage(message, 'success');
}

// Show message to user
function showMessage(message, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.error-message, .success-message');
    existingMessages.forEach(msg => msg.remove());

    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
    messageDiv.textContent = message;

    // Insert at top of results panel
    const resultsPanel = document.querySelector('.results-panel');
    resultsPanel.insertBefore(messageDiv, resultsPanel.firstChild.nextSibling);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Console output functions
function addConsoleLine(text, type = 'default') {
    const consoleOutput = document.getElementById('consoleOutput');
    if (!consoleOutput) return;

    const lineDiv = document.createElement('div');
    lineDiv.className = 'console-line';
    lineDiv.setAttribute('data-type', type);
    lineDiv.textContent = text;

    consoleOutput.appendChild(lineDiv);
    scrollConsoleToBottom();
}

function clearConsole() {
    const consoleOutput = document.getElementById('consoleOutput');
    if (consoleOutput) {
        consoleOutput.innerHTML = '';
    }
}

function scrollConsoleToBottom() {
    const consoleOutput = document.getElementById('consoleOutput');
    if (consoleOutput) {
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
}

function parseAndDisplayConsoleOutput(output) {
    if (!output) {
        addConsoleLine('No output received from backtest', 'error');
        return;
    }

    console.log('Raw output received:', output); // Debug logging

    // Split output into lines and process each one
    const lines = output.split('\n').filter(line => line.trim());

    console.log('Parsed lines:', lines); // Debug logging

    if (lines.length === 0) {
        addConsoleLine('Output received but no lines found', 'error');
        return;
    }

    for (const line of lines) {
        let type = 'default';

        // Determine line type based on content
        if (line.includes('[PROGRESS]')) {
            type = 'progress';
        } else if (line.includes('[STATUS]')) {
            type = 'status';
        } else if (line.includes('[API]')) {
            type = 'api';
        } else if (line.includes('[MODEL]')) {
            type = 'model';
        } else if (line.includes('[BET]')) {
            type = 'bet';
        } else if (line.includes('[COMPLETE]')) {
            type = 'complete';
        } else if (line.includes('[INIT]')) {
            type = 'status';
        } else if (line.includes('[WEB]')) {
            type = 'status';
        } else if (line.toLowerCase().includes('error') || line.toLowerCase().includes('failed')) {
            type = 'error';
        }

        // Clean up the line by removing the prefix tags for display
        let displayText = line.replace(/^\[.*?\]\s*/, '');
        console.log('Adding line:', displayText, 'type:', type); // Debug logging
        addConsoleLine(displayText, type);
    }
}

// Utility functions for future chart implementation
function createEquityChart(data) {
    // Placeholder for equity curve chart
    console.log('Creating equity chart with data:', data);
}

function createCalibrationChart(data) {
    // Placeholder for calibration chart
    console.log('Creating calibration chart with data:', data);
}

// Export functions for potential future use
window.BacktestingUI = {
    loadBacktestResults,
    displayLatestResults,
    displayComparisonResults,
    setRunningState
};
