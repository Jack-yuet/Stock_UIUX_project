// UI Display Module
const UI = {
    // Display Basic Info
    displayBasicInfo: function(basicInfo) {
        const html = `
            <div class="info-card">
                <div class="info-label">Company Name</div>
                <div class="info-value">${basicInfo.name}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Stock Code</div>
                <div class="info-value">${basicInfo.code}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Industry</div>
                <div class="info-value">${basicInfo.industry}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Sector</div>
                <div class="info-value">${basicInfo.sector}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Market Cap</div>
                <div class="info-value format-number">${Utils.formatMarketCap(basicInfo.market_cap)}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Price</div>
                <div class="info-value">$${basicInfo.current_price ? basicInfo.current_price.toFixed(2) : 'N/A'}</div>
            </div>
            <div class="info-card">
                <div class="info-label">PE Ratio</div>
                <div class="info-value">${basicInfo.pe_ratio ? basicInfo.pe_ratio.toFixed(2) : 'N/A'}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Div Yield</div>
                <div class="info-value">${basicInfo.dividend_yield ? (basicInfo.dividend_yield * 100).toFixed(2) + '%' : 'N/A'}</div>
            </div>
        `;
        $('#basicInfo').html(html);
    },
    
    // Display Historical Data
    displayHistData: function(histData) {
        let html = '';
        histData.forEach(function(item) {
            const changeClass = item.daily_return > 0 ? 'change-up' : 
                              item.daily_return < 0 ? 'change-down' : '';
            const changeSymbol = item.daily_return > 0 ? '+' : '';
            
            // Process Candlestick Pattern Coloring
            let patternsHtml = '';
            let patternArr = [];
            if (item.patterns && item.patterns.trim()) {
                patternArr = item.patterns.split(',').map(p => p.trim());
            }
            if (patternArr.length > 0) {
                const firstPattern = patternArr[0];
                patternsHtml = UI._getColoredPattern(firstPattern);
            }
            
            html += `
                <tr>
                    <td>${item.date}</td>
                    <td>$${item.open.toFixed(2)}</td>
                    <td>$${item.high.toFixed(2)}</td>
                    <td>$${item.low.toFixed(2)}</td>
                    <td>$${item.close.toFixed(2)}</td>
                    <td class="format-number">${Utils.formatVolume(item.volume)}</td>
                    <td class="${changeClass}">${changeSymbol}${item.daily_return.toFixed(2)}%</td>
                    <td class="patterns-cell">${patternsHtml}</td>
                </tr>
            `;
            // Remaining patterns on new lines
            if (patternArr.length > 1) {
                for (let i = 1; i < patternArr.length; i++) {
                    html += `
                        <tr>
                            <td></td><td></td><td></td><td></td><td></td><td></td><td></td>
                            <td class="patterns-cell">${UI._getColoredPattern(patternArr[i])}</td>
                        </tr>
                    `;
                }
            }
        });
        $('#histTable tbody').html(html);
    },

    // Helper for coloring patterns
    _getColoredPattern: function(pattern) {
        let colorClass = 'pattern-neutral';
        if (pattern.includes('Bullish') || 
            pattern.includes('Hammer') || 
            pattern.includes('Morning Star') || 
            pattern.includes('White Soldiers') || 
            pattern.includes('Piercing') || 
            pattern.includes('Inverted Hammer') || 
            pattern.includes('Rising Three')) {
            colorClass = 'pattern-bullish';
        } else if (pattern.includes('Bearish') || 
                   pattern.includes('Hanging Man') || 
                   pattern.includes('Evening Star') || 
                   pattern.includes('Black Crows') || 
                   pattern.includes('Dark Cloud') || 
                   pattern.includes('Shooting Star') || 
                   pattern.includes('Falling Three') || 
                   pattern.includes('Breakdown')) {
            colorClass = 'pattern-bearish';
        }
        return `<span class="${colorClass}">${pattern}</span>`;
    },
    
    // Display Financial Data
    displayFinancialData: function(financialData, institutionalData, stockCode) {
        console.log('displayFinancialData called:', { financialData, institutionalData, stockCode });
        
        // Financial Indicators Details
        const financialDetails = {
            'Market Cap': {
                title: 'Market Cap',
                description: 'The total value of a company\'s outstanding shares.',
                calculation: 'Market Cap = Share Price × Outstanding Shares',
                interpretation: 'Reflects overall size. Large caps are stable; small caps may have growth potential.'
            },
            'Revenue': {
                title: 'Total Revenue',
                description: 'The total amount of income generated by the sale of goods or services.',
                calculation: 'Revenue = Operating Revenue + Non-operating Revenue',
                interpretation: 'Growth indicates business expansion.'
            },
            'Net Income': {
                title: 'Net Income',
                description: 'The total profit of the company after all expenses and taxes.',
                calculation: 'Net Income = Revenue - Expenses - Taxes',
                interpretation: 'Indicates profitability.'
            },
            'EPS (TTM)': {
                title: 'Earnings Per Share (TTM)',
                description: 'Net income divided by outstanding shares. TTM = Trailing Twelve Months.',
                calculation: 'EPS = Net Income / Shares Outstanding',
                interpretation: 'Key profitability metric. Higher is generally better.'
            },
            'PE (TTM)': {
                title: 'Price-to-Earnings Ratio (TTM)',
                description: 'Ratio of share price to earnings per share.',
                calculation: 'P/E = Share Price / EPS',
                interpretation: 'Valuation metric. Low P/E might mean undervalued, high might mean overvalued or high growth.'
            },
            'PB Ratio': {
                title: 'Price-to-Book Ratio',
                description: 'Ratio of share price to book value per share.',
                calculation: 'P/B = Share Price / Book Value per Share',
                interpretation: 'Valuation metric relative to assets.'
            },
            'PS Ratio (TTM)': {
                title: 'Price-to-Sales Ratio (TTM)',
                description: 'Ratio of share price to revenue per share.',
                calculation: 'P/S = Share Price / Revenue per Share',
                interpretation: 'Valuation metric relative to sales.'
            },
            'Div Yield': {
                title: 'Dividend Yield',
                description: 'Annual dividend per share divided by share price.',
                calculation: 'Yield = Annual Dividend / Share Price',
                interpretation: 'Return on investment from dividends.'
            },
            'ROE': {
                title: 'Return on Equity',
                description: 'Net income divided by shareholders\' equity.',
                calculation: 'ROE = Net Income / Equity',
                interpretation: 'Efficiency in generating profits from equity.'
            },
            'ROA': {
                title: 'Return on Assets',
                description: 'Net income divided by total assets.',
                calculation: 'ROA = Net Income / Total Assets',
                interpretation: 'Efficiency in generating profits from assets.'
            },
            'Debt/Equity': {
                title: 'Debt-to-Equity Ratio',
                description: 'Total liabilities divided by shareholder equity.',
                calculation: 'D/E = Total Liabilities / Shareholders\' Equity',
                interpretation: 'Measure of financial leverage and risk.'
            },
            'Current Ratio': {
                title: 'Current Ratio',
                description: 'Current assets divided by current liabilities.',
                calculation: 'Current Ratio = Current Assets / Current Liabilities',
                interpretation: 'Measure of short-term liquidity.'
            },
            'Quick Ratio': {
                title: 'Quick Ratio',
                description: 'Liquid assets divided by current liabilities.',
                calculation: 'Quick Ratio = (Current Assets - Inventory) / Current Liabilities',
                interpretation: 'Stricter measure of liquidity.'
            }
        };

        // Display Financial Table
        if (financialData && financialData.length > 0) {
            console.log('Processing financial data:', financialData.length);
            let html = '';
            financialData.forEach(function(item, index) {
                const financialDetail = financialDetails[item.indicator] || {
                    title: item.indicator,
                    description: 'No detailed description available.',
                    interpretation: ''
                };
                
                html += `
                    <tr class="financial-row" data-financial-index="${index}">
                        <td>${item.indicator}</td>
                        <td class="format-number">${item.value}${item.unit || ''}</td>
                    </tr>
                    <tr class="financial-description-row">
                        <td colspan="2">
                            <div class="financial-description" id="financial-desc-${index}">
                                <h5>${financialDetail.title}</h5>
                                <p><strong>Desc:</strong> ${financialDetail.description}</p>
                                ${financialDetail.interpretation ? `<div class="interpretation"><strong>Interp:</strong> ${financialDetail.interpretation}</div>` : ''}
                            </div>
                        </td>
                    </tr>
                `;
            });
            $('#financialTable tbody').html(html);
            
            // Bind click events
            $('.financial-row').click(function() {
                const index = $(this).data('financial-index');
                const $row = $(this);
                const $descriptionRow = $(this).next('.financial-description-row');
                const $description = $(`#financial-desc-${index}`);
                
                if ($row.hasClass('expanded')) {
                    $row.removeClass('expanded');
                    $descriptionRow.removeClass('show');
                    $description.removeClass('show');
                } else {
                    $('.financial-row').removeClass('expanded');
                    $('.financial-description-row').removeClass('show');
                    $('.financial-description').removeClass('show');
                    
                    $row.addClass('expanded');
                    $descriptionRow.addClass('show');
                    $description.addClass('show');
                }
            });
        } else {
            $('#financialTable tbody').html('<tr><td colspan="2" class="no-data">No Financial Data</td></tr>');
        }
        
        // Display Institutional Data
        this.displayInstitutionalData(institutionalData, stockCode);
    },
    
    // Display Institutional Data
    displayInstitutionalData: function(institutionalData, stockCode) {
        // Check if A-Share (6 digits) - usually institution data is limited/different source, maybe hide?
        // Original logic hid it for A-Shares. Keeping logic but translating.
        const isAShare = /^\d{6}$/.test(stockCode);
        
        if (isAShare) {
            $('#institutionalSection').hide();
            return;
        }
        
        $('#institutionalSection').show();
        
        if (institutionalData && institutionalData.length > 0) {
            let html = '';
            institutionalData.forEach(function(item) {
                html += `
                    <tr>
                        <td>${item.holder}</td>
                        <td class="format-number">${Utils.formatVolume(item.shares)}</td>
                        <td>${item.date_reported}</td>
                    </tr>
                `;
            });
            $('#institutionalTable tbody').html(html);
        } else {
            $('#institutionalTable tbody').html('<tr><td colspan="3" class="no-data">No Institutional Data</td></tr>');
        }
    },
    
    // Show Success
    showSuccess: function(message) {
        $('#successMsg').text(message).show();
        setTimeout(() => {
            $('#successMsg').hide();
        }, 3000);
    },
    
    // Show Error
    showError: function(message) {
        $('#errorMsg').text(message).show();
    },
    
    // Display Trend Analysis
    displayTrendAnalysis: function(analysisData) {
        // Pattern Details
        const patternDetails = {
            'Hammer': {
                title: 'Hammer',
                description: 'A bullish reversal pattern at the bottom of a downtrend.',
                features: 'Long lower shadow, small body at the top. Lower shadow >= 2x body.',
                usage: 'Potential reversal signal. Requires volume confirmation and subsequent candle confirmation.'
            },
            'Morning Star': {
                title: 'Morning Star',
                description: 'A bullish reversal pattern consisting of three candles.',
                features: 'Large bearish candle, small body candle (gap down), large bullish candle (gap up).',
                usage: 'Strong reversal signal at bottom. Needs confirmation.'
            },
            'Bullish Engulfing': {
                title: 'Bullish Engulfing',
                description: 'A bullish reversal pattern where a green candle engulfs the previous red candle.',
                features: 'Small bearish candle followed by large bullish candle covering it.',
                usage: 'Reversal signal. Stronger if large size difference and high volume.'
            },
            'Doji': {
                title: 'Doji',
                description: 'Neutral pattern indicating indecision.',
                features: 'Open and close are virtually the same.',
                usage: 'Potential reversal warning if at trend extremes.'
            },
            'Three White Soldiers': {
                title: 'Three White Soldiers',
                description: 'A bullish continuation pattern.',
                features: 'Three consecutive long bullish candles closing higher.',
                usage: 'Strong uptrend confirmation.'
            },
            'Three Black Crows': {
                title: 'Three Black Crows',
                description: 'A bearish continuation pattern.',
                features: 'Three consecutive long bearish candles closing lower.',
                usage: 'Strong downtrend confirmation.'
            },
            'Hanging Man': {
                title: 'Hanging Man',
                description: 'A bearish reversal pattern at the top of an uptrend.',
                features: 'Long lower shadow, small body at top. Similar to Hammer but at peak.',
                usage: 'Warning of potential top. Needs bearish confirmation next day.'
            },
            'Evening Star': {
                title: 'Evening Star',
                description: 'A bearish reversal pattern consisting of three candles.',
                features: 'Large bullish candle, small body candle, large bearish candle.',
                usage: 'Strong reversal signal at top.'
            },
            'Dark Cloud Cover': {
                title: 'Dark Cloud Cover',
                description: 'A bearish reversal pattern.',
                features: 'Bullish candle followed by bearish candle opening higher but closing below midpoint of first candle.',
                usage: 'Potential top reversal.'
            },
            'Piercing Line': {
                title: 'Piercing Line',
                description: 'A bullish reversal pattern.',
                features: 'Bearish candle followed by bullish candle opening lower but closing above midpoint of first candle.',
                usage: 'Potential bottom reversal.'
            },
            'Shooting Star': {
                title: 'Shooting Star',
                description: 'A bearish reversal pattern.',
                features: 'Long upper shadow, small body at bottom.',
                usage: 'Warning of potential reversal at resistance.'
            },
            'Inverted Hammer': {
                title: 'Inverted Hammer',
                description: 'A bullish reversal pattern.',
                features: 'Long upper shadow, small body at bottom.',
                usage: 'Potential bottom signal, requires confirmation.'
            },
            'Rising Three Methods': {
                title: 'Rising Three Methods',
                description: 'A bullish continuation pattern.',
                features: 'Long bullish candle, small consolidation candles, another long bullish candle.',
                usage: 'Trend continuation signal.'
            },
            'Falling Three Methods': {
                title: 'Falling Three Methods',
                description: 'A bearish continuation pattern.',
                features: 'Long bearish candle, small consolidation candles, another long bearish candle.',
                usage: 'Trend continuation signal.'
            },
            'Breakdown Long Bearish Candle': {
                title: 'Breakdown Long Bearish Candle',
                description: 'Bearish signal indicating support failure.',
                features: 'Large bearish candle breaking support with volume.',
                usage: 'Confirmation of breakdown.'
            }
        };

        // Render Pattern Table
        let patternsHtml = '';
        analysisData.candlestick_patterns.forEach(function(item, index) {
            const patternDetail = patternDetails[item.pattern] || {
                title: item.pattern,
                description: 'No details available.',
                features: '',
                usage: ''
            };
            
            let statusText = item.status;
            if (statusText.includes('Bullish')) statusText = 'Bullish';
            else if (statusText.includes('Bearish')) statusText = 'Bearish';
            
            patternsHtml += `
                <tr class="pattern-row" data-pattern-index="${index}">
                    <td>${item.pattern}</td>
                    <td class="${item.status_class}">${statusText}</td>
                </tr>
                <tr class="pattern-description-row">
                    <td colspan="2">
                        <div class="pattern-description" id="pattern-desc-${index}">
                            <h5>${patternDetail.title}</h5>
                            <p><strong>Desc:</strong> ${patternDetail.description}</p>
                            ${patternDetail.features ? `<p><strong>Features:</strong> ${patternDetail.features}</p>` : ''}
                            ${patternDetail.usage ? `<div class="usage"><strong>Usage:</strong> ${patternDetail.usage}</div>` : ''}
                        </div>
                    </td>
                </tr>
            `;
        });
        $('#candlestickPatternsTable tbody').html(patternsHtml);
        
        // Bind pattern clicks
        $('.pattern-row').click(function() {
            const index = $(this).data('pattern-index');
            const $row = $(this);
            const $descriptionRow = $(this).next('.pattern-description-row');
            const $description = $(`#pattern-desc-${index}`);
            
            if ($row.hasClass('expanded')) {
                $row.removeClass('expanded');
                $descriptionRow.removeClass('show');
                $description.removeClass('show');
            } else {
                $('.pattern-row').removeClass('expanded');
                $('.pattern-description-row').removeClass('show');
                $('.pattern-description').removeClass('show');
                
                $row.addClass('expanded');
                $descriptionRow.addClass('show');
                $description.addClass('show');
            }
        });
        
        // Technical Indicators Details
        const technicalIndicatorDetails = {
            'MA_Trend': {
                description: 'Basic trend direction based on price vs MA20.',
                calculation: 'Price > MA20 → Bullish; Price < MA20 → Bearish',
                interpretation: 'Identifies medium-term trend direction.'
            },
            'MA5vsMA20': {
                description: 'Short vs Medium term MA relationship.',
                calculation: 'MA5 > MA20 → Short-term Bullish',
                interpretation: 'Crossovers indicate potential trend changes.'
            },
            'MA20vsMA50': {
                description: 'Medium vs Long term MA relationship.',
                calculation: 'MA20 > MA50 → Medium-term Bullish',
                interpretation: 'Golden Cross / Death Cross identification.'
            },
            'MACD': {
                title: 'MACD',
                description: 'Trend-following momentum indicator.',
                calculation: 'MACD Line - Signal Line',
                interpretation: 'Crossovers and histograms show momentum shifts.'
            },
            'RSI': {
                title: 'RSI',
                description: 'Momentum oscillator measuring speed/change of price.',
                calculation: '0-100 scale.',
                interpretation: '>70 Overbought, <30 Oversold.'
            },
            'Bollinger_Bands': {
                title: 'Bollinger Bands',
                description: 'Volatility bands above/below moving average.',
                interpretation: 'Price near upper band = overbought, lower = oversold.'
            },
            'Volume': {
                title: 'Volume Analysis',
                description: 'Trading activity level.',
                interpretation: 'High volume confirms trend.'
            },
            'Momentum': {
                title: 'Momentum',
                description: 'Rate of acceleration of price.',
                interpretation: 'Positive = Bullish.'
            },
            'ROC': {
                title: 'Rate of Change',
                description: 'Percentage change in price.',
                interpretation: '>0 Bullish.'
            },
            'OBV': {
                title: 'On-Balance Volume',
                description: 'Cumulative volume flow.',
                interpretation: 'Divergence with price suggests reversal.'
            },
            'ADX_Strength': {
                title: 'ADX',
                description: 'Trend Strength Indicator.',
                interpretation: '>25 Strong Trend.'
            },
            'KDJ': {
                title: 'KDJ',
                description: 'Stochastic oscillator variant.',
                interpretation: '>80 Overbought, <20 Oversold.'
            },
            'ROC_Inflection': {
                title: 'ROC Inflection',
                description: 'Change in ROC.',
                interpretation: 'Acceleration/Deceleration of momentum.'
            },
            'WilliamsR': {
                title: 'Williams %R',
                description: 'Momentum indicator.',
                interpretation: '>-20 Overbought, <-80 Oversold.'
            },
            'CCI': {
                title: 'CCI',
                description: 'Cyclical trend indicator.',
                interpretation: '>100 Overbought, <-100 Oversold.'
            },
            'HT_DCPERIOD': {
                title: 'Dominant Cycle Period',
                description: 'Dominant cycle length.',
                interpretation: 'Current market cycle length.'
            },
            'HT_DCPHASE': {
                title: 'Dominant Cycle Phase',
                description: 'Position in the cycle (0-360).',
                interpretation: '0=Start, 180=Peak.'
            },
            'HT_TRENDMODE': {
                title: 'Trend Mode',
                description: 'Trending or Cycling mode.',
                interpretation: 'Identifies if market is trending or ranging.'
            }
        };

        // Render Technical Indicators
        let indicatorsHtml = '';
        analysisData.technical_indicators.forEach(function(item, index) {
            let indicatorName = item.indicator;
            if (indicatorName === 'HT_DCPERIOD') indicatorName = 'Dominant Cycle';
            else if (indicatorName === 'HT_DCPHASE') indicatorName = 'Cycle Phase';
            else if (indicatorName === 'HT_TRENDMODE') indicatorName = 'Trend Mode';
            else if (indicatorName === 'MA趋势') indicatorName = 'MA Trend';
            else if (indicatorName === 'MA5vsMA20') indicatorName = 'MA5 vs MA20';
            else if (indicatorName === 'MA20vsMA50') indicatorName = 'MA20 vs MA50';
            else if (indicatorName === '布林带') indicatorName = 'Bollinger Bands';
            else if (indicatorName === '成交量') indicatorName = 'Volume';
            else if (indicatorName === '动量') indicatorName = 'Momentum';
            else if (indicatorName === '变化率') indicatorName = 'ROC';
            else if (indicatorName === 'OBV能量') indicatorName = 'OBV';
            else if (indicatorName === 'ADX趋势强度') indicatorName = 'ADX';
            else if (indicatorName === 'ROC拐点') indicatorName = 'ROC Inflection';
            else if (indicatorName === '威廉指标') indicatorName = 'Williams %R';

            const indicatorDetail = technicalIndicatorDetails[item.indicator] || {
                title: item.indicator,
                description: 'No details.',
                calculation: '',
                interpretation: ''
            };
            
            indicatorsHtml += `
                <tr class="indicator-row" data-indicator-index="${index}">
                    <td>${indicatorName}</td>
                    <td class="${item.signal_class}">${item.signal}</td>
                </tr>
                <tr class="indicator-description-row">
                    <td colspan="2">
                        <div class="indicator-description" id="indicator-desc-${index}">
                            <h5>${indicatorDetail.title || indicatorName}</h5>
                            <p><strong>Desc:</strong> ${indicatorDetail.description}</p>
                            ${indicatorDetail.calculation ? `<p><strong>Calc:</strong> ${indicatorDetail.calculation}</p>` : ''}
                            ${indicatorDetail.interpretation ? `<div class="interpretation"><strong>Interp:</strong> ${indicatorDetail.interpretation}</div>` : ''}
                        </div>
                    </td>
                </tr>
            `;
        });
        $('#technicalIndicatorsTable tbody').html(indicatorsHtml);
        
        // Bind click events
        $('.indicator-row').click(function() {
            const index = $(this).data('indicator-index');
            const $row = $(this);
            const $descriptionRow = $(this).next('.indicator-description-row');
            const $description = $(`#indicator-desc-${index}`);
            
            if ($row.hasClass('expanded')) {
                $row.removeClass('expanded');
                $descriptionRow.removeClass('show');
                $description.removeClass('show');
            } else {
                $('.indicator-row').removeClass('expanded');
                $('.indicator-description-row').removeClass('show');
                $('.indicator-description').removeClass('show');
                
                $row.addClass('expanded');
                $descriptionRow.addClass('show');
                $description.addClass('show');
            }
        });
        
        // Render Support & Resistance
        let supportResistanceHtml = '';
        analysisData.support_resistance.forEach(function(item) {
            supportResistanceHtml += `
                <tr>
                    <td>${item.type}</td>
                    <td>$${item.price.toFixed(2)}</td>
                    <td class="${item.strength_class}">${item.strength}</td>
                    <td>${item.touches}</td>
                    <td>${item.distance}</td>
                </tr>
            `;
        });
        $('#supportResistanceTable tbody').html(supportResistanceHtml);
        
        // Render All Levels
        let allLevelsHtml = '';
        analysisData.all_levels.forEach(function(item) {
            allLevelsHtml += `
                <tr>
                    <td>${item.type}</td>
                    <td>$${item.price.toFixed(2)}</td>
                    <td class="${item.strength_class}">${item.strength}</td>
                    <td>${item.touches}</td>
                    <td>${item.distance}</td>
                </tr>
            `;
        });
        $('#allLevelsTable tbody').html(allLevelsHtml);
        
        // Render Conclusion
        $('#trendConclusion').text(analysisData.trend_conclusion);
        
        // Render Detailed Summary
        const summary = analysisData.detailed_summary || '';
        let summaryHtml = '';
        summary.split('\n').forEach(line => {
            if (line.startsWith('[Candlestick Analysis]')) {
                summaryHtml += `<div style="margin-bottom:6px;"><span style="font-weight:bold;color:#2e8b57;">Candlestick: </span>${line.replace('[Candlestick Analysis]','')}</div>`;
            } else if (line.startsWith('[Dominant Cycle]')) {
                summaryHtml += `<div style="margin-bottom:6px;"><span style="font-weight:bold;color:#1e90ff;">Cycle: </span>${line.replace('[Dominant Cycle]','')}</div>`;
            } else if (line.startsWith('[Technical Indicators]')) {
                summaryHtml += `<div style="margin-bottom:6px;"><span style="font-weight:bold;">Technical: </span>${line.replace('[Technical Indicators]','')}</div>`;
            } else if (line.startsWith('[Support & Resistance]')) {
                summaryHtml += `<div style="margin-bottom:6px;"><span style="font-weight:bold;color:#ff8c00;">S&R: </span>${line.replace('[Support & Resistance]','')}</div>`;
            } else if (line.startsWith('[Risk Warning]')) {
                summaryHtml += `<div style="margin-bottom:6px;"><span style="font-weight:bold;color:#d32f2f;">Risk Warning: </span>${line.replace('[Risk Warning]','')}</div>`;
            } else if (line.trim() !== '') {
                summaryHtml += `<div style="margin-bottom:6px;">${line}</div>`;
            }
        });
        $('#detailedSummary').html(summaryHtml);
        
        // Show Content
        $('#trendAnalysisContent').show();
    },
    
    // Hide Trend Analysis
    hideTrendAnalysis: function() {
        $('#trendAnalysisContent').hide();
    },
    
    // Show Loading
    showTrendAnalysisLoading: function() {
        $('#trendAnalysisLoading').show();
        $('#trendAnalysisContent').hide();
    },
    
    // Hide Loading
    hideTrendAnalysisLoading: function() {
        $('#trendAnalysisLoading').hide();
    }
};