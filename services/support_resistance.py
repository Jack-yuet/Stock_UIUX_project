"""
Support and Resistance Analysis Module
Contains functions for calculating and analyzing support and resistance levels
"""

def calculate_support_resistance(df):
    """Calculate support and resistance levels"""
    try:
        # Get price data
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        
        # Find peaks and troughs
        def find_peaks(data, window=5):
            peaks = []
            for i in range(window, len(data) - window):
                if all(data[i] >= data[j] for j in range(i - window, i)) and \
                   all(data[i] >= data[j] for j in range(i + 1, i + window + 1)):
                    peaks.append(i)
            return peaks
        
        def find_troughs(data, window=5):
            troughs = []
            for i in range(window, len(data) - window):
                if all(data[i] <= data[j] for j in range(i - window, i)) and \
                   all(data[i] <= data[j] for j in range(i + 1, i + window + 1)):
                    troughs.append(i)
            return troughs
        
        # Find resistance levels (peaks)
        resistance_peaks = find_peaks(highs)
        resistance_levels = [highs[i] for i in resistance_peaks]
        
        # Find support levels (troughs)
        support_troughs = find_troughs(lows)
        support_levels = [lows[i] for i in support_troughs]
        
        # Merge nearby levels
        def merge_levels(levels, tolerance=0.02):
            if not levels:
                return []
            
            merged = []
            levels = sorted(levels)
            
            current_group = [levels[0]]
            for level in levels[1:]:
                if abs(level - current_group[-1]) / current_group[-1] <= tolerance:
                    current_group.append(level)
                else:
                    merged.append(sum(current_group) / len(current_group))
                    current_group = [level]
            
            merged.append(sum(current_group) / len(current_group))
            return merged
        
        resistance_levels = merge_levels(resistance_levels)
        support_levels = merge_levels(support_levels)
        
        # Calculate strength (touches)
        def calculate_strength(levels, data, is_high=True):
            strength_data = []
            for level in levels:
                touches = 0
                for price in data:
                    if is_high:
                        if abs(price - level) / level <= 0.01:  # 1% tolerance
                            touches += 1
                    else:
                        if abs(price - level) / level <= 0.01:  # 1% tolerance
                            touches += 1
                
                strength_data.append({
                    'price': level,
                    'touches': touches,
                    'strength': 'Strong' if touches >= 3 else 'Medium' if touches >= 2 else 'Weak'
                })
            
            return strength_data
        
        resistance_strength = calculate_strength(resistance_levels, highs, True)
        support_strength = calculate_strength(support_levels, lows, False)
        
        # Calculate distance to current price
        current_price = closes[-1]
        
        def calculate_distance(level_price):
            return f"{((current_price - level_price) / level_price * 100):.2f}%"
        
        # Format support data
        support_data = []
        for item in support_strength:
            support_data.append({
                'price': item['price'],
                'strength': item['strength'],
                'touches': item['touches'],
                'distance': calculate_distance(item['price'])
            })
        
        # Format resistance data
        resistance_data = []
        for item in resistance_strength:
            resistance_data.append({
                'price': item['price'],
                'strength': item['strength'],
                'touches': item['touches'],
                'distance': calculate_distance(item['price'])
            })
        
        # Find nearest levels
        def find_nearest_level(levels, current_price, is_support=True):
            if not levels:
                return None
            
            nearest = min(levels, key=lambda x: abs(x['price'] - current_price))
            if is_support and nearest['price'] < current_price:
                return nearest
            elif not is_support and nearest['price'] > current_price:
                return nearest
            return None
        
        nearest_support = find_nearest_level(support_data, current_price, True)
        nearest_resistance = find_nearest_level(resistance_data, current_price, False)
        
        # Detect breakout
        def detect_breakout(levels, current_price, is_support=True):
            if not levels:
                return None
            
            for level in levels:
                if is_support:
                    if current_price < level['price']:
                        return {
                            'type': 'True Breakout',
                            'breakout_price': level['price']
                        }
                else:
                    if current_price > level['price']:
                        return {
                            'type': 'True Breakout',
                            'breakout_price': level['price']
                        }
            return None
        
        support_breakout = detect_breakout(support_data, current_price, True)
        resistance_breakout = detect_breakout(resistance_data, current_price, False)
        
        # Find next level
        def find_next_level(levels, current_price, is_support=True):
            if not levels:
                return None
            
            if is_support:
                # Find support below current price
                valid_levels = [level for level in levels if level['price'] < current_price]
                if valid_levels:
                    return max(valid_levels, key=lambda x: x['price'])
            else:
                # Find resistance above current price
                valid_levels = [level for level in levels if level['price'] > current_price]
                if valid_levels:
                    return min(valid_levels, key=lambda x: x['price'])
            
            return None
        
        next_support = find_next_level(support_data, current_price, True)
        next_resistance = find_next_level(resistance_data, current_price, False)
        
        return {
            'all_supports': support_data,
            'all_resistances': resistance_data,
            'support_detail': {
                'price': nearest_support['price'] if nearest_support else 0,
                'strength': nearest_support['strength'] if nearest_support else '',
                'touches': nearest_support['touches'] if nearest_support else 0,
                'distance': nearest_support['distance'] if nearest_support else '',
                'breakout_status': support_breakout,
                'next_support': next_support
            } if nearest_support else {},
            'resistance_detail': {
                'price': nearest_resistance['price'] if nearest_resistance else 0,
                'strength': nearest_resistance['strength'] if nearest_resistance else '',
                'touches': nearest_resistance['touches'] if nearest_resistance else 0,
                'distance': nearest_resistance['distance'] if nearest_resistance else '',
                'breakout_status': resistance_breakout,
                'next_resistance': next_resistance
            } if nearest_resistance else {}
        }
        
    except Exception as e:
        print(f"Failed to calculate support/resistance: {e}")
        return {
            'all_supports': [],
            'all_resistances': [],
            'support_detail': {},
            'resistance_detail': {}
        } 