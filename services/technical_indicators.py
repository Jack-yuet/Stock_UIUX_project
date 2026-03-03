"""
技术指标计算模块
包含各种技术指标的计算函数
"""

import pandas as pd
import talib

def calculate_technical_indicators(df):
    """Calculate Technical Indicators"""
    try:
        # Moving Averages
        df['MA5'] = talib.SMA(df['Close'], timeperiod=5)
        df['MA10'] = talib.SMA(df['Close'], timeperiod=10)
        df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
        df['MA50'] = talib.SMA(df['Close'], timeperiod=50)
        
        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = talib.MACD(df['Close'])
        
        # RSI
        df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
        
        # Bollinger Bands
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = talib.BBANDS(df['Close'])
        
        # Volume MA
        df['Volume_MA20'] = talib.SMA(df['Volume'], timeperiod=20)
        
        # Momentum
        df['MOM'] = talib.MOM(df['Close'], timeperiod=10)
        
        # ROC
        df['ROC'] = talib.ROC(df['Close'], timeperiod=10)
        
        # OBV
        df['OBV'] = talib.OBV(df['Close'], df['Volume'])
        
        # ADX
        df['ADX'] = talib.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)
        
        # KDJ
        df['STOCH_K'], df['STOCH_D'] = talib.STOCH(df['High'], df['Low'], df['Close'])
        
        # Williams %R
        df['WILLR'] = talib.WILLR(df['High'], df['Low'], df['Close'], timeperiod=14)
        
        # CCI
        df['CCI'] = talib.CCI(df['High'], df['Low'], df['Close'], timeperiod=14)
        
        # ATR
        df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
        
        # HT_DCPERIOD, HT_DCPHASE, HT_TRENDMODE
        df['HT_DCPERIOD'] = talib.HT_DCPERIOD(df['Close'])
        df['HT_DCPHASE'] = talib.HT_DCPHASE(df['Close'])
        df['HT_TRENDMODE'] = talib.HT_TRENDMODE(df['Close'])
        
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
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # 1. Moving Average Trend
    signals['MA_Trend'] = 'Bullish' if latest['Close'] > latest['MA20'] else 'Bearish'
    signals['MA5vsMA20'] = 'Bullish' if latest['MA5'] > latest['MA20'] else 'Bearish'
    signals['MA20vsMA50'] = 'Bullish' if latest['MA20'] > latest['MA50'] else 'Bearish'
    
    # 2. MACD Signal
    if latest['MACD'] > latest['MACD_Signal']:
        signals['MACD'] = 'Bullish'
    elif latest['MACD'] < latest['MACD_Signal']:
        signals['MACD'] = 'Bearish'
    else:
        signals['MACD'] = 'Neutral'
    
    # 3. RSI Signal
    if latest['RSI'] > 70:
        signals['RSI'] = 'Overbought'
    elif latest['RSI'] < 30:
        signals['RSI'] = 'Oversold'
    else:
        signals['RSI'] = 'Neutral'
    
    # 4. Bollinger Bands Signal
    if latest['Close'] > latest['BB_Upper']:
        signals['Bollinger_Bands'] = 'Overbought'
    elif latest['Close'] < latest['BB_Lower']:
        signals['Bollinger_Bands'] = 'Oversold'
    else:
        signals['Bollinger_Bands'] = 'Normal'
    
    # 5. Volume Signal
    if latest['Volume'] > latest['Volume_MA20'] * 1.5:
        signals['Volume'] = 'High Volume'
    elif latest['Volume'] < latest['Volume_MA20'] * 0.5:
        signals['Volume'] = 'Low Volume'
    else:
        signals['Volume'] = 'Normal'
    
    # 6. Price Momentum
    if latest['MOM'] > 0:
        signals['Momentum'] = 'Bullish'
    else:
        signals['Momentum'] = 'Bearish'
    
    # 7. Rate of Change
    if latest['ROC'] > 0:
        signals['ROC'] = 'Bullish'
    else:
        signals['ROC'] = 'Bearish'
    
    # 8. OBV Analysis
    if len(df) >= 2:
        obv_trend = 'Bullish' if latest['OBV'] > prev['OBV'] else 'Bearish'
        price_trend = 'Bullish' if latest['Close'] > prev['Close'] else 'Bearish'
        
        if obv_trend == price_trend:
            signals['OBV'] = f'Resonance {obv_trend}'
        else:
            signals['OBV'] = f'Divergence {obv_trend}'
    else:
        signals['OBV'] = 'Insufficient Data'
    
    # 9. ADX (Trend Strength) Analysis
    if 'ADX' not in df.columns:
        # Calculate ADX
        high_prices = df['High'].values
        low_prices = df['Low'].values
        close_prices = df['Close'].values
        df['ADX'] = talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)
        latest = df.iloc[-1]  # Refresh latest data
    
    if latest['ADX'] > 25:
        signals['ADX_Strength'] = 'Strong Trend'
    elif latest['ADX'] > 20:
        signals['ADX_Strength'] = 'Medium Trend'
    else:
        signals['ADX_Strength'] = 'Weak Trend'
    
    # 10. KDJ Analysis
    if 'STOCH_K' in df.columns and 'STOCH_D' in df.columns:
        k_value = latest['STOCH_K']
        d_value = latest['STOCH_D']
        
        # Calculate J value
        j_value = 3 * k_value - 2 * d_value
        
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
        roc_current = latest['ROC']
        roc_prev = prev['ROC']
        roc_prev2 = df.iloc[-3]['ROC']
        
        if roc_current > roc_prev > roc_prev2:
            signals['ROC_Inflection'] = 'Accelerating'
        elif roc_current < roc_prev < roc_prev2:
            signals['ROC_Inflection'] = 'Decelerating'
        else:
            signals['ROC_Inflection'] = 'Oscillating'
    else:
        signals['ROC_Inflection'] = 'Insufficient Data'
    
    # 12. Williams %R Analysis
    if 'WILLR' in df.columns:
        willr_value = latest['WILLR']
        if willr_value < -80:
            signals['WilliamsR'] = 'Oversold'
        elif willr_value > -20:
            signals['WilliamsR'] = 'Overbought'
        else:
            signals['WilliamsR'] = 'Normal'
    
    # 13. CCI Analysis
    if 'CCI' in df.columns:
        cci_value = latest['CCI']
        if cci_value > 100:
            signals['CCI'] = 'Overbought'
        elif cci_value < -100:
            signals['CCI'] = 'Oversold'
        else:
            signals['CCI'] = 'Normal'
    
    # HT_DCPERIOD
    if 'HT_DCPERIOD' in df.columns:
        signals['HT_DCPERIOD'] = f"Dominant Cycle: {latest['HT_DCPERIOD']:.2f}" if not pd.isna(latest['HT_DCPERIOD']) else 'No Data'
    # HT_DCPHASE
    if 'HT_DCPHASE' in df.columns:
        signals['HT_DCPHASE'] = f"Dominant Phase: {latest['HT_DCPHASE']:.2f}" if not pd.isna(latest['HT_DCPHASE']) else 'No Data'
    # HT_TRENDMODE
    if 'HT_TRENDMODE' in df.columns:
        if latest['HT_TRENDMODE'] == 1:
            signals['HT_TRENDMODE'] = 'Trending Mode'
        elif latest['HT_TRENDMODE'] == 0:
            signals['HT_TRENDMODE'] = 'No Trend'
        else:
            signals['HT_TRENDMODE'] = 'No Data'
    
    return signals 