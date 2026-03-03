// Score Details Module
const ScoreDetails = {
    showScoreDetails: function(scoreResult, stockCode, stockName) {
        $('#scoreDetailsModal').remove();
        
        const modal = this.createScoreDetailsModal(scoreResult, stockCode, stockName);
        $('body').append(modal);
        
        $('#scoreDetailsModal').show();
        
        $('#scoreDetailsModal .close, #scoreDetailsModal .btn-secondary').click(function() {
            $('#scoreDetailsModal').hide();
        });
        
        $('#scoreDetailsModal').click(function(e) {
            if (e.target === this) {
                $(this).hide();
            }
        });
        
        $(document).keydown(function(e) {
            if (e.keyCode === 27 && $('#scoreDetailsModal').is(':visible')) {
                $('#scoreDetailsModal').hide();
            }
        });
    },
    
    createScoreDetailsModal: function(scoreResult, stockCode, stockName) {
        const finalScore = scoreResult.finalScore || scoreResult;
        const breakdown = scoreResult.breakdown || {};
        const details = scoreResult.details || {};
        
        let displayStockName = stockName || stockCode;
        if (!stockName) {
            if (typeof stockInfoMap !== 'undefined' && stockInfoMap[stockCode] && stockInfoMap[stockCode].name) {
                displayStockName = stockInfoMap[stockCode].name;
            }
        }
        
        return `
            <div class="score-modal" id="scoreDetailsModal" style="display: none;">
                <div class="score-modal-content">
                    <div class="score-modal-header">
                        <h5 class="score-modal-title">Score Details - ${displayStockName} - ${stockCode}</h5>
                        <button type="button" class="close">&times;</button>
                    </div>
                    <div class="score-modal-body">
                        ${this.createScoreOverview(finalScore)}
                        ${this.createScoreBreakdown(breakdown, details)}
                        ${this.createTechnicalDetails(details)}
                        ${this.createPatternDetails(details)}
                        ${this.createVolumeDetails(details)}
                    </div>
                    <div class="score-modal-footer">
                        <button type="button" class="btn-secondary">Close</button>
                    </div>
                </div>
            </div>
        `;
    },
    
    createScoreOverview: function(finalScore) {
        finalScore = parseFloat(finalScore) || 0;
        const formattedScore = finalScore.toFixed(1);
        
        const level = this.getScoreLevel(finalScore);
        const levelText = this.getScoreLevelText(level);
        const signalType = this.getSignalType(finalScore);
        const signalText = this.getSignalTypeText(signalType);
        
        return `
            <div class="score-overview">
                <div class="score-overview-row">
                    <div class="score-overview-col">
                        <div class="score-card ${level}">
                            <h3>Overall Score</h3>
                            <div class="score-value">${formattedScore}</div>
                            <div class="score-level">${levelText}</div>
                            <div class="signal-info">
                                <div class="signal-label">Signal Type</div>
                                <div class="signal-value ${signalType}">${signalText}</div>
                                <div class="signal-description">${this.getSignalDescription(signalType)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    createScoreBreakdown: function(breakdown, details) {
        const trendScore = breakdown.trendScore || 0;
        const technicalScore = breakdown.technicalScore || 0;
        const consistencyBonus = breakdown.consistencyBonus || 0;
        const patternScore = breakdown.patternScore || 0;
        const marketEnvironmentScore = breakdown.marketEnvironmentScore || 0;
        const trendPositionScore = breakdown.trendPositionScore || 0;
        const volumeModifier = breakdown.volumeModifier || 1.0;
        
        const totalBeforeVolume = trendScore + technicalScore + consistencyBonus + patternScore + marketEnvironmentScore + trendPositionScore;
        const finalScore = totalBeforeVolume * volumeModifier;
        
        return `
            <div class="score-breakdown">
                <h4>Score Breakdown</h4>
                <div class="breakdown-item">
                    <div class="breakdown-label">Trend (33%)</div>
                    <div class="breakdown-value ${this.getScoreColor(trendScore)}">${trendScore.toFixed(1)}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Technical (28%)</div>
                    <div class="breakdown-value ${this.getScoreColor(technicalScore)}">${technicalScore.toFixed(1)}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Consistency</div>
                    <div class="breakdown-value ${this.getScoreColor(consistencyBonus)}">${consistencyBonus.toFixed(1)}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Pattern (18%)</div>
                    <div class="breakdown-value ${this.getScoreColor(patternScore)}">${patternScore.toFixed(1)}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Market Env (9%)</div>
                    <div class="breakdown-value ${this.getScoreColor(marketEnvironmentScore)}">${marketEnvironmentScore.toFixed(1)}</div>
                    ${this.renderMarketEnvironmentDetails(details.marketEnvironment)}
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Trend Pos (7%)</div>
                    <div class="breakdown-value ${this.getScoreColor(trendPositionScore)}">${trendPositionScore.toFixed(1)}</div>
                    ${this.renderTrendPositionDetails(details.trendPosition)}
                </div>
                <div class="breakdown-item total">
                    <div class="breakdown-label">Subtotal</div>
                    <div class="breakdown-value">${totalBeforeVolume.toFixed(1)}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Vol Modifier</div>
                    <div class="breakdown-value">×${volumeModifier.toFixed(2)}</div>
                </div>
                <div class="breakdown-item final">
                    <div class="breakdown-label">Final Score</div>
                    <div class="breakdown-value">${finalScore.toFixed(1)}</div>
                </div>
            </div>
        `;
    },
    
    renderMarketEnvironmentDetails: function(marketEnv) {
        if (!marketEnv || !marketEnv.details) {
            return '<div class="market-env-detail">No Market Data</div>';
        }
        
        const regimeText = this.getMarketRegimeText(marketEnv.regime);
        const regimeClass = marketEnv.regime === 'bullish' ? 'positive' : 
                           marketEnv.regime === 'bearish' ? 'negative' : 'neutral';
        
        return `
            <div class="market-env-detail">
                <div class="market-regime">
                    Status: <span class="${regimeClass}">${regimeText}</span>
                    (${marketEnv.factor.toFixed(3)})
                </div>
                <div class="market-indices">
                    ${this.renderMarketIndices(marketEnv.details)}
                </div>
            </div>
        `;
    },
    
    createTechnicalDetails: function(details) {
        const signals = details.technicalSignals || [];
        
        if (signals.length === 0) {
            return `
                <div class="technical-details">
                    <h4>Technical Details</h4>
                    <p class="text-muted">No Technical Data</p>
                </div>
            `;
        }
        
        const signalsHtml = signals.map(signal => `
            <div class="signal-item">
                <div class="signal-name">${signal.indicator}</div>
                <div class="signal-text">${signal.signal}</div>
                <div class="signal-strength ${this.getStrengthColor(signal.strength)}">
                    ${(signal.strength * 100).toFixed(0)}%
                </div>
            </div>
        `).join('');
        
        return `
            <div class="technical-details">
                <h4>Technical Details</h4>
                <div class="signals-grid">
                    ${signalsHtml}
                </div>
            </div>
        `;
    },
    
    createPatternDetails: function(details) {
        const patterns = details.patternSignals || [];
        
        if (patterns.length === 0) {
            return `
                <div class="pattern-details">
                    <h4>Pattern Details</h4>
                    <p class="text-muted">No Patterns Detected</p>
                </div>
            `;
        }
        
        const patternsHtml = patterns.map(pattern => `
            <div class="pattern-item">
                <div class="pattern-name">${pattern.pattern}</div>
                <div class="pattern-score ${this.getScoreColor(pattern.finalScore)}">
                    ${pattern.finalScore.toFixed(2)}
                </div>
                <div class="pattern-modifier">
                    Modifier: ${pattern.volumeModifier.toFixed(2)}
                </div>
            </div>
        `).join('');
        
        return `
            <div class="pattern-details">
                <h4>Pattern Details</h4>
                <div class="patterns-grid">
                    ${patternsHtml}
                </div>
            </div>
        `;
    },
    
    createVolumeDetails: function(details) {
        const volumeRatio = details.volumeRatio || 1.0;
        const modifier = details.volumeModifier || 1.0;
        
        let volumeStatus = 'Normal';
        let volumeClass = 'normal';
        
        if (volumeRatio > 1.2) {
            volumeStatus = 'High Vol';
            volumeClass = 'high';
        } else if (volumeRatio < 0.8) {
            volumeStatus = 'Low Vol';
            volumeClass = 'low';
        }
        
        return `
            <div class="volume-details">
                <h4>Volume Analysis</h4>
                <div class="volume-info">
                    <div class="volume-item">
                        <div class="volume-label">Volume Ratio</div>
                        <div class="volume-value ${volumeClass}">${volumeRatio.toFixed(2)}</div>
                        <div class="volume-status">${volumeStatus}</div>
                    </div>
                    <div class="volume-item">
                        <div class="volume-label">Modifier</div>
                        <div class="volume-value">${modifier.toFixed(2)}</div>
                        <div class="volume-description">Affects Final Score</div>
                    </div>
                </div>
            </div>
        `;
    },
    
    getScoreLevel: function(score) {
        if (score >= 6.0) return 'excellent';
        if (score >= 4.5) return 'good';
        if (score >= 3.0) return 'average';
        if (score >= 1.5) return 'poor';
        return 'very-poor';
    },
    
    getScoreLevelText: function(level) {
        const texts = {
            'excellent': 'Excellent',
            'good': 'Good',
            'average': 'Average',
            'poor': 'Poor',
            'very-poor': 'Very Poor'
        };
        return texts[level] || 'Unknown';
    },
    
    getSignalType: function(score) {
        if (score >= 3.5) return 'buy';
        if (score < 2.0) return 'sell';
        return 'neutral';
    },
    
    getSignalTypeText: function(type) {
        const texts = {
            'buy': 'Buy Signal',
            'sell': 'Sell Signal',
            'neutral': 'Neutral Signal'
        };
        return texts[type] || 'Unknown';
    },
    
    getSignalDescription: function(type) {
        const descriptions = {
            'buy': 'Buy recommended, technical bullish',
            'sell': 'Sell recommended, technical bearish',
            'neutral': 'Wait recommended, await signals'
        };
        return descriptions[type] || '';
    },
    
    getScoreColor: function(score) {
        if (score > 0) return 'positive';
        if (score < 0) return 'negative';
        return 'neutral';
    },
    
    getStrengthColor: function(strength) {
        if (strength > 0.5) return 'strong-positive';
        if (strength > 0) return 'positive';
        if (strength < -0.5) return 'strong-negative';
        if (strength < 0) return 'negative';
        return 'neutral';
    },

    getMarketRegimeText: function(regime) {
        const regimeMap = {
            'bullish': 'Bullish',
            'bearish': 'Bearish',
            'neutral': 'Neutral'
        };
        return regimeMap[regime] || 'Unknown';
    },

    renderMarketIndices: function(indices) {
        if (!indices || Object.keys(indices).length === 0) {
            return '<div class="no-data">No Market Data</div>';
        }
        
        const indexNameMap = {
            'SSE': 'SSE',
            'SZSE': 'SZSE',
            'CSI300': 'CSI300'
        };
        
        return Object.entries(indices).map(([key, data]) => {
            const name = indexNameMap[key] || key;
            return `
                <div class="index-item">
                    <strong>${name}</strong>
                    <div class="index-details">
                        Trend: <span class="${data.Trend === 'Bullish' ? 'bullish' : 'bearish'}">${data.Trend}</span>
                        ${data['5D Change'] ? `| 5D: ${data['5D Change']}` : ''}
                        ${data['Volatility'] ? `| Vol: ${data['Volatility']}` : ''}
                        ${data['RSI'] ? `| RSI: ${data['RSI']}` : ''}
                    </div>
                </div>
            `;
        }).join('');
    },

    renderTrendPositionDetails: function(trendPosition) {
        if (!trendPosition || !trendPosition.position || trendPosition.position === 'unknown') {
            return '<div class="trend-position-detail">No Cycle Data</div>';
        }
        
        const positionClass = trendPosition.score_factor > 0.5 ? 'positive' : 
                             trendPosition.score_factor < -0.5 ? 'negative' : 'neutral';
        
        return `
            <div class="trend-position-detail">
                <div class="position-info">
                    Pos: <span class="${positionClass}">${trendPosition.position}</span>
                    ${trendPosition.phase ? `(${trendPosition.phase.toFixed(0)}°)` : ''}
                </div>
                <div class="position-score">
                    Pos Factor: ${trendPosition.score_factor.toFixed(2)}
                </div>
            </div>
        `;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScoreDetails;
}