import sqlite3

def clear_all_bookings():
    conn = sqlite3.connect('barbershop.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings')
    conn.commit()
    conn.close()
    print("✅ Все записи удалены!")

if __name__ == '__main__':
    clear_all_bookings()