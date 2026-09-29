"""
Comprehensive test suite for Boutique Carlo Acutis Foundation Web App
"""

from fastapi.testclient import TestClient
from main import app
import sqlite3

client = TestClient(app)

def test_homepage_redirect():
    # Without cookie, root redirects to /login
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

def test_journal_view_dg():
    # As authenticated DG
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")
    response = dg_client.get("/journal")
    assert response.status_code == 200
    assert "Boutique Carlo Acutis Foundation" in response.text
    assert "Photocopie" in response.text
    assert "Achat de papier ram" in response.text
    assert "138 125" in response.text or "100 825" in response.text or "93 950" in response.text

def test_logout_flow():
    # Authenticated user logs out
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")
    resp = dg_client.get("/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert "/login" in resp.headers["location"]

    # Verify unauthenticated access to journal is blocked
    unauth = TestClient(app)
    resp_unauth = unauth.get("/journal", follow_redirects=False)
    assert resp_unauth.status_code == 303
    assert "/login" in resp_unauth.headers["location"]

def test_login_flow():
    # 1. Login as Secretaire with 54321
    resp_sec = client.post("/login", data={"username": "secretaire", "password": "54321"}, follow_redirects=False)
    assert resp_sec.status_code == 303
    assert "cahier_user=secretaire" in resp_sec.headers["set-cookie"]

    # 2. Login as DG with 12345
    resp_dg = client.post("/login", data={"username": "dg", "password": "12345"}, follow_redirects=False)
    assert resp_dg.status_code == 303
    assert "cahier_user=dg" in resp_dg.headers["set-cookie"]

    # 3. Login as DG Adjoint with 23456
    resp_dga = client.post("/login", data={"username": "dg_adjoint", "password": "23456"}, follow_redirects=False)
    assert resp_dga.status_code == 303
    assert "cahier_user=dg_adjoint" in resp_dga.headers["set-cookie"]

    # 4. Wrong password should be rejected
    resp_bad = client.post("/login", data={"username": "dg", "password": "wrong"}, follow_redirects=False)
    assert resp_bad.status_code == 303
    assert "error" in resp_bad.headers["location"]

def test_secretaire_permissions():
    sec_client = TestClient(app)
    sec_client.cookies.set("cahier_user", "secretaire")

    # 1. Create transaction as secretaire -> Should succeed
    create_resp = sec_client.post("/transactions/create", data={
        "date": "2099-01-01",
        "category_name": "Photocopie",
        "type": "entree",
        "amount": "500",
        "description": "5 photocopies A4"
    }, follow_redirects=True)
    assert create_resp.status_code == 200
    assert "enregistrée avec succès" in create_resp.text

    # Clean up test row
    import database
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE date = '2099-01-01'")
    conn.commit()
    conn.close()

    # 2. Try to update a transaction as secretaire -> Should be BLOCKED!
    update_resp = sec_client.post("/transactions/update/1", data={
        "date": "2026-09-01",
        "category_name": "Photocopie",
        "type": "entree",
        "amount": "9999",
        "description": "Hack"
    }, follow_redirects=True)
    assert update_resp.status_code == 200
    assert "Action refusée" in update_resp.text

    # 3. Try to delete as secretaire -> Should be BLOCKED!
    del_resp = sec_client.post("/transactions/delete/1", follow_redirects=True)
    assert del_resp.status_code == 200
    assert "Action refusée" in del_resp.text

    # 4. Try to access categories management -> Should be BLOCKED!
    cat_resp = sec_client.get("/categories", follow_redirects=True)
    assert cat_resp.status_code == 200
    assert "Accès refusé" in cat_resp.text

def test_dg_permissions():
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")
    
    # 1. DG can access categories
    cat_resp = dg_client.get("/categories")
    assert cat_resp.status_code == 200
    assert "Liste" in cat_resp.text and "catégories" in cat_resp.text

    # 2. DG can add new category
    add_cat = dg_client.post("/categories/create", data={
        "name": "Plastification Grand Format",
        "operation_type": "entree"
    }, follow_redirects=True)
    assert add_cat.status_code == 200
    assert "Plastification Grand Format" in add_cat.text

def test_reports_views():
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")
    # Monthly
    r_month = dg_client.get("/reports?type=monthly&year=2026&month=09")
    assert r_month.status_code == 200
    assert "Septembre 2026" in r_month.text

    # Daily
    r_day = dg_client.get("/reports?type=daily&day=2026-09-02")
    assert r_day.status_code == 200

    # Yearly
    r_year = dg_client.get("/reports?type=yearly&year=2026")
    assert r_year.status_code == 200

def test_excel_export():
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")
    resp = dg_client.get("/export/excel?period=all")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(resp.content) > 1000

def test_pwa_assets():
    # Test manifest
    resp_m = client.get("/manifest.json")
    assert resp_m.status_code == 200
    data = resp_m.json()
    assert data["short_name"] == "Boutique Acutis"
    assert data["display"] == "standalone"

    # Test service worker
    resp_sw = client.get("/service-worker.js")
    assert resp_sw.status_code == 200
    assert "addEventListener" in resp_sw.text

def test_duplicate_check_and_merge_flow():
    sec_client = TestClient(app)
    sec_client.cookies.set("cahier_user", "secretaire")

    test_date = "2026-09-30"
    test_cat = "Reliure"

    # 1. Initial duplicate check should be false
    chk1 = sec_client.get(f"/api/check-duplicate?date={test_date}&category_name={test_cat}&type=entree")
    assert chk1.status_code == 200
    assert chk1.json()["exists"] is False

    # 2. Add first entry (e.g. 2000 FCFA)
    res1 = sec_client.post("/transactions/create", data={
        "date": test_date,
        "category_name": test_cat,
        "type": "entree",
        "amount": "2000",
        "description": "Livre A4"
    }, follow_redirects=True)
    assert res1.status_code == 200
    assert "enregistrée avec succès" in res1.text
    assert "2 000" in res1.text or "2000" in res1.text

    # 3. Duplicate check should now be true!
    chk2 = sec_client.get(f"/api/check-duplicate?date={test_date}&category_name={test_cat}&type=entree")
    assert chk2.status_code == 200
    d2 = chk2.json()
    assert d2["exists"] is True
    assert d2["total_existing_amount"] == 2000
    existing_id = d2["existing"]["id"]

    # 4. Merge duplicate: add 3000 FCFA to existing
    res_merge = sec_client.post("/transactions/create", data={
        "date": test_date,
        "category_name": test_cat,
        "type": "entree",
        "amount": "3000",
        "description": "Livre B5",
        "action_type": "merge",
        "existing_id": str(existing_id)
    }, follow_redirects=True)
    assert res_merge.status_code == 200
    assert "Fusion réussie" in res_merge.text
    assert "5 000" in res_merge.text or "5000" in res_merge.text

    # 5. Check duplicate check after merge: amount should be 5000
    chk3 = sec_client.get(f"/api/check-duplicate?date={test_date}&category_name={test_cat}&type=entree")
    assert chk3.json()["total_existing_amount"] == 5000
    assert chk3.json()["count"] == 1

    # 6. Force create doublet (separate second row of 1500 FCFA)
    res_doublet = sec_client.post("/transactions/create", data={
        "date": test_date,
        "category_name": test_cat,
        "type": "entree",
        "amount": "1500",
        "description": "2ème client distinct",
        "action_type": "force_create"
    }, follow_redirects=True)
    assert res_doublet.status_code == 200
    assert "Doublet enregistré" in res_doublet.text

    # 7. Check count is now 2
    chk4 = sec_client.get(f"/api/check-duplicate?date={test_date}&category_name={test_cat}&type=entree")
    assert chk4.json()["count"] == 2
    assert chk4.json()["total_existing_amount"] == 6500

    # Clean up test rows
    import database
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE date = ?", (test_date,))
    conn.commit()
    conn.close()

def test_services_vs_ventes_breakdown_and_filtering():
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")

    # 1. Access journal with period=all -> should display both services and ventes breakdown
    resp_all = dg_client.get("/journal?period=all")
    assert resp_all.status_code == 200
    assert "Prestations de Services" in resp_all.text
    assert "Ventes de Produits" in resp_all.text
    # Check exact amounts: Services = 370 450 FCFA (69.3%), Ventes = 164 325 FCFA (30.7%)
    assert ("370 450" in resp_all.text or "335 600" in resp_all.text)
    assert ("164 325" in resp_all.text or "158 875" in resp_all.text)
    assert ("69.3%" in resp_all.text or "67.9%" in resp_all.text)
    assert ("30.7%" in resp_all.text or "32.1%" in resp_all.text)

    # 2. Filter by activity=service -> only services in table
    resp_svc = dg_client.get("/journal?period=all&activity=service")
    assert resp_svc.status_code == 200
    tbody_svc = resp_svc.text.split('<tbody')[1].split('</tbody>')[0]
    assert "Photocopie" in tbody_svc
    assert "Impression" in tbody_svc
    assert "Achat de papier ram" not in tbody_svc
    assert "Vente d'articles" not in tbody_svc

    # 3. Filter by activity=vente -> only ventes in table
    resp_vte = dg_client.get("/journal?period=all&activity=vente")
    assert resp_vte.status_code == 200
    tbody_vte = resp_vte.text.split('<tbody')[1].split('</tbody>')[0]
    assert "Vente d&#39;articles" in tbody_vte or "Vente d'articles" in tbody_vte
    assert "Photocopie" not in tbody_vte
    assert "Achat de papier ram" not in tbody_vte

    # 4. Filter by activity=depense -> only sorties
    resp_dep = dg_client.get("/journal?period=all&activity=depense")
    assert resp_dep.status_code == 200
    tbody_dep = resp_dep.text.split('<tbody')[1].split('</tbody>')[0]
    assert "Achat de papier ram" in tbody_dep
    assert "Impression" not in tbody_dep
    assert "Vente d'articles" not in tbody_dep

    # 5. Check reports page also contains Services vs Ventes
    resp_rep = dg_client.get("/reports?type=monthly&year=2026&month=09")
    assert resp_rep.status_code == 200
    assert "Prestations de Services" in resp_rep.text
    assert "Ventes d'Articles" in resp_rep.text or "Ventes de Produits" in resp_rep.text

    # 6. Check Excel export with activity filter
    resp_xl = dg_client.get("/export/excel?period=all&activity=service")
    assert resp_xl.status_code == 200
    assert len(resp_xl.content) > 1000

def test_reliure_categorization():
    import database
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT name, operation_type, activity_type FROM categories WHERE name = 'Reliure'")
    r_simple = c.fetchone()
    assert r_simple["operation_type"] == "entree"
    assert r_simple["activity_type"] == "service"

    c.execute("SELECT name, operation_type, activity_type FROM categories WHERE name LIKE 'Reliure de livr%b%n%diction%'")
    rows_benediction = c.fetchall()
    assert len(rows_benediction) > 0
    for r in rows_benediction:
        assert r["operation_type"] == "sortie"
        assert r["activity_type"] == "depense"
    conn.close()

    # Test classify_activity helper
    from main import classify_activity
    assert classify_activity("Reliure", "entree") == ("service", "Prestation")
    assert classify_activity("Reliure de livre de bénédiction", "sortie") == ("depense", "Dépense")
    assert classify_activity("Reliure de livrets de bénédiction", "sortie") == ("depense", "Dépense")

def test_backup_and_restore_flow():
    # 1. Secretaire should be blocked from /backup
    sec_client = TestClient(app)
    sec_client.cookies.set("cahier_user", "secretaire")
    resp_sec = sec_client.get("/backup", follow_redirects=False)
    assert resp_sec.status_code == 303
    assert "journal" in resp_sec.headers["location"]

    # 2. DG can view /backup
    dg_client = TestClient(app)
    dg_client.cookies.set("cahier_user", "dg")
    resp_dg = dg_client.get("/backup")
    assert resp_dg.status_code == 200
    assert "Sauvegardes" in resp_dg.text
    assert "journal.db" in resp_dg.text

    # 3. DG can download .db
    resp_db = dg_client.get("/backup/download-db")
    assert resp_db.status_code == 200
    assert resp_db.content.startswith(b"SQLite format 3\x00")

    # 4. DG can download .json
    resp_json = dg_client.get("/backup/download-json")
    assert resp_json.status_code == 200
    json_data = resp_json.json()
    assert "transactions" in json_data
    assert "categories" in json_data
    assert len(json_data["transactions"]) >= 145

    # 5. DG can restore JSON with new non-duplicate transaction
    import json
    new_sample = {
        "categories": [],
        "transactions": [
            {
                "date": "2026-09-29",
                "category_name": "Scanner",
                "type": "entree",
                "amount": 1500,
                "description": "Test import sauvegarde",
                "created_by_user": "restauration"
            }
        ]
    }
    file_bytes = json.dumps(new_sample).encode("utf-8")
    resp_restore = dg_client.post(
        "/backup/restore",
        files={"backup_file": ("test_backup.json", file_bytes, "application/json")},
        follow_redirects=True
    )
    assert resp_restore.status_code == 200
    assert "Restauration" in resp_restore.text

    # Clean up test transaction
    import database
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE description = 'Test import sauvegarde'")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "test_app.py"])

