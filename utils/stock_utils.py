import pandas as pd
from datetime import datetime
from typing import Any, List

def safe_get(row, keys: List[str], default: Any = None):
    """安全获取字典中的值，支持多个可能的键名"""
    for key in keys:
        if key in row:
            return row[key]
    return default

def get_period_string(period):
    """将时间范围转换为yfinance支持的格式"""
    period_map = {
        '7d': '7d',
        '1mo': '1mo', 
        '1y': '1y',
        '3y': '3y',
        '7y': '7y'
    }
    return period_map.get(period, '1y')

def calculate_technical_indicators(hist_data):
    """计算技术指标"""
    if hist_data.empty:
        return hist_data
    
    # 确保数据按时间排序
    hist_data = hist_data.sort_index()
    
    # 移动平均线
    hist_data['MA5'] = hist_data['Close'].rolling(window=5).mean()
    hist_data['MA10'] = hist_data['Close'].rolling(window=10).mean()
    hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
    
    # 计算涨跌幅
    hist_data['Daily_Return'] = hist_data['Close'].pct_change() * 100
    
    # 计算成交量移动平均
    hist_data['Volume_MA5'] = hist_data['Volume'].rolling(window=5).mean()
    
    return hist_data

def calculate_kline_data(hist_data, interval='D'):
    """计算K线图数据，支持日(D)、周(W)、月(M)"""
    if hist_data.empty:
        return []
    
    # 确保索引是datetime类型
    hist_data.index = pd.to_datetime(hist_data.index)
    
    if interval == 'D':
        # 日K线，直接使用原始数据
        kline_data = hist_data
    elif interval == 'W':
        # 周K线，按周聚合
        kline_data = hist_data.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
    elif interval == 'M':
        # 月K线，按月聚合
        kline_data = hist_data.resample('M').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
    else:
        # 默认使用日K线
        kline_data = hist_data
    
    # 移除空值
    kline_data = kline_data.dropna()
    
    # 转换为列表格式
    kline_list = []
    for date, row in kline_data.iterrows():
        kline_item = {
            'date': date.strftime('%Y-%m-%d'),
            'open': round(row['Open'], 2),
            'high': round(row['High'], 2),
            'low': round(row['Low'], 2),
            'close': round(row['Close'], 2),
            'volume': int(row['Volume'])
        }
        
        # 添加技术指标（如果存在）
        if 'MA5' in row and pd.notna(row['MA5']):
            kline_item['ma5'] = round(row['MA5'], 2)
        if 'MA10' in row and pd.notna(row['MA10']):
            kline_item['ma10'] = round(row['MA10'], 2)
        if 'MA20' in row and pd.notna(row['MA20']):
            kline_item['ma20'] = round(row['MA20'], 2)
        if 'Daily_Return' in row and pd.notna(row['Daily_Return']):
            kline_item['daily_return'] = round(row['Daily_Return'], 2)
        if 'Volume_MA5' in row and pd.notna(row['Volume_MA5']):
            kline_item['volume_ma5'] = int(row['Volume_MA5'])
        
        kline_list.append(kline_item)
    
    return kline_list

def format_large_number(number):
    """格式化大数字"""
    if number >= 1e12:
        return f"{number / 1e12:.2f}T"
    elif number >= 1e9:
        return f"{number / 1e9:.2f}B"
    elif number >= 1e6:
        return f"{number / 1e6:.2f}M"
    elif number >= 1e3:
        return f"{number / 1e3:.2f}K"
    else:
        return f"{number:.2f}" 