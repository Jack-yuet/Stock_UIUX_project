"""
Candlestick Pattern Detection Module
Contains pure Python/Pandas detection functions for various candlestick patterns
to avoid TA-Lib binary dependencies on Vercel
"""

import pandas as pd
import numpy as np

# Candlestick Pattern Configuration
CANDLESTICK_CONFIG = [
    {"name": "Hammer", "direction": "bullish"},
    {"name": "Morning Star", "direction": "bullish"},
    {"name": "Bullish Engulfing", "direction": "bullish", "value": 100},
    {"name": "Bearish Engulfing", "direction": "bearish", "value": -100},
    {"name": "Doji", "direction": "neutral"},
    {"name": "Three White Soldiers", "direction": "bullish"},
    {"name": "Three Black Crows", "direction": "bearish"},
    {"name": "Hanging Man", "direction": "bearish"},
    {"name": "Evening Star", "direction": "bearish"},
    {"name": "Dark Cloud Cover", "direction": "bearish"},
    {"name": "Piercing Line", "direction": "bullish"},
    {"name": "Shooting Star", "direction": "bearish"},
    {"name": "Inverted Hammer", "direction": "bullish"},
    {"name": "Rising Three Methods", "direction": "bullish", "value": 100},
    {"name": "Falling Three Methods", "direction": "bearish", "value": -100},
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

# Helper functions for pattern detection
def is_bullish(row):
    return row['Close'] > row['Open']

def is_bearish(row):
    return row['Close'] < row['Open']

def body_size(row):
    return abs(row['Close'] - row['Open'])

def upper_shadow(row):
    return row['High'] - max(row['Close'], row['Open'])

def lower_shadow(row):
    return min(row['Close'], row['Open']) - row['Low']

def is_doji(row, threshold=0.1):
    return body_size(row) <= (row['High'] - row['Low']) * threshold

def detect_candlestick_patterns(df, window=30):
    """Batch detect candlestick patterns and output structured results (Pure Python implementation)"""
    patterns = {}
    pattern_meanings = PATTERN_MEANINGS.copy()
    structured_patterns = []
    
    if len(df) < 3:
        return patterns, pattern_meanings, structured_patterns
        
    closes = df['Close']
    dates = df.index if hasattr(df.index, 'values') else pd.RangeIndex(len(df))
    
    # We iterate over the dataframe window
    # Optimized: only check the last 'window' candles, plus buffer for multi-candle patterns
    start_idx = max(3, len(df) - window)
    
    for i in range(start_idx, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        
        date_str = str(dates[i]) if hasattr(dates, '__getitem__') else str(i)
        position = get_position(curr['Close'], closes[max(0, i-window):i+1])
        
        detected = []
        
        # 1. Hammer / Hanging Man (Long lower shadow, small body)
        # Hammer: Downtrend (Low position), Hanging Man: Uptrend (High position)
        if lower_shadow(curr) > 2 * body_size(curr) and upper_shadow(curr) < body_size(curr):
            if position == "Bottom":
                detected.append(("Hammer", 100))
            elif position == "Top":
                detected.append(("Hanging Man", -100))
                
        # 2. Inverted Hammer / Shooting Star (Long upper shadow, small body)
        if upper_shadow(curr) > 2 * body_size(curr) and lower_shadow(curr) < body_size(curr):
            if position == "Bottom":
                detected.append(("Inverted Hammer", 100))
            elif position == "Top":
                detected.append(("Shooting Star", -100))
        
        # 3. Engulfing
        if is_bearish(prev) and is_bullish(curr) and \
           curr['Close'] > prev['Open'] and curr['Open'] < prev['Close']:
            detected.append(("Bullish Engulfing", 100))
            
        if is_bullish(prev) and is_bearish(curr) and \
           curr['Close'] < prev['Open'] and curr['Open'] > prev['Close']:
            detected.append(("Bearish Engulfing", -100))
            
        # 4. Doji
        if is_doji(curr):
            name = "Bullish Doji" if is_bullish(curr) else "Bearish Doji"
            detected.append((name, 50 if is_bullish(curr) else -50))
            # Also generic Doji
            detected.append(("Doji", 10))
            
        # 5. Morning Star (Bearish, Doji/Small, Bullish)
        if is_bearish(prev2) and is_bullish(curr) and \
           body_size(prev) < body_size(prev2) * 0.3 and \
           curr['Close'] > (prev2['Open'] + prev2['Close'])/2:
            detected.append(("Morning Star", 100))
            
        # 6. Evening Star (Bullish, Doji/Small, Bearish)
        if is_bullish(prev2) and is_bearish(curr) and \
           body_size(prev) < body_size(prev2) * 0.3 and \
           curr['Close'] < (prev2['Open'] + prev2['Close'])/2:
            detected.append(("Evening Star", -100))
            
        # 7. Dark Cloud Cover (Bullish, Bearish opens above high, closes below mid)
        if is_bullish(prev) and is_bearish(curr) and \
           curr['Open'] > prev['High'] and \
           curr['Close'] < (prev['Open'] + prev['Close'])/2 and \
           curr['Close'] > prev['Open']:
            detected.append(("Dark Cloud Cover", -100))
            
        # 8. Piercing Line (Bearish, Bullish opens below low, closes above mid)
        if is_bearish(prev) and is_bullish(curr) and \
           curr['Open'] < prev['Low'] and \
           curr['Close'] > (prev['Open'] + prev['Close'])/2 and \
           curr['Close'] < prev['Open']:
            detected.append(("Piercing Line", 100))
            
        # 9. Three White Soldiers (3 bullish candles)
        if i >= 2 and is_bullish(curr) and is_bullish(prev) and is_bullish(prev2) and \
           curr['Close'] > prev['Close'] and prev['Close'] > prev2['Close']:
            detected.append(("Three White Soldiers", 100))
            
        # 10. Three Black Crows (3 bearish candles)
        if i >= 2 and is_bearish(curr) and is_bearish(prev) and is_bearish(prev2) and \
           curr['Close'] < prev['Close'] and prev['Close'] < prev2['Close']:
            detected.append(("Three Black Crows", -100))
            
        # Register found patterns
        for name, val in detected:
            strength = get_strength_level(val)
            structured_patterns.append({
                "name": name,
                "index": i,
                "date": date_str,
                "strength": int(val),
                "strength_level": strength,
                "position": position
            })
            
            # Update latest patterns dict (only for the very last candle)
            if i == len(df) - 1:
                # Map specific Doji back to generic Doji signal in patterns dict if needed
                key = "Doji" if "Doji" in name else name
                if key in [c["name"] for c in CANDLESTICK_CONFIG]: 
                    patterns[key] = int(val)

    # Custom: Breakdown Long Bearish Candle
    if len(df) >= 2:
        current = df.iloc[-1]
        support_level = df.tail(20)['Low'].min()
        avg_body = (df['Close'] - df['Open']).abs().tail(20).mean()
        
        if (
            is_bearish(current) and
            current['Close'] < support_level and
            body_size(current) > avg_body * 1.5
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
    
    # Fill missing patterns with 0
    for conf in CANDLESTICK_CONFIG:
        if conf["name"] not in patterns:
            patterns[conf["name"]] = 0
            
    return patterns, pattern_meanings, structured_patterns