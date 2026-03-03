/**
 * Batch Results Page
 */

$(document).ready(function() {
    loadAnalysisResults();
    
    $('#exportBtn').click(function() {
        exportResults();
    });
    
    $('#trendClose').click(function() {
        $('#trendModal').hide();
    });
    
    $(window).click(function(event) {
        if (event.target == $('#trendModal')[0]) {
            $('#trendModal').hide();
        }
    });
});

let stockInfoMap = {};
let currentResultId = null;

async function loadAnalysisResults() {
    const urlParams = new URLSearchParams(window.location.search);
    const resultId = urlParams.get('id');
    currentResultId = resultId;
    
    if (!resultId) {
        const resultsData = localStorage.getItem('batchAnalysisResults');
        if (!resultsData) {
            showError('No results found, please run batch analysis again');
            return;
        }
        
        try {
            const results = JSON.parse(resultsData);
            buildStockInfoMap(results);
            seedAnalysisHistory(results);
            displayResults(results);
        } catch (error) {
            console.error('Parse error:', error);
            showError('Result data format error');
        }
        return;
    }
    
    try {
        const response = await api.getBatchResults(resultId);
        
        if (response.success) {
            const results = response.data;
            buildStockInfoMap(results);
            seedAnalysisHistory(results);
            displayResults(results);
        } else {
            showError('Failed to get results: ' + response.message);
        }
    } catch (error) {
        console.error('Fetch error:', error);
        showError('Failed to get results, please run batch analysis again');
    }
}

function buildStockInfoMap(results) {
    stockInfoMap = {};
    if (results.stock_info && Array.isArray(results.stock_info)) {
        results.stock_info.forEach(item => {
            stockInfoMap[item.code] = item;
        });
    }
}

function displayResults(results) {
    const {
        buySignals,
        sellSignals,
        neutralSignals,
        totalStocks,
        analysisResults,
        analysisTime
    } = results;
    
    $('#totalStocks').text(totalStocks);
    $('#buySignals').text(buySignals);
    $('#sellSignals').text(sellSignals);
    $('#neutralSignals').text(neutralSignals);
    
    analysisResults.sort((a, b) => b.score - a.score);
    
    displaySignalTable('buySignalsTable', analysisResults.filter(r => r.signalType === 'buy'));
    
    displaySignalTable('sellSignalsTable', analysisResults.filter(r => r.signalType === 'sell'));
    
    displayAllResultsTable(analysisResults);
}

function seedAnalysisHistory(results) {
    try {
        if (currentResultId) {
            const seededKey = `seeded_${currentResultId}`;
            if (localStorage.getItem(seededKey)) {
                return;
            }
            localStorage.setItem(seededKey, '1');
        }

        const analysisResults = results.analysisResults || [];
        if (!Array.isArray(analysisResults) || analysisResults.length === 0) return;

        const analysisHistory = JSON.parse(localStorage.getItem('analysisHistory') || '{}');
        const timestamp = (results.analysisTime && !isNaN(new Date(results.analysisTime)))
            ? new Date(results.analysisTime).toISOString()
            : new Date().toISOString();

        for (const item of analysisResults) {
            const code = item.stockCode;
            if (!code) continue;
            if (!analysisHistory[code]) analysisHistory[code] = [];

            const a = item.analysis || {};
            const compact = {
                stock_code: a.stock_code,
                period: a.period,
                trend_conclusion: a.trend_conclusion,
                detailed_summary: a.detailed_summary,
                technical_indicators: Array.isArray(a.technical_indicators) ? a.technical_indicators.slice(0, 20) : [],
                candlestick_patterns: Array.isArray(a.candlestick_patterns) ? a.candlestick_patterns.slice(0, 20) : [],
                market_environment: a.market_environment || {}
            };

            analysisHistory[code].push({
                timestamp: timestamp,
                analysis: compact
            });

            if (analysisHistory[code].length > 10) {
                analysisHistory[code] = analysisHistory[code].slice(-10);
            }
        }

        try {
            localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
        } catch (e) {
            try {
                Object.keys(analysisHistory).forEach(code => {
                    const arr = Array.isArray(analysisHistory[code]) ? analysisHistory[code] : [];
                    if (arr.length > 5) analysisHistory[code] = arr.slice(-5);
                });
                localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
            } catch (e2) {
                console.error('Seed history failed:', e2);
            }
        }
    } catch (e) {
        console.error('Seed history error:', e);
    }
}

