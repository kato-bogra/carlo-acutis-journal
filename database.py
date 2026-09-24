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
    ("Abonnement Wifi", "sortie"),
    ("Achat d'articles", "sortie"),
    ("Achat d'encre", "sortie"),
    ("Achat de cash power", "sortie"),
    ("Achat de papier ram", "sortie"),
    ("Conception", "entree"),
    ("Coupe", "entree"),
    ("Déplacement", "sortie"),
    ("Entretien des machines", "sortie"),
    ("Frais d'électricité", "sortie"),
    ("Impression", "entree"),
    ("Lamination", "entree"),
    ("Loyer", "sortie"),
    ("Photo passeport", "entree"),
    ("Photocopie", "entree"),
    ("Reliure", "entree"),
    ("Reliure de livrets de bénédiction", "entree"),
    ("Saisie", "entree"),
    ("Scanner", "entree"),
    ("Vente d'articles", "entree"),
    ("Vente d'image", "entree"),
    ("Vente de livres Anedoctes Mgr", "entree"),
    ("Vente de livret de bénédiction", "entree"),
    ("Vente de livret de confirmation", "entree"),
    ("Vente de livret de rosaire", "entree"),
    ("Vente de livret Esprit Saint", "entree"),
    ("Vente de Wifi", "entree"),
    ("Confection de tampon", "entree"),
]

INITIAL_TRANSACTIONS = [
    # 01/09/2026
    ("2026-09-01", "Photocopie", "entree", 2150, "Photocopies journée", "secretaire"),
    ("2026-09-01", "Impression", "entree", 675, "Impressions diverses", "secretaire"),
    ("2026-09-01", "Vente d'articles", "entree", 2950, "Ventes comptoir", "secretaire"),
    ("2026-09-01", "Photo passeport", "entree", 3000, "Photos d'identité", "secretaire"),
    ("2026-09-01", "Saisie", "entree", 300, "Saisie documents", "secretaire"),
    # 02/09/2026
    ("2026-09-02", "Photocopie", "entree", 625, "Photocopies", "secretaire"),
    ("2026-09-02", "Impression", "entree", 7450, "Gros tirage d'impression", "secretaire"),
    ("2026-09-02", "Vente d'articles", "entree", 1900, "Ventes boutique", "secretaire"),
    ("2026-09-02", "Saisie", "entree", 600, "Saisie rapports", "secretaire"),
    ("2026-09-02", "Achat de papier ram", "sortie", 10000, "Achat stock ramettes de papier", "secretaire"),
    ("2026-09-02", "Scanner", "entree", 1500, "Numérisation documents", "secretaire"),
    # 03/09/2026
    ("2026-09-03", "Photocopie", "entree", 825, "Photocopies", "secretaire"),
    ("2026-09-03", "Impression", "entree", 2125, "Impressions", "secretaire"),
    ("2026-09-03", "Vente d'articles", "entree", 650, "Articles divers", "secretaire"),
    ("2026-09-03", "Saisie", "entree", 1200, "Saisie de textes", "secretaire"),
    ("2026-09-03", "Reliure", "entree", 200, "Reliure spirale", "secretaire"),
    ("2026-09-03", "Photo passeport", "entree", 3000, "Photos passeport express", "secretaire"),
    ("2026-09-03", "Déplacement", "sortie", 2000, "Frais de déplacement courses", "secretaire"),
    # 04/09/2026
    ("2026-09-04", "Reliure", "entree", 100, "Reliure", "secretaire"),
    ("2026-09-04", "Photocopie", "entree", 1600, "Photocopies", "secretaire"),
]

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
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

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
            ("dg", "Directeur Général", "dg", hash_pw("dg2026"), "1234"),
            ("dg_adjoint", "DG Adjoint", "dg_adjoint", hash_pw("dga2026"), "1234"),
            ("secretaire", "Secrétaire de Caisse", "secretaire", hash_pw("sec2026"), "1234"),
        ]
        c.executemany("INSERT INTO users (username, full_name, role, password_hash, pin) VALUES (?, ?, ?, ?, ?)", users)

    # Seed categories if empty
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO categories (name, operation_type) VALUES (?, ?)",
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
