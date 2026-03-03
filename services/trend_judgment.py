"""
Trend Judgment and Summary Generation Module
Contains functions for comprehensive trend judgment and detailed analysis summary generation
"""

def generate_comprehensive_trend_judgment(signals, patterns=None, levels=None, pattern_meanings=None):
    """Generate comprehensive trend judgment conclusion"""
    # Count signals
    bullish_count = 0
    bearish_count = 0
    overbought_count = 0
    oversold_count = 0
    neutral_count = 0
    
    # Classify signals
    for signal in signals.values():
        if 'Bullish' in signal or 'Resonance Bullish' in signal:
            bullish_count += 1
        elif 'Bearish' in signal or 'Resonance Bearish' in signal:
            bearish_count += 1
        elif 'Overbought' in signal:
            overbought_count += 1
        elif 'Oversold' in signal:
            oversold_count += 1
        else:
            neutral_count += 1
    
    # Analyze trend strength
    trend_strength = "Weak"
    if any('Strong Trend' in signal for signal in signals.values()):
        trend_strength = "Strong"
    elif any('Medium Trend' in signal for signal in signals.values()):
        trend_strength = "Medium"
    
    # Analyze divergence
    divergence_signals = []
    if 'OBV' in signals and 'Divergence' in signals['OBV']:
        divergence_signals.append('OBV Divergence')
    if 'MACD' in signals and 'MA_Trend' in signals:
        if (signals['MACD'] == 'Bullish' and signals['MA_Trend'] == 'Bearish') or \
           (signals['MACD'] == 'Bearish' and signals['MA_Trend'] == 'Bullish'):
            divergence_signals.append('MACD & MA Divergence')
    
    # Dominant cycle related
    dcperiod = signals.get('HT_DCPERIOD', '')
    dcphase = signals.get('HT_DCPHASE', '')
    trendmode = signals.get('HT_TRENDMODE', '')
    dcperiod_val = None
    dcphase_val = None
    if isinstance(dcperiod, str) and 'Dominant Cycle:' in dcperiod:
        try:
            dcperiod_val = float(dcperiod.split(':')[1])
        except:
            pass
    if isinstance(dcphase, str) and 'Dominant Phase:' in dcphase:
        try:
            dcphase_val = float(dcphase.split(':')[1])
        except:
            pass
    
    # Generate comprehensive judgment
    judgment_parts = []
    # Count core signal consensus
    core_signals = []
    for key in ['MACD', 'MA_Trend', 'MA5vsMA20', 'MA20vsMA50', 'OBV', 'KDJ', 'Bollinger_Bands', 'Volume']:
        val = signals.get(key, '')
        if 'Bullish' in val or 'Resonance Bullish' in val:
            core_signals.append(1)
        elif 'Bearish' in val or 'Resonance Bearish' in val:
            core_signals.append(-1)
        else:
            core_signals.append(0)
    adx_strong = signals.get('ADX_Strength', '') == 'Strong Trend'
    bullish_consensus = core_signals.count(1) >= 5 and adx_strong
    bearish_consensus = core_signals.count(-1) >= 5 and adx_strong

    # Main trend judgment
    if bullish_consensus:
        main_trend = "bull"
        judgment_parts.append("Strong Bullish Trend, Trend Strength Confirmed")
    elif bearish_consensus:
        main_trend = "bear"
        judgment_parts.append("Strong Bearish Trend, Trend Strength Confirmed")
    elif bullish_count > bearish_count + 2:
        main_trend = "bull"
        judgment_parts.append("Bullish Trend")
    elif bearish_count > bullish_count + 2:
        main_trend = "bear"
        judgment_parts.append("Bearish Trend")
    else:
        main_trend = "neutral"
        judgment_parts.append("Trend Unclear, Possible Consolidation")

    # Dominant cycle interpretation
    if dcperiod_val:
        if dcperiod_val < 15:
            judgment_parts.append("Short-term Cycle Dominant")
        elif dcperiod_val < 30:
            judgment_parts.append("Medium-term Cycle Dominant")
        else:
            judgment_parts.append("Long-term Cycle Dominant")
            
    if dcphase_val is not None:
        if main_trend == "bull":
            if dcphase_val < 30:
                judgment_parts.append(f"Cycle in Bottom Start Phase, Momentum Appearing ({dcphase_val:.0f}°)")
            elif dcphase_val < 60:
                judgment_parts.append(f"Cycle in Early Rise, Trend Established ({dcphase_val:.0f}°)")
            elif dcphase_val < 90:
                judgment_parts.append(f"Cycle in Accelerated Rise, Strong Momentum ({dcphase_val:.0f}°)")
            elif dcphase_val < 120:
                judgment_parts.append(f"Cycle in Late Rise, Momentum Weaking ({dcphase_val:.0f}°)")
            elif dcphase_val < 150:
                judgment_parts.append(f"Cycle Nearing Top, Caution on Chasing Highs ({dcphase_val:.0f}°)")
            elif dcphase_val < 180:
                judgment_parts.append(f"Cycle in Top Area, Watch for Pullback ({dcphase_val:.0f}°)")
            elif dcphase_val < 210:
                judgment_parts.append(f"Cycle Starting Correction, Top Confirmed ({dcphase_val:.0f}°)")
            elif dcphase_val < 240:
                judgment_parts.append(f"Cycle in Early Decline, Trend Weakening ({dcphase_val:.0f}°)")
            elif dcphase_val < 270:
                judgment_parts.append(f"Cycle in Accelerated Decline, Risk Off ({dcphase_val:.0f}°)")
            elif dcphase_val < 300:
                judgment_parts.append(f"Cycle in Deep Correction, Be Patient ({dcphase_val:.0f}°)")
            elif dcphase_val < 330:
                judgment_parts.append(f"Cycle Nearing Bottom, Watch for Stabilization ({dcphase_val:.0f}°)")
            else:
                judgment_parts.append(f"Cycle Building Bottom, Preparing for Next Rise ({dcphase_val:.0f}°)")
        elif main_trend == "bear":
            if dcphase_val < 30:
                judgment_parts.append(f"Cycle in Bottom Rebound, Technical Repair ({dcphase_val:.0f}°)")
            elif dcphase_val < 60:
                judgment_parts.append(f"Cycle in Mid Rebound, Trend Still Weak ({dcphase_val:.0f}°)")
            elif dcphase_val < 90:
                judgment_parts.append(f"Cycle Rebound Nearing End, Watch for Secondary Dip ({dcphase_val:.0f}°)")
            elif dcphase_val < 120:
                judgment_parts.append(f"Cycle Turning Weak Again, Downtrend Continues ({dcphase_val:.0f}°)")
            elif dcphase_val < 150:
                judgment_parts.append(f"Cycle in Accelerated Decline, Bears Dominant ({dcphase_val:.0f}°)")
            elif dcphase_val < 180:
                judgment_parts.append(f"Cycle in Deep Decline, Panic Prevails ({dcphase_val:.0f}°)")
            elif dcphase_val < 210:
                judgment_parts.append(f"Cycle Decline Momentum Weakening, Seeking Support ({dcphase_val:.0f}°)")
            elif dcphase_val < 240:
                judgment_parts.append(f"Cycle in Late Decline, Watch for Stop ({dcphase_val:.0f}°)")
            elif dcphase_val < 270:
                judgment_parts.append(f"Cycle Nearing Cyclical Bottom, Prepare to Buy ({dcphase_val:.0f}°)")
            elif dcphase_val < 300:
                judgment_parts.append(f"Cycle Building Bottom, Positive Signals Increasing ({dcphase_val:.0f}°)")
            elif dcphase_val < 330:
                judgment_parts.append(f"Cycle Bottom Confirmed, Rebound Brewing ({dcphase_val:.0f}°)")
            else:
                judgment_parts.append(f"Cycle Ready to Launch, New Upward Cycle Starting ({dcphase_val:.0f}°)")
        else:
            if dcphase_val < 30:
                judgment_parts.append(f"Cycle in Bottom Area, Ready to Launch ({dcphase_val:.0f}°)")
            elif dcphase_val < 60:
                judgment_parts.append(f"Cycle Starting Rise, Trend Preliminary Confirmation ({dcphase_val:.0f}°)")
            elif dcphase_val < 90:
                judgment_parts.append(f"Cycle in Early Rise, Momentum Accumulating ({dcphase_val:.0f}°)")
            elif dcphase_val < 120:
                judgment_parts.append(f"Cycle in Mid Rise, Trend Improving ({dcphase_val:.0f}°)")
            elif dcphase_val < 150:
                judgment_parts.append(f"Cycle in Late Rise, Watch High Risks ({dcphase_val:.0f}°)")
            elif dcphase_val < 180:
                judgment_parts.append(f"Cycle Nearing Top, Caution on Correction ({dcphase_val:.0f}°)")
            elif dcphase_val < 210:
                judgment_parts.append(f"Cycle Starting Correction, High Volatility ({dcphase_val:.0f}°)")
            elif dcphase_val < 240:
                judgment_parts.append(f"Cycle in Early Decline, Operate with Caution ({dcphase_val:.0f}°)")
            elif dcphase_val < 270:
                judgment_parts.append(f"Cycle in Mid Decline, Bears Dominant ({dcphase_val:.0f}°)")
            elif dcphase_val < 300:
                judgment_parts.append(f"Cycle in Late Decline, Seeking Support ({dcphase_val:.0f}°)")
            elif dcphase_val < 330:
                judgment_parts.append(f"Cycle Nearing Bottom, Watch for Rebound ({dcphase_val:.0f}°)")
            else:
                judgment_parts.append(f"Cycle in Bottom Area, Preparing for Rise ({dcphase_val:.0f}°)")
    if trendmode:
        if main_trend in ["bull", "bear"] and trend_strength == "Strong":
            if 'Trending Mode' in trendmode:
                judgment_parts.append("Market in Trending State, Follow the Trend")
        else:
            if 'Trending Mode' in trendmode:
                judgment_parts.append("Market in Trending State, Follow the Trend")
            elif 'No Trend' in trendmode:
                judgment_parts.append("Market in Consolidation/No Trend, Avoid Chasing")
    
    # Feature signals
    if overbought_count >= 2:
        judgment_parts.append("Multiple Indicators Overbought, Risk of Pullback")
    if oversold_count >= 2:
        judgment_parts.append("Multiple Indicators Oversold, Possible Rebound")
    if divergence_signals:
        judgment_parts.append(f"Divergence detected: {', '.join(divergence_signals)}, Alert for Reversal")
    if 'KDJ' in signals and signals['KDJ'] in ['Overbought', 'Oversold']:
        judgment_parts.append(f"KDJ shows short-term rhythm: {signals['KDJ']}")
    if 'ROC_Inflection' in signals and signals['ROC_Inflection'] in ['Accelerating', 'Decelerating']:
        judgment_parts.append(f"ROC shows {signals['ROC_Inflection']} trend")
    if 'Volume' in signals:
        if signals['Volume'] == 'High Volume':
            judgment_parts.append("Volume Increasing, Active Trading")
        elif signals['Volume'] == 'Low Volume':
            judgment_parts.append("Volume Decreasing, Wait-and-See Mood")
    if 'Bollinger_Bands' in signals:
        if signals['Bollinger_Bands'] == 'Overbought':
            judgment_parts.append("Bollinger Upper Band Breach, Short-term Pullback Likely")
        elif signals['Bollinger_Bands'] == 'Oversold':
            judgment_parts.append("Bollinger Lower Band Breach, Short-term Rebound Likely")
    if 'WilliamsR' in signals:
        if signals['WilliamsR'] == 'Overbought':
            judgment_parts.append("Williams %R Overbought, Alert for Top Risk")
        elif signals['WilliamsR'] == 'Oversold':
            judgment_parts.append("Williams %R Oversold, Watch for Rebound")
    if 'CCI' in signals:
        if signals['CCI'] == 'Overbought':
            judgment_parts.append("CCI Overbought, Increased Short-term Risk")
        elif signals['CCI'] == 'Oversold':
            judgment_parts.append("CCI Oversold, Possible Short-term Rebound")
    
    # Generate detailed summary
    if patterns and levels and pattern_meanings:
        detailed_summary = generate_detailed_summary(signals, patterns, levels, pattern_meanings)
        return "; ".join(judgment_parts), detailed_summary
    
    return "; ".join(judgment_parts), ""


