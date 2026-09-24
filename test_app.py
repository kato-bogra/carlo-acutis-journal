"""
Comprehensive test suite for Boutique Carlo Acutis Foundation Web App
"""

from fastapi.testclient import TestClient
from main import app
import sqlite3

client = TestClient(app)

def test_homepage_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/journal"

def test_journal_view_dg():
    # As default DG
    response = client.get("/journal")
    assert response.status_code == 200
    assert "Boutique Carlo Acutis Foundation" in response.text
    assert "Photocopie" in response.text
    assert "Achat de papier ram" in response.text
    assert "18 850" in response.text  # Cumulative balance from image!

def test_login_flow():
    # Login as Secretaire
    resp = client.post("/login", data={"username": "secretaire", "password": "1234"}, follow_redirects=False)
    assert resp.status_code == 303
    assert "cahier_user=secretaire" in resp.headers["set-cookie"]

def test_secretaire_permissions():
    # 1. Create transaction as secretaire -> Should succeed
    cookies = {"cahier_user": "secretaire"}
    create_resp = client.post("/transactions/create", data={
        "date": "2026-09-24",
        "category_name": "Photocopie",
        "type": "entree",
        "amount": "500",
        "description": "5 photocopies A4"
    }, cookies=cookies, follow_redirects=True)
    assert create_resp.status_code == 200
    assert "enregistrée avec succès" in create_resp.text

    # 2. Try to update a transaction as secretaire -> Should be BLOCKED!
    update_resp = client.post("/transactions/update/1", data={
        "date": "2026-09-01",
        "category_name": "Photocopie",
        "type": "entree",
        "amount": "9999",
        "description": "Hack"
    }, cookies=cookies, follow_redirects=True)
    assert update_resp.status_code == 200
    assert "Action refusée" in update_resp.text

    # 3. Try to delete as secretaire -> Should be BLOCKED!
    del_resp = client.post("/transactions/delete/1", cookies=cookies, follow_redirects=True)
    assert del_resp.status_code == 200
    assert "Action refusée" in del_resp.text

    # 4. Try to access categories management -> Should be BLOCKED!
    cat_resp = client.get("/categories", cookies=cookies, follow_redirects=True)
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

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "test_app.py"])
