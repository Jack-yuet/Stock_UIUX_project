/**
 * Batch Stock Trend Analysis
 */

// Global Variables
let stockList = [];
let analysisResults = [];
let stockInfoMap = {};

$(document).ready(function() {
    if (typeof api === 'undefined') {
        console.error('API module not loaded');
        showError('System Error: API module not loaded');
        return;
    }
    
    loadStockList();
    
    $('#analyzeBtn').click(function() {
        if (stockList && stockList.length > 0) {
            startBatchAnalysis();
        } else {
            showError('Stock list is empty, please check stock_list.txt');
        }
    });
});

/**
 * Load Stock List
 */
function loadStockList() {
    api.getStockList()
        .done(function(data) {
            if (data.success) {
                stockList = data.stock_list || [];
                stockInfoMap = {};
                (data.stock_info || []).forEach(item => {
                    stockInfoMap[item.code] = item;
                });
                
                $('#stockCount').text(data.count || stockList.length);
                updateStockListDisplay(stockList);
            } else {
                showError(data.message);
                $('#stockCount').text('0');
                $('#stockList').text('Load Failed');
                stockList = [];
            }
        })
        .fail(function(error) {
            showError('Failed to load stock list, check network connection');
            $('#stockCount').text('0');
            $('#stockList').text('Load Failed');
            stockList = [];
        });
}

/**
 * Start Batch Analysis
 */
async function startBatchAnalysis() {
    if (!stockList || stockList.length === 0) {
        showError('Stock list is empty, please check stock_list.txt');
        return;
    }
    
    $('#progressSection').show();
    $('#resultsSection').hide();
    $('#errorMessage').hide();
    
    const totalStocks = stockList.length;
    let buySignals = 0;
    let sellSignals = 0;
    let neutralSignals = 0;
    
    analysisResults = [];
    
    // Get Market Environment
    let marketEnvironment = null;
    try {
        $('#progressText').text('Fetching market environment data...');
        $('#currentStock').text('Fetching index data...');
        
        const marketResult = await api.getMarketEnvironment('3mo');
        if (marketResult.success) {
            marketEnvironment = marketResult.market_environment;
            console.log('Market environment fetched:', marketEnvironment);
        } else {
            console.warn('Failed to fetch market environment, using defaults');
            marketEnvironment = {'factor': 0, 'regime': 'neutral', 'details': {}};
        }
    } catch (error) {
        console.error('Failed to fetch market environment:', error);
        marketEnvironment = {'factor': 0, 'regime': 'neutral', 'details': {}};
    }
    
    // Analyze Stocks
    for (let i = 0; i < stockList.length; i++) {
        const stockCode = stockList[i];
        
        const progress = ((i + 1) / totalStocks) * 100;
        $('#progressFill').css('width', progress + '%');
        const name = (stockInfoMap[stockCode] && stockInfoMap[stockCode].name) ? stockInfoMap[stockCode].name : stockCode;
        $('#progressText').text(`Progress: ${i + 1}/${totalStocks}`);
        $('#currentStock').text(`Analyzing: ${stockCode} ${name}`);
        
        try {
            const result = await api.getTrendAnalysis(stockCode, '1y', marketEnvironment);
            
            if (result.success) {
                const analysis = result;
                
                recordAnalysisHistory(stockCode, analysis);
                try {
                    if (typeof api !== 'undefined' && api.recordScoreHistory) {
                        api.recordScoreHistory(stockCode, analysis);
                    }
                } catch (e) {
                    console.error('Failed to record scoreHistory:', e);
                }
                
                const scoreResult = api.calculateFinalScore(analysis);
                const payloadScore = (typeof scoreResult === 'object' && scoreResult !== null) ? scoreResult : (parseFloat(scoreResult) || 0);
                
                try {
                    await api.recordScoreToBackend(stockCode, analysis, payloadScore);
                } catch (error) {
                    console.error(`Failed to record score: ${stockCode}`, error);
                }
                
                const score = (typeof scoreResult === 'object' && scoreResult !== null) ? scoreResult.finalScore : (parseFloat(scoreResult) || 0);
                let signalType = 'neutral';
                if (score >= 5.0) {
                    signalType = 'buy';
                    buySignals++;
                } else if (score < 2.0) {
                    signalType = 'sell';
                    sellSignals++;
                } else {
                    neutralSignals++;
                }
                
                analysisResults.push({
                    stockCode: stockCode,
                    analysis: analysis,
                    score: score,
                    signalType: signalType
                });
            } else {
                console.error(`Analysis failed for ${stockCode}:`, result.message);
            }
        } catch (error) {
            console.error(`Analysis failed for ${stockCode}:`, error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 800));
    }
    
    $('#progressText').text('Analysis Completed!');
    $('#currentStock').text('');
    
    const resultsData = {
        buySignals: buySignals,
        sellSignals: sellSignals,
        neutralSignals: neutralSignals,
        totalStocks: analysisResults.length,
        analysisResults: analysisResults,
        analysisTime: new Date().toLocaleString(),
        stock_info: Object.values(stockInfoMap),
        marketEnvironment: marketEnvironment
    };
    
    try {
        $('#progressText').text('Saving results...');
        const saveResult = await api.saveBatchResults(resultsData);
        
        if (saveResult.success) {
            window.location.href = `/batch_results?id=${saveResult.result_id}`;
        } else {
            alert('Failed to save results: ' + saveResult.message);
        }
    } catch (error) {
        console.error('Failed to save results:', error);
        alert('Failed to save results, please try again');
    }
}

/**
 * Export Results
 */
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
    
    let csvContent = 'Stock Code,Name,Price,Change,Score,Trend,Signals,Patterns\n';
    
    for (let result of analysisResults) {
        const analysis = result.analysis;
        const row = [
            result.stockCode,
            (stockInfoMap[result.stockCode] && stockInfoMap[result.stockCode].name) || 'Unknown',
            analysis.current_price || 0,
            (analysis.price_change_pct || 0) + '%',
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

function getTechnicalSignals(analysis) {
    const signals = analysis.technical_indicators || [];
    return signals.map(s => `${s.indicator}:${s.signal}`).slice(0, 3).join(', ');
}

function getPatternSignals(analysis) {
    const patterns = analysis.candlestick_patterns || [];
    return patterns.map(p => `${p.pattern}:${p.status}`).slice(0, 3).join(', ');
}

function showError(message) {
    $('#errorMessage').text(message).show();
    setTimeout(() => {
        $('#errorMessage').hide();
    }, 5000);
}

function recordAnalysisHistory(stockCode, analysis) {
    try {
        const analysisHistory = JSON.parse(localStorage.getItem('analysisHistory') || '{}');
        
        if (!analysisHistory[stockCode]) {
            analysisHistory[stockCode] = [];
        }
        
        analysisHistory[stockCode].push({
            timestamp: new Date().toISOString(),
            analysis: analysis
        });
        
        if (analysisHistory[stockCode].length > 10) {
            analysisHistory[stockCode] = analysisHistory[stockCode].slice(-10);
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
                console.warn('analysisHistory cleaned up');
            } catch (e2) {
                console.error('analysisHistory save failed:', e2);
            }
        }
    } catch (error) {
        console.error('Record history failed:', error);
    }
}

function updateStockListDisplay(stockList) {
    if (!Array.isArray(stockList)) return;
    const html = stockList.map(code => {
        const name = (stockInfoMap[code] && stockInfoMap[code].name) ? stockInfoMap[code].name : code;
        return `<span class="stock-code">${code} ${name}</span>`;
    }).join('');
    $('#stockList').html(html);
}