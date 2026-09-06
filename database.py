import sqlite3
import json
from datetime import datetime, timedelta
from config import Config

DB_NAME = 'barbershop.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица записей (обновлена)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            user_phone TEXT,
            master_id INTEGER NOT NULL,
            master_name TEXT,
            service_id INTEGER NOT NULL,
            service_name TEXT,
            service_price INTEGER,
            service_duration INTEGER,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TEXT,
            reminder_sent INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица для временных данных
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temp_data (
            user_id INTEGER PRIMARY KEY,
            data TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def save_temp_data(user_id, data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO temp_data (user_id, data, updated_at) VALUES (?, ?, ?)',
        (user_id, json.dumps(data, ensure_ascii=False), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_temp_data(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM temp_data WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row['data']) if row else None

def delete_temp_data(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM temp_data WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_booking(user_id, user_name, user_phone, master_id, master_name, 
                service_id, service_name, service_price, service_duration, date, time):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (
            user_id, user_name, user_phone, master_id, master_name,
            service_id, service_name, service_price, service_duration, date, time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, user_phone, master_id, master_name,
          service_id, service_name, service_price, service_duration, date, time))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return booking_id

def get_booking(booking_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_bookings(user_id, status=None):
    conn = get_db()
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM bookings WHERE user_id = ? AND status = ? ORDER BY date, time', (user_id, status))
    else:
        cursor.execute('SELECT * FROM bookings WHERE user_id = ? ORDER BY date, time', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_bookings(status=None):
    conn = get_db()
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM bookings WHERE status = ? ORDER BY date, time', (status,))
    else:
        cursor.execute('SELECT * FROM bookings ORDER BY date, time')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_master_bookings(master_id, date=None, status=None):
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM bookings WHERE master_id = ?'
    params = [master_id]
    if date:
        query += ' AND date = ?'
        params.append(date)
    if status:
        query += ' AND status = ?'
        params.append(status)
    query += ' ORDER BY time'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_booking_status(booking_id, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE bookings SET status = ?, confirmed_at = CURRENT_TIMESTAMP WHERE id = ?',
        (status, booking_id)
    )
    conn.commit()
    conn.close()

def cancel_booking(booking_id):
    """Полностью удаляет запись из базы данных"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()

def delete_old_temp_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM temp_data WHERE datetime(updated_at) < datetime("now", "-1 hour")')
    conn.commit()
    conn.close()

def get_bookings_for_reminder(hours_before=2):
    """Получить записи, по которым нужно отправить напоминание"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now()
    target_time = now + timedelta(hours=hours_before)
    
    cursor.execute('''
        SELECT * FROM bookings 
        WHERE status = 'confirmed' 
        AND reminder_sent = 0
        AND date = ? 
        AND time = ?
        AND (strftime('%s', datetime(date || ' ' || time)) - strftime('%s', 'now')) / 3600 BETWEEN ? AND ?
    ''', (
        now.strftime('%Y-%m-%d'),
        target_time.strftime('%H:%M'),
        hours_before - 1,
        hours_before + 1
    ))
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_reminder_sent(booking_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE bookings SET reminder_sent = 1 WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()

def delete_booking_permanently(booking_id):
    """Полное удаление записи из базы"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()