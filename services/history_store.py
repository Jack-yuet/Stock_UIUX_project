import sqlite3
import datetime
import os
import logging

if 'VERCEL' in os.environ:
    # Use ephemeral storage in serverless environment
    DB_DIR = '/tmp/data'
else:
    # Use persistent storage in local environment
    DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, 'score_history.db')

def init_db():
    """Initialize database table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            stock_code TEXT,
            final_score REAL,
            signal TEXT,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def record_score_entry(stock_code, final_score, signal, details):
    """Record scoring result"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO score_history (timestamp, stock_code, final_score, signal, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, stock_code, final_score, signal, details))
    conn.commit()
    conn.close()

def fetch_history(limit=50):
    """Fetch recent history records"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM score_history ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "timestamp": row[1],
            "stock_code": row[2],
            "final_score": row[3],
            "signal": row[4],
            "details": row[5]
        })
    return result
