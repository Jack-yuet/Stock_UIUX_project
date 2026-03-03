// API Module
const api = {
    // Search Stock
    searchStock: function(stockName, period) {
        return $.ajax({
            url: '/api/search',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 
                stock_name: stockName,
                period: period
            })
        });
    },
    
    // Get Kline Data
    getKlineData: function(stockCode, period, interval) {
        return $.ajax({
            url: `/api/kline_data/${stockCode}`,
            method: 'GET',
            data: {
                period: period,
                interval: interval
            }
        });
    },
    
    // Get Market Environment
    getMarketEnvironment: function(period) {
        return $.ajax({
            url: '/api/market_environment',
            method: 'GET',
            data: {
                period: period || '3mo'
            }
        });
    },
    
    // Get Trend Analysis
    getTrendAnalysis: function(stockCode, period, marketEnvironment) {
        const requestData = { 
            stock_code: stockCode,
            period: period
        };
        
        if (marketEnvironment) {
            requestData.market_environment = marketEnvironment;
        }
        
        return $.ajax({
            url: '/api/trend_analysis',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requestData)
        });
    },
    
    // Record Score to Backend
    recordScoreToBackend: function(stockCode, analysisResult, score) {
        return $.ajax({
            url: '/api/record_score',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                stock_code: stockCode,
                analysis_result: analysisResult,
                frontend_score: score
            })
        });
    },
    
    // Save Batch Results
    saveBatchResults: function(resultsData) {
        return $.ajax({
            url: '/api/save_batch_results',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(resultsData)
        });
    },
    
    // Get Batch Results
    getBatchResults: function(resultId) {
        return $.ajax({
            url: `/api/get_batch_results/${resultId}`,
            method: 'GET'
        });
    },
    
    // Get Score History (Backend Persistent)
    getScoreHistory: function(stockCode, days) {
        return $.ajax({
            url: `/api/score_history/${encodeURIComponent(stockCode)}`,
            method: 'GET',
            data: { days: days || 60 }
        });
    },

    // Model Info
    getModelInfo: function() {
        return $.ajax({
            url: '/api/model/info',
            method: 'GET'
        });
    },

    // Train Model
    trainModel: function(horizon, model) {
        return $.ajax({
            url: '/api/model/train',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ horizon: horizon || 10, model: model || 'logistic' })
        });
    },

    // Backtest Model
    backtestModel: function(horizon, model) {
        return $.ajax({
            url: '/api/model/backtest',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ horizon: horizon || 10, model: model || 'logistic' })
        });
    },
    
    // Get Stock List
    getStockList: function() {
        return $.ajax({
            url: '/api/get_stock_list',
            method: 'GET'
        });
    },
    
    // Record Score History (Local Storage)
    recordScoreHistory: function(stockCode, analysisResult) {
        try {
            const scoreResult = this.calculateFinalScore(analysisResult);
            let finalScore = 0;
            let breakdown = {};
            let details = {};
            if (typeof scoreResult === 'object' && scoreResult !== null && scoreResult.finalScore !== undefined) {
                finalScore = parseFloat(scoreResult.finalScore) || 0;
                breakdown = scoreResult.breakdown || {};
                details = scoreResult.details || {};
            } else {
                finalScore = parseFloat(scoreResult) || 0;
            }
            
            const compactAnalysis = (function(a){
                if (!a || typeof a !== 'object') return {};
                return {
                    stock_code: a.stock_code,
                    period: a.period,
                    trend_conclusion: a.trend_conclusion,
                    detailed_summary: a.detailed_summary,
                    technical_indicators: Array.isArray(a.technical_indicators) ? a.technical_indicators.slice(0, 20) : [],
                    candlestick_patterns: Array.isArray(a.candlestick_patterns) ? a.candlestick_patterns.slice(0, 20) : [],
                    market_environment: a.market_environment || {}
                };
            })(analysisResult);

            const scoreRecord = {
                timestamp: new Date().toISOString(),
                stockCode: stockCode,
                stockName: analysisResult.stock_name || '',
                finalScore: finalScore,
                breakdown: breakdown,
                details: details,
                trend_conclusion: analysisResult.trend_conclusion || '',
                technical_indicators: analysisResult.technical_indicators || [],
                candlestick_patterns: analysisResult.candlestick_patterns || [],
                support_resistance: analysisResult.support_resistance || [],
                detailed_summary: analysisResult.detailed_summary || '',
                analysis: compactAnalysis
            };
            
            const scoreHistory = JSON.parse(localStorage.getItem('scoreHistory') || '{}');

            const variants = [];
            const trimmedCode = (stockCode || '').trim();
            if (trimmedCode) {
                variants.push(trimmedCode);
                const dotIndex = trimmedCode.indexOf('.');
                if (dotIndex > 0) {
                    const plain = trimmedCode.substring(0, dotIndex);
                    if (plain && !variants.includes(plain)) variants.push(plain);
                }
            }

            const sixtyDaysAgo = new Date();
            sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60);

            for (const codeKey of variants) {
                if (!scoreHistory[codeKey]) {
                    scoreHistory[codeKey] = [];
                }
                scoreHistory[codeKey].push(scoreRecord);
                scoreHistory[codeKey] = scoreHistory[codeKey].filter(record => {
                    const recordDate = new Date(record.timestamp);
                    return recordDate >= sixtyDaysAgo;
                });
                if (scoreHistory[codeKey].length > 20) {
                    scoreHistory[codeKey] = scoreHistory[codeKey].slice(-20);
                }
            }
            
            this._safeSetItem('scoreHistory', scoreHistory, stockCode);
            
            console.log(`Score recorded: ${stockCode} - ${finalScore}`);
            
        } catch (error) {
            console.error('Failed to record score history:', error);
        }
    },
    
    // Calculate Final Score
    calculateFinalScore: function(analysisResult) {
        if (typeof ScoreEngine !== 'undefined') {
            return ScoreEngine.calculateFinalScore(analysisResult);
        } else {
            console.warn('ScoreEngine not loaded, using legacy mode');
            return this.calculateFinalScoreLegacy(analysisResult);
        }
    },
    
    // Legacy Score Calculation (Fallback)
    calculateFinalScoreLegacy: function(analysisResult) {
        let score = 0;
        
        const trendConclusion = analysisResult.trend_conclusion;
        if (trendConclusion) {
            if (trendConclusion.includes('Strong Bullish')) {
                score += 3;
            } else if (trendConclusion.includes('Bullish')) {
                score += 1.5;
            } else if (trendConclusion.includes('Bearish')) {
                score -= 1.5;
            } else if (trendConclusion.includes('Strong Bearish')) {
                score -= 3;
            }
        }
        
        const signals = analysisResult.technical_signals || {};
        let bullishCount = 0;
        let bearishCount = 0;
        
        for (const [indicator, signal] of Object.entries(signals)) {
            if (signal.includes('Bullish')) {
                score += 0.4;
                bullishCount++;
            } else if (signal.includes('Bearish')) {
                score -= 0.4;
                bearishCount++;
            }
        }
        
        if (bullishCount >= 4) {
            score += 0.5;
        } else if (bearishCount >= 4) {
            score -= 0.5;
        }
        
        return Math.max(0, Math.round(score * 10) / 10);
    },

    // Safe Set Item to LocalStorage
    _safeSetItem: function(key, objValue, currentCode) {
        try {
            localStorage.setItem(key, JSON.stringify(objValue));
        } catch (e) {
            try {
                if (e && (e.name === 'QuotaExceededError' || e.code === 22)) {
                    this._pruneScoreHistory(objValue, currentCode);
                    localStorage.setItem(key, JSON.stringify(objValue));
                    console.warn('LocalStorage quota exceeded, pruned old history');
                } else {
                    throw e;
                }
            } catch (e2) {
                console.error('LocalStorage write failed:', e2);
            }
        }
    },

    // Prune Score History
    _pruneScoreHistory: function(scoreHistoryObj, currentCode) {
        try {
            if (!scoreHistoryObj || typeof scoreHistoryObj !== 'object') return;
            const codes = Object.keys(scoreHistoryObj);
            for (const code of codes) {
                const arr = Array.isArray(scoreHistoryObj[code]) ? scoreHistoryObj[code] : [];
                if (arr.length > 20) {
                    scoreHistoryObj[code] = arr.slice(-20);
                }
            }
            const totalCount = codes.reduce((sum, c) => sum + (Array.isArray(scoreHistoryObj[c]) ? scoreHistoryObj[c].length : 0), 0);
            if (totalCount < 1000) return;

            const all = [];
            for (const code of codes) {
                const arr = Array.isArray(scoreHistoryObj[code]) ? scoreHistoryObj[code] : [];
                for (let i = 0; i < arr.length; i++) {
                    all.push({ code, idx: i, ts: new Date(arr[i].timestamp).getTime() || 0 });
                }
            }
            all.sort((a, b) => a.ts - b.ts);

            let removed = 0;
            for (const item of all) {
                const list = scoreHistoryObj[item.code];
                if (!Array.isArray(list) || list.length <= 5) continue;
                list.shift();
                removed++;
                if (removed >= 200) break;
            }
        } catch (e) {
            console.error('Prune failed:', e);
        }
    }
};