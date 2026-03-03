"""
Candlestick Pattern Detection Module
Contains detection functions for various candlestick patterns
"""

import talib
import pandas as pd

# Candlestick Pattern Configuration
CANDLESTICK_CONFIG = [
    {"name": "Hammer", "talib_func": "CDLHAMMER", "direction": "bullish"},
    {"name": "Morning Star", "talib_func": "CDLMORNINGSTAR", "direction": "bullish"},
    {"name": "Bullish Engulfing", "talib_func": "CDLENGULFING", "direction": "bullish", "value": 100},
    {"name": "Bearish Engulfing", "talib_func": "CDLENGULFING", "direction": "bearish", "value": -100},
    {"name": "Doji", "talib_func": "CDLDOJI", "direction": "neutral"},
    {"name": "Three White Soldiers", "talib_func": "CDL3WHITESOLDIERS", "direction": "bullish"},
    {"name": "Three Black Crows", "talib_func": "CDL3BLACKCROWS", "direction": "bearish"},
    {"name": "Hanging Man", "talib_func": "CDLHANGINGMAN", "direction": "bearish"},
    {"name": "Evening Star", "talib_func": "CDLEVENINGSTAR", "direction": "bearish"},
    {"name": "Dark Cloud Cover", "talib_func": "CDLDARKCLOUDCOVER", "direction": "bearish"},
    {"name": "Piercing Line", "talib_func": "CDLPIERCING", "direction": "bullish"},
    {"name": "Shooting Star", "talib_func": "CDLSHOOTINGSTAR", "direction": "bearish"},
    {"name": "Inverted Hammer", "talib_func": "CDLINVERTEDHAMMER", "direction": "bullish"},
    {"name": "Rising Three Methods", "talib_func": "CDLRISEFALL3METHODS", "direction": "bullish", "value": 100},
    {"name": "Falling Three Methods", "talib_func": "CDLRISEFALL3METHODS", "direction": "bearish", "value": -100},
]

# Pattern Meanings
PATTERN_MEANINGS = {
    "Hammer": "Bottom reversal signal. Long lower shadow, small body, indicating buying pressure.",
    "Morning Star": "Bottom reversal signal. Consists of three candlesticks.",
    "Bullish Engulfing": "Small bearish candle followed by a large bullish candle that completely engulfs it. Strong reversal signal.",
    "Bearish Engulfing": "Small bullish candle followed by a large bearish candle that completely engulfs it. Strong reversal signal.",
    "Doji": "Opening and closing prices are virtually the same. Indicates indecision between buyers and sellers.",
    "Three White Soldiers": "Three consecutive long bullish candles, each closing higher. Strong bullish signal.",
    "Three Black Crows": "Three consecutive long bearish candles. Indicates a strong downtrend.",
    "Hanging Man": "Top reversal signal. Long lower shadow, small body, indicating selling pressure.",
    "Evening Star": "Top reversal signal. Consists of three candlesticks, indicating a downtrend.",
    "Dark Cloud Cover": "Top reversal signal. Bearish candle opens above the previous bullish candle's high and closes below its midpoint.",
    "Piercing Line": "Bottom reversal signal. Bullish candle opens below the previous bearish candle's low and closes above its midpoint.",
    "Shooting Star": "Top reversal signal. Long upper shadow, small body.",
    "Inverted Hammer": "Bottom reversal signal. Long upper shadow, small body.",
    "Rising Three Methods": "A long bullish candle followed by three small bearish candles within its range, then another long bullish candle. Continuation signal.",
    "Falling Three Methods": "A long bearish candle followed by three small bullish candles within its range, then another long bearish candle. Continuation signal.",
    "Breakdown Long Bearish Candle": "Strong downside confirmation, breaking through structural levels."
}

# Signal Strength Levels
def get_strength_level(val):
    abs_val = abs(val)
    if abs_val >= 100:
        return "Strong"
    elif abs_val >= 50:
        return "Medium"
    elif abs_val > 0:
        return "Weak"
    else:
        return "None"
    
# Determine Pattern Position (Top/Bottom/Neutral)
def get_position(close, closes):
    if close >= closes.quantile(0.66):
        return "Top"
    elif close <= closes.quantile(0.33):
        return "Bottom"
    else:
        return "Neutral"

