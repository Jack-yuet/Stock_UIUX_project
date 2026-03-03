import os
import json
import math
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier


class FeatureBuilder:
    """Build orthogonal features consistent with scoring engine for ML training/backtesting."""
    CORE_TECHS = ['MACD', 'RSI', 'Bollinger_Bands', 'ROC', 'OBV']

    @staticmethod
    def to_signal_strength(indicator: str, text: str) -> float:
        if not text:
            return 0.0
        s = text.lower()
        # Support both English and Chinese keywords for compatibility
        if any(k in s for k in ['strong bullish', 'resonance bullish', 'golden cross', 'oversold', '强烈看涨', '共振看涨', '金叉', '超卖']):
            return 0.8
        if any(k in s for k in ['bullish', 'accelerating', '看涨', '加速']):
            return 0.6
        if any(k in s for k in ['strong bearish', 'resonance bearish', 'death cross', 'overbought', '强烈看跌', '共振看跌', '死叉', '超买']):
            return -0.8
        if any(k in s for k in ['bearish', 'decelerating', '看跌', '减速']):
            return -0.6
        return 0.0

    @staticmethod
    def build_features_from_analysis(analysis: Dict) -> Dict[str, float]:
        signals = analysis.get('technical_indicators', [])
        sig_map = {s.get('indicator'): s.get('signal') for s in signals if isinstance(s, dict)}
        feats: Dict[str, float] = {}
        for indi in FeatureBuilder.CORE_TECHS:
            # Handle English/Chinese key mapping if necessary, or rely on correct keys in input
            # Current technical_indicators.py uses English keys: 'Bollinger_Bands', 'ROC', 'OBV'
            # Old data might have Chinese keys? Let's check keys in sig_map.
            # We assume new data uses English keys.
            val = sig_map.get(indi, '')
            if not val and indi == 'Bollinger_Bands': val = sig_map.get('布林带', '')
            if not val and indi == 'ROC': val = sig_map.get('变化率', '')
            if not val and indi == 'OBV': val = sig_map.get('OBV能量', '')
            
            feats[f"tech_{indi}"] = FeatureBuilder.to_signal_strength(indi, val)

        # Trend related
        # MA20vsMA50
        ma20_val = sig_map.get('MA20vsMA50', '')
        if 'bullish' in ma20_val.lower() or '看涨' in ma20_val:
            feats['trend_ma20vs50'] = 0.8
        elif 'bearish' in ma20_val.lower() or '看跌' in ma20_val:
            feats['trend_ma20vs50'] = -0.8
        else:
            feats['trend_ma20vs50'] = 0
            
        # MA_Alignment / MA排列
        ma_align_val = sig_map.get('MA_Alignment', sig_map.get('MA排列', ''))
        if 'bullish' in ma_align_val.lower() or '多头' in ma_align_val:
            feats['trend_arrange'] = 0.8
        elif 'bearish' in ma_align_val.lower() or '空头' in ma_align_val:
            feats['trend_arrange'] = -0.8
        else:
            feats['trend_arrange'] = 0
            
        # ADX Strength / ADX趋势强度
        adx_txt = sig_map.get('ADX_Strength', sig_map.get('ADX趋势强度', ''))
        if 'strong trend' in adx_txt.lower() or '强趋势' in adx_txt:
            feats['trend_adx'] = 1.0
        elif 'medium trend' in adx_txt.lower() or '中等趋势' in adx_txt:
            feats['trend_adx'] = 0.5
        else:
            feats['trend_adx'] = 0.0
            
        # HT_TRENDMODE
        ht_txt = sig_map.get('HT_TRENDMODE', '')
        if 'trending mode' in ht_txt.lower() or '趋势模式' in ht_txt:
            feats['trend_mode'] = 1.0
        elif 'cycling mode' in ht_txt.lower() or '无趋势' in ht_txt:
            feats['trend_mode'] = -0.5
        else:
            feats['trend_mode'] = 0.0

        # Market Environment
        me = analysis.get('market_environment', {}) or {}
        feats['me_factor'] = float(me.get('factor', 0.0))
        feats['me_bull'] = 1.0 if me.get('regime') == 'bullish' else 0.0
        feats['me_bear'] = 1.0 if me.get('regime') == 'bearish' else 0.0

        return feats

    @staticmethod
    def build_features_from_ohlcv(df: pd.DataFrame) -> Dict[str, float]:
        """Construct quantitative price/volume features based on OHLCV.
        Expects columns: ['Open','High','Low','Close','Volume'], index ascending by time.
        """
        feats: Dict[str, float] = {}
        if df is None or df.empty:
            return feats
        d = df.copy()
        d = d.dropna()
        if d.empty:
            return feats
        # Returns and Volatility
        d['ret1'] = d['Close'].pct_change()
        for w in [5, 10, 20, 60, 120]:
            d[f'mom_{w}'] = d['Close'].pct_change(w)
        # ATR Approximation
        tr = (d['High'] - d['Low']).abs()
        tr = np.maximum(tr, (d['High'] - d['Close'].shift(1)).abs())
        tr = np.maximum(tr, (d['Low'] - d['Close'].shift(1)).abs())
        d['atr14'] = tr.rolling(14).mean()
        d['atr_pct'] = (d['atr14'] / d['Close']).clip(lower=0, upper=1)
        # Bollinger Width
        d['ma20'] = d['Close'].rolling(20).mean()
        d['std20'] = d['Close'].rolling(20).std()
        d['bb_width'] = (4 * d['std20'] / (d['ma20'] + 1e-9)).clip(lower=0, upper=1)
        # Volume
        d['vol_ma20'] = d['Volume'].rolling(20).mean()
        d['vol_ratio'] = (d['Volume'] / (d['vol_ma20'] + 1e-9)).clip(upper=5)
        # Amihud Illiquidity (20d median)
        dollar = d['Close'] * d['Volume']
        amihud = (d['ret1'].abs() / (dollar + 1e-9)).rolling(20).median()
        d['amihud'] = amihud.replace([np.inf, -np.inf], np.nan)
        # Gap
        d['gap'] = (d['Open'] / d['Close'].shift(1) - 1.0).fillna(0)
        # Recent Drawdown
        roll_max = d['Close'].rolling(60).max()
        d['drawdown_60'] = (d['Close'] / (roll_max + 1e-9) - 1.0)
        # Latest row
        last = d.iloc[-1]
        feats.update({
            'px_mom_5': float(last.get('mom_5', 0.0) or 0.0),
            'px_mom_10': float(last.get('mom_10', 0.0) or 0.0),
            'px_mom_20': float(last.get('mom_20', 0.0) or 0.0),
            'px_mom_60': float(last.get('mom_60', 0.0) or 0.0),
            'px_mom_120': float(last.get('mom_120', 0.0) or 0.0),
            'px_atr_pct': float(last.get('atr_pct', 0.0) or 0.0),
            'px_bb_width': float(last.get('bb_width', 0.0) or 0.0),
            'px_vol_ratio': float(last.get('vol_ratio', 1.0) or 1.0),
            'px_amihud': float(last.get('amihud', 0.0) or 0.0),
            'px_gap': float(last.get('gap', 0.0) or 0.0),
            'px_drawdown_60': float(last.get('drawdown_60', 0.0) or 0.0)
        })
        # Clip Extremes
        for k in list(feats.keys()):
            if k.startswith('px_'):
                v = feats[k]
                if isinstance(v, (int, float)) and not math.isnan(v):
                    feats[k] = float(np.clip(v, -1.0, 1.0))
                else:
                    feats[k] = 0.0
        return feats


