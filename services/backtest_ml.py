import os
import json
import math
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

# Mock ML classes for serverless environment where sklearn/xgboost are too heavy
class FeatureBuilder:
    """Build orthogonal features consistent with scoring engine."""
    CORE_TECHS = ['MACD', 'RSI', 'Bollinger_Bands', 'ROC', 'OBV']

    @staticmethod
    def to_signal_strength(indicator: str, text: str) -> float:
        if not text:
            return 0.0
        s = text.lower()
        if any(k in s for k in ['strong bullish', 'resonance bullish', 'golden cross', 'oversold']):
            return 0.8
        if any(k in s for k in ['bullish', 'accelerating']):
            return 0.6
        if any(k in s for k in ['strong bearish', 'resonance bearish', 'death cross', 'overbought']):
            return -0.8
        if any(k in s for k in ['bearish', 'decelerating']):
            return -0.6
        return 0.0

    @staticmethod
    def build_features_from_analysis(analysis: Dict) -> Dict[str, float]:
        return {} # Mock implementation

    @staticmethod
    def build_features_from_ohlcv(df: pd.DataFrame) -> Dict[str, float]:
        return {} # Mock implementation

def make_forward_returns(close_series: pd.Series, horizon: int = 10) -> pd.Series:
    return close_series.shift(-horizon) / close_series - 1.0

class MLBacktester:
    """Mock ML Backtester for serverless environment"""
    def __init__(self, horizon_days: int = 10, model: str = 'logistic'):
        self.horizon = horizon_days
        self.model_name = model
        print("ML Module disabled in serverless environment to save space.")

    def fit_calibrated(self, X: pd.DataFrame, y: pd.Series):
        pass

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.array([0.5] * len(X))

    def save(self, path: str):
        pass

    def load(self, path: str):
        pass

def build_dataset_from_results(results_json: Dict, ohlcv_lookup: Dict[str, pd.DataFrame], horizon: int = 10) -> Tuple[pd.DataFrame, pd.Series]:
    return pd.DataFrame(), pd.Series(dtype=int)

def fuse_rule_prob_to_score(rule_score: float, prob: float, alpha: float = 0.6) -> float:
    return rule_score

__all__ = [
    'FeatureBuilder',
    'MLBacktester',
    'build_dataset_from_results',
    'fuse_rule_prob_to_score'
]