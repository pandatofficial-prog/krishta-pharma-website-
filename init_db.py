"""
Database Initialization Script for Krishat Pharma
Run this script to initialize the database with default admin users and sample products.
"""

import os
import sqlite3
import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if not USE_POSTGRES:
    DATABASE = 'pharma.db'

def get_db_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DATABASE)
        return conn

def init_database():
    """Initialize the database with tables and default admin users."""
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if USE_POSTGRES:
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (id SERIAL PRIMARY KEY,
                      username VARCHAR(255) UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id SERIAL PRIMARY KEY,
                      name TEXT NOT NULL,
                      price REAL NOT NULL,
                      description TEXT,
                      image TEXT)''')
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      price REAL NOT NULL,
                      description TEXT,
                      image TEXT)''')
    
    if USE_POSTGRES:
        c.execute("SELECT COUNT(*) FROM admins")
    else:
        c.execute("SELECT COUNT(*) FROM admins")
    count = c.fetchone()[0]
    
    if count == 0:
        admin_password = generate_password_hash('admin123')
        manager_password = generate_password_hash('manager123')
        
        if USE_POSTGRES:
            c.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", 
                      ('admin', admin_password))
            c.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", 
                      ('manager', manager_password))
        else:
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                      ('admin', admin_password))
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                      ('manager', manager_password))
        
        print("Default admin users created:")
        print("  Admin: admin / admin123")
        print("  Manager: manager / manager123")
    else:
        print(f"Database already initialized with {count} admin user(s).")
    
    conn.commit()
    conn.close()
    print("Database initialization complete!")

def add_sample_products():
    """Add Krishat Pharma sample products to the database."""
    
    sample_products = [
        ('Diclokris 50 - UN', 1500.00, 'Pain relief tablets for headaches and inflammation', '4NhLDTv2Y-diclokris-un-50.jpg'),
        ('Krishat Relief Gel', 1200.00, 'Topical gel for muscle and joint pain relief', 'PybQ2E9fL-relief-gel.jpg'),
        ('Becloderm-G Cream', 1800.00, 'Anti-inflammatory cream for skin conditions', 'pusq1X4Ty-becloderm-g.jpg'),
        ('Parakris 500 - Green', 800.00, 'Paracetamol 500mg for pain and fever', 'parakris-500.jpg'),
        ('Hydrokris Injection', 2500.00, 'Hydrocortisone injection for inflammation', 'hydrokris.jpg'),
        ('Gentakris-80 Injection', 3200.00, 'Gentamicin injection for bacterial infections', 'VHfsFpZwM-gentakris-80.jpg'),
        ('Vitakris', 950.00, 'Multivitamin supplement for overall health', 'ASKspe9t1-vitakris.jpg'),
        ('Combikris Extra', 2100.00, 'Combination pain relief tablets', 'ChvZutjXE-combikris-extra.jpg'),
        ('KPI', 1500.00, 'Potassium iodide supplement', 'kpi.jpg'),
        ('Kristen', 2800.00, 'Iron supplement for anemia', 'mepPkCdtw-kristen.jpg'),
        ('Krishat Jects', 4500.00, 'Injectable solution for various conditions', 'ject.jpg'),
        ('Krishat Doxycycline Capsules', 2200.00, 'Antibiotic capsules for infections', 'yPzKobH3j-doxycycline.jpg'),
    ]
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        if USE_POSTGRES:
            c.executemany('INSERT INTO products (name, price, description, image) VALUES (%s, %s, %s, %s)', 
                          sample_products)
        else:
            c.executemany('INSERT INTO products (name, price, description, image) VALUES (?, ?, ?, ?)', 
                          sample_products)
        print(f"Added {len(sample_products)} sample products.")
    else:
        print("Products already exist in database.")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Initializing Krishat Pharma Database...")
    init_database()
    add_sample_products()
    print("\nYou can now run the application with: python app.py")
