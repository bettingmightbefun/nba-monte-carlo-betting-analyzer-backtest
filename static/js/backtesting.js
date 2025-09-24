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

    const payload = {
        seasons: document.getElementById('seasons').value,
        dataset: document.getElementById('dataset').value,
        simulations: document.getElementById('simulations').value,
        minEdge: document.getElementById('minEdge').value
    };

    setRunningState(true);

    let completionEvent = null;

    try {
        const response = await fetch('/api/backtesting/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        if (!response.body) {
            throw new Error('Streaming response not supported in this browser');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let cancelRequested = false;

        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const rawLine of lines) {
                if (!rawLine.trim()) {
                    continue;
                }

                let eventData = null;
                try {
                    eventData = JSON.parse(rawLine);
                } catch (parseError) {
                    addConsoleLine(`Malformed stream chunk: ${rawLine}`, 'error');
                    continue;
                }

                const { event: eventType } = eventData;
                switch (eventType) {
                    case 'status':
                        if (eventData.message) {
                            addConsoleLine(eventData.message, 'status');
                        }
                        break;
                    case 'output':
                        if (eventData.line) {
                            handleConsoleLine(eventData.line);
                        }
                        break;
                    case 'progress':
                        if (typeof eventData.percent === 'number') {
                            updateProgressBar(eventData.percent, eventData.message);
                        }
                        break;
                    case 'error':
                        if (eventData.message) {
                            addConsoleLine(eventData.message, 'error');
                        }
                        if (!completionEvent) {
                            showErrorMessage(eventData.message || 'Backtest encountered an error.');
                        }
                        break;
                    case 'completed':
                        completionEvent = eventData;
                        cancelRequested = true;
                        if (completionEvent.success) {
                            showSuccessMessage(completionEvent.message || 'Backtest completed successfully!');
                        } else {
                            showErrorMessage(completionEvent.message || 'Backtest failed.');
                        }
                        break;
                    default:
                        addConsoleLine(`Unknown event: ${rawLine}`, 'status');
                }
            }

            if (cancelRequested) {
                await reader.cancel();
                break;
            }
        }

        if (buffer.trim()) {
            try {
                const leftoverEvent = JSON.parse(buffer);
                if (leftoverEvent.event === 'output' && leftoverEvent.line) {
                    handleConsoleLine(leftoverEvent.line);
                } else if (leftoverEvent.event === 'completed') {
                    completionEvent = leftoverEvent;
                }
            } catch (error) {
                // Ignore trailing parse errors
            }
        }

        if (!completionEvent) {
            completionEvent = { success: false, message: 'Backtest did not complete.' };
            showErrorMessage(completionEvent.message);
        }

        if (completionEvent.success) {
            setTimeout(() => {
                loadBacktestResults();
            }, 500);
        }
    } catch (error) {
        addConsoleLine(`ERROR: ${error.message}`, 'error');
        showErrorMessage(`Error running backtest: ${error.message}`);
        if (!completionEvent) {
            completionEvent = { success: false, message: error.message };
        }
    } finally {
        const wasSuccessful = completionEvent && completionEvent.success;
        updateProgressBar(wasSuccessful ? 100 : 0, completionEvent ? completionEvent.message : null);
        setRunningState(false, {
            success: wasSuccessful,
            message: completionEvent ? completionEvent.message : undefined,
        });
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
function setRunningState(isRunning, options = {}) {
    const runButton = document.getElementById('runButton');
    const progressContainer = document.getElementById('progressContainer');
    const consoleContainer = document.getElementById('consoleContainer');

    if (isRunning) {
        runButton.disabled = true;
        runButton.textContent = 'Running...';
        progressContainer.classList.remove('hidden');
        consoleContainer.classList.remove('hidden');
        updateProgressBar(0, 'Running backtest...');

        clearConsole();
        addConsoleLine('Starting backtest execution...', 'status');
    } else {
        runButton.disabled = false;
        runButton.textContent = '🚀 Run Backtest';
        const { success = true, message } = options;
        if (success) {
            updateProgressBar(100, message || 'Completed!');
        } else {
            updateProgressBar(0, message || 'Failed');
        }

        // Hide progress and console after a delay
        setTimeout(() => {
            progressContainer.classList.add('hidden');
            consoleContainer.classList.add('hidden');
        }, 3000);
    }
}

function updateProgressBar(percent, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (!progressFill || !progressText) {
        return;
    }

    if (typeof percent === 'number' && !Number.isNaN(percent)) {
        const clamped = Math.max(0, Math.min(100, percent));
        progressFill.style.width = `${clamped}%`;
    }

    if (typeof message === 'string' && message.trim()) {
        const cleaned = message.replace(/^\[.*?\]\s*/, '').trim();
        progressText.textContent = cleaned || 'Running backtest...';
    } else if (!progressText.textContent) {
        progressText.textContent = 'Running backtest...';
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

function handleConsoleLine(line) {
    if (!line) {
        return;
    }

    let type = 'default';
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

    const displayText = line.replace(/^\[.*?\]\s*/, '').trim() || line;
    addConsoleLine(displayText, type);

    if (type === 'progress') {
        const match = line.match(/\[PROGRESS\]\s+([\d.]+)%/);
        if (match) {
            const percent = parseFloat(match[1]);
            if (!Number.isNaN(percent)) {
                updateProgressBar(percent, displayText);
            }
        }
    } else if (line.includes('[COMPLETE]')) {
        updateProgressBar(100, displayText);
    }
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

    const lines = output.split('\n').filter(line => line.trim());

    if (lines.length === 0) {
        addConsoleLine('Output received but no lines found', 'error');
        return;
    }

    for (const line of lines) {
        handleConsoleLine(line);
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
