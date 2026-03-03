// Global Variables
let currentStockCode = ''; 
let currentKlineData = {}; 

// Page Load
$(document).ready(function() {
    // Enter key search
    $('#stockInput').keypress(function(e) {
        if (e.which == 13) {
            searchStock();
        }
    });
    
    // Clear error on focus
    $('#stockInput').focus(function() {
        $('#errorMsg').hide();
    });
    
    // Auto update chart on period change
    $('#periodSelect').change(function() {
        if (currentStockCode && currentKlineData) {
            Chart.displayKlineChart(currentKlineData, currentStockCode);
        }
    });
    
    // Check URL params
    const urlParams = new URLSearchParams(window.location.search);
    const stockParam = urlParams.get('stock');
    if (stockParam) {
        $('#stockInput').val(stockParam);
        searchStock();
    }
});

// Search Stock
function searchStock() {
    const stockName = $('#stockInput').val().trim();
    
    if (!stockName) {
        UI.showError('Please enter stock code');
        return;
    }
    
    const period = $('#periodSelect').val();
    
    // Loading state
    $('#searchBtn').prop('disabled', true).text('Searching...');
    $('#errorMsg').hide();
    $('#successMsg').hide();
    $('#stockData').hide();
    
    api.searchStock(stockName, period)
        .done(function(data) {
            console.log('API Response:', data);
            if (data.success) {
                currentStockCode = stockName;
                currentKlineData = data.kline_data;
                UI.showSuccess(`Successfully fetched data for ${data.basic_info.name}`);
                displayStockData(data);
            } else {
                console.error('API Error:', data.message);
                UI.showError(data.message);
            }
        })
        .fail(function(xhr, status, error) {
            console.error('Network Failed:', xhr.responseText, status, error);
            UI.showError('Network error, please try again later');
        })
        .always(function() {
            $('#searchBtn').prop('disabled', false).text('Search');
        });
}

// Update Period Data
function updatePeriodData() {
    if (!currentStockCode) {
        UI.showError('Please search stock code first');
        return;
    }
    
    const period = $('#periodSelect').val();
    
    $('#periodBtn').prop('disabled', true).text('Drawing...');
    $('#errorMsg').hide();
    
    $('#chartContent').show().html('<div class="loading">Drawing chart...</div>');
    
    api.searchStock(currentStockCode, period)
        .done(function(data) {
            if (data.success) {
                currentKlineData = data.kline_data;
                UI.showSuccess(`Successfully drawn ${Utils.getPeriodText(period)} chart for ${data.basic_info.name}`);
                UI.displayHistData(data.hist_data);
                Chart.displayKlineChart(currentKlineData, currentStockCode);
            } else {
                UI.showError(data.message);
            }
        })
        .fail(function() {
            UI.showError('Network error, please try again later');
        })
        .always(function() {
            $('#periodBtn').prop('disabled', false).text('Draw Chart');
        });
}

// Display Stock Data
function displayStockData(data) {
    console.log('Displaying stock data:', data);
    
    if (data.basic_info) {
        UI.displayBasicInfo(data.basic_info);
    } else {
        console.error('Missing basic info');
    }
    
    if (data.hist_data) {
        UI.displayHistData(data.hist_data);
    } else {
        console.error('Missing history data');
    }
    
    if (data.financial_data) {
        UI.displayFinancialData(data.financial_data, data.institutional_holders, currentStockCode);
    } else {
        console.error('Missing financial data');
    }
    
    $('#chartContent').hide();
    
    if (data.basic_info && data.basic_info.code) {
        getTrendAnalysis(data.basic_info.code);
    } else {
        console.error('Cannot get trend analysis, missing stock code');
    }
    
    $('#stockData').show();
}

// Get Trend Analysis
function getTrendAnalysis(stockCode) {
    const period = $('#periodSelect').val();
    
    UI.showTrendAnalysisLoading();
    
    api.getTrendAnalysis(stockCode, period)
        .done(function(data) {
            if (data.success) {
                UI.displayTrendAnalysis(data);
                UI.showSuccess('Trend Analysis Completed');
                
                try {
                    const scoreResult = api.calculateFinalScore(data);
                    const payloadScore = (typeof scoreResult === 'object' && scoreResult !== null) ? scoreResult : (parseFloat(scoreResult) || 0);
                    api.recordScoreToBackend(stockCode, data, payloadScore)
                        .fail(function(err) {
                            console.error('Failed to record score:', err);
                        });
                } catch (e) {
                    console.error('Failed to record score:', e);
                }
            } else {
                UI.hideTrendAnalysis();
                UI.showError(data.message);
            }
        })
        .fail(function() {
            UI.hideTrendAnalysis();
            UI.showError('Trend Analysis Failed, please try again later');
        })
        .always(function() {
            UI.hideTrendAnalysisLoading();
        });
}