function displaySignalTable(tableId, results) {
    const tbody = $(`#${tableId} tbody`);
    tbody.empty();
    
    for (let result of results) {
        const analysis = result.analysis;
        const trendChartId = `trend-${result.stockCode}-${Date.now()}`;
        const name = (stockInfoMap[result.stockCode] && stockInfoMap[result.stockCode].name) ? stockInfoMap[result.stockCode].name : result.stockCode;
        
        const row = `
            <tr>
                <td>${result.stockCode}</td>
                <td>${name}</td>
                <td class="score-${getScoreClass(result.score)}">
                    <span class="score-value clickable" onclick="showScoreDetails('${result.stockCode}', ${result.score}, ${JSON.stringify(result.analysis).replace(/"/g, '&quot;').replace(/'/g, '&#39;')})">${result.score}</span>
                </td>
                <td>${getMainSignals(analysis)}</td>
                <td class="trend-cell">
                    <div id="${trendChartId}" class="score-trend-chart"></div>
                </td>
                <td>
                    <a href="/?stock=${result.stockCode}" class="action-btn view-btn" target="_blank">View</a>
                </td>
            </tr>
        `;
        tbody.append(row);
        
        drawScoreTrendChart(trendChartId, result.stockCode);
    }
}

function displayAllResultsTable(analysisResults) {
    const tbody = $('#allResultsTable tbody');
    tbody.empty();
    
    for (let result of analysisResults) {
        const analysis = result.analysis;
        const trendChartId = `trend-${result.stockCode}-${Date.now()}`;
        const name = (stockInfoMap[result.stockCode] && stockInfoMap[result.stockCode].name) ? stockInfoMap[result.stockCode].name : result.stockCode;
        
        const row = `
            <tr>
                <td>${result.stockCode}</td>
                <td>${name}</td>
                <td class="score-${getScoreClass(result.score)}">
                    <span class="score-value clickable" onclick="showScoreDetails('${result.stockCode}', ${result.score}, ${JSON.stringify(result.analysis).replace(/"/g, '&quot;').replace(/'/g, '&#39;')})">${result.score}</span>
                </td>
                <td>${analysis.trend_conclusion || 'No Data'}</td>
                <td>${getTechnicalSignals(analysis)}</td>
                <td>${getPatternSignals(analysis)}</td>
                <td class="trend-cell">
                    <div id="${trendChartId}" class="score-trend-chart"></div>
                </td>
                <td>
                    <a href="/?stock=${result.stockCode}" class="action-btn view-btn" target="_blank">View</a>
                </td>
            </tr>
        `;
        tbody.append(row);
        
        drawScoreTrendChart(trendChartId, result.stockCode);
    }
}

function getScoreClass(score) {
    score = parseFloat(score) || 0;
    if (score >= 6.0) return 'score-excellent';
    if (score >= 4.5) return 'score-good';
    if (score >= 3.0) return 'score-average';
    if (score >= 1.5) return 'score-poor';
    return 'score-very-poor';
}

function getMainSignals(analysis) {
    const signals = [];
    const technicalSignals = analysis.technical_indicators || [];
    for (let signal of technicalSignals.slice(0, 3)) {
        if (signal.signal && (signal.signal.includes('Bullish') || signal.signal.includes('Bearish'))) {
            signals.push(signal.indicator + ':' + signal.signal);
        }
    }
    const patterns = analysis.candlestick_patterns || [];
    for (let pattern of patterns.slice(0, 2)) {
        if (pattern.status && (pattern.status.includes('Bullish') || pattern.status.includes('Bearish'))) {
            signals.push(pattern.pattern + ':' + pattern.status);
        }
    }
    return signals.slice(0, 3).join(', ');
}

function getTechnicalSignals(analysis) {
    const signals = analysis.technical_indicators || [];
    return signals.map(s => `${s.indicator}:${s.signal}`).slice(0, 3).join(', ');
}

function getPatternSignals(analysis) {
    const patterns = analysis.candlestick_patterns || [];
    return patterns
        .filter(p => p.status && !p.status.includes('Not Detected') && !p.status.includes('Not Formed') && !p.status.includes('Weak'))
        .map(p => `${p.pattern}:${p.status}`)
        .slice(0, 3)
        .join(', ');
}

