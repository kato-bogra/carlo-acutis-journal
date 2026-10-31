import os
import sys
import json
import datetime
import openpyxl
import sqlite3
import urllib.request
from pathlib import Path

# Paths
REPO_DIR = Path(__file__).parent
EXCEL_FOLDER = Path(r"C:\Users\katoe\Downloads\Cahier journal")
DB_PATH = REPO_DIR / "journal.db"
GIST_ID = os.environ.get("GIST_ID", "4045a8b5aa79da1a3d2d43aca2d8b1d2")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

patterns = [
    ("01", "Janvier", lambda f: "janvier" in f.lower(), 270230.0),
    ("02", "Février", lambda f: "vrier" in f.lower(), 236525.0),
    ("03", "Mars", lambda f: "mars" in f.lower(), 398000.0),
    ("04", "Avril", lambda f: "avril" in f.lower(), 146200.0),
    ("05", "Mai", lambda f: "mai" in f.lower(), 193025.0),
    ("06", "Juin", lambda f: "juin" in f.lower(), 187450.0),
    ("07", "Juillet", lambda f: "juillet" in f.lower(), 108600.0),
    ("08", "Août", lambda f: "2026(1)" in f.lower() or "ao" in f.lower(), 206350.0),
    ("09", "Septembre", lambda f: "septembre" in f.lower(), 152500.0),
    ("10", "Octobre", lambda f: "octobre" in f.lower(), 440025.0),
]

files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith(".xlsx")]
all_cleaned_txs = []

print("=== 1. PARSING EXCEL FILES WITH CANONICAL 2026 DATES ===")
for m_num, m_name, fn, expected_solde in patterns:
    f_match = [f for f in files if fn(f)][0]
    path = EXCEL_FOLDER / f_match
    wb = openpyxl.load_workbook(path, data_only=True)
    sheet = wb.active
    
    h_row = 2
    for r in range(1, 6):
        v2 = str(sheet.cell(r, 2).value or "")
        if "Libell" in v2:
            h_row = r
            break
            
    cur_date = None
    m_in = 0.0
    m_out = 0.0
    m_txs = []
    
    for r in range(h_row + 1, sheet.max_row + 1):
        d_val = sheet.cell(r, 1).value
        lib_val = sheet.cell(r, 2).value
        in_val = sheet.cell(r, 3).value
        out_val = sheet.cell(r, 4).value
        
        # Date parsing: extract day and enforce 2026-MM-DD
        if d_val is not None and str(d_val).strip():
            if isinstance(d_val, (datetime.datetime, datetime.date)):
                day = d_val.day
            elif isinstance(d_val, str):
                s = d_val.strip()
                if "/" in s:
                    day = int(s.split("/")[0])
                elif "-" in s:
                    day = int(s.split("-")[2][:2])
                else:
                    day = int(s)
            cur_date = f"2026-{m_num}-{int(day):02d}"
            
        if lib_val is None and in_val is None and out_val is None:
            continue
            
        lib_clean = str(lib_val or "").strip()
        description = ""
        
        # Specific normalizations
        if not lib_clean:
            if cur_date == "2026-09-17" and (out_val == 54400.0 or in_val == 54400.0):
                lib_clean = "Achat d'articles"
                description = "Dépense diverse"
            else:
                lib_clean = "Divers"
        elif lib_clean == "Livret de rosaire":
            lib_clean = "Vente de livret de rosaire"
        elif lib_clean == "Achat d'articles" and in_val is not None and in_val > 0:
            lib_clean = "Vente d'articles"
            description = "Article divers"
            
        op_type = "entree" if in_val is not None and (out_val is None or in_val > 0) else "sortie"
        amount = float(in_val) if op_type == "entree" else float(out_val or 0.0)
        
        if amount <= 0:
            continue
            
        if op_type == "entree":
            m_in += amount
        else:
            m_out += amount
            
        tx_obj = {
            "date": cur_date,
            "category_name": lib_clean,
            "type": op_type,
            "amount": amount,
            "description": description,
            "created_by_user": "secretaire"
        }
        m_txs.append(tx_obj)
        all_cleaned_txs.append(tx_obj)
        
    actual_solde = m_in - m_out
    assert abs(actual_solde - expected_solde) < 0.01, f"Mismatch in {m_name}: got {actual_solde}, expected {expected_solde}"
    print(f"  [OK] {m_num} - {m_name:<10}: {len(m_txs):3d} txs | Dates: {m_txs[0]['date']} -> {m_txs[-1]['date']} | Solde: {actual_solde:10,.0f} FCFA")

print(f"\nTotal validated transactions: {len(all_cleaned_txs)}")

# === 2. UPDATE update_cahier_reel.py ===
print("\n=== 2. UPDATING update_cahier_reel.py ===")
reel_py = REPO_DIR / "update_cahier_reel.py"
reel_lines = [
    '"""\nUpdate database with the real monthly journal data for January to October 2026.\n"""\n\n',
    "REAL_TRANSACTIONS = [\n"
]
for tx in all_cleaned_txs:
    d = tx["date"]
    cat = tx["category_name"].replace('"', '\\"')
    t = tx["type"]
    amt = int(tx["amount"]) if tx["amount"].is_integer() else tx["amount"]
    desc = tx["description"].replace('"', '\\"')
    user = tx["created_by_user"]
    reel_lines.append(f'    ("{d}", "{cat}", "{t}", {amt}, "{desc}", "{user}"),\n')
reel_lines.append("]\n")

with open(reel_py, "w", encoding="utf-8") as f:
    f.writelines(reel_lines)
print(f"Successfully wrote {len(all_cleaned_txs)} transactions into {reel_py}")

# === 3. UPDATE journal.db ===
print("\n=== 3. UPDATING LOCAL journal.db ===")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Ensure all categories exist
categories_to_ensure = [
    ("Abonnement Wifi", "sortie", "depense"),
    ("Achat d'articles", "both", "depense"),
    ("Achat d'encre", "sortie", "depense"),
    ("Achat de cash power", "sortie", "depense"),
    ("Achat de papier ram", "sortie", "depense"),
    ("Conception", "entree", "service"),
    ("Confection de tampon", "both", "service"),
    ("Coupe", "both", "service"),
    ("Déplacement", "sortie", "depense"),
    ("Entretien des machines", "sortie", "depense"),
    ("Frais d'électricité", "sortie", "depense"),
    ("Frais de mairie", "sortie", "depense"),
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
    ("Vente de sanctoral", "entree", "vente"),
    ("Vente de Wifi", "entree", "service"),
]

for name, op_type, act_type in categories_to_ensure:
    c.execute("SELECT id FROM categories WHERE name = ?", (name,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE categories SET operation_type = ?, activity_type = ?, is_active = 1 WHERE name = ?", (op_type, act_type, name))
    else:
        c.execute("INSERT INTO categories (name, operation_type, activity_type, is_active) VALUES (?, ?, ?, 1)", (name, op_type, act_type))

# Re-populate transactions table cleanly
c.execute("DELETE FROM transactions")
for tx in all_cleaned_txs:
    c.execute(
        "INSERT INTO transactions (date, category_name, type, amount, description, created_by_user) VALUES (?, ?, ?, ?, ?, ?)",
        (tx["date"], tx["category_name"], tx["type"], tx["amount"], tx["description"], tx["created_by_user"])
    )

conn.commit()

# Verify counts in DB
c.execute("SELECT COUNT(*), SUM(CASE WHEN type='entree' THEN amount ELSE 0 END), SUM(CASE WHEN type='sortie' THEN amount ELSE 0 END) FROM transactions")
cnt, tot_in, tot_out = c.fetchone()
conn.close()

print(f"Database populated with {cnt} transactions.")
print(f"Total Entrées : {tot_in:,.0f} FCFA")
print(f"Total Sorties : {tot_out:,.0f} FCFA")
print(f"Solde Net     : {tot_in - tot_out:,.0f} FCFA")
assert cnt == 1377
assert abs((tot_in - tot_out) - 2338905.0) < 0.01

# === 4. EXPORT JSON AND PUSH TO GITHUB GIST ===
print("\n=== 4. EXPORTING JSON & SYNCING TO GITHUB GIST ===")
import database
export_data = database.export_data_json()
backup_file = REPO_DIR / "journal_backup.json"
with open(backup_file, "w", encoding="utf-8") as f:
    json.dump(export_data, f, indent=2, ensure_ascii=False)
print(f"Saved local export: {backup_file} ({len(export_data['transactions'])} transactions)")

# Patch GitHub Gist
payload = {
    "files": {
        "journal_backup.json": {
            "content": json.dumps(export_data, indent=2, ensure_ascii=False)
        }
    }
}
req = urllib.request.Request(
    f"https://api.github.com/gists/{GIST_ID}",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Boutique-Carlo-Acutis"
    },
    method="PATCH"
)

with urllib.request.urlopen(req) as resp:
    print(f"Gist successfully updated! HTTP Status: {resp.status}")

print("\nALL TASKS COMPLETED SUCCESSFULLY!")