def make_forward_returns(close_series: pd.Series, horizon: int = 10) -> pd.Series:
    return close_series.shift(-horizon) / close_series - 1.0


class MLBacktester:
    def __init__(self, horizon_days: int = 10, model: str = 'logistic'):
        self.horizon = horizon_days
        if model == 'xgb':
            self.model = XGBClassifier(
                n_estimators=200,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=2,
                objective='binary:logistic',
                eval_metric='logloss',
                base_score=0.5
            )
        else:
            self.model = LogisticRegression(max_iter=200, n_jobs=2)
        self.calibrator = None

    def fit_calibrated(self, X: pd.DataFrame, y: pd.Series):
        base = self.model
        
        # Check data quality, decide CV folds
        label_counts = y.value_counts()
        min_class_samples = label_counts.min()
        
        if min_class_samples >= 3:
            cv_folds = 3
        elif min_class_samples >= 2:
            cv_folds = 2
        else:
            # Too few samples, skip CV
            cv_folds = None
        
        if cv_folds:
            self.calibrator = CalibratedClassifierCV(base, method='isotonic', cv=cv_folds)
        else:
            # Skip calibration if samples too few
            print(f"⚠️  Too few samples (min class:{min_class_samples}), skipping calibration")
            base.fit(X, y)
            self.calibrator = base
        
        if hasattr(self.calibrator, 'fit'):
            self.calibrator.fit(X, y)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.calibrator is None:
            raise RuntimeError('Model not fitted')
        
        # Check if calibrated
        if hasattr(self.calibrator, 'predict_proba'):
            proba = self.calibrator.predict_proba(X)
            # Calibrated model returns 2D array, take positive class probability
            if proba.ndim == 2 and proba.shape[1] == 2:
                return proba[:, 1]
            else:
                return proba
        else:
            # Non-calibrated model might not have predict_proba
            if hasattr(self.calibrator, 'decision_function'):
                # Use decision_function and convert to probability
                decision_scores = self.calibrator.decision_function(X)
                from scipy.special import expit
                return expit(decision_scores)
            else:
                # Fallback to predict
                return self.calibrator.predict(X).astype(float)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.calibrator, path)

    def load(self, path: str):
        self.calibrator = joblib.load(path)


