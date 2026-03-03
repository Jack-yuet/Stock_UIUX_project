import yfinance as yf
import pandas as pd
from datetime import datetime
from utils.stock_utils import (
    calculate_technical_indicators, 
    calculate_kline_data, 
    format_large_number,
    safe_get
)

def get_stock_data(stock_code, period="1y"):
    """Fetch stock data by stock code"""
    try:
        print(f"Start fetching stock data: {stock_code}, Period: {period}")
        ticker = yf.Ticker(stock_code)
        
        # Get history data
        hist_data = ticker.history(period=period)
        if hist_data.empty:
            print(f"Stock code {stock_code} has no history data")
            return None
        print(f"History data fetched successfully, {len(hist_data)} records")
            
        # Get basic info
        info = ticker.info
        if not info:
            print(f"Stock code {stock_code} has no basic info")
            return None
        if 'longName' not in info:
            print(f"Stock code {stock_code} missing longName field")
            print(f"info fields: {list(info.keys())[:10] if info else 'No Data'}")
            # Try other name fields
            if 'shortName' in info:
                info['longName'] = info['shortName']
            elif 'symbol' in info:
                info['longName'] = info['symbol']
            else:
                info['longName'] = stock_code
        
        # Get institutional holders
        try:
            institutional_holders = ticker.institutional_holders
        except Exception as e:
            print(f"Failed to get institutional holders: {e}")
            institutional_holders = None
        
        # Get financial data
        try:
            financial_data = get_financial_data(info)
        except Exception as e:
            print(f"Failed to get financial data: {e}")
            financial_data = []
        

        
        # Calculate technical indicators
        hist_data = calculate_technical_indicators(hist_data)
        
        return {
            'hist_data': hist_data,
            'info': info,
            'institutional_holders': institutional_holders,
            'financial_data': financial_data
        }
        
    except Exception as e:
        print(f"Failed to fetch stock {stock_code} data: {e}")
        return None

def get_financial_data(info):
    """Extract financial data from stock info"""
    financial_data = []
    
    # Market Cap
    if 'marketCap' in info and info['marketCap']:
        financial_data.append({
            'indicator': 'Market Cap',
            'value': format_large_number(info['marketCap']),
            'unit': ''
        })
    
    # Total Revenue
    if 'totalRevenue' in info and info['totalRevenue']:
        financial_data.append({
            'indicator': 'Revenue',
            'value': format_large_number(info['totalRevenue']),
            'unit': ''
        })
    
    # Net Income
    if 'netIncomeToCommon' in info and info['netIncomeToCommon']:
        financial_data.append({
            'indicator': 'Net Income',
            'value': format_large_number(info['netIncomeToCommon']),
            'unit': ''
        })
    
    # EPS
    if 'trailingEps' in info and info['trailingEps']:
        try:
            eps_value = float(info['trailingEps'])
            financial_data.append({
                'indicator': 'EPS (TTM)',
                'value': f"{eps_value:.2f}",
                'unit': ''
            })
        except (ValueError, TypeError):
            pass
    
    # PE Ratio
    if 'trailingPE' in info and info['trailingPE']:
        try:
            pe_value = float(info['trailingPE'])
            financial_data.append({
                'indicator': 'PE (TTM)',
                'value': f"{pe_value:.2f}",
                'unit': ''
            })
        except (ValueError, TypeError):
            pass
    
    # PB Ratio
    if 'priceToBook' in info and info['priceToBook']:
        try:
            pb_value = float(info['priceToBook'])
            financial_data.append({
                'indicator': 'PB Ratio',
                'value': f"{pb_value:.2f}",
                'unit': ''
            })
        except (ValueError, TypeError):
            pass
    
    # PS Ratio
    if 'priceToSalesTrailing12Months' in info and info['priceToSalesTrailing12Months']:
        try:
            ps_value = float(info['priceToSalesTrailing12Months'])
            financial_data.append({
                'indicator': 'PS Ratio (TTM)',
                'value': f"{ps_value:.2f}",
                'unit': ''
            })
        except (ValueError, TypeError):
            pass
    
    # Dividend Yield
    if 'dividendYield' in info and info['dividendYield']:
        try:
            dy_value = float(info['dividendYield'])
            financial_data.append({
                'indicator': 'Div Yield',
                'value': f"{dy_value * 100:.2f}",
                'unit': '%'
            })
        except (ValueError, TypeError):
            pass
    
    # ROE
    if 'returnOnEquity' in info and info['returnOnEquity']:
        try:
            roe_value = float(info['returnOnEquity'])
            financial_data.append({
                'indicator': 'ROE',
                'value': f"{roe_value * 100:.2f}",
                'unit': '%'
            })
        except (ValueError, TypeError):
            pass
    
    # ROA
    if 'returnOnAssets' in info and info['returnOnAssets']:
        try:
            roa_value = float(info['returnOnAssets'])
            financial_data.append({
                'indicator': 'ROA',
                'value': f"{roa_value * 100:.2f}",
                'unit': '%'
            })
        except (ValueError, TypeError):
            pass
    
    # Debt to Equity
    if 'debtToEquity' in info and info['debtToEquity']:
        try:
            de_value = float(info['debtToEquity'])
            financial_data.append({
                'indicator': 'Debt/Equity',
                'value': f"{de_value * 100:.2f}",
                'unit': '%'
            })
        except (ValueError, TypeError):
            pass
    
    # Current Ratio
    if 'currentRatio' in info and info['currentRatio']:
        try:
            cr_value = float(info['currentRatio'])
            financial_data.append({
                'indicator': 'Current Ratio',
                'value': f"{cr_value:.2f}",
                'unit': ''
            })
        except (ValueError, TypeError):
            pass
    
    # Quick Ratio
    if 'quickRatio' in info and info['quickRatio']:
        try:
            qr_value = float(info['quickRatio'])
            financial_data.append({
                'indicator': 'Quick Ratio',
                'value': f"{qr_value:.2f}",
                'unit': ''
            })
        except (ValueError, TypeError):
            pass
    
    return financial_data

def get_market_indices_data(period="3mo"):
    """Get market indices data"""
    try:
        indices = {
            'SSE': '000001.SS',      # SSE Composite
            'SZSE': '399002.SZ',     # SZSE Component
            'CSI300': '000300.SS'    # CSI 300
        }
        
        market_data = {}
        for name, code in indices.items():
            try:
                ticker = yf.Ticker(code)
                hist_data = ticker.history(period=period)
                if not hist_data.empty:
                    # Calculate basic technical indicators
                    hist_data = calculate_technical_indicators(hist_data)
                    market_data[name] = hist_data
                else:
                    print(f"Failed to get {name}({code}) data")
            except Exception as e:
                print(f"Failed to get {name}({code}) data: {e}")
        
        return market_data
    except Exception as e:
        print(f"Failed to get market indices data: {e}")
        return {}

def calculate_market_environment_factor(market_data):
    """Calculate market environment factor"""
    try:
        if not market_data:
            return {'factor': 0, 'regime': 'neutral', 'details': {}}
        
        environment_scores = []
        details = {}
        
        for index_name, df in market_data.items():
            if df.empty:
                continue
                
            latest = df.iloc[-1]
            score = 0
            index_details = {}
            
            # 1. Trend Direction (Weight 40%)
            if 'MA5' in df.columns and 'MA20' in df.columns:
                if latest['Close'] > latest['MA20']:
                    trend_score = 0.4 if latest['MA5'] > latest['MA20'] else 0.2
                else:
                    trend_score = -0.4 if latest['MA5'] < latest['MA20'] else -0.2
                score += trend_score
                index_details['Trend'] = 'Bullish' if trend_score > 0 else 'Bearish'
            
            # 2. Momentum Strength (Weight 30%)
            if len(df) >= 5:
                recent_return = (latest['Close'] / df.iloc[-5]['Close'] - 1) * 100
                if recent_return > 2:
                    momentum_score = 0.3
                elif recent_return > 0:
                    momentum_score = 0.15
                elif recent_return > -2:
                    momentum_score = -0.15
                else:
                    momentum_score = -0.3
                score += momentum_score
                index_details['5D Change'] = f"{recent_return:.2f}%"
            
            # 3. Volatility Environment (Weight 20%)
            if len(df) >= 20:
                returns = df['Close'].pct_change().dropna()
                volatility = returns.std() * (252 ** 0.5) * 100  # Annualized volatility
                if volatility < 15:  # Low volatility
                    vol_score = 0.1
                elif volatility < 25:  # Medium volatility
                    vol_score = 0
                else:  # High volatility
                    vol_score = -0.2
                score += vol_score
                index_details['Volatility'] = f"{volatility:.1f}%"
            
            # 4. RSI Overbought/Oversold (Weight 10%)
            if 'RSI' in df.columns:
                rsi = latest['RSI']
                if rsi > 70:
                    rsi_score = -0.1  # Overbought, negative
                elif rsi < 30:
                    rsi_score = 0.1   # Oversold, positive
                else:
                    rsi_score = 0
                score += rsi_score
                index_details['RSI'] = f"{rsi:.1f}"
            
            environment_scores.append(score)
            details[index_name] = index_details
        
        # Calculate composite market factor
        if environment_scores:
            avg_score = sum(environment_scores) / len(environment_scores)
            # Normalize to [-1, 1]
            market_factor = max(-1, min(1, avg_score))
            
            # Determine market regime
            if market_factor > 0.3:
                regime = 'bullish'
            elif market_factor < -0.3:
                regime = 'bearish'
            else:
                regime = 'neutral'
        else:
            market_factor = 0
            regime = 'neutral'
        
        return {
            'factor': market_factor,
            'regime': regime,
            'details': details,
            'scores': environment_scores
        }
    
    except Exception as e:
        print(f"Failed to calculate market environment factor: {e}")
        return {'factor': 0, 'regime': 'neutral', 'details': {}}


def process_institutional_data(institutional_holders):
    """Process institutional holders data"""
    institutional_data = []
    if institutional_holders is not None and not institutional_holders.empty:
        for _, row in institutional_holders.iterrows():
            # Process date format
            date_reported = safe_get(row, ['Date Reported', 'dateReported', 'date_reported'], 'Unknown')
            if date_reported != 'Unknown' and pd.notna(date_reported):
                try:
                    # If string format date, convert to datetime first
                    if isinstance(date_reported, str):
                        # Handle GMT format date
                        if 'GMT' in date_reported:
                            date_obj = datetime.strptime(date_reported, '%a, %d %b %Y %H:%M:%S GMT')
                        else:
                            # Try other common formats
                            date_obj = pd.to_datetime(date_reported)
                    else:
                        date_obj = pd.to_datetime(date_reported)
                    
                    # Convert to YYYY.MM.DD format
                    formatted_date = date_obj.strftime('%Y.%m.%d')
                except:
                    formatted_date = 'Unknown'
            else:
                formatted_date = 'Unknown'
            
            institutional_data.append({
                'holder': safe_get(row, ['Holder', 'holder', 'Name', 'name'], 'Unknown'),
                'shares': int(safe_get(row, ['Shares', 'shares'], 0)),
                'date_reported': formatted_date
            })
    
    return institutional_data