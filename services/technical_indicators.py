"""
Technical Indicators Calculation Module
Contains functions for calculating various technical indicators using pandas_ta (pure python compatible)
"""

import pandas as pd
import pandas_ta as ta
import numpy as np

def calculate_technical_indicators(df):
    """Calculate Technical Indicators"""
    try:
        # Ensure correct index
        # pandas_ta attaches to df.ta
        
        # Moving Averages
        df['MA5'] = df.ta.sma(length=5)
        df['MA10'] = df.ta.sma(length=10)
        df['MA20'] = df.ta.sma(length=20)
        df['MA50'] = df.ta.sma(length=50)
        
        # MACD (Returns 3 columns: MACD, Histogram, Signal)
        macd = df.ta.macd(close='Close', fast=12, slow=26, signal=9)
        if macd is not None:
            # Column names from pandas_ta are usually MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
            # We rename them to match our convention
            cols = macd.columns
            df['MACD'] = macd[cols[0]]
            df['MACD_Hist'] = macd[cols[1]]
            df['MACD_Signal'] = macd[cols[2]]
        
        # RSI
        df['RSI'] = df.ta.rsi(length=14)
        
        # Bollinger Bands
        bb = df.ta.bbands(length=20, std=2)
        if bb is not None:
            # BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
            cols = bb.columns
            df['BB_Lower'] = bb[cols[0]]
            df['BB_Middle'] = bb[cols[1]]
            df['BB_Upper'] = bb[cols[2]]
        
        # Volume MA
        df['Volume_MA20'] = df.ta.sma(close='Volume', length=20)
        
        # Momentum (MOM)
        df['MOM'] = df.ta.mom(length=10)
        
        # ROC
        df['ROC'] = df.ta.roc(length=10)
        
        # OBV
        df['OBV'] = df.ta.obv()
        
        # ADX (Requires High, Low, Close)
        adx = df.ta.adx(length=14)
        if adx is not None:
            # ADX_14, DMP_14, DMN_14
            cols = adx.columns
            df['ADX'] = adx[cols[0]]
        
        # KDJ (Stochastic)
        stoch = df.ta.stoch()
        if stoch is not None:
            # STOCHk_14_3_3, STOCHd_14_3_3
            cols = stoch.columns
            df['STOCH_K'] = stoch[cols[0]]
            df['STOCH_D'] = stoch[cols[1]]
        
        # Williams %R
        df['WILLR'] = df.ta.willr(length=14)
        
        # CCI
        df['CCI'] = df.ta.cci(length=14)
        
        # ATR
        df['ATR'] = df.ta.atr(length=14)
        
        # Hilbert Transform Indicators - pandas_ta may not have exact equivalents
        # We will mock them or use approximation if crucial, or remove reliance.
        # For Vercel deployment without TA-Lib C library, we skip HT functions 
        # or implement basic versions if needed. 
        # For now, we set them to None or 0 to avoid errors in downstream logic.
        df['HT_DCPERIOD'] = 0
        df['HT_DCPHASE'] = 0
        df['HT_TRENDMODE'] = 0
        
        # Daily Return
        df['Daily_Return'] = df['Close'].pct_change() * 100
        
        return df
    except Exception as e:
        print(f"Failed to calculate technical indicators: {e}")
        return df

