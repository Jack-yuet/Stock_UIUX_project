import os
import sqlite3
from datetime import datetime, timedelta


    if 'VERCEL' in os.environ:
        DB_DIR = '/tmp/data'
    else:
        DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    DB_PATH = os.path.join(DB_DIR, 'score_history.db')


def _get_conn():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                timestamp TEXT NOT NULL,
                final_score REAL NOT NULL,
                breakdown TEXT,
                details TEXT,
                trend_conclusion TEXT,
                technical_indicators TEXT,
                candlestick_patterns TEXT,
                support_resistance TEXT,
                detailed_summary TEXT
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_score_history_code_time ON score_history(stock_code, timestamp);")
        conn.commit()
    finally:
        conn.close()


def record_score_entry(stock_code: str,
                       stock_name: str,
                       timestamp_iso: str,
                       final_score: float,
                       breakdown_json: str = None,
                       details_json: str = None,
                       trend_conclusion: str = None,
                       technical_indicators_json: str = None,
                       candlestick_patterns_json: str = None,
                       support_resistance_json: str = None,
                       detailed_summary: str = None):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO score_history (
                stock_code, stock_name, timestamp, final_score,
                breakdown, details, trend_conclusion,
                technical_indicators, candlestick_patterns,
                support_resistance, detailed_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stock_code, stock_name, timestamp_iso, float(final_score),
                breakdown_json, details_json, trend_conclusion,
                technical_indicators_json, candlestick_patterns_json,
                support_resistance_json, detailed_summary
            )
        )
        conn.commit()
    finally:
        conn.close()


def fetch_history(stock_code: str, days: int = 30):
    """Fetch history by canonical stock_code (with suffix)."""
    since = datetime.utcnow() - timedelta(days=max(1, int(days)))
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT stock_code, stock_name, timestamp, final_score, breakdown, details,
                   trend_conclusion, technical_indicators, candlestick_patterns,
                   support_resistance, detailed_summary
            FROM score_history
            WHERE stock_code = ? AND timestamp >= ?
            ORDER BY datetime(timestamp) ASC
            """,
            (stock_code, since.isoformat())
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