function exportResults() {
    const resultsData = localStorage.getItem('batchAnalysisResults');
    if (!resultsData) {
        showError('No data to export');
        return;
    }
    
    const results = JSON.parse(resultsData);
    const analysisResults = results.analysisResults || [];
    
    if (analysisResults.length === 0) {
        showError('No data to export');
        return;
    }
    
    let csvContent = 'Stock Code,Name,Score,Trend,Signals,Patterns\n';
    
    for (let result of analysisResults) {
        const analysis = result.analysis;
        const name = (stockInfoMap[result.stockCode] && stockInfoMap[result.stockCode].name) ? stockInfoMap[result.stockCode].name : result.stockCode;
        const row = [
            result.stockCode,
            name,
            result.score,
            analysis.trend_conclusion || 'No Data',
            getTechnicalSignals(analysis),
            getPatternSignals(analysis)
        ];
        csvContent += row.map(field => `"${field}"`).join(',') + '\n';
    }
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `Trend_Analysis_Results_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showError(message) {
    $('#errorMessage').text(message).show();
    setTimeout(() => {
        $('#errorMessage').hide();
    }, 5000);
}

function drawScoreTrendChart(chartId, stockCode) {
    api.getScoreHistory(stockCode, 60)
        .done(function(resp) {
            if (!resp || !resp.success) {
                $(`#${chartId}`).html('<div class="no-trend-data">No Data</div>');
                $(`#${chartId}`).off('click').on('click', function() { showNoDataModal(stockCode); });
                return;
            }
            let rows = Array.isArray(resp.history) ? resp.history : [];
            const scoreHistory = rows.map(r => ({
                timestamp: r.timestamp,
                finalScore: parseFloat(r.final_score) || 0,
                breakdown: (function(){ try { return r.breakdown ? JSON.parse(r.breakdown) : {}; } catch(e){ return {}; } })(),
                details: (function(){ try { return r.details ? JSON.parse(r.details) : {}; } catch(e){ return {}; } })()
            }));

            if (!scoreHistory || scoreHistory.length === 0) {
                $(`#${chartId}`).html('<div class="no-trend-data">No Data</div>');
                $(`#${chartId}`).off('click').on('click', function() { showNoDataModal(stockCode); });
                return;
            }
    
            scoreHistory.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
            const lookbackDays = 30;
            const since = new Date();
            since.setDate(since.getDate() - lookbackDays);
            let recentScores = scoreHistory.filter(score => new Date(score.timestamp) >= since);
            if (recentScores.length === 0) {
                recentScores = scoreHistory;
            }
    
            let displayData = recentScores;
            
            if (recentScores.length > 5) {
                const step = Math.floor(recentScores.length / 5);
                displayData = [];
                for (let i = 0; i < recentScores.length; i += step) {
                    displayData.push(recentScores[i]);
                }
                if (displayData[displayData.length - 1] !== recentScores[recentScores.length - 1]) {
                    displayData.push(recentScores[recentScores.length - 1]);
                }
            }
    
            const xValues = displayData.map((_, index) => index + 1);
            const scores = displayData.map(score => score.finalScore);
    
            const minScore = Math.min(...scores);
            const maxScore = Math.max(...scores);
            const scoreRange = maxScore - minScore;
    
            const yMin = scoreRange === 0 ? minScore - 0.5 : minScore - scoreRange * 0.1;
            const yMax = scoreRange === 0 ? maxScore + 0.5 : maxScore + scoreRange * 0.1;
    
            const trace = {
                x: xValues,
                y: scores,
                type: displayData.length === 1 ? 'markers' : 'lines+markers',
                name: 'Score',
                line: {
                    color: '#667eea',
                    width: 2
                },
                marker: {
                    size: displayData.length === 1 ? 4 : 3,
                    color: '#667eea'
                },
                fill: displayData.length > 1 ? 'tonexty' : 'none',
                fillcolor: 'rgba(102, 126, 234, 0.1)'
            };
    
            const layout = {
                margin: { l: 15, r: 15, t: 15, b: 15 },
                xaxis: {
                    showgrid: false,
                    showticklabels: false,
                    zeroline: false,
                    range: [0.5, displayData.length + 0.5]
                },
                yaxis: {
                    showgrid: false,
                    showticklabels: false,
                    zeroline: false,
                    range: [yMin, yMax]
                },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                showlegend: false,
                hovermode: false
            };
    
            const config = {
                responsive: true,
                displayModeBar: false,
                staticPlot: true
            };
    
            Plotly.newPlot(chartId, [trace], layout, config);
    
            $(`#${chartId}`).off('click').on('click', function() {
                showTrendDetailModal(stockCode, scoreHistory);
            });
        })
        .fail(function() {
            $(`#${chartId}`).html('<div class="no-trend-data">No Data</div>');
            $(`#${chartId}`).off('click').on('click', function() { showNoDataModal(stockCode); });
        });
}

