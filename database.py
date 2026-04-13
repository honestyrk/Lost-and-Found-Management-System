import sqlite3
import os

DB_PATH = 'campus_lost_found.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            location TEXT,
            contact_number TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            status TEXT DEFAULT 'Lost',
            reported_by INTEGER,
            FOREIGN KEY (reported_by) REFERENCES users (user_id)
        )
    ''')
    
    # Claims Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            user_id INTEGER,
            claim_status TEXT DEFAULT 'Pending',
            claim_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (item_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create an admin user if not exists
    cursor.execute("SELECT * FROM users WHERE email = 'admin@campus.com'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                       ('Admin', 'admin@campus.com', 'admin123', 'admin'))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
