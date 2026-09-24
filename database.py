"""
Database management for Boutique Carlo Acutis Foundation - Cahier Journal
SQLite with robust schemas, seeded categories, and historical data.
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent / "journal.db"))
# Ensure parent directory exists if custom path provided
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

INITIAL_CATEGORIES = [
    ("Abonnement Wifi", "sortie", "depense"),
    ("Achat d'articles", "sortie", "depense"),
    ("Achat d'encre", "sortie", "depense"),
    ("Achat de cash power", "sortie", "depense"),
    ("Achat de papier ram", "sortie", "depense"),
    ("Conception", "entree", "service"),
    ("Coupe", "entree", "service"),
    ("Déplacement", "sortie", "depense"),
    ("Entretien des machines", "sortie", "depense"),
    ("Frais d'électricité", "sortie", "depense"),
    ("Impression", "entree", "service"),
    ("Lamination", "entree", "service"),
    ("Loyer", "sortie", "depense"),
    ("Photo passeport", "entree", "service"),
    ("Photocopie", "entree", "service"),
    ("Reliure", "entree", "service"),
    ("Reliure de livrets de bénédiction", "entree", "service"),
    ("Saisie", "entree", "service"),
    ("Scanner", "entree", "service"),
    ("Vente d'articles", "entree", "vente"),
    ("Vente d'image", "entree", "vente"),
    ("Vente de livres Anedoctes Mgr", "entree", "vente"),
    ("Vente de livret de bénédiction", "entree", "vente"),
    ("Vente de livret de confirmation", "entree", "vente"),
    ("Vente de livret de rosaire", "entree", "vente"),
    ("Vente de livret Esprit Saint", "entree", "vente"),
    ("Vente de Wifi", "entree", "service"),
    ("Confection de tampon", "entree", "service"),
]

from update_cahier_reel import REAL_TRANSACTIONS
INITIAL_TRANSACTIONS = REAL_TRANSACTIONS

def hash_pw(pwd: str) -> str:
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL, -- 'dg', 'dg_adjoint', 'secretaire'
        password_hash TEXT NOT NULL,
        pin TEXT NOT NULL DEFAULT '1234'
    )
    """)

    # Categories table
    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        operation_type TEXT NOT NULL DEFAULT 'both', -- 'entree', 'sortie', 'both'
        activity_type TEXT NOT NULL DEFAULT 'service', -- 'service', 'vente', 'depense'
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Dynamic migration to ensure activity_type column exists
    try:
        c.execute("ALTER TABLE categories ADD COLUMN activity_type TEXT DEFAULT 'service'")
    except sqlite3.OperationalError:
        pass

    # Synchronize default activity types
    c.execute("""
        UPDATE categories SET activity_type = 'vente' 
        WHERE operation_type != 'sortie' 
          AND ((name LIKE 'Vente %' AND name != 'Vente de Wifi') 
               OR name LIKE '%livret%' 
               OR name LIKE '%livre%' 
               OR name LIKE '%article%')
          AND name NOT LIKE 'Reliure%'
    """)
    c.execute("""
        UPDATE categories SET activity_type = 'service' 
        WHERE operation_type != 'sortie' 
          AND (activity_type IS NULL OR activity_type = '' OR activity_type != 'vente' OR name LIKE 'Reliure%')
    """)
    c.execute("UPDATE categories SET activity_type = 'depense' WHERE operation_type = 'sortie'")

    # Transactions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, -- YYYY-MM-DD
        category_name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'entree' ou 'sortie'
        amount REAL NOT NULL,
        description TEXT,
        created_by_user TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by_user TEXT,
        updated_at TIMESTAMP
    )
    """)

    # Audit log table
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Seed default users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users = [
            ("dg", "Directeur Général", "dg", hash_pw("12345"), "12345"),
            ("dg_adjoint", "DG Adjoint", "dg_adjoint", hash_pw("23456"), "23456"),
            ("secretaire", "Secrétaire de Caisse", "secretaire", hash_pw("4231"), "4231"),
        ]
        c.executemany("INSERT INTO users (username, full_name, role, password_hash, pin) VALUES (?, ?, ?, ?, ?)", users)

    # Seed categories if empty
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO categories (name, operation_type, activity_type) VALUES (?, ?, ?)",
            INITIAL_CATEGORIES
        )

    # Seed initial transactions if empty
    c.execute("SELECT COUNT(*) FROM transactions")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO transactions (date, category_name, type, amount, description, created_by_user) VALUES (?, ?, ?, ?, ?, ?)",
            INITIAL_TRANSACTIONS
        )

    conn.commit()
    conn.close()

# Initialize DB on module import
init_db()