function showTrendDetailModal(stockCode, scoreHistory) {
    const sortedHistory = [...scoreHistory].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    const dates = sortedHistory.map(score => {
        const date = new Date(score.timestamp);
        return date.toLocaleString('en-US', { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    });
    
    const scores = sortedHistory.map(score => score.finalScore);
    
    const trace = {
        x: dates,
        y: scores,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Score',
        line: {
            color: '#667eea',
            width: 3
        },
        marker: {
            size: 8,
            color: '#667eea',
            line: {
                color: '#ffffff',
                width: 2
            }
        },
        fill: 'tonexty',
        fillcolor: 'rgba(102, 126, 234, 0.1)'
    };
    
    const layout = {
        xaxis: {
            title: 'Time',
            gridcolor: '#f1f3f4',
            zeroline: false
        },
        yaxis: {
            title: 'Score',
            gridcolor: '#f1f3f4',
            zeroline: false
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        font: {
            family: 'Arial, sans-serif',
            size: 12
        },
        margin: {
            l: 60,
            r: 40,
            t: 60,
            b: 60
        },
        hovermode: 'closest',
        showlegend: false
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    $("#trendModal .trend-modal-header").html(`
        <h3 style='flex:1;text-align:left;margin:0;font-size:1.3em;font-weight:600;'>Score Trend - ${stockInfoMap[stockCode] ? stockInfoMap[stockCode].name : stockCode} - ${stockCode}</h3>
        <span class="trend-close" id="trendClose">&times;</span>
    `);
    
    $('#trendClose').off('click').on('click', function() {
        $('#trendModal').hide();
    });

    const modalContent = `
        <div class="trend-chart-container">
            <div id="trendChartLarge" class="trend-chart-large"></div>
        </div>
        <div class="trend-history-table">
            <h4>History Details</h4>
            <div class="table-container">
                <div class="scrollable-table">
                    <table class="data-table" id="trendHistoryTable">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Score</th>
                                <th>Trend</th>
                                <th>Tech</th>
                                <th>Pattern</th>
                                <th>Vol Mod</th>
                                <th>Signal</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${generateTrendHistoryRows(scoreHistory)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    $('#trendModalBody').html(modalContent);
    $('#trendModal').show();
    
    setTimeout(() => {
        Plotly.newPlot('trendChartLarge', [trace], layout, config);
    }, 100);
}

function generateTrendHistoryRows(scoreHistory) {
    let html = '';
    const sortedHistory = [...scoreHistory].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    sortedHistory.forEach((score, index) => {
        const date = new Date(score.timestamp);
        const dateStr = date.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const scoreClass = getScoreClass(score.finalScore);
        const breakdown = score.breakdown || {};
        const trend = typeof breakdown.trendScore === 'number' ? breakdown.trendScore : 0;
        const technical = typeof breakdown.technicalScore === 'number' ? breakdown.technicalScore : 0;
        const pattern = typeof breakdown.patternScore === 'number' ? breakdown.patternScore : 0;
        const volumeModifier = typeof breakdown.volumeModifier === 'number' ? breakdown.volumeModifier : 1.0;
        const signalType = getSignalType(score.finalScore);
        const signalText = getSignalTypeText(signalType);
        
        html += `
            <tr>
                <td>${dateStr}</td>
                <td class="${scoreClass}">${score.finalScore.toFixed(1)}</td>
                <td class="${getScoreColor(trend)}">${trend.toFixed(1)}</td>
                <td class="${getScoreColor(technical)}">${technical.toFixed(1)}</td>
                <td class="${getScoreColor(pattern)}">${pattern.toFixed(1)}</td>
                <td>×${volumeModifier.toFixed(2)}</td>
                <td class="signal-${signalType}">${signalText}</td>
            </tr>
        `;
    });
    
    return html;
}

function getTrendText(trendConclusion) {
    if (!trendConclusion) return '--';
    return trendConclusion.length > 30 ? trendConclusion.substring(0, 30) + '...' : trendConclusion;
}

function getTechnicalText(technicalIndicators) {
    if (!technicalIndicators || technicalIndicators.length === 0) return '--';
    
    const signals = technicalIndicators
        .filter(item => item.signal && (item.signal.includes('Bullish') || item.signal.includes('Bearish')))
        .slice(0, 2)
        .map(item => `${item.indicator}:${item.signal}`);
    
    return signals.length > 0 ? signals.join(', ') : '--';
}

function getPatternText(patterns) {
    if (!patterns || patterns.length === 0) return '--';
    
    const validPatterns = patterns
        .filter(pattern => pattern.status && !pattern.status.includes('Not Detected'))
        .slice(0, 2)
        .map(pattern => `${pattern.pattern}:${pattern.status}`);
    
    return validPatterns.length > 0 ? validPatterns.join(', ') : '--';
}

function getScoreColor(score) {
    if (score > 0) return 'positive';
    if (score < 0) return 'negative';
    return 'neutral';
}

function closeTrendModal() {
    $('#trendModal').hide();
}

function showNoDataModal(stockCode) {
    const modalContent = `
        <div class="trend-chart-container">
            <h4>No Score Data</h4>
            <div style="text-align: center; padding: 50px; color: #6c757d;">
                <p>No historical score data for this stock</p>
                <p>Please run individual or batch analysis to generate records</p>
            </div>
        </div>
    `;
    
    $('#trendModalBody').html(modalContent);
    $('#trendModal').show();
}

function showScoreDetails(stockCode, score, analysis) {
    try {
        if (typeof score === 'object' && score.finalScore !== undefined) {
            score = score.finalScore;
        }
        score = parseFloat(score) || 0;
        
        if (typeof analysis === 'string') {
            analysis = JSON.parse(analysis);
        }
        
        if (typeof ScoreEngine !== 'undefined') {
            const scoreResult = ScoreEngine.calculateFinalScore(analysis);
            
            if (typeof ScoreDetails !== 'undefined') {
                const stockName = (stockInfoMap[stockCode] && stockInfoMap[stockCode].name) ? 
                                  stockInfoMap[stockCode].name : stockCode;
                ScoreDetails.showScoreDetails(scoreResult, stockCode, stockName);
            } else {
                showSimpleScoreDetails(stockCode, score, analysis);
            }
        } else {
            showSimpleScoreDetails(stockCode, score, analysis);
        }
    } catch (error) {
        showSimpleScoreDetails(stockCode, score, analysis);
    }
}

function showSimpleScoreDetails(stockCode, score, analysis) {
    score = parseFloat(score) || 0;
    const stockName = (stockInfoMap[stockCode] && stockInfoMap[stockCode].name) ? 
                      stockInfoMap[stockCode].name : stockCode;
    
    const modal = `
        <div class="modal fade" id="simpleScoreModal" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Score Details - ${stockName} - ${stockCode}</h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="score-card ${getScoreClass(score)}">
                                    <h3>Final Score</h3>
                                    <div class="score-value">${score.toFixed(1)}</div>
                                    <div class="score-level">${getScoreLevelText(getScoreClass(score))}</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="signal-card ${getSignalType(score)}">
                                    <h3>Signal Type</h3>
                                    <div class="signal-value">${getSignalTypeText(getSignalType(score))}</div>
                                    <div class="signal-description">${getSignalDescription(getSignalType(score))}</div>
                                </div>
                            </div>
                        </div>
                        <div class="analysis-details mt-4">
                            <h4>Analysis Details</h4>
                            <div class="detail-item">
                                <strong>Trend:</strong> ${analysis.trend_conclusion || 'No Data'}
                            </div>
                            <div class="detail-item">
                                <strong>Technical:</strong> ${getTechnicalSignals(analysis)}
                            </div>
                            <div class="detail-item">
                                <strong>Pattern:</strong> ${getPatternSignals(analysis)}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(modal);
    $('#simpleScoreModal').modal('show');
    
    $('#simpleScoreModal').on('hidden.bs.modal', function() {
        $(this).remove();
    });
}

function getScoreLevelText(level) {
    const texts = {
        'score-excellent': 'Excellent',
        'score-good': 'Good',
        'score-average': 'Average',
        'score-poor': 'Poor',
        'score-very-poor': 'Very Poor'
    };
    return texts[level] || 'Unknown';
}

function getSignalType(score) {
    score = parseFloat(score) || 0;
    if (score >= 3.5) return 'buy';
    if (score < 2.0) return 'sell';
    return 'neutral';
}

function getSignalTypeText(type) {
    const texts = {
        'buy': 'Buy Signal',
        'sell': 'Sell Signal',
        'neutral': 'Neutral Signal'
    };
    return texts[type] || 'Unknown';
}

function getSignalDescription(type) {
    const descriptions = {
        'buy': 'Buy recommended, technical bullish',
        'sell': 'Sell recommended, technical bearish',
        'neutral': 'Wait recommended, await signals'
    };
    return descriptions[type] || '';
}