def detect_candlestick_patterns(df, window=30):
    """Batch detect candlestick patterns and output structured results"""
    patterns = {}
    pattern_meanings = PATTERN_MEANINGS.copy()
    structured_patterns = []
    closes = df['Close']
    dates = df.index if hasattr(df.index, 'values') else pd.RangeIndex(len(df))

    for conf in CANDLESTICK_CONFIG:
        func = getattr(talib, conf["talib_func"])
        # Special handling: Engulfing and Three Methods need to distinguish positive/negative
        if conf["name"] in ["Bullish Engulfing", "Bearish Engulfing"]:
            arr = func(df['Open'], df['High'], df['Low'], df['Close'])
            if conf["name"] == "Bullish Engulfing":
                mask = arr == 100
            else:
                mask = arr == -100
        elif conf["name"] in ["Rising Three Methods", "Falling Three Methods"]:
            arr = func(df['Open'], df['High'], df['Low'], df['Close'])
            if conf["name"] == "Rising Three Methods":
                mask = arr == 100
            else:
                mask = arr == -100
        elif conf["name"] == "Doji":
            arr = func(df['Open'], df['High'], df['Low'], df['Close'])
            mask = arr != 0
            for idx in range(-window, 0):
                if abs(idx) > len(df):
                    continue
                i = idx if idx >= 0 else len(df) + idx
                if mask[i]:
                    val = arr[i]
                    strength = get_strength_level(val)
                    position = get_position(closes[i], closes[-window:])
                    # Distinguish Bullish/Bearish Doji
                    if df['Close'].iloc[i] >= df['Open'].iloc[i]:
                        doji_name = "Bullish Doji"
                    else:
                        doji_name = "Bearish Doji"
                    structured_patterns.append({
                        "name": doji_name,
                        "index": i,
                        "date": str(dates[i]) if hasattr(dates, '__getitem__') else str(i),
                        "strength": int(val),
                        "strength_level": strength,
                        "position": position
                    })
            # patterns dict still keeps the original Doji signal
            if mask[-1]:
                patterns[conf["name"]] = int(arr[-1])
            else:
                patterns[conf["name"]] = 0
            continue
        else:
            arr = func(df['Open'], df['High'], df['Low'], df['Close'])
            mask = arr != 0
        # Check the last 'window' candles
        for idx in range(-window, 0):
            if abs(idx) > len(df):
                continue
            i = idx if idx >= 0 else len(df) + idx
            if mask[i]:
                val = arr[i]
                strength = get_strength_level(val)
                position = get_position(closes[i], closes[-window:])
                structured_patterns.append({
                    "name": conf["name"],
                    "index": i,
                    "date": str(dates[i]) if hasattr(dates, '__getitem__') else str(i),
                    "strength": int(val),
                    "strength_level": strength,
                    "position": position
                })
        # Compatibility: Keep only the last candle signal
        if mask[-1]:
            patterns[conf["name"]] = int(arr[-1])
        else:
            patterns[conf["name"]] = 0
    
    # Custom detection: Breakdown Long Bearish Candle
    if len(df) >= 2:
        current = df.iloc[-1]
        prev = df.iloc[-2]
        support_level = df.tail(20)['Low'].min()
        avg_body = abs(current['Close'] - current['Open'])
        avg_atr = df['ATR'].tail(20).mean() if 'ATR' in df.columns else 0
        if (
            current['Close'] < current['Open'] and
            current['Close'] < support_level and
            avg_atr > 0 and
            avg_body > avg_atr * 0.5
        ):
            patterns['Breakdown Long Bearish Candle'] = -100
            structured_patterns.append({
                "name": "Breakdown Long Bearish Candle",
                "index": len(df)-1,
                "date": str(dates[-1]) if hasattr(dates, '__getitem__') else str(len(df)-1),
                "strength": -100,
                "strength_level": "Strong",
                "position": get_position(current['Close'], closes[-window:])
            })
        else:
            patterns['Breakdown Long Bearish Candle'] = 0
    else:
        patterns['Breakdown Long Bearish Candle'] = 0

    pattern_meanings['Breakdown Long Bearish Candle'] = PATTERN_MEANINGS['Breakdown Long Bearish Candle']
    
    return patterns, pattern_meanings, structured_patterns 