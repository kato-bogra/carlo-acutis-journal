"""
Database management for Boutique Carlo Acutis Foundation - Cahier Journal
SQLite with robust schemas, seeded categories, and historical data.
"""

import sqlite3
import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path

LOCAL_SOURCE_DB = Path(__file__).parent / "journal.db"

def resolve_db_path() -> Path:
    # 1. Custom DB_PATH from environment variable
    if "DB_PATH" in os.environ and os.environ["DB_PATH"].strip():
        p = Path(os.environ["DB_PATH"].strip())
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return p

    # 2. Render persistent disk auto-detection (/data)
    render_data = Path("/data")
    if render_data.exists() and os.access(render_data, os.W_OK):
        return render_data / "journal.db"

    # 3. Default local repository database
    return LOCAL_SOURCE_DB

DB_PATH = resolve_db_path()


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
    ("Reliure de livre de bénédiction", "sortie", "depense"),
    ("Reliure de livrets de bénédiction", "sortie", "depense"),
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

class LibsqlRow:
    def __init__(self, cols, values):
        self._cols = cols
        self._values = values
        self._map = dict(zip(cols, values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._map[key]

    def get(self, key, default=None):
        return self._map.get(key, default)

    def keys(self):
        return self._cols

    def values(self):
        return self._values

    def items(self):
        return self._map.items()

    def __iter__(self):
        return iter(self._cols)

class LibsqlCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=()):
        return self._cursor.execute(sql, params)

    def executemany(self, sql, params=()):
        return self._cursor.executemany(sql, params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        cols = [col[0] for col in self._cursor.description]
        return LibsqlRow(cols, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        cols = [col[0] for col in self._cursor.description]
        return [LibsqlRow(cols, r) for r in rows]

    @property
    def lastrowid(self):
        return getattr(self._cursor, 'lastrowid', None)

    def __getattr__(self, name):
        return getattr(self._cursor, name)

class LibsqlConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return LibsqlCursorWrapper(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)

def get_connection():
    turso_url = os.environ.get("TURSO_DATABASE_URL", "").strip()
    turso_token = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
    if turso_url:
        try:
            import libsql
            raw_conn = libsql.connect(database=turso_url, auth_token=turso_token or None)
            return LibsqlConnectionWrapper(raw_conn)
        except Exception as e:
            print(f"Warning: Failed to connect to Turso ({e}), falling back to SQLite.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # If DB_PATH is a separate storage directory (e.g. Render /data) and the file doesn't exist yet, copy initial DB
    try:
        if DB_PATH.resolve() != LOCAL_SOURCE_DB.resolve() and not DB_PATH.exists() and LOCAL_SOURCE_DB.exists():
            shutil.copy2(LOCAL_SOURCE_DB, DB_PATH)
    except Exception as e:
        print(f"Notice: Initial DB copy skipped: {e}")

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
        UPDATE categories 
        SET operation_type = 'entree', activity_type = 'service' 
        WHERE name = 'Reliure'
    """)
    c.execute("""
        UPDATE categories SET activity_type = 'service' 
        WHERE operation_type != 'sortie' 
          AND (activity_type IS NULL OR activity_type = '' OR activity_type != 'vente')
          AND name NOT LIKE 'Reliure de livr%'
    """)
    c.execute("""
        UPDATE categories 
        SET operation_type = 'sortie', activity_type = 'depense' 
        WHERE name LIKE 'Reliure de livr%'
    """)
    c.execute("UPDATE categories SET activity_type = 'depense' WHERE operation_type = 'sortie'")

    # Ensure 'Reliure de livre de bénédiction' exists as a configured category
    c.execute("SELECT id FROM categories WHERE name = 'Reliure de livre de bénédiction'")
    if not c.fetchone():
        c.execute("INSERT INTO categories (name, operation_type, activity_type) VALUES ('Reliure de livre de bénédiction', 'sortie', 'depense')")

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
            ("secretaire", "Secrétaire de Caisse", "secretaire", hash_pw("54321"), "54321"),
        ]
        c.executemany("INSERT INTO users (username, full_name, role, password_hash, pin) VALUES (?, ?, ?, ?, ?)", users)

    # Ensure secretaire password is set to 54321
    c.execute("UPDATE users SET pin = '54321', password_hash = ? WHERE username = 'secretaire'", (hash_pw("54321"),))

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

    # Automatic Cloud Sync from GitHub Gist if configured
    try:
        sync_from_cloud()
    except Exception as e:
        print(f"[CloudSync] Notice au démarrage: {e}")

def get_db_stats():
    """Retrieve runtime database metrics and storage information."""
    turso_url = os.environ.get("TURSO_DATABASE_URL", "").strip()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM transactions")
    tx_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM categories")
    cat_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    conn.close()

    file_size_kb = 0
    last_modified = "N/A"
    gist_id = os.environ.get("GIST_ID", "").strip()
    if gist_id:
        storage_mode = "Cloud Permanent Automatique (GitHub Sync 100% Gratuit)"
        is_persistent = True
        path_display = f"GitHub Cloud Gist #{gist_id[:8]}... (0 FCFA)"
        last_modified = "Synchronisé Cloud (Automatique)"
    elif turso_url:
        storage_mode = "Cloud Permanent Turso (100% Gratuit à vie)"
        is_persistent = True
        path_display = turso_url
        last_modified = "Synchronisé Cloud (Temps réel)"
    else:
        if DB_PATH.exists():
            file_size_kb = round(DB_PATH.stat().st_size / 1024, 2)
            last_modified = datetime.fromtimestamp(DB_PATH.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S")

        is_persistent = "/data" in str(DB_PATH) or "DB_PATH" in os.environ
        storage_mode = "Disque Persistant (/data)" if is_persistent else "Stockage Local Temporaire"
        path_display = str(DB_PATH)

    return {
        "path": path_display,
        "storage_mode": storage_mode,
        "is_persistent": is_persistent,
        "tx_count": tx_count,
        "cat_count": cat_count,
        "user_count": user_count,
        "size_kb": file_size_kb,
        "last_modified": last_modified,
    }

def export_data_json():
    """Export all categories and transactions into a clean dictionary."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY id ASC")
    categories = [dict(r) for r in c.fetchall()]
    c.execute("SELECT * FROM transactions ORDER BY date ASC, id ASC")
    transactions = [dict(r) for r in c.fetchall()]
    conn.close()
    return {
        "exported_at": datetime.now().isoformat(),
        "total_categories": len(categories),
        "total_transactions": len(transactions),
        "categories": categories,
        "transactions": transactions,
    }

def restore_from_json(data: dict) -> int:
    """Safely restore categories and transactions from a JSON backup without duplicates."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Categories
    for cat in data.get("categories", []):
        c.execute("""
            INSERT OR IGNORE INTO categories (name, operation_type, activity_type, is_active)
            VALUES (?, ?, ?, ?)
        """, (cat.get("name"), cat.get("operation_type", "both"), cat.get("activity_type", "service"), cat.get("is_active", 1)))

    # 2. Transactions
    imported_count = 0
    for tx in data.get("transactions", []):
        c.execute("""
            SELECT id FROM transactions 
            WHERE date = ? AND category_name = ? AND type = ? AND amount = ? 
              AND ((description IS NULL AND ? IS NULL) OR description = ?)
        """, (tx.get("date"), tx.get("category_name"), tx.get("type"), tx.get("amount"), tx.get("description"), tx.get("description")))
        if not c.fetchone():
            c.execute("""
                INSERT INTO transactions (date, category_name, type, amount, description, created_by_user)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tx.get("date"), tx.get("category_name"), tx.get("type"), tx.get("amount"), tx.get("description"), tx.get("created_by_user", "restauration")))
            imported_count += 1
            
    conn.commit()
    conn.close()
    return imported_count

def sync_from_cloud() -> int:
    """Fetch latest transactions from private GitHub Gist on startup."""
    gist_id = os.environ.get("GIST_ID", "").strip()
    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not gist_id or not github_token:
        return 0

    try:
        import urllib.request
        import json
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Boutique-Carlo-Acutis'
        }
        req = urllib.request.Request(f'https://api.github.com/gists/{gist_id}', headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode())
            file_info = res.get('files', {}).get('journal_backup.json')
            if file_info and file_info.get('content'):
                data = json.loads(file_info['content'])
                imported = restore_from_json(data)
                print(f"[CloudSync] Synchronisé avec succès depuis GitHub Gist ({imported} nouvelles transactions importées).")
                return imported
    except Exception as e:
        print(f"[CloudSync] Notice au démarrage sync cloud: {e}")
    return 0

def sync_to_cloud_async():
    """Trigger background sync to cloud Gist."""
    import threading
    t = threading.Thread(target=_push_to_gist, daemon=True)
    t.start()

def _push_to_gist():
    """Push current complete state to private GitHub Gist."""
    gist_id = os.environ.get("GIST_ID", "").strip()
    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not gist_id or not github_token:
        return

    try:
        import urllib.request
        import json
        data = export_data_json()
        payload = {
            'files': {
                'journal_backup.json': {
                    'content': json.dumps(data, indent=2, ensure_ascii=False)
                }
            }
        }
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'Boutique-Carlo-Acutis'
        }
        req = urllib.request.Request(f'https://api.github.com/gists/{gist_id}', data=json.dumps(payload).encode('utf-8'), headers=headers, method='PATCH')
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("[CloudSync] Sauvegarde cloud GitHub Gist mise à jour.")
    except Exception as e:
        print(f"[CloudSync] Erreur mise à jour Gist: {e}")

# Initialize DB on module import
init_db()