def generate_detailed_summary(signals, patterns, levels, pattern_meanings):
    """Generate detailed analysis summary (Structured)"""
    summary_parts = []

    # 1. Candlestick Pattern Analysis
    pattern_signals = [p for p, v in patterns.items() if v != 0]
    kline_section = "[Candlestick Analysis]"
    if pattern_signals:
        bullish_patterns = [p for p in pattern_signals if patterns[p] > 0]
        bearish_patterns = [p for p in pattern_signals if patterns[p] < 0]
        # Compatibility
        if 'Doji' in bullish_patterns:
            bullish_patterns = [p if p != 'Doji' else 'Bullish Doji' for p in bullish_patterns]
        if 'Doji' in bearish_patterns:
            bearish_patterns = [p if p != 'Doji' else 'Bearish Doji' for p in bearish_patterns]
        if 'Bullish Doji' in pattern_signals and 'Bullish Doji' not in bullish_patterns:
            bullish_patterns.append('Bullish Doji')
        if 'Bearish Doji' in pattern_signals and 'Bearish Doji' not in bearish_patterns:
            bearish_patterns.append('Bearish Doji')
        if bullish_patterns:
            kline_section += f" Detected Bullish Patterns: {', '.join(bullish_patterns)}."
        if bearish_patterns:
            kline_section += f" Detected Bearish Patterns: {', '.join(bearish_patterns)}."
    else:
        kline_section += " No significant reversal patterns detected."
    summary_parts.append(kline_section)

    # 2. Dominant Cycle Interpretation
    cycle_section = "[Dominant Cycle]"
    dcperiod = signals.get('HT_DCPERIOD', '')
    dcphase = signals.get('HT_DCPHASE', '')
    trendmode = signals.get('HT_TRENDMODE', '')
    if dcperiod:
        cycle_section += f" Length: {dcperiod};"
    if dcphase:
        cycle_section += f" Phase: {dcphase};"
    if trendmode:
        cycle_section += f" Mode: {trendmode}."
    if cycle_section != "[Dominant Cycle]":
        summary_parts.append(cycle_section)

    # 3. Technical Indicators Analysis
    tech_section = "[Technical Indicators]"
    if 'MACD' in signals:
        tech_section += f" MACD: {signals['MACD']};"
    if 'RSI' in signals:
        tech_section += f" RSI: {signals['RSI']};"
    if 'OBV' in signals:
        tech_section += f" OBV: {signals['OBV']};"
    if 'ADX_Strength' in signals:
        tech_section += f" ADX: {signals['ADX_Strength']};"
    if 'KDJ' in signals:
        tech_section += f" KDJ: {signals['KDJ']};"
    if 'ROC_Inflection' in signals:
        tech_section += f" ROC: {signals['ROC_Inflection']};"
    if 'Volume' in signals:
        tech_section += f" Volume: {signals['Volume']};"
    if 'Bollinger_Bands' in signals:
        tech_section += f" Bollinger: {signals['Bollinger_Bands']};"
    if 'WilliamsR' in signals:
        tech_section += f" Williams %R: {signals['WilliamsR']};"
    if 'CCI' in signals:
        tech_section += f" CCI: {signals['CCI']};"
    if tech_section != "[Technical Indicators]":
        summary_parts.append(tech_section)

    # 4. Support & Resistance Analysis
    sr_section = "[Support & Resistance]"
    if levels and 'support_detail' in levels and 'resistance_detail' in levels:
        support_detail = levels['support_detail']
        resistance_detail = levels['resistance_detail']
        if support_detail and resistance_detail:
            sr_section += f" Price near Resistance ${resistance_detail.get('price', 0):.2f}. Breakout targets higher; Failure to break, watch Support at ${support_detail.get('price', 0):.2f}."
    if sr_section != "[Support & Resistance]":
        summary_parts.append(sr_section)

    # 5. Risk Warnings
    risk_section = "[Risk Warning]"
    risk_warnings = []
    if any('Divergence' in signal for signal in signals.values()):
        risk_warnings.append("Technical Divergence Detected")
    if any('Overbought' in signal for signal in signals.values()):
        risk_warnings.append("Multiple Indicators Overbought")
    if any('Oversold' in signal for signal in signals.values()):
        risk_warnings.append("Multiple Indicators Oversold")
    if risk_warnings:
        risk_section += ", ".join(risk_warnings) + ", Alert for Reversal."
        summary_parts.append(risk_section)

    # 6. Conclusion
    summary_parts.append("Overall momentum is neutral. Moving averages not fully aligned. Short-term trend direction remains mixed.")

    return "\n".join(summary_parts)
