import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from stock_mapping import add_stock_suffix

def get_correlation_analysis(us_stock_code, cn_stock_code, period="1y"):
    """
    Analyze correlation between US stock daily change (T) and A-share next day change (T+1)
    """
    try:
        # Process stock codes
        # US stock usually no suffix, or user input AAPL
        # A-share needs suffix like .SS or .SZ
        cn_full_code = add_stock_suffix(cn_stock_code)
        
        print(f"Starting correlation analysis: US={us_stock_code}, CN={cn_full_code}, Period={period}")
        
        # Fetch data
        us_ticker = yf.Ticker(us_stock_code)
        cn_ticker = yf.Ticker(cn_full_code)
        
        # We need slightly more than 1 year to ensure T and T+1 alignment
        # Or just use period
        us_hist = us_ticker.history(period=period)
        cn_hist = cn_ticker.history(period=period)
        
        if us_hist.empty or cn_hist.empty:
            return {"success": False, "message": "Unable to fetch history data for one or both stocks"}
            
        # Calculate daily returns
        us_hist['US_Return'] = us_hist['Close'].pct_change() * 100
        cn_hist['CN_Return'] = cn_hist['Close'].pct_change() * 100
        
        # Focus on US (T) and CN (T+1)
        # Shift US date forward? No, we compare dates.
        # US and CN holidays differ.
        
        us_data = us_hist[['US_Return', 'Close']].copy()
        us_data.index = us_data.index.tz_localize(None) # Remove timezone
        
        cn_data = cn_hist[['Open', 'High', 'Low', 'Close', 'CN_Return']].copy()
        cn_data.index = cn_data.index.tz_localize(None) # Remove timezone
        
        # Result list
        daily_records = []
        
        # 1. Align data, build base records
        for i in range(len(us_data) - 1):
            us_date = us_data.index[i]
            us_return = us_data['US_Return'].iloc[i]
            if pd.isna(us_return): continue
                
            subsequent_cn = cn_data[cn_data.index > us_date]
            if not subsequent_cn.empty:
                cn_date = subsequent_cn.index[0]
                cn_day = subsequent_cn.iloc[0]
                
                # Match if within 4 days (weekend/holiday buffer)
                if (cn_date - us_date).days <= 4:
                    daily_records.append({
                        'us_date': us_date.strftime('%Y-%m-%d'),
                        'us_return': float(round(us_return, 2)),
                        'cn_date': cn_date.strftime('%Y-%m-%d'),
                        'cn_return': float(round(cn_day['CN_Return'], 2)),
                        'cn_open': float(cn_day['Open']),
                        'cn_close': float(cn_day['Close']),
                        'matched': bool((us_return > 0 and cn_day['CN_Return'] > 0) or (us_return < 0 and cn_day['CN_Return'] < 0)),
                        'action': '',
                        'strategy_return': 0.0
                    })

        if not daily_records:
            return {"success": False, "message": "No matched trading days found"}

        # 2. Simulate T+1 Holding Strategy
        holding = False
        entry_price = 0
        cumulative_factor = 1.0 # Compound factor
        trade_count = 0
        
        for i in range(len(daily_records)):
            rec = daily_records[i]
            us_ret = rec['us_return']
            cn_open = rec['cn_open']
            
            if not holding:
                if us_ret > 0: # US Up, Buy CN
                    holding = True
                    entry_price = cn_open
                    rec['action'] = 'Buy'
                    trade_count += 1
            else: # Holding
                if us_ret < 0: # US Down, Sell CN
                    holding = False
                    exit_price = cn_open
                    # Calculate return
                    trade_return = (exit_price / entry_price - 1)
                    cumulative_factor *= (1 + trade_return)
                    rec['action'] = 'Sell'
                    rec['strategy_return'] = float(round(trade_return * 100, 2))
        
        # Force close at end if holding
        if holding:
            exit_price = daily_records[-1]['cn_close']
            trade_return = (exit_price / entry_price - 1)
            cumulative_factor *= (1 + trade_return)
            rec = daily_records[-1]
            rec['action'] = 'Close Position'
            rec['strategy_return'] = float(round(trade_return * 100, 2))

        strategy_total_return = (cumulative_factor - 1) * 100

        # Calculate Statistics
        df_records = pd.DataFrame(daily_records)
        correlation = df_records['us_return'].corr(df_records['cn_return'])
        
        # Benchmark Return (Buy and Hold CN)
        first_cn_open = daily_records[0]['cn_open']
        last_cn_close = daily_records[-1]['cn_close']
        buy_and_hold_return = (last_cn_close / first_cn_open - 1) * 100

        # Win Rate
        total = len(daily_records)
        matched_count = df_records['matched'].sum()
        win_rate = (matched_count / total) * 100
        
        us_up = df_records[df_records['us_return'] > 1.0]
        us_up_win_rate = (us_up['cn_return'] > 0).mean() * 100 if not us_up.empty else 0
        
        us_down = df_records[df_records['us_return'] < -1.0]
        us_down_win_rate = (us_down['cn_return'] < 0).mean() * 100 if not us_down.empty else 0
        
        summary = {
            'us_stock': us_stock_code,
            'cn_stock': cn_full_code,
            'total_days': int(total),
            'correlation': float(round(correlation, 3)) if not pd.isna(correlation) else 0.0,
            'win_rate': float(round(win_rate, 2)),
            'us_up_win_rate': float(round(us_up_win_rate, 2)),
            'us_down_win_rate': float(round(us_down_win_rate, 2)),
            'strategy_return': float(round(strategy_total_return, 2)),
            'buy_and_hold_return': float(round(buy_and_hold_return, 2)),
            'trade_count': int(trade_count),
            'period': period
        }
        
        return {
            'success': True,
            'summary': summary,
            'daily_records': daily_records[::-1] # Reverse order for display
        }
        
    except Exception as e:
        print(f"Correlation analysis failed: {e}")
        return {"success": False, "message": f"Error during analysis: {str(e)}"}