def _cross_sectional_rank_scale(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return df
    ranked = df.copy()
    for c in cols:
        if c in ranked.columns:
            s = ranked[c].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
            order = s.rank(method='average', pct=True)
            ranked[c] = (order * 2.0 - 1.0)  # Map to [-1,1]
    return ranked


def build_dataset_from_results(results_json: Dict, ohlcv_lookup: Dict[str, pd.DataFrame], horizon: int = 10) -> Tuple[pd.DataFrame, pd.Series]:
    rows = []
    labels = []
    for item in results_json.get('analysisResults', []):
        code = item.get('stockCode')
        analysis = item.get('analysis', {})
        # Analysis features
        feats = FeatureBuilder.build_features_from_analysis(analysis)
        # Price/Volume features
        ohlcv = ohlcv_lookup.get(code)
        if ohlcv is None or ohlcv.empty:
            continue
        pf = FeatureBuilder.build_features_from_ohlcv(ohlcv)
        feats.update(pf)
        # Label
        close_series = ohlcv['Close']
        fr = make_forward_returns(close_series, horizon=horizon).dropna()
        if fr.empty:
            continue
        y = 1 if fr.iloc[-1] > 0 else 0
        rows.append(feats)
        labels.append(y)
    if not rows:
        return pd.DataFrame(), pd.Series(dtype=int)
    X = pd.DataFrame(rows).fillna(0.0)
    # Cross-sectional rank scaling (only for price/volume features)
    px_cols = [c for c in X.columns if c.startswith('px_')]
    X = _cross_sectional_rank_scale(X, px_cols)
    y = pd.Series(labels, dtype=int)
    return X, y


def fuse_rule_prob_to_score(rule_score: float, prob: float, alpha: float = 0.6) -> float:
    # Linear function mapping probability to [0,10]
    prob_score = max(0.0, min(10.0, 10.0 * (prob - 0.3) / 0.7))  # p=0.3->0, p=1->10
    fused = alpha * rule_score + (1 - alpha) * prob_score
    return max(0.0, min(10.0, fused))


__all__ = [
    'FeatureBuilder',
    'MLBacktester',
    'build_dataset_from_results',
    'fuse_rule_prob_to_score'
]