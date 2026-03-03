"""
趋势分析服务模块
整合各个子模块，提供完整的趋势分析功能
"""

import yfinance as yf
import pandas as pd
from .technical_indicators import calculate_technical_indicators, analyze_trend_signals
from .candlestick_patterns import detect_candlestick_patterns
from .support_resistance import calculate_support_resistance
from .trend_judgment import generate_comprehensive_trend_judgment

def analyze_stock_trend(stock_code, period="1y"):
    """
    Analyze stock trend
    Args:
        stock_code: Stock code
        period: Analysis period, default 1 year
    Returns:
        dict: Dictionary containing full analysis results
    """
    try:
        # Get stock data
        stock = yf.Ticker(stock_code)
        df = stock.history(period=period)
        
        if df.empty:
            return {"error": "Unable to fetch stock data"}
        
        # Calculate technical indicators
        df = calculate_technical_indicators(df)
        
        # Analyze trend signals
        signals = analyze_trend_signals(df)
        
        # Detect candlestick patterns (adapted for structured output)
        patterns, pattern_meanings, structured_patterns = detect_candlestick_patterns(df)
        
        # Calculate support and resistance levels
        levels = calculate_support_resistance(df)
        
        # Generate comprehensive trend judgment
        judgment, detailed_summary = generate_comprehensive_trend_judgment(
            signals, patterns, levels, pattern_meanings
        )
        
        # Get current price info
        current_price = df['Close'].iloc[-1]
        price_change = df['Close'].iloc[-1] - df['Close'].iloc[-2] if len(df) > 1 else 0
        price_change_pct = (price_change / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0
        
        # Build result
        result = {
            "stock_code": stock_code,
            "current_price": round(current_price, 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "period": period,
            "technical_signals": signals,
            "candlestick_patterns": patterns,
            "pattern_meanings": pattern_meanings,
            "support_resistance": levels,
            "trend_judgment": judgment,
            "detailed_summary": detailed_summary,
            "analysis_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "structured_candlestick_patterns": structured_patterns,
            # Backward compatibility keys (if frontend uses them directly)
            "技术指标信号": signals,
            "K线形态": patterns,
            "形态含义": pattern_meanings,
            "支撑阻力位": levels,
            "综合趋势判断": judgment,
            "详细分析总结": detailed_summary,
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Error during analysis: {str(e)}"}

def get_stock_info(stock_code):
    """
    Get stock basic info
    Args:
        stock_code: Stock code
    Returns:
        dict: Stock basic info
    """
    try:
        stock = yf.Ticker(stock_code)
        info = stock.info
        
        return {
            "stock_code": stock_code,
            "company_name": info.get('longName', 'Unknown'),
            "industry": info.get('industry', 'Unknown'),
            "market_cap": info.get('marketCap', 0),
            "week_52_high": info.get('fiftyTwoWeekHigh', 0),
            "week_52_low": info.get('fiftyTwoWeekLow', 0),
            "avg_volume": info.get('averageVolume', 0),
            # Backward compatibility
            "股票代码": stock_code,
            "公司名称": info.get('longName', 'Unknown'),
            "行业": info.get('industry', 'Unknown'),
            "市值": info.get('marketCap', 0),
            "52周最高": info.get('fiftyTwoWeekHigh', 0),
            "52周最低": info.get('fiftyTwoWeekLow', 0),
            "平均成交量": info.get('averageVolume', 0)
        }
    except Exception as e:
        return {"error": f"Failed to get stock info: {str(e)}"} 