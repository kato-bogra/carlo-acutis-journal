"""
Update database with the real monthly journal data for September 2026 (from PDF)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "journal.db"

REAL_TRANSACTIONS = [
    # 01/09/2026
    ("2026-09-01", "Photocopie", "entree", 2150, "", "secretaire"),
    ("2026-09-01", "Impression", "entree", 675, "", "secretaire"),
    ("2026-09-01", "Vente d'articles", "entree", 2950, "", "secretaire"),
    ("2026-09-01", "Photo passeport", "entree", 3000, "", "secretaire"),
    ("2026-09-01", "Saisie", "entree", 300, "", "secretaire"),
    # 02/09/2026
    ("2026-09-02", "Photocopie", "entree", 625, "", "secretaire"),
    ("2026-09-02", "Impression", "entree", 7450, "", "secretaire"),
    ("2026-09-02", "Vente d'articles", "entree", 1900, "", "secretaire"),
    ("2026-09-02", "Saisie", "entree", 600, "", "secretaire"),
    ("2026-09-02", "Achat de papier ram", "sortie", 10000, "", "secretaire"),
    ("2026-09-02", "Scanner", "entree", 1500, "", "secretaire"),
    # 03/09/2026
    ("2026-09-03", "Photocopie", "entree", 825, "", "secretaire"),
    ("2026-09-03", "Impression", "entree", 2125, "", "secretaire"),
    ("2026-09-03", "Vente d'articles", "entree", 650, "", "secretaire"),
    ("2026-09-03", "Saisie", "entree", 1200, "", "secretaire"),
    ("2026-09-03", "Reliure", "entree", 200, "", "secretaire"),
    ("2026-09-03", "Photo passeport", "entree", 3000, "", "secretaire"),
    ("2026-09-03", "Déplacement", "sortie", 2000, "", "secretaire"),
    # 04/09/2026
    ("2026-09-04", "Reliure", "entree", 100, "", "secretaire"),
    ("2026-09-04", "Photocopie", "entree", 1600, "", "secretaire"),
    ("2026-09-04", "Impression", "entree", 1300, "", "secretaire"),
    ("2026-09-04", "Vente d'articles", "entree", 700, "", "secretaire"),
    ("2026-09-04", "Scanner", "entree", 300, "", "secretaire"),
    ("2026-09-04", "Photo passeport", "entree", 3000, "", "secretaire"),
    ("2026-09-04", "Achat d'articles", "sortie", 10300, "", "secretaire"),
    ("2026-09-04", "Déplacement", "sortie", 1000, "", "secretaire"),
    # 05/09/2026
    ("2026-09-05", "Photocopie", "entree", 100, "", "secretaire"),
    ("2026-09-05", "Impression", "entree", 34450, "", "secretaire"),
    ("2026-09-05", "Vente d'articles", "entree", 23300, "", "secretaire"),
    ("2026-09-05", "Conception", "entree", 2000, "", "secretaire"),
    ("2026-09-05", "Coupe", "entree", 1000, "", "secretaire"),
    ("2026-09-05", "Achat d'articles", "sortie", 6300, "", "secretaire"),
    ("2026-09-05", "Déplacement", "sortie", 1000, "", "secretaire"),
    # 07/09/2026
    ("2026-09-07", "Photocopie", "entree", 1325, "", "secretaire"),
    ("2026-09-07", "Impression", "entree", 3125, "", "secretaire"),
    ("2026-09-07", "Vente d'articles", "entree", 2500, "", "secretaire"),
    ("2026-09-07", "Photo passeport", "entree", 2000, "", "secretaire"),
    ("2026-09-07", "Scanner", "entree", 100, "", "secretaire"),
    ("2026-09-07", "Saisie", "entree", 600, "", "secretaire"),
    ("2026-09-07", "Entretien des machines", "sortie", 2000, "", "secretaire"),
    # 08/09/2026
    ("2026-09-08", "Photocopie", "entree", 1000, "", "secretaire"),
    ("2026-09-08", "Impression", "entree", 20900, "", "secretaire"),
    ("2026-09-08", "Vente d'articles", "entree", 15700, "", "secretaire"),
    ("2026-09-08", "Photo passeport", "entree", 4000, "", "secretaire"),
    ("2026-09-08", "Reliure", "entree", 325, "", "secretaire"),
    ("2026-09-08", "Scanner", "entree", 1800, "", "secretaire"),
    ("2026-09-08", "Achat de papier ram", "sortie", 10000, "", "secretaire"),
    ("2026-09-08", "Achat d'articles", "sortie", 3000, "", "secretaire"),
    ("2026-09-08", "Vente de livret Esprit Saint", "entree", 29000, "", "secretaire"),
    ("2026-09-08", "Déplacement", "sortie", 1000, "", "secretaire"),
    # 09/09/2026
    ("2026-09-09", "Photocopie", "entree", 1350, "", "secretaire"),
    ("2026-09-09", "Impression", "entree", 19375, "", "secretaire"),
    ("2026-09-09", "Vente d'articles", "entree", 10650, "", "secretaire"),
    ("2026-09-09", "Saisie", "entree", 1400, "", "secretaire"),
    ("2026-09-09", "Reliure", "entree", 100, "", "secretaire"),
    ("2026-09-09", "Lamination", "entree", 200, "", "secretaire"),
    ("2026-09-09", "Photo passeport", "entree", 2000, "", "secretaire"),
    ("2026-09-09", "Scanner", "entree", 400, "", "secretaire"),
    # 10/09/2026
    ("2026-09-10", "Photocopie", "entree", 1150, "", "secretaire"),
    ("2026-09-10", "Impression", "entree", 1100, "", "secretaire"),
    ("2026-09-10", "Vente d'articles", "entree", 925, "", "secretaire"),
    ("2026-09-10", "Photo passeport", "entree", 2000, "", "secretaire"),
    ("2026-09-10", "Saisie", "entree", 1100, "", "secretaire"),
    # 11/09/2026
    ("2026-09-11", "Photocopie", "entree", 775, "", "secretaire"),
    ("2026-09-11", "Impression", "entree", 2325, "", "secretaire"),
    ("2026-09-11", "Vente d'articles", "entree", 425, "", "secretaire"),
    ("2026-09-11", "Saisie", "entree", 1200, "", "secretaire"),
    ("2026-09-11", "Entretien des machines", "sortie", 2000, "", "secretaire"),
    # 12/09/2026
    ("2026-09-12", "Photocopie", "entree", 125, "", "secretaire"),
    ("2026-09-12", "Impression", "entree", 1850, "", "secretaire"),
    ("2026-09-12", "Vente d'articles", "entree", 4125, "", "secretaire"),
    ("2026-09-12", "Photo passeport", "entree", 1000, "", "secretaire"),
    # 14/09/2026
    ("2026-09-14", "Photocopie", "entree", 3175, "", "secretaire"),
    ("2026-09-14", "Impression", "entree", 7725, "", "secretaire"),
    ("2026-09-14", "Vente d'articles", "entree", 3325, "", "secretaire"),
    ("2026-09-14", "Lamination", "entree", 200, "", "secretaire"),
    ("2026-09-14", "Photo passeport", "entree", 3000, "", "secretaire"),
    ("2026-09-14", "Achat d'articles", "sortie", 1000, "", "secretaire"),
    # 15/09/2026
    ("2026-09-15", "Photocopie", "entree", 7150, "", "secretaire"),
    ("2026-09-15", "Impression", "entree", 12225, "", "secretaire"),
    ("2026-09-15", "Vente d'articles", "entree", 8675, "", "secretaire"),
    ("2026-09-15", "Reliure", "entree", 200, "", "secretaire"),
    ("2026-09-15", "Lamination", "entree", 5000, "", "secretaire"),
    ("2026-09-15", "Photo passeport", "entree", 1000, "", "secretaire"),
    ("2026-09-15", "Conception", "entree", 300, "", "secretaire"),
    ("2026-09-15", "Coupe", "entree", 4400, "", "secretaire"),
    ("2026-09-15", "Achat d'articles", "sortie", 2300, "", "secretaire"),
    ("2026-09-15", "Achat de papier ram", "sortie", 10000, "", "secretaire"),
    # 16/09/2026
    ("2026-09-16", "Photocopie", "entree", 4175, "", "secretaire"),
    ("2026-09-16", "Impression", "entree", 29125, "", "secretaire"),
    ("2026-09-16", "Vente d'articles", "entree", 7050, "", "secretaire"),
    ("2026-09-16", "Reliure", "entree", 500, "", "secretaire"),
    ("2026-09-16", "Lamination", "entree", 2500, "", "secretaire"),
    ("2026-09-16", "Coupe", "entree", 250, "", "secretaire"),
    ("2026-09-16", "Photo passeport", "entree", 2000, "", "secretaire"),
    ("2026-09-16", "Vente de livret de bénédiction", "entree", 4000, "", "secretaire"),
    # 17/09/2026
    ("2026-09-17", "Photocopie", "entree", 4525, "", "secretaire"),
    ("2026-09-17", "Impression", "entree", 10100, "", "secretaire"),
    ("2026-09-17", "Vente d'articles", "entree", 2850, "", "secretaire"),
    ("2026-09-17", "Saisie", "entree", 250, "", "secretaire"),
    ("2026-09-17", "Lamination", "entree", 200, "", "secretaire"),
    ("2026-09-17", "Abonnement Wifi", "sortie", 15000, "", "secretaire"),
    ("2026-09-17", "Achat de papier ram", "sortie", 10000, "", "secretaire"),
    ("2026-09-17", "Achat d'articles", "sortie", 54400, "Dépense diverse", "secretaire"),
    # 18/09/2026
    ("2026-09-18", "Photocopie", "entree", 6950, "", "secretaire"),
    ("2026-09-18", "Impression", "entree", 14600, "", "secretaire"),
    ("2026-09-18", "Vente d'articles", "entree", 2475, "", "secretaire"),
    ("2026-09-18", "Saisie", "entree", 300, "", "secretaire"),
    ("2026-09-18", "Photo passeport", "entree", 1000, "", "secretaire"),
    ("2026-09-18", "Reliure", "entree", 200, "", "secretaire"),
    # 19/09/2026
    ("2026-09-19", "Impression", "entree", 8175, "", "secretaire"),
    ("2026-09-19", "Photocopie", "entree", 275, "", "secretaire"),
    ("2026-09-19", "Scanner", "entree", 400, "", "secretaire"),
    ("2026-09-19", "Photo passeport", "entree", 1000, "", "secretaire"),
    ("2026-09-19", "Vente d'articles", "entree", 6000, "", "secretaire"),
    ("2026-09-19", "Entretien des machines", "sortie", 34600, "", "secretaire"),
    ("2026-09-19", "Achat d'articles", "sortie", 185250, "Achat stock fournitures", "secretaire"),
    ("2026-09-19", "Déplacement", "sortie", 1500, "", "secretaire"),
    # 21/09/2026
    ("2026-09-21", "Photocopie", "entree", 8175, "", "secretaire"),
    ("2026-09-21", "Impression", "entree", 2450, "", "secretaire"),
    ("2026-09-21", "Vente d'articles", "entree", 22400, "", "secretaire"),
    ("2026-09-21", "Lamination", "entree", 200, "", "secretaire"),
    ("2026-09-21", "Reliure", "entree", 200, "", "secretaire"),
    ("2026-09-21", "Achat de papier ram", "sortie", 10000, "", "secretaire"),
    ("2026-09-21", "Scanner", "entree", 2200, "", "secretaire"),
    ("2026-09-21", "Déplacement", "sortie", 1000, "", "secretaire"),
    # 22/09/2026 (Dans le PDF noté 22/6/2026)
    ("2026-09-22", "Photocopie", "entree", 11475, "Noté 22/6 sur cahier", "secretaire"),
    ("2026-09-22", "Impression", "entree", 4675, "", "secretaire"),
    ("2026-09-22", "Vente d'articles", "entree", 2725, "", "secretaire"),
    ("2026-09-22", "Photo passeport", "entree", 1000, "", "secretaire"),
    ("2026-09-22", "Achat de papier ram", "sortie", 10000, "", "secretaire"),
    # 23/09/2026
    ("2026-09-23", "Photocopie", "entree", 5200, "", "secretaire"),
    ("2026-09-23", "Impression", "entree", 6675, "", "secretaire"),
    ("2026-09-23", "Vente d'articles", "entree", 5800, "", "secretaire"),
    ("2026-09-23", "Scanner", "entree", 1100, "", "secretaire"),
    ("2026-09-23", "Reliure", "entree", 100, "", "secretaire"),
    ("2026-09-23", "Saisie", "entree", 3600, "", "secretaire"),
    ("2026-09-23", "Photo passeport", "entree", 1000, "", "secretaire"),
    ("2026-09-23", "Lamination", "entree", 400, "", "secretaire"),
]

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Empty transactions table
    c.execute("DELETE FROM transactions")
    
    # Insert all real transactions
    c.executemany(
        "INSERT INTO transactions (date, category_name, type, amount, description, created_by_user) VALUES (?, ?, ?, ?, ?, ?)",
        REAL_TRANSACTIONS
    )
    conn.commit()

    # Verify counts and totals
    c.execute("""
        SELECT 
            COUNT(*), 
            SUM(CASE WHEN type='entree' THEN amount ELSE 0 END), 
            SUM(CASE WHEN type='sortie' THEN amount ELSE 0 END) 
        FROM transactions
    """)
    cnt, total_e, total_s = c.fetchone()
    solde = total_e - total_s
    print(f"Total Opérations enregistrées : {cnt}")
    print(f"Total Entrées : {total_e:,.0f} FCFA")
    print(f"Total Sorties : {total_s:,.0f} FCFA")
    print(f"Solde Final : {solde:,.0f} FCFA")
    
    conn.close()

if __name__ == "__main__":
    main()
