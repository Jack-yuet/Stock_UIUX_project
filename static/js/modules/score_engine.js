/**
 * Stock Score Engine
 */

const ScoreEngine = {
    
    calculateFinalScore: function(analysisResult) {
        const result = {
            finalScore: 0,
            breakdown: {
                trendScore: 0,
                technicalScore: 0,
                patternScore: 0,
                marketEnvironmentScore: 0,
                trendPositionScore: 0,
                consistencyBonus: 0,
                volumeModifier: 1.0
            },
            details: {
                technicalSignals: [],
                patternSignals: [],
                marketEnvironment: {},
                trendPosition: {},
                volumeRatio: 1.0
            }
        };

        const signals = this.extractSignalsFromAPI(analysisResult);

        // 1) Trend Score (0~33)
        const ma20vs50 = signals['MA20vsMA50'] || '';
        const maArrange = signals['MA_Arrange'] || '';
        const adx = signals['ADX_Strength'] || '';
        const htMode = signals['HT_TRENDMODE'] || '';
        let comp_trend = 0;
        
        if (ma20vs50.includes('Bullish')) comp_trend += 0.8 * 0.45;
        else if (ma20vs50.includes('Bearish')) comp_trend += -0.8 * 0.45;
        
        if (maArrange.includes('Long')) comp_trend += 0.8 * 0.25;
        else if (maArrange.includes('Short')) comp_trend += -0.8 * 0.25;
        
        if (adx.includes('Strong Trend')) comp_trend += 1.0 * 0.15;
        else if (adx.includes('Medium Trend')) comp_trend += 0.5 * 0.15;
        
        if (htMode.includes('Trending Mode')) comp_trend += 1.0 * 0.15;
        else if (htMode.includes('No Trend')) comp_trend += -0.5 * 0.15;
        
        comp_trend = Math.max(-1, Math.min(1, comp_trend));
        let trendScore = comp_trend * 33;

        // 2) Technical Score (0~35) + Consistency (0~3)
        const coreIndis = ['MACD', 'RSI', 'Bollinger_Bands', 'ROC', 'OBV'];
        const techStrengths = [];
        const techSignals = [];
        for (const indi of coreIndis) {
            const s = signals[indi];
            if (!s) continue;
            const st = this.calculateSignalStrength(indi, s);
            techStrengths.push(st);
            techSignals.push({ indicator: indi, signal: s, strength: st });
        }
        result.details.technicalSignals = techSignals;
        let avgTech = techStrengths.length ? (techStrengths.reduce((a,b)=>a+b,0) / techStrengths.length) : 0;
        let technicalScore = avgTech * 35;
        const posCnt = techStrengths.filter(v=>v>0).length;
        const ratio = techStrengths.length ? posCnt / techStrengths.length : 0;
        let consistencyBonus = 0;
        if (ratio >= 0.7) consistencyBonus = Math.min(3, (ratio - 0.7) * 10);

        // 3) Pattern Score (0~10)
        const pat = this.extractPatternsFromAPI(analysisResult);
        const patternScoreMap = {
            'Three White Soldiers': 1.0,
            'Morning Star': 1.0,
            'Bullish Engulfing': 0.8,
            'Inverted Hammer': 0.7,
            'Bullish Doji': 0.6,
            'Piercing Line': 0.5,
            'Three Black Crows': -1.0,
            'Evening Star': -1.0,
            'Bearish Engulfing': -0.9,
            'Dark Cloud Cover': -0.8,
            'Shooting Star': -0.8,
            'Bearish Doji': -0.7
        };
        let basePattern = 0;
        for (const p of pat) {
            if (Object.prototype.hasOwnProperty.call(patternScoreMap, p)) basePattern += patternScoreMap[p];
        }
        
        const volRes = this.calculateVolumeModifier(analysisResult);
        const volumeRatio = volRes.ratio || 1.0;
        const trendDir = trendScore >= 0 ? 1 : -1;
        const patternDir = basePattern >= 0 ? 1 : -1;
        let patternScore = 0;
        const alignmentOk = (patternDir === trendDir) || basePattern === 0;
        const volumeOk = volumeRatio > 1.3;
        if (basePattern !== 0 && alignmentOk && volumeOk) {
            patternScore = Math.max(-10, Math.min(10, basePattern));
        } else if (basePattern !== 0 && alignmentOk) {
            patternScore = Math.max(-10, Math.min(10, basePattern * 0.5));
        } else {
            patternScore = 0;
        }

        // 4) Market Env
        const me = analysisResult.market_environment || {};
        const meFactor = Math.abs(me.factor || 0);
        const regime = me.regime || 'neutral';
        result.details.marketEnvironment = me;
        let marketEnvironmentScore = 0;
        if (regime === 'bullish') marketEnvironmentScore = 0.6 * meFactor * 10;
        else if (regime === 'bearish') marketEnvironmentScore = -0.6 * meFactor * 10;
        else marketEnvironmentScore = 0;
        marketEnvironmentScore = Math.max(-10, Math.min(10, marketEnvironmentScore)) * 0.9;
        
        if (regime === 'bearish') {
            technicalScore *= 0.8;
            patternScore *= 0.5;
        } else if (regime === 'neutral') {
            trendScore *= 0.8;
            patternScore *= 0.7;
        } else if (regime === 'bullish') {
            technicalScore *= 1.05;
        }

        // 5) Trend Position (0~7)
        const posRes = this.calculateTrendPositionScore(analysisResult);
        let trendPositionScore = posRes.score; 
        result.details.trendPosition = posRes.details;

        // 6) Volume Modifier (0.9~1.1)
        let volumeModifier = 1 + (volumeRatio - 1) * 0.2;
        volumeModifier = Math.max(0.9, Math.min(1.1, volumeModifier));

        // Set breakdown
        result.breakdown.trendScore = trendScore;
        result.breakdown.technicalScore = technicalScore;
        result.breakdown.patternScore = patternScore;
        result.breakdown.marketEnvironmentScore = marketEnvironmentScore;
        result.breakdown.trendPositionScore = trendPositionScore;
        result.breakdown.consistencyBonus = consistencyBonus;
        result.breakdown.volumeModifier = volumeModifier;

        // Total
        let total = Math.max(0, trendScore + technicalScore + consistencyBonus + patternScore + marketEnvironmentScore + trendPositionScore);
        let fs = (total * volumeModifier) / 10;
        fs = Math.max(0, Math.min(10, fs));
        result.finalScore = Math.round(fs * 10) / 10;
        return result;
    },
    
    calculateTrendScore: function(analysisResult) {
        // Simplified trend score calculation used internally if needed
        // Main logic is in calculateFinalScore
        return 0;
    },
    
    calculateMASlope: function(signals, signalKey) {
        const signal = signals[signalKey];
        if (!signal) return 0;
        
        if (signal.includes('Bullish')) {
            return 0.8; 
        } else if (signal.includes('Bearish')) {
            return -0.8; 
        }
        return 0;
    },
    
    calculateADXStrength: function(signals) {
        const adxSignal = signals['ADX_Strength'];
        if (!adxSignal) return 0;
        
        if (adxSignal.includes('Strong Trend')) {
            return 1.0;
        } else if (adxSignal.includes('Medium Trend')) {
            return 0.5;
        } else if (adxSignal.includes('Weak Trend')) {
            return 0.2;
        }
        return 0;
    },
    
    calculateTechnicalScore: function(analysisResult) {
       // Simplified
       return { baseScore: 0, consistencyBonus: 0, signals: [] };
    },
    
    calculateSignalStrength: function(indicator, signal) {
        const signalText = signal.toLowerCase();
        
        if (signalText.includes('strong bullish') || 
            signalText.includes('resonance bullish') || 
            signalText.includes('golden cross') ||
            signalText.includes('oversold')) {
            return 0.8;
        }
        else if (signalText.includes('bullish') || 
                 signalText.includes('accelerating')) {
            return 0.6;
        }
        else if (signalText.includes('strong bearish') || 
                 signalText.includes('resonance bearish') || 
                 signalText.includes('death cross') ||
                 signalText.includes('overbought')) {
            return -0.8;
        }
        else if (signalText.includes('bearish') || 
                 signalText.includes('decelerating')) {
            return -0.6;
        }
        else if (signalText.includes('neutral') || 
                 signalText.includes('normal')) {
            return 0;
        }
        
        return 0;
    },
    
    calculatePatternScore: function(analysisResult) {
        // Simplified
        return { score: 0, signals: [] };
    },
    
    calculateSinglePatternScore: function(pattern) {
        const patternText = pattern.toLowerCase();
        let baseScore = 0;
        let volumeModifier = 1.0;
        
        if (patternText.includes('morning star') ||
            patternText.includes('engulfing') ||
            patternText.includes('white soldiers') ||
            patternText.includes('piercing line')) {
            baseScore = 1.0;
            volumeModifier = 1.3;
        }
        else if (patternText.includes('hammer') ||
                 patternText.includes('doji') ||
                 patternText.includes('inverted hammer')) {
            baseScore = 0.5;
            volumeModifier = 1.2;
        }
        else if (patternText.includes('evening star') ||
                 patternText.includes('black crows') ||
                 patternText.includes('dark cloud')) {
            baseScore = -1.0;
            volumeModifier = 1.3;
        }
        else if (patternText.includes('hanging man') ||
                 patternText.includes('shooting star')) {
            baseScore = -0.5;
            volumeModifier = 1.2;
        }
        
        return {
            baseScore: baseScore,
            volumeModifier: volumeModifier,
            score: baseScore * volumeModifier
        };
    },
    
    calculateVolumeModifier: function(analysisResult) {
        const signals = this.extractSignalsFromAPI(analysisResult);
        const volumeSignal = signals['Volume'];
        
        if (!volumeSignal) {
            return { modifier: 1.0, ratio: 1.0 };
        }
        
        let volumeRatio = 1.0;
        const signalText = volumeSignal.toLowerCase();
        
        if (signalText.includes('high vol')) {
            volumeRatio = 1.5; 
        } else if (signalText.includes('low vol')) {
            volumeRatio = 0.5; 
        }
        
        const modifier = Math.min(1.3, Math.max(0.7, 1 + (volumeRatio - 1) * 0.3));
        
        return {
            modifier: modifier,
            ratio: volumeRatio
        };
    },
    
    calculateMarketEnvironmentScore: function(analysisResult) {
        // ... (Similar logic, simplified for brevity as core logic is in calculateFinalScore)
        return { score: 0, details: {} };
    },
    
    calculateTrendPositionScore: function(analysisResult) {
        const result = {
            score: 0,
            details: {
                phase: null,
                period: null,
                position: 'unknown',
                score_factor: 0
            }
        };
        
        const signals = this.extractSignalsFromAPI(analysisResult);
        
        const dcphase = signals['HT_DCPHASE'];
        const dcperiod = signals['HT_DCPERIOD'];
        
        let dcphase_val = null;
        let dcperiod_val = null;
        
        if (dcphase && dcphase.includes('Dominant Phase:')) {
            try {
                dcphase_val = parseFloat(dcphase.split(':')[1]);
                result.details.phase = dcphase_val;
            } catch (e) {}
        }
        
        if (dcperiod && dcperiod.includes('Dominant Cycle:')) {
            try {
                dcperiod_val = parseFloat(dcperiod.split(':')[1]);
                result.details.period = dcperiod_val;
            } catch (e) {}
        }
        
        if (dcphase_val === null) {
            return result;
        }
        
        let positionScore = 0;
        let position = 'unknown';
        
        if (dcphase_val < 30) {
            position = 'Bottom Start';
            positionScore = 0.8;
        } else if (dcphase_val < 60) {
            position = 'Early Rise';
            positionScore = 0.9;
        } else if (dcphase_val < 90) {
            position = 'Accelerated Rise';
            positionScore = 0.7;
        } else if (dcphase_val < 120) {
            position = 'Late Rise';
            positionScore = 0.5;
        } else if (dcphase_val < 150) {
            position = 'Near Top';
            positionScore = 0.3;
        } else if (dcphase_val < 180) {
            position = 'Top Area';
            positionScore = 0.1;
        } else if (dcphase_val < 210) {
            position = 'Start Correction';
            positionScore = -0.7;
        } else if (dcphase_val < 240) {
            position = 'Early Decline';
            positionScore = -0.8;
        } else if (dcphase_val < 270) {
            position = 'Accelerated Decline';
            positionScore = -0.9;
        } else if (dcphase_val < 300) {
            position = 'Deep Correction';
            positionScore = -0.6;
        } else if (dcphase_val < 330) {
            position = 'Near Bottom';
            positionScore = -0.3;
        } else {
            position = 'Bottom Building';
            positionScore = -0.1;
        }
        
        result.details.position = position;
        result.details.score_factor = positionScore;
        
        result.score = positionScore * 7;
        
        return result;
    },
    
    getScoreLevel: function(score) {
        if (score >= 6.0) return 'excellent';
        if (score >= 4.5) return 'good';
        if (score >= 3.0) return 'average';
        if (score >= 1.5) return 'poor';
        return 'very-poor';
    },
    
    extractSignalsFromAPI: function(analysisResult) {
        const signals = {};
        
        if (analysisResult.technical_indicators && Array.isArray(analysisResult.technical_indicators)) {
            for (const indicator of analysisResult.technical_indicators) {
                if (indicator.indicator && indicator.signal) {
                    signals[indicator.indicator] = indicator.signal;
                }
            }
        }
        
        if (analysisResult.technical_signals && typeof analysisResult.technical_signals === 'object') {
            Object.assign(signals, analysisResult.technical_signals);
        }
        
        return signals;
    },
    
    extractPatternsFromAPI: function(analysisResult) {
        const patterns = [];
        
        if (analysisResult.candlestick_patterns && Array.isArray(analysisResult.candlestick_patterns)) {
            for (const pattern of analysisResult.candlestick_patterns) {
                if (pattern.pattern && pattern.status) {
                    if (!pattern.status.includes('Not Detected') && 
                        !pattern.status.includes('Not Formed') &&
                        !pattern.status.includes('Weak')) {
                        patterns.push(pattern.pattern);
                    }
                }
            }
        }
        
        if (analysisResult.candlestick_patterns_raw && typeof analysisResult.candlestick_patterns_raw === 'object') {
            for (const [pattern, value] of Object.entries(analysisResult.candlestick_patterns_raw)) {
                if (value !== 0) {
                    patterns.push(pattern);
                }
            }
        }
        
        return patterns;
    },
    
    getSignalType: function(score) {
        if (score >= 3.5) return 'buy';
        if (score < 2.0) return 'sell';
        return 'neutral';
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScoreEngine;
}