def analyze_trend_signals(df):
    """Analyze trend signals"""
    signals = {}
    
    # Get latest data
    if df.empty:
        return signals
        
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # Helper to safe get
    def get_val(row, key, default=0):
        return row[key] if key in row and pd.notna(row[key]) else default

    # 1. Moving Average Trend
    close = get_val(latest, 'Close')
    ma20 = get_val(latest, 'MA20')
    ma5 = get_val(latest, 'MA5')
    ma50 = get_val(latest, 'MA50')
    
    signals['MA_Trend'] = 'Bullish' if close > ma20 else 'Bearish'
    signals['MA5vsMA20'] = 'Bullish' if ma5 > ma20 else 'Bearish'
    signals['MA20vsMA50'] = 'Bullish' if ma20 > ma50 else 'Bearish'
    
    # 2. MACD Signal
    macd = get_val(latest, 'MACD')
    macd_sig = get_val(latest, 'MACD_Signal')
    if macd > macd_sig:
        signals['MACD'] = 'Bullish'
    elif macd < macd_sig:
        signals['MACD'] = 'Bearish'
    else:
        signals['MACD'] = 'Neutral'
    
    # 3. RSI Signal
    rsi = get_val(latest, 'RSI', 50)
    if rsi > 70:
        signals['RSI'] = 'Overbought'
    elif rsi < 30:
        signals['RSI'] = 'Oversold'
    else:
        signals['RSI'] = 'Neutral'
    
    # 4. Bollinger Bands Signal
    bb_upper = get_val(latest, 'BB_Upper', float('inf'))
    bb_lower = get_val(latest, 'BB_Lower', 0)
    if close > bb_upper:
        signals['Bollinger_Bands'] = 'Overbought'
    elif close < bb_lower:
        signals['Bollinger_Bands'] = 'Oversold'
    else:
        signals['Bollinger_Bands'] = 'Normal'
    
    # 5. Volume Signal
    vol = get_val(latest, 'Volume')
    vol_ma20 = get_val(latest, 'Volume_MA20')
    if vol > vol_ma20 * 1.5:
        signals['Volume'] = 'High Volume'
    elif vol < vol_ma20 * 0.5:
        signals['Volume'] = 'Low Volume'
    else:
        signals['Volume'] = 'Normal'
    
    # 6. Price Momentum
    mom = get_val(latest, 'MOM')
    if mom > 0:
        signals['Momentum'] = 'Bullish'
    else:
        signals['Momentum'] = 'Bearish'
    
    # 7. Rate of Change
    roc = get_val(latest, 'ROC')
    if roc > 0:
        signals['ROC'] = 'Bullish'
    else:
        signals['ROC'] = 'Bearish'
    
    # 8. OBV Analysis
    if len(df) >= 2:
        obv = get_val(latest, 'OBV')
        prev_obv = get_val(prev, 'OBV')
        prev_close = get_val(prev, 'Close')
        
        obv_trend = 'Bullish' if obv > prev_obv else 'Bearish'
        price_trend = 'Bullish' if close > prev_close else 'Bearish'
        
        if obv_trend == price_trend:
            signals['OBV'] = f'Resonance {obv_trend}'
        else:
            signals['OBV'] = f'Divergence {obv_trend}'
    else:
        signals['OBV'] = 'Insufficient Data'
    
    # 9. ADX (Trend Strength) Analysis
    # Ensure ADX is calculated
    adx = get_val(latest, 'ADX', 0)
    
    if adx > 25:
        signals['ADX_Strength'] = 'Strong Trend'
    elif adx > 20:
        signals['ADX_Strength'] = 'Medium Trend'
    else:
        signals['ADX_Strength'] = 'Weak Trend'
    
    # 10. KDJ Analysis
    k_value = get_val(latest, 'STOCH_K', 50)
    d_value = get_val(latest, 'STOCH_D', 50)
    
    if k_value > 80 and d_value > 80:
        signals['KDJ'] = 'Overbought'
    elif k_value < 20 and d_value < 20:
        signals['KDJ'] = 'Oversold'
    elif k_value > d_value:
        signals['KDJ'] = 'Bullish'
    else:
        signals['KDJ'] = 'Bearish'
    
    # 11. ROC Inflection Analysis
    if len(df) >= 3:
        roc_current = roc
        roc_prev = get_val(prev, 'ROC')
        roc_prev2 = get_val(df.iloc[-3], 'ROC')
        
        if roc_current > roc_prev > roc_prev2:
            signals['ROC_Inflection'] = 'Accelerating'
        elif roc_current < roc_prev < roc_prev2:
            signals['ROC_Inflection'] = 'Decelerating'
        else:
            signals['ROC_Inflection'] = 'Oscillating'
    else:
        signals['ROC_Inflection'] = 'Insufficient Data'
    
    # 12. Williams %R Analysis
    willr_value = get_val(latest, 'WILLR', -50)
    if willr_value < -80:
        signals['WilliamsR'] = 'Oversold'
    elif willr_value > -20:
        signals['WilliamsR'] = 'Overbought'
    else:
        signals['WilliamsR'] = 'Normal'
    
    # 13. CCI Analysis
    cci_value = get_val(latest, 'CCI', 0)
    if cci_value > 100:
        signals['CCI'] = 'Overbought'
    elif cci_value < -100:
        signals['CCI'] = 'Oversold'
    else:
        signals['CCI'] = 'Normal'
    
    # HT Indicators (Mocked)
    signals['HT_DCPERIOD'] = 'No Data (Serverless)'
    signals['HT_DCPHASE'] = 'No Data (Serverless)'
    signals['HT_TRENDMODE'] = 'No Data (Serverless)'
    
    return signals