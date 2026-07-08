import sqlite3
import os

DB_NAME = "financial_reports.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            source TEXT,
            date TEXT,
            recommendation TEXT,
            current_price_at_report REAL,
            target_price REAL,
            business_status TEXT,
            business_outlook TEXT,
            financial_forecast TEXT,
            risks TEXT,
            investment_thesis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_report(data):
    if not data or not data.get("ticker"):
        return "failed"
        
    ticker = data.get("ticker").upper().strip()
    source = data.get("source", "Không rõ").strip()
    date = data.get("date", "Không rõ").strip()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM reports 
        WHERE ticker = ? AND source = ? AND date = ?
    ''', (ticker, source, date))
    
    if cursor.fetchone():
        conn.close()
        return "ignored"
        
    cursor.execute('''
        INSERT INTO reports (
            ticker, source, date, recommendation, current_price_at_report, target_price,
            business_status, business_outlook, financial_forecast, risks, investment_thesis
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ticker,
        source,
        date,
        data.get("recommendation", "Theo dõi"),
        data.get("current_price_at_report", 1.0),
        data.get("target_price", 0.0),
        data.get("business_status", ""),
        data.get("business_outlook", ""),
        data.get("financial_forecast", ""),
        data.get("risks", ""),
        data.get("investment_thesis", "")
    ))
    
    conn.commit()
    conn.close()
    return "success"

def get_stock_valuation(ticker):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, source, date, recommendation, current_price_at_report, target_price
        FROM reports 
        WHERE ticker = ? 
        ORDER BY date DESC
    ''', (ticker.upper().strip(),))
    
    rows = cursor.fetchall()
    conn.close()
    
    processed_valuation = []
    for r in rows:
        try:
            current = float(r[4]) if r[4] is not None else 0.0
        except (ValueError, TypeError):
            current = 0.0
            
        try:
            target = float(r[5]) if r[5] is not None else 0.0
        except (ValueError, TypeError):
            target = 0.0
            
        if current > 0 and target > 0:
            upside = round(((target - current) / current * 100), 2)
        else:
            upside = 0.0
        
        processed_valuation.append(r + (upside,))
        
    return processed_valuation

def get_stock_pillars(ticker):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT source, business_status, business_outlook, financial_forecast, risks, investment_thesis 
        FROM reports 
        WHERE ticker = ? 
        ORDER BY (LENGTH(COALESCE(business_status, '')) + 
                  LENGTH(COALESCE(business_outlook, '')) + 
                  LENGTH(COALESCE(financial_forecast, '')) + 
                  LENGTH(COALESCE(risks, '')) + 
                  LENGTH(COALESCE(investment_thesis, ''))) DESC 
        LIMIT 3
    ''', (ticker.upper().strip(),))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_reports_by_ids(list_ids):
    if not list_ids:
        return False
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in list_ids)
    query = f"DELETE FROM reports WHERE id IN ({placeholders})"
    
    try:
        cursor.execute(query, list_ids)
        conn.commit()
        changes = conn.total_changes
        conn.close()
        return changes > 0
    except Exception:
        conn.close()
        return False