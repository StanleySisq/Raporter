import sqlite3
import os

def init_database():
    if not os.path.exists('tickets.db'):
        conn = sqlite3.connect('tickets.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_tickets (
                ticket_id INTEGER PRIMARY KEY
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized.")
    else:
        print("Database exists.")

def add_ticket_id(ticket_id):
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO processed_tickets (ticket_id) VALUES (?)', (ticket_id,))
    conn.commit()
    conn.close()
    print(f"Ticket {ticket_id} added to the database.")

def is_ticket(ticket_id):
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ticket_id FROM processed_tickets WHERE ticket_id = ?', (ticket_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None