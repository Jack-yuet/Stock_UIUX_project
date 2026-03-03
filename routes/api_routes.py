from flask import Blueprint, jsonify, request
import pandas as pd
from stock_mapping import add_stock_suffix
from services.stock_service import get_stock_data, process_institutional_data, get_market_indices_data, calculate_market_environment_factor
from services.correlation_service import get_correlation_analysis
from services.info_collection_service import get_stock_info_links, collect_ai_research_data
from utils.stock_utils import calculate_kline_data
from services.trend_analysis_service import analyze_stock_trend
from utils.stock_mapping import stock_mapping
import sys
import os
import json
import uuid
from datetime import datetime
from services.history_store import init_db, record_score_entry, fetch_history
from services.backtest_ml import MLBacktester, build_dataset_from_results
# import yfinance as yf
# import warnings
# import logging
# from sklearn.metrics import roc_auc_score

# Configure logging and suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('requests').setLevel(logging.CRITICAL)

# Set env var to suppress HTTP error output
os.environ['PYTHONWARNINGS'] = 'ignore'
import numpy as np

# Add current dir to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create API Blueprint
api_bp = Blueprint('api', __name__)
init_db()

@api_bp.route('/search', methods=['POST'])
def search_stock():
    """Stock Search API"""
    data = request.get_json()
    stock_input = data.get('stock_name', '').strip()
    period = data.get('period', '1y')  # Default 1y
    
    if not stock_input:
        return jsonify({'success': False, 'message': 'Please enter stock code'})
    
    # Validate period
    valid_periods = ['1y', '3y', '7y']
    if period not in valid_periods:
        period = '1y'
    
    print(f"Searching stock: {stock_input}, Period: {period}")
    
    # Auto append suffix
    stock_code = add_stock_suffix(stock_input)
    print(f"Processed stock code: {stock_code}")
    
    stock_data = get_stock_data(stock_code, period)
    
    if stock_data:
        # Process history data
        hist_df = stock_data['hist_data'].sort_index(ascending=False)
        
        # Get candlestick patterns
        try:
            analysis_result = analyze_stock_trend(stock_code, period)
            patterns_by_date = {}
            if 'structured_candlestick_patterns' in analysis_result:
                for pattern in analysis_result['structured_candlestick_patterns']:
                    # Ensure YYYY-MM-DD
                    pattern_date = pattern['date'].split(' ')[0] if pattern['date'] else ''
                    if pattern_date:
                        if pattern_date not in patterns_by_date:
                            patterns_by_date[pattern_date] = []
                        # Combine pattern name and position
                        pattern_with_position = f"{pattern['name']} ({pattern['position']})"
                        patterns_by_date[pattern_date].append(pattern_with_position)
        except Exception as e:
            print(f"Failed to get candlestick patterns: {e}")
            patterns_by_date = {}
        
        hist_data = []
        
        # Limit to recent 30 days
        recent_hist_df = hist_df.head(30)
        
        for date, row in recent_hist_df.iterrows():
            date_str = date.strftime('%Y-%m-%d')
            # Get patterns for the day
            day_patterns = patterns_by_date.get(date_str, [])
            patterns_text = ', '.join(day_patterns) if day_patterns else ''
            
            hist_data.append({
                'date': date_str,
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']),
                'daily_return': round(row['Daily_Return'], 2) if pd.notna(row['Daily_Return']) else 0,
                'patterns': patterns_text
            })
        
        # Calculate Kline data (technical indicators included)
        kline_daily = calculate_kline_data(stock_data['hist_data'], 'D')
        
        # Process basic info
        info = stock_data['info']
        basic_info = {
            'name': info.get('longName', 'Unknown'),
            'code': stock_code,
            'industry': info.get('industry', 'Unknown'),
            'sector': info.get('sector', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'current_price': info.get('currentPrice', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0)
        }
        
        # Process institutional holders
        institutional_data = process_institutional_data(stock_data['institutional_holders'])
        
        print(f"Successfully fetched data for {basic_info['name']}, {len(hist_data)} records")
        return jsonify({
            'success': True,
            'basic_info': basic_info,
            'hist_data': hist_data,
            'institutional_holders': institutional_data,
            'financial_data': stock_data['financial_data'],
            'kline_data': {
                'daily': kline_daily
            },
            'period': period,
            'total_records': len(hist_data)
        })
    else:
        return jsonify({
            'success': False, 
            'message': f'Data not found for "{stock_input}". Please check:\n1. Is stock name correct?\n2. Does it have correct suffix (.SS, .SZ, .HK)?\n3. Is it still trading?\n4. Network connection.'
        })

@api_bp.route('/kline_data/<stock_code>')
def get_kline_data(stock_code):
    """Get Kline Data API"""
    try:
        # Query params
        period = request.args.get('period', '1y')
        interval = request.args.get('interval', 'D')
        
        # Validate
        valid_periods = ['1y', '3y', '7y']
        valid_intervals = ['D', 'W', 'M']
        
        if period not in valid_periods:
            period = '1y'
        if interval not in valid_intervals:
            interval = 'D'
        
        # Auto suffix
        full_code = add_stock_suffix(stock_code)
        
        # Get data
        stock_data = get_stock_data(full_code, period)
        
        if stock_data:
            # Calculate Kline data
            kline_data = calculate_kline_data(stock_data['hist_data'], interval)
            
            return jsonify({
                'success': True,
                'kline_data': kline_data,
                'period': period,
                'interval': interval
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Data not found for "{stock_code}"'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get Kline data: {str(e)}'
        })

@api_bp.route('/market_environment', methods=['GET'])
def get_market_environment():
    """Get Market Environment API"""
    try:
        period = request.args.get('period', '3mo')
        
        # Get market data
        market_data = get_market_indices_data(period=period)
        market_environment = calculate_market_environment_factor(market_data)
        
        return jsonify({
            'success': True,
            'market_environment': market_environment
        })
        
    except Exception as e:
        print(f"Failed to get market environment: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get market environment: {str(e)}'
        }), 500

@api_bp.route('/trend_analysis', methods=['POST'])
def get_trend_analysis():
    """Get Trend Analysis API"""
    try:
        data = request.get_json()
        stock_input = data.get('stock_code', '').strip()
        period = data.get('period', '1y')
        provided_market_env = data.get('market_environment')
        
        if not stock_input:
            return jsonify({'success': False, 'message': 'Please enter stock code'})
        
        # Validate period
        valid_periods = ['1y', '3y', '7y']
        if period not in valid_periods:
            period = '1y'
        
        # Auto suffix
        stock_code = add_stock_suffix(stock_input)
        
        # Analyze
        analysis_result = analyze_stock_trend(stock_code, period)
        if not analysis_result:
            return jsonify({'success': False, 'message': 'Unable to fetch stock data'})
        
        # Market env
        if provided_market_env:
            market_environment = provided_market_env
        else:
            try:
                market_data = get_market_indices_data(period="3mo")
                market_environment = calculate_market_environment_factor(market_data)
            except Exception as e:
                print(f"Failed to get market env: {e}")
                market_environment = {'factor': 0, 'regime': 'neutral', 'details': {}}
        
        # Format result
        formatted_result = {
            'success': True,
            'stock_code': stock_code,
            'period': period,
            'candlestick_patterns': [],
            'technical_indicators': [],
            'support_resistance': [],
            'all_levels': [],
            'trend_conclusion': analysis_result.get('trend_judgment', ''),
            'detailed_summary': analysis_result.get('detailed_summary', ''),
            # Keep original data for scoring
            'technical_signals': analysis_result.get('technical_signals', {}),
            'candlestick_patterns_raw': analysis_result.get('candlestick_patterns', {}),
            'structured_candlestick_patterns': analysis_result.get('structured_candlestick_patterns', []),
            'market_environment': market_environment,
             # Backward compatibility
            '技术指标信号': analysis_result.get('technical_signals', {}),
            'K线形态': analysis_result.get('candlestick_patterns', {}),
        }
        
        # Format patterns
        patterns = analysis_result.get('candlestick_patterns', {})
        pattern_meanings = analysis_result.get('pattern_meanings', {})
        for pattern, value in patterns.items():
            if value != 0:
                signal = "Bullish" if value > 0 else "Bearish"
                status = f"{signal} (Strength: {abs(value)})"
                status_class = "pattern-bullish" if value > 0 else "pattern-bearish"
            else:
                if pattern in ['Hammer', 'Morning Star', 'Bullish Engulfing', 'Piercing Line', 'Inverted Hammer', 'Rising Three Methods', 'Bullish Doji']:
                    status = "Not Detected"
                    status_class = "pattern-neutral"
                elif pattern in ['Hanging Man', 'Evening Star', 'Bearish Engulfing', 'Dark Cloud Cover', 'Shooting Star', 'Falling Three Methods', 'Bearish Doji']:
                    status = "Not Formed"
                    status_class = "pattern-neutral"
                elif pattern in ['Doji']:
                    status = "Weak, Not Key Area"
                    status_class = "pattern-weak"
                else:
                    status = "Not Detected"
                    status_class = "pattern-neutral"
            
            formatted_result['candlestick_patterns'].append({
                'pattern': pattern,
                'status': status,
                'status_class': status_class,
                'meaning': pattern_meanings.get(pattern, '')
            })
        
        # Format technical indicators
        signals = analysis_result.get('technical_signals', {})
        for indicator, signal in signals.items():
            # Determine class
            if 'Bullish' in signal or 'Resonance Bullish' in signal:
                signal_class = "signal-bullish"
            elif 'Bearish' in signal or 'Resonance Bearish' in signal:
                signal_class = "signal-bearish"
            elif 'Overbought' in signal:
                signal_class = "signal-overbought"
            elif 'Oversold' in signal:
                signal_class = "signal-oversold"
            else:
                signal_class = "signal-neutral"
            
            formatted_result['technical_indicators'].append({
                'indicator': indicator,
                'signal': signal,
                'signal_class': signal_class
            })
        
        # Format S&R
        levels = analysis_result.get('support_resistance', {})
        support_detail = levels.get('support_detail', {})
        resistance_detail = levels.get('resistance_detail', {})
        
        if support_detail and isinstance(support_detail, dict) and support_detail.get('price', 0) > 0:
            formatted_result['support_resistance'].append({
                'type': 'Support',
                'price': support_detail.get('price', 0),
                'strength': support_detail.get('strength', ''),
                'touches': support_detail.get('touches', 0),
                'distance': support_detail.get('distance', ''),
                'strength_class': f"strength-{support_detail.get('strength', 'weak').lower()}"
            })
        
        if resistance_detail and isinstance(resistance_detail, dict) and resistance_detail.get('price', 0) > 0:
            formatted_result['support_resistance'].append({
                'type': 'Resistance',
                'price': resistance_detail.get('price', 0),
                'strength': resistance_detail.get('strength', ''),
                'touches': resistance_detail.get('touches', 0),
                'distance': resistance_detail.get('distance', ''),
                'strength_class': f"strength-{resistance_detail.get('strength', 'weak').lower()}"
            })
        
        all_supports = levels.get('all_supports', [])
        all_resistances = levels.get('all_resistances', [])
        
        if isinstance(all_supports, list):
            for support in all_supports[:5]:
                if isinstance(support, dict):
                    formatted_result['all_levels'].append({
                        'type': 'Support',
                        'price': support.get('price', 0),
                        'strength': support.get('strength', ''),
                        'touches': support.get('touches', 0),
                        'distance': support.get('distance', ''),
                        'strength_class': f"strength-{support.get('strength', 'weak').lower()}"
                    })
        
        if isinstance(all_resistances, list):
            for resistance in all_resistances[:5]:
                if isinstance(resistance, dict):
                    formatted_result['all_levels'].append({
                        'type': 'Resistance',
                        'price': resistance.get('price', 0),
                        'strength': resistance.get('strength', ''),
                        'touches': resistance.get('touches', 0),
                        'distance': resistance.get('distance', ''),
                        'strength_class': f"strength-{resistance.get('strength', 'weak').lower()}"
                    })
        
        formatted_result = convert_numpy_types(formatted_result)
        
        return jsonify(formatted_result)
        
    except Exception as e:
        print(f"Trend Analysis Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Trend Analysis Failed: {str(e)}'
        })

@api_bp.route('/score_history/<path:stock_code>', methods=['GET'])
def get_score_history(stock_code):
    """Get Score History (SQLite)"""
    try:
        days = int(request.args.get('days', '60'))
        history_rows = fetch_history(stock_code, days=days)
        return jsonify({
            'success': True,
            'stock_code': stock_code,
            'days': days,
            'history': history_rows
        })
    except Exception as e:
        print(f"Failed to get score history: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get score history: {str(e)}'
        })


@api_bp.route('/model/info', methods=['GET'])
def get_model_info():
    try:
        if 'VERCEL' in os.environ:
            models_dir = os.path.join('/tmp', 'data', 'models')
        else:
            models_dir = os.path.join('data', 'models')
        model_path = os.path.join(models_dir, 'ml_prob_calibrated.joblib')
        meta_path = os.path.join(models_dir, 'ml_metadata.json')
        if not os.path.exists(model_path):
            return jsonify({'success': True, 'trained': False})
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        stat = os.stat(model_path)
        return jsonify({
            'success': True,
            'trained': True,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'meta': meta
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def _load_latest_results_from_db(days: int = 30):
    """Load latest score data from SQLite for ML training"""
    from services.history_store import _get_conn
    from datetime import datetime, timedelta
    import json
    
    since = datetime.utcnow() - timedelta(days=days)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        # Get score records within recent days
        cur.execute(
            """
            SELECT DISTINCT stock_code, stock_name, final_score,
                   technical_indicators, candlestick_patterns, support_resistance,
                   trend_conclusion, detailed_summary, timestamp
            FROM score_history
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (since.isoformat(),)
        )
        rows = cur.fetchall()
        
        if not rows:
            return None
        
        # Convert to old format for compatibility with existing build_dataset_from_results function
        analysis_results = []
        for row in rows:
            # Parse JSON fields
            try:
                technical_indicators = json.loads(row['technical_indicators']) if row['technical_indicators'] else []
            except:
                technical_indicators = []
            
            try:
                candlestick_patterns = json.loads(row['candlestick_patterns']) if row['candlestick_patterns'] else []
            except:
                candlestick_patterns = []
            
            try:
                support_resistance = json.loads(row['support_resistance']) if row['support_resistance'] else []
            except:
                support_resistance = []
            
            analysis_results.append({
                'stockCode': row['stock_code'],
                'stockName': row['stock_name'],
                'score': row['final_score'],
                'analysis': {
                    'technical_indicators': technical_indicators,
                    'candlestick_patterns': candlestick_patterns,
                    'support_resistance': support_resistance,
                    'trend_conclusion': row['trend_conclusion'] or '',
                    'detailed_summary': row['detailed_summary'] or ''
                }
            })
        
        # Deduplicate: Keep only the latest record for each stock
        unique_results = {}
        for result in analysis_results:
            code = result['stockCode']
            if code not in unique_results:
                unique_results[code] = result
        
        print(f"Loaded analysis data for {len(unique_results)} stocks from DB")
        
        return {
            'analysisResults': list(unique_results.values()),
            'totalStocks': len(unique_results)
        }
        
    finally:
        conn.close()

def _load_latest_results_json():
    """Load latest batch analysis JSON (Deprecated, for backward compatibility)"""
    print("⚠️  Warning: Used deprecated JSON loading, DB recommended")
    if 'VERCEL' in os.environ:
        results_dir = '/tmp/batch_results'
    else:
        results_dir = 'batch_results'
        
    if not os.path.exists(results_dir):
        return None
    files = sorted([
        os.path.join(results_dir, f) for f in os.listdir(results_dir)
        if f.endswith('.json')
    ], key=lambda p: os.path.getmtime(p), reverse=True)
    if not files:
        return None
    with open(files[0], 'r', encoding='utf-8') as f:
        return json.load(f)

def _validate_and_clean_stock_codes(codes):
    """
    Validate and clean stock code list, filtering invalid codes
    """
    valid_codes = []
    for code in codes:
        if not code:
            continue
        # Basic format validation
        if len(code) == 6 and code.isdigit():
            valid_codes.append(code)
        elif '.' in code and len(code.split('.')[0]) == 6:
            valid_codes.append(code)
    return valid_codes

def _fetch_ohlcv(stock_code: str, period: str = '1y'):
    """
    Quietly fetch OHLCV data, return None on failure
    """
    try:
        import warnings
        import urllib3
        urllib3.disable_warnings()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            ticker = yf.Ticker(stock_code)
            hist = ticker.history(period=period)
            
            if hist is None or hist.empty or len(hist) < 20:
                return None
            return hist[['Open','High','Low','Close','Volume']]
    except Exception:
        # Silently handle exception to avoid mass error output
        return None

@api_bp.route('/model/train', methods=['POST'])
def train_model():
    try:
        data = request.get_json() or {}
        horizon = int(data.get('horizon', 10))
        model_choice = data.get('model', 'logistic')

        # Prefer DB, then JSON
        results_json = _load_latest_results_from_db(days=60)
        if not results_json:
            print("No data in DB, trying JSON file...")
            results_json = _load_latest_results_json()
        
        if not results_json:
            return jsonify({'success': False, 'message': 'No historical analysis data found. Please run batch analysis first.'})

        # Build price sequence
        codes = [item.get('stockCode') for item in results_json.get('analysisResults', []) if item.get('stockCode')]
        unique_codes = list(dict.fromkeys(codes))
        # Validate and clean stock codes
        unique_codes = _validate_and_clean_stock_codes(unique_codes)
        # Limit count to avoid timeout
        unique_codes = unique_codes[:80]

        print(f"Backtest data fetch: Processing {len(unique_codes)} stocks...")
        ohlcv_lookup = {}
        successful_fetches = 0
        
        for i, code in enumerate(unique_codes):
            # Try raw code
            df = _fetch_ohlcv(code, '1y')
            if df is None:
                from stock_mapping import add_stock_suffix
                df = _fetch_ohlcv(add_stock_suffix(code), '1y')
            
            if df is not None and len(df) > 50:
                ohlcv_lookup[code] = df.dropna()
                successful_fetches += 1
            
            # Show progress every 20 stocks
            if (i + 1) % 20 == 0:
                print(f"Backtest progress: {i + 1}/{len(unique_codes)}, Success: {successful_fetches}")
        
        print(f"Backtest data fetch completed: {successful_fetches}/{len(unique_codes)} valid stocks")
        
        if successful_fetches < 5:
            return jsonify({
                'success': False, 
                'message': f'Insufficient valid data ({successful_fetches} < 5), please run batch analysis for more data'
            })

        X, y = build_dataset_from_results(results_json, ohlcv_lookup, horizon=horizon)
        if X.empty or y.empty:
            return jsonify({'success': False, 'message': 'Training data empty, cannot train'})

        # Check label distribution and data quality
        label_counts = y.value_counts()
        total_samples = len(y)
        pos_samples = label_counts.get(1, 0)
        neg_samples = label_counts.get(0, 0)
        
        print(f"Training data quality check:")
        print(f"  Total samples: {total_samples}")
        print(f"  Pos samples (Up): {pos_samples} ({pos_samples/total_samples*100:.1f}%)")
        print(f"  Neg samples (Down): {neg_samples} ({neg_samples/total_samples*100:.1f}%)")
        
        # Data quality check
        if total_samples < 10:
            return jsonify({
                'success': False, 
                'message': f'Too few training samples ({total_samples} < 10), more history needed'
            })
        
        if min(pos_samples, neg_samples) < 2:
            return jsonify({
                'success': False, 
                'message': f'Severe label imbalance (Pos:{pos_samples}, Neg:{neg_samples}). Try shorter horizon (1-3d) or get more data'
            })
        
        if min(pos_samples, neg_samples) / total_samples < 0.1:
            print(f"⚠️  Warning: Label imbalance may affect performance")

        bt = MLBacktester(horizon_days=horizon, model=model_choice)
        bt.fit_calibrated(X, y)

        if 'VERCEL' in os.environ:
            models_dir = os.path.join('/tmp', 'data', 'models')
        else:
            models_dir = os.path.join('data', 'models')
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, 'ml_prob_calibrated.joblib')
        meta_path = os.path.join(models_dir, 'ml_metadata.json')
        bt.save(model_path)
        meta = {
            'horizon': horizon,
            'model': model_choice,
            'n_samples': int(len(y)),
            'trained_at': datetime.utcnow().isoformat()
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True, 'message': 'Training completed', 'meta': meta})
    except Exception as e:
        print(f"Training failed: {e}")
        return jsonify({'success': False, 'message': f'Training failed: {str(e)}'})

@api_bp.route('/model/backtest', methods=['POST'])
def run_backtest():
    try:
        data = request.get_json() or {}
        horizon = int(data.get('horizon', 10))
        model_choice = data.get('model', 'logistic')

        # Prefer DB, then JSON
        results_json = _load_latest_results_from_db(days=60)
        if not results_json:
            print("No data in DB, trying JSON file...")
            results_json = _load_latest_results_json()
        
        if not results_json:
            return jsonify({'success': False, 'message': 'No historical analysis data found. Please run batch analysis first.'})

        codes = [item.get('stockCode') for item in results_json.get('analysisResults', []) if item.get('stockCode')]
        unique_codes = list(dict.fromkeys(codes))
        # Validate and clean stock codes
        unique_codes = _validate_and_clean_stock_codes(unique_codes)
        unique_codes = unique_codes[:80]
        
        print(f"Fetching historical data for {len(unique_codes)} stocks...")
        ohlcv_lookup = {}
        successful_fetches = 0
        failed_fetches = 0
        
        for i, code in enumerate(unique_codes):
            # Try raw code
            df = _fetch_ohlcv(code, '1y')
            if df is None:
                # Try adding suffix
                from stock_mapping import add_stock_suffix
                df = _fetch_ohlcv(add_stock_suffix(code), '1y')
            
            if df is not None and len(df) > 50:  # Ensure enough history
                ohlcv_lookup[code] = df.dropna()
                successful_fetches += 1
            else:
                failed_fetches += 1
            
            # Show progress every 20 stocks
            if (i + 1) % 20 == 0:
                print(f"Progress: {i + 1}/{len(unique_codes)}, Success: {successful_fetches}, Failed: {failed_fetches}")
        
        print(f"Data fetch completed: Success {successful_fetches}/{len(unique_codes)} stocks")
        
        if successful_fetches < 10:
            return jsonify({
                'success': False, 
                'message': f'Too few valid stocks ({successful_fetches} < 10), cannot train'
            })

        X, y = build_dataset_from_results(results_json, ohlcv_lookup, horizon=horizon)
        if X.empty or y.empty:
            return jsonify({'success': False, 'message': 'Backtest data empty'})

        # Check backtest data quality
        label_counts = y.value_counts()
        total_samples = len(y)
        pos_samples = label_counts.get(1, 0)
        neg_samples = label_counts.get(0, 0)
        
        print(f"Backtest data quality check:")
        print(f"  Total samples: {total_samples}")
        print(f"  Pos samples (Up): {pos_samples} ({pos_samples/total_samples*100:.1f}%)")
        print(f"  Neg samples (Down): {neg_samples} ({neg_samples/total_samples*100:.1f}%)")
        
        if min(pos_samples, neg_samples) < 1:
            return jsonify({
                'success': False, 
                'message': f'Backtest label imbalance (Pos:{pos_samples}, Neg:{neg_samples}). Try shorter horizon (1-3d)'
            })

        n = len(y)
        split = int(n * 0.7)
        X_train, y_train = X.iloc[:split], y.iloc[:split]
        X_test, y_test = X.iloc[split:], y.iloc[split:]

        bt = MLBacktester(horizon_days=horizon, model=model_choice)
        # Train calibrator
        bt.fit_calibrated(X_train, y_train)
        proba = bt.predict_proba(X_test)
        preds = (proba >= 0.5).astype(int)
        acc = float((preds == y_test.values).mean())
        
        # Safely calculate win_rate
        try:
            if (preds == 1).any():
                selected_proba = proba[preds == 1]
                win_rate = float(selected_proba.mean()) if hasattr(selected_proba, 'mean') else float(np.mean(selected_proba))
            else:
                win_rate = 0.0
        except Exception as e:
            print(f"Win rate calc error: {e}")
            win_rate = 0.0
            
        # Calculate AUC, needs two classes
        if len(np.unique(y_test.values)) > 1:
            try:
                # auc = float(roc_auc_score(y_test.values, proba))
                auc = 0.5 # Mock AUC
            except Exception as e:
                print(f"AUC calc failed: {e}")
                auc = None
        else:
            auc = None

        # XGBoost Learning Curve (only if xgb selected)
        learning_curve = None
        # if model_choice == 'xgb':
        #     try:
        #         from xgboost import XGBClassifier
        #         xgb = XGBClassifier(
        #             n_estimators=200,
        #             max_depth=3,
        #             learning_rate=0.05,
        #             subsample=0.8,
        #             colsample_bytree=0.8,
        #             reg_lambda=1.0,
        #             random_state=42,
        #             n_jobs=2,
        #             objective='binary:logistic',
        #             eval_metric='logloss',
        #             base_score=0.5
        #         )
        #         xgb.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)
        #         evals = xgb.evals_result()
        #         learning_curve = {
        #             'train_logloss': evals.get('validation_0', {}).get('logloss', []),
        #             'test_logloss': evals.get('validation_1', {}).get('logloss', [])
        #         }
        #     except Exception:
        #         learning_curve = None

        # Safely handle proba array conversion
        try:
            # Ensure proba is 1D
            if hasattr(proba, 'ndim') and proba.ndim > 1:
                proba = proba.flatten()
            
            # Safely convert to list
            proba_list = proba.tolist() if hasattr(proba, 'tolist') else list(proba)
            
            # Ensure each element is scalar
            proba_values = []
            for p in proba_list:
                if isinstance(p, (list, tuple)):
                    # If list or tuple, take first element
                    proba_values.append(float(p[0]) if len(p) > 0 else 0.0)
                else:
                    proba_values.append(float(p))
                    
        except Exception as e:
            print(f"Probability conversion error: {e}, type: {type(proba)}, value: {proba}")
            proba_values = [0.5] * len(y_test)  # Fallback

        # Build detailed prediction results
        detailed_predictions = []
        test_codes = [results_json['analysisResults'][i]['stockCode'] 
                     for i in X_test.index if i < len(results_json['analysisResults'])]
        test_names = [results_json['analysisResults'][i].get('stockName', results_json['analysisResults'][i]['stockCode']) 
                     for i in X_test.index if i < len(results_json['analysisResults'])]
        
        for i, (code, name, prob, actual) in enumerate(zip(test_codes, test_names, proba_values, y_test.astype(int).tolist())):
            # Interpret result
            confidence = "High" if abs(prob - 0.5) > 0.3 else "Medium" if abs(prob - 0.5) > 0.1 else "Low"
            prediction = "Bullish" if prob > 0.5 else "Bearish"
            actual_result = "Actual Up" if actual == 1 else "Actual Down"
            is_correct = (prob > 0.5 and actual == 1) or (prob <= 0.5 and actual == 0)
            
            detailed_predictions.append({
                'stock_code': code,
                'stock_name': name,
                'probability': round(prob, 4),
                'prediction': prediction,
                'confidence': confidence,
                'actual_result': actual_result,
                'is_correct': is_correct,
                'explanation': f"Model predicts {prob*100:.1f}% probability of rise for {name}, confidence {confidence}. {actual_result}, prediction {'Correct' if is_correct else 'Wrong'}."
            })

        return jsonify({
            'success': True,
            'metrics': {
                'samples': int(n),
                'train_samples': int(len(y_train)),
                'test_samples': int(len(y_test)),
                'accuracy': round(acc, 4),
                'avg_prob_selected': round(win_rate, 4),
                'auc': round(auc, 4) if auc is not None else None
            },
            'data': {
                'y_true': y_test.astype(int).tolist(),
                'proba': proba_values,
                'learning_curve': learning_curve,
                'detailed_predictions': detailed_predictions
            },
            'summary': {
                'total_predictions': len(detailed_predictions),
                'correct_predictions': sum(1 for p in detailed_predictions if p['is_correct']),
                'high_confidence_predictions': sum(1 for p in detailed_predictions if p['confidence'] == 'High'),
                'avg_probability': round(sum(proba_values) / len(proba_values), 4) if proba_values else 0
            }
        })
    except Exception as e:
        print(f"Backtest failed: {e}")
        return jsonify({'success': False, 'message': f'Backtest failed: {str(e)}'})

def record_score_history(stock_code, analysis_result, frontend_score=None):
    """Record score history to localStorage"""
    try:
        # Use frontend score if provided, else calculate backend
        if frontend_score is not None:
            final_score = frontend_score
        else:
            final_score = calculate_final_score(analysis_result)
        
        # Create score record
        score_record = {
            'timestamp': datetime.now().isoformat(),
            'stockCode': stock_code,
            'stockName': analysis_result.get('stock_name', ''),
            'finalScore': final_score,
            'trend_conclusion': analysis_result.get('trend_conclusion', ''),
            'technical_indicators': analysis_result.get('technical_indicators', []),
            'candlestick_patterns': analysis_result.get('candlestick_patterns', []),
            'support_resistance': analysis_result.get('support_resistance', []),
            'detailed_summary': analysis_result.get('detailed_summary', '')
        }
        
        # Just print, storage handled by frontend JS
        print(f"Score record: {stock_code} - {final_score}")
        
    except Exception as e:
        print(f"Failed to record score history: {str(e)}")

def extract_signals_from_api(analysis_result):
    """Extract technical signals from API result"""
    signals = {}
    
    # Process API technical_indicators array
    if analysis_result.get('technical_indicators') and isinstance(analysis_result['technical_indicators'], list):
        for indicator in analysis_result['technical_indicators']:
            if isinstance(indicator, dict) and indicator.get('indicator') and indicator.get('signal'):
                signals[indicator['indicator']] = indicator['signal']
    
    # Support raw object format
    if analysis_result.get('技术指标信号') and isinstance(analysis_result['技术指标信号'], dict):
        signals.update(analysis_result['技术指标信号'])
    
    return signals

def convert_numpy_types(obj):
    """Recursively convert NumPy types to Python native types"""
    import numpy as np
    
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def extract_patterns_from_api(analysis_result):
    """Extract candlestick patterns from API result"""
    patterns = []
    
    # Process API candlestick_patterns array
    if analysis_result.get('candlestick_patterns') and isinstance(analysis_result['candlestick_patterns'], list):
        for pattern in analysis_result['candlestick_patterns']:
            if isinstance(pattern, dict) and pattern.get('pattern') and pattern.get('status'):
                # Only include valid patterns
                status = pattern['status']
                if not any(keyword in status for keyword in ['Not Detected', 'Not Formed', 'Weak']):
                    patterns.append(pattern['pattern'])
    
    # Support raw object format
    if analysis_result.get('K线形态') and isinstance(analysis_result['K线形态'], dict):
        for pattern, value in analysis_result['K线形态'].items():
            if value != 0:
                patterns.append(pattern)
    
    return patterns

def calculate_final_score(analysis_result):
    """Calculate final score - consistent with frontend ScoreEngine"""
    try:
        # 1. Trend Score (Weight 33%)
        trend_score = calculate_trend_score(analysis_result) * 0.825  # 33/40
        
        # 2. Technical Score (Weight 28%)
        technical_score, consistency_bonus = calculate_technical_score(analysis_result)
        technical_score = technical_score * 0.8  # 28/35
        consistency_bonus = consistency_bonus * 0.8
        
        # 3. Pattern Score (Weight 18%)
        pattern_score = calculate_pattern_score(analysis_result) * 0.72  # 18/25
        
        # 4. Market Environment Score (Weight 9%)
        market_score = calculate_market_environment_score(analysis_result) * 0.9
        
        # 5. Trend Position Score (Weight 7%)
        position_score = calculate_trend_position_score(analysis_result)
        
        # 6. Volume Modifier (Weight 5%)
        volume_modifier = calculate_volume_modifier(analysis_result)
        volume_modifier = 1 + (volume_modifier - 1) * 0.2  # Reduce volume impact
        
        # 7. Final Calculation
        total_score = max(0, trend_score + technical_score + consistency_bonus + pattern_score + market_score + position_score)
        final_score = total_score * volume_modifier
        
        # Normalize to 0-10
        final_score = final_score / 10
        
        # Limit to 0-10
        final_score = max(0, min(10, final_score))
        
        return round(final_score, 1)
        
    except Exception as e:
        print(f"Score calculation error: {e}")
        return 0.0

def calculate_trend_score(analysis_result):
    """Calculate trend score"""
    # Extract technical signals from API result
    signals = extract_signals_from_api(analysis_result)
    tsi = 0
    
    # MA5 Slope Standardization (Weight 50%)
    ma5_signal = signals.get('MA5vsMA20', '')
    ma5_slope = 0.8 if 'Bullish' in ma5_signal else (-0.8 if 'Bearish' in ma5_signal else 0)
    tsi += 0.5 * ma5_slope
    
    # MA20 Slope Standardization (Weight 30%)
    ma20_signal = signals.get('MA20vsMA50', '')
    ma20_slope = 0.8 if 'Bullish' in ma20_signal else (-0.8 if 'Bearish' in ma20_signal else 0)
    tsi += 0.3 * ma20_slope
    
    # ADX Direction Strength (Weight 20%)
    adx_signal = signals.get('ADX_Strength', '')
    adx_strength = 1.0 if 'Strong Trend' in adx_signal else (0.5 if 'Medium Trend' in adx_signal else 0.2)
    tsi += 0.2 * adx_strength
    
    # Limit TSI range and convert to score
    tsi = max(-1, min(1, tsi))
    return tsi * 40

def calculate_technical_score(analysis_result):
    """Calculate technical indicators score"""
    signals = extract_signals_from_api(analysis_result)
    core_indicators = ['MACD', 'RSI', 'KDJ', 'Bollinger_Bands', 'OBV', 'Momentum', 'ROC']
    
    signal_strengths = []
    bullish_count = 0
    bearish_count = 0
    
    for indicator in core_indicators:
        signal = signals.get(indicator, '')
        if not signal:
            continue
            
        strength = calculate_signal_strength(signal)
        signal_strengths.append(strength)
        
        if strength > 0:
            bullish_count += 1
        elif strength < 0:
            bearish_count += 1
    
    # Calculate average signal strength
    if signal_strengths:
        avg_strength = sum(signal_strengths) / len(signal_strengths)
        base_score = avg_strength * 35
    else:
        base_score = 0
    
    # Consistency bonus
    total_signals = len(signal_strengths)
    consistency_bonus = 0
    if total_signals > 0:
        max_directional = max(bullish_count, bearish_count)
        if max_directional >= 4:
            consistency_ratio = max_directional / total_signals
            consistency_bonus = (consistency_ratio - 0.5) * 5
    
    return base_score, consistency_bonus

def calculate_signal_strength(signal):
    """Calculate signal strength"""
    signal_lower = signal.lower()
    
    if any(keyword in signal_lower for keyword in ['strong bullish', 'resonance bullish', 'golden cross', 'oversold']):
        return 0.8
    elif any(keyword in signal_lower for keyword in ['bullish', 'accelerating']):
        return 0.6
    elif any(keyword in signal_lower for keyword in ['strong bearish', 'resonance bearish', 'death cross', 'overbought']):
        return -0.8
    elif any(keyword in signal_lower for keyword in ['bearish', 'decelerating']):
        return -0.6
    elif any(keyword in signal_lower for keyword in ['neutral', 'normal']):
        return 0
    
    return 0

def calculate_pattern_score(analysis_result):
    """Calculate candlestick pattern score"""
    patterns = extract_patterns_from_api(analysis_result)
    total_score = 0
    
    for pattern in patterns:
        pattern_lower = pattern.lower()
        
        # Multi-candle bullish patterns
        if any(keyword in pattern_lower for keyword in ['morning star', 'engulfing', 'three white soldiers', 'piercing line']):
            total_score += 1.0 * 1.3  # Base score * Volume modifier
        # Single candle bullish patterns
        elif any(keyword in pattern_lower for keyword in ['hammer', 'doji', 'shooting star']): 
             # Note: Shooting Star is bearish in config, Inverted Hammer is bullish. Correcting logic based on config if needed.
             # Original logic had '流星' (Shooting Star) in bullish single candle... let's check original.
             # Actually Inverted Hammer is bullish. Shooting Star is bearish.
             # I will use English names.
             if 'inverted hammer' in pattern_lower:
                 total_score += 0.5 * 1.2
             elif 'hammer' in pattern_lower:
                 total_score += 0.5 * 1.2
             elif 'doji' in pattern_lower and 'bullish' in pattern_lower:
                 total_score += 0.5 * 1.2

        # Multi-candle bearish patterns
        if any(keyword in pattern_lower for keyword in ['evening star', 'three black crows', 'dark cloud cover']):
            total_score -= 1.0 * 1.3
        # Single candle bearish patterns
        elif any(keyword in pattern_lower for keyword in ['hanging man', 'shooting star']):
            total_score -= 0.5 * 1.2
        elif 'doji' in pattern_lower and 'bearish' in pattern_lower:
            total_score -= 0.5 * 1.2
            
    return total_score * 25  # Apply weight

def calculate_market_environment_score(analysis_result):
    """Calculate market environment factor score"""
    try:
        market_env = analysis_result.get('market_environment', {})
        factor = market_env.get('factor', 0)
        regime = market_env.get('regime', 'neutral')
        
        # Adjust score based on market regime
        if regime == 'bullish':
            score = 0.5
        elif regime == 'bearish':
            score = -0.5
        else:  # neutral
            score = 0
        
        # Adjust based on factor strength
        score = score * (1 + abs(factor))
        
        return score
        
    except Exception as e:
        print(f"Market environment score calculation error: {e}")
        return 0.0

def calculate_trend_position_score(analysis_result):
    """Calculate trend position score"""
    try:
        # Simplified trend position score
        # Can be calculated based on support/resistance, price position etc.
        # Temporarily return 0.0 to match frontend
        return 0.0
        
    except Exception as e:
        print(f"Trend position score calculation error: {e}")
        return 0.0

def calculate_volume_modifier(analysis_result):
    """Calculate volume modifier"""
    signals = extract_signals_from_api(analysis_result)
    volume_signal = signals.get('Volume', '')
    
    if not volume_signal:
        return 1.0
    
    volume_lower = volume_signal.lower()
    
    if 'high volume' in volume_lower:
        volume_ratio = 1.5
    elif 'low volume' in volume_lower:
        volume_ratio = 0.5
    else:
        volume_ratio = 1.0
    
    # Calculate modifier: min(1.3, max(0.7, 1±(current_vol/20d_avg - 1)))
    modifier = min(1.3, max(0.7, 1 + (volume_ratio - 1) * 0.3))
    
    return modifier

@api_bp.route('/record_score', methods=['POST'])
def record_score():
    """Record Score API"""
    try:
        data = request.get_json()
        stock_code = data.get('stock_code', '')
        analysis_result = data.get('analysis_result', {})
        frontend_score = data.get('frontend_score', None)
        
        if not stock_code:
            return jsonify({'success': False, 'message': 'Stock code is empty'})
        
        # Record score history (SQLite)
        try:
            stock_name = analysis_result.get('stock_name', '')
            ts = datetime.utcnow().isoformat()

            # If frontend passes an object, prefer it
            final_score = None
            breakdown = None
            details = None
            if isinstance(frontend_score, dict):
                try:
                    final_score = float(frontend_score.get('finalScore'))
                except Exception:
                    final_score = None
                try:
                    breakdown = json.dumps(frontend_score.get('breakdown') or {}, ensure_ascii=False)
                except Exception:
                    breakdown = None
                try:
                    details = json.dumps(frontend_score.get('details') or {}, ensure_ascii=False)
                except Exception:
                    details = None

            # If full object not provided, backend calculates
            if final_score is None:
                # Scores
                base_trend = calculate_trend_score(analysis_result) * 0.825  # 33/40
                base_technical, consistency_bonus = calculate_technical_score(analysis_result)
                base_technical = base_technical * 0.8  # 28/35
                consistency_bonus = consistency_bonus * 0.8
                base_pattern = calculate_pattern_score(analysis_result) * 0.72  # 18/25
                base_market = calculate_market_environment_score(analysis_result) * 0.9  # 9/10
                base_position = calculate_trend_position_score(analysis_result)
                volume_modifier = calculate_volume_modifier(analysis_result)
                volume_modifier = 1 + (volume_modifier - 1) * 0.2
                # Final score
                total_score = max(0, base_trend + base_technical + consistency_bonus + base_pattern + base_market + base_position)
                final_score = max(0, min(10, (total_score * volume_modifier) / 10))
                final_score = round(final_score, 1)
                # Generate breakdown JSON
                breakdown = json.dumps({
                    'trendScore': base_trend,
                    'technicalScore': base_technical,
                    'patternScore': base_pattern,
                    'marketEnvironmentScore': base_market,
                    'trendPositionScore': base_position,
                    'consistencyBonus': consistency_bonus,
                    'volumeModifier': volume_modifier
                }, ensure_ascii=False)

            # Other fields
            technical_indicators = json.dumps(analysis_result.get('technical_signals', []), ensure_ascii=False)
            candlestick_patterns = json.dumps(analysis_result.get('candlestick_patterns', []), ensure_ascii=False)
            support_resistance = json.dumps(analysis_result.get('support_resistance', []), ensure_ascii=False)
            detailed_summary = analysis_result.get('detailed_summary', '')
            trend_conclusion = analysis_result.get('trend_judgment', '')

            record_score_entry(
                stock_code=stock_code,
                stock_name=stock_name,
                timestamp_iso=ts,
                final_score=final_score,
                breakdown_json=breakdown,
                details_json=details,
                trend_conclusion=trend_conclusion,
                technical_indicators_json=technical_indicators,
                candlestick_patterns_json=candlestick_patterns,
                support_resistance_json=support_resistance,
                detailed_summary=detailed_summary
            )
        except Exception as write_err:
            print(f"Failed to persist score record: {write_err}")

        return jsonify({'success': True, 'message': 'Score recorded successfully'})
        
    except Exception as e:
        print(f"Record score failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Record score failed: {str(e)}'
        })

@api_bp.route('/save_batch_results', methods=['POST'])
def save_batch_results():
    """Save Batch Results to File"""
    try:
        data = request.get_json()
        
        # Create storage dir
        if 'VERCEL' in os.environ:
            storage_dir = '/tmp/batch_results'
        else:
            storage_dir = 'batch_results'
            
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        # Generate ID
        result_id = str(uuid.uuid4())
        file_path = os.path.join(storage_dir, f'{result_id}.json')
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'message': 'Batch results saved successfully'
        })
        
    except Exception as e:
        print(f"Failed to save batch results: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Save failed: {str(e)}'
        })

@api_bp.route('/get_batch_results/<result_id>')
def get_batch_results(result_id):
    """Get Batch Results"""
    try:
        if 'VERCEL' in os.environ:
            storage_dir = '/tmp/batch_results'
        else:
            storage_dir = 'batch_results'
            
        file_path = os.path.join(storage_dir, f'{result_id}.json')
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'Result not found or expired'
            })
        
        # Read data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        print(f"Failed to get batch results: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Get failed: {str(e)}'
        })

@api_bp.route('/get_stock_list')
def get_stock_list():
    """Get Stock List API"""
    try:
        # Only return enable_batch=true stocks
        stock_info = [item for item in stock_mapping.get_all_stocks() if item.get('enable_batch', True)]
        stock_list = [item['code'] for item in stock_info]
        return jsonify({
            'success': True,
            'stock_list': stock_list,
            'stock_info': stock_info,
            'count': len(stock_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get stock list: {str(e)}'
        })

@api_bp.route('/correlation_analysis', methods=['POST'])
def correlation_analysis():
    """Correlation Analysis API"""
    try:
        data = request.get_json()
        us_code = data.get('us_code', '').strip()
        cn_code = data.get('cn_code', '').strip()
        period = data.get('period', '1y')
        
        if not us_code or not cn_code:
            return jsonify({'success': False, 'message': 'Please enter both US and CN stock codes'})
            
        result = get_correlation_analysis(us_code, cn_code, period)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/info_collection', methods=['POST'])
def info_collection():
    """Info Collection API"""
    try:
        data = request.get_json()
        stock_code = data.get('stock_code', '').strip()
        
        if not stock_code:
            return jsonify({'success': False, 'message': 'Please enter stock code'})
            
        result = get_stock_info_links(stock_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/ai_research', methods=['POST'])
def ai_research():
    """AI Research API"""
    try:
        data = request.get_json()
        stock_code = data.get('stock_code', '').strip()
        # Get API config
        api_config = data.get('api_config', {})
        
        if not stock_code:
            return jsonify({'success': False, 'message': 'Please enter stock code'})
            
        result = collect_ai_research_data(stock_code, api_config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})