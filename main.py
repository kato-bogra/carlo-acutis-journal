"""
Boutique Carlo Acutis Foundation — Cahier Journal & Gestion de Caisse
Web Application built with FastAPI, Jinja2, SQLite, and Tailwind CSS.
"""

import os
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database
from export import generate_journal_excel

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Boutique Carlo Acutis Foundation - Cahier Journal")

# Static files & templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/manifest.json")
async def get_manifest():
    return FileResponse(BASE_DIR / "static" / "manifest.json", media_type="application/manifest+json")

@app.get("/service-worker.js")
async def get_service_worker():
    return FileResponse(BASE_DIR / "static" / "service-worker.js", media_type="application/javascript")

# Month names in French
MONTHS_FR = [
    ("01", "Janvier"), ("02", "Février"), ("03", "Mars"),
    ("04", "Avril"), ("05", "Mai"), ("06", "Juin"),
    ("07", "Juillet"), ("08", "Août"), ("09", "Septembre"),
    ("10", "Octobre"), ("11", "Novembre"), ("12", "Décembre")
]

def get_current_user(request: Request) -> Optional[dict]:
    """Extract authenticated user from cookie or return None."""
    username = request.cookies.get("cahier_user")
    if not username:
        return None
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, full_name, role FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def format_date_display(date_str: str) -> str:
    """Format YYYY-MM-DD into DD/MM/YYYY."""
    try:
        parts = date_str.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        return date_str

@app.get("/", response_class=HTMLResponse)
async def root_redirect(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/journal", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    # If user is already logged in, redirect straight to journal
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/journal", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error, "message": message}
    )

@app.post("/login")
async def login_submit(username: str = Form(...), password: str = Form(...)):
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, full_name, role, password_hash, pin FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if not user:
        return RedirectResponse(url="/login?error=Utilisateur+inconnu", status_code=303)

    # Check pin or password
    entered_hash = database.hash_pw(password)
    if password != user["pin"] and entered_hash != user["password_hash"]:
        return RedirectResponse(url="/login?error=Code+PIN+ou+mot+de+passe+incorrect", status_code=303)

    response = RedirectResponse(url="/journal", status_code=303)
    response.set_cookie(key="cahier_user", value=user["username"], max_age=86400 * 30, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login?message=Vous+êtes+déconnecté.+Entrez+votre+mot+de+passe+pour+vous+reconnecter.", status_code=303)
    response.delete_cookie(key="cahier_user")
    return response

@app.get("/journal", response_class=HTMLResponse)
async def journal_view(
    request: Request,
    period: Optional[str] = "current_month",
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    search: Optional[str] = None,
    message: Optional[str] = None,
    message_type: Optional[str] = "success"
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login?error=Veuillez+entrer+votre+mot+de+passe+pour+accéder+au+cahier+journal", status_code=303)
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    conn = database.get_connection()
    c = conn.cursor()

    # 1. Fetch categories for the dropdown
    c.execute("SELECT id, name, operation_type, is_active FROM categories WHERE is_active = 1 ORDER BY name ASC")
    categories = [dict(r) for r in c.fetchall()]

    # 2. Fetch all transactions ordered by date and ID to compute continuous running balances
    c.execute("SELECT * FROM transactions ORDER BY date ASC, id ASC")
    all_raw = [dict(r) for r in c.fetchall()]

    # Calculate global running balances row by row
    running_balance = 0.0
    for item in all_raw:
        amt = float(item["amount"])
        if item["type"] == "entree":
            running_balance += amt
        else:
            running_balance -= amt
        item["running_balance"] = running_balance
        item["date_display"] = format_date_display(item["date"])

    # 3. Filter by period & search query
    filtered_items = []
    filter_title = "Tous les comptes"

    if period == "today":
        target_day = today_str
        filter_title = f"Comptes du Jour ({format_date_display(target_day)})"
        filtered_items = [t for t in all_raw if t["date"] == target_day]
    elif period == "current_month":
        cur_year_month = now.strftime("%Y-%m")
        # Format month name
        month_idx = int(now.strftime("%m")) - 1
        month_name = MONTHS_FR[month_idx][1]
        filter_title = f"Comptes de {month_name} {now.year} (Mois en cours)"
        filtered_items = [t for t in all_raw if t["date"].startswith(cur_year_month)]
    elif period == "custom" and (date_start or date_end):
        filter_title = f"Période du {format_date_display(date_start or 'Origine')} au {format_date_display(date_end or today_str)}"
        filtered_items = []
        for t in all_raw:
            match = True
            if date_start and t["date"] < date_start:
                match = False
            if date_end and t["date"] > date_end:
                match = False
            if match:
                filtered_items.append(t)
    else:
        period = "all"
        filter_title = "Historique Complet"
        filtered_items = list(all_raw)

    # Apply search filter if present
    if search:
        s = search.lower().strip()
        filtered_items = [
            t for t in filtered_items
            if s in t["category_name"].lower()
            or s in (t.get("description") or "").lower()
            or s in (t.get("created_by_user") or "").lower()
        ]
        filter_title += f" — Recherche '{search}'"

    # Compute period totals
    total_entrees = sum(t["amount"] for t in filtered_items if t["type"] == "entree")
    total_sorties = sum(t["amount"] for t in filtered_items if t["type"] == "sortie")
    
    # Current cash balance is the latest running balance of filtered items, or latest of all
    current_solde = filtered_items[-1]["running_balance"] if filtered_items else (all_raw[-1]["running_balance"] if all_raw else 0.0)

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="journal.html",
        context={
            "active_page": "journal",
            "current_user": user,
            "categories": categories,
            "transactions": filtered_items,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "current_solde": current_solde,
            "current_period": period,
            "current_filter_title": filter_title,
            "today_str": today_str,
            "date_start": date_start,
            "date_end": date_end,
            "search_query": search,
            "message": message,
            "message_type": message_type
        }
    )

@app.post("/transactions/create")
async def create_transaction(
    request: Request,
    date: str = Form(...),
    category_name: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    description: Optional[str] = Form(None)
):
    user = get_current_user(request)

    if amount <= 0:
        return RedirectResponse(
            url="/journal?message=Le+montant+doit+être+supérieur+à+zéro&message_type=error",
            status_code=303
        )

    conn = database.get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (date, category_name, type, amount, description, created_by_user)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, category_name, type, amount, description, user["full_name"]))
    conn.commit()
    conn.close()

    msg = f"Opération '{category_name}' de {amount:,.0f} FCFA enregistrée avec succès au journal."
    return RedirectResponse(url=f"/journal?message={msg}&message_type=success", status_code=303)

@app.post("/transactions/update/{id}")
async def update_transaction(
    id: int,
    request: Request,
    date: str = Form(...),
    category_name: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    description: Optional[str] = Form(None)
):
    user = get_current_user(request)
    
    # Security Rule: Only DG and DG Adjoint can modify existing transactions
    if user["role"] not in ["dg", "dg_adjoint"]:
        return RedirectResponse(
            url="/journal?message=Action+refusée:+seule+la+Direction+Générale+(DG)+peut+modifier+les+écritures&message_type=error",
            status_code=303
        )

    conn = database.get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE transactions
        SET date = ?, category_name = ?, type = ?, amount = ?, description = ?, updated_by_user = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (date, category_name, type, amount, description, user["full_name"], id))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/journal?message=Écriture+corrigée+avec+succès+par+la+Direction&message_type=success", status_code=303)

@app.post("/transactions/delete/{id}")
async def delete_transaction(id: int, request: Request):
    user = get_current_user(request)

    # Security Rule: Only DG and DG Adjoint can delete transactions
    if user["role"] not in ["dg", "dg_adjoint"]:
        return RedirectResponse(
            url="/journal?message=Action+refusée:+seule+la+Direction+Générale+(DG)+peut+supprimer+les+écritures&message_type=error",
            status_code=303
        )

    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/journal?message=Opération+supprimée+du+cahier+journal&message_type=warning", status_code=303)

@app.get("/reports", response_class=HTMLResponse)
async def reports_view(
    request: Request,
    type: Optional[str] = "monthly",
    day: Optional[str] = None,
    month: Optional[str] = None,
    year: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login?error=Veuillez+entrer+votre+mot+de+passe+pour+accéder+aux+rapports", status_code=303)
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # Default period selections
    selected_year = year or str(now.year)
    selected_month = month or now.strftime("%m")
    selected_day = day or today_str

    conn = database.get_connection()
    c = conn.cursor()

    # Determine query filter based on report type
    where_clause = ""
    params = []
    report_title = ""

    if type == "daily":
        where_clause = "WHERE date = ?"
        params = [selected_day]
        report_title = f"Comptes du Jour : {format_date_display(selected_day)}"
    elif type == "yearly":
        where_clause = "WHERE strftime('%Y', date) = ?"
        params = [selected_year]
        report_title = f"Bilan Annuel : Année {selected_year}"
    elif type == "custom" and (date_start or date_end):
        clauses = []
        if date_start:
            clauses.append("date >= ?")
            params.append(date_start)
        if date_end:
            clauses.append("date <= ?")
            params.append(date_end)
        where_clause = "WHERE " + " AND ".join(clauses)
        report_title = f"Comptes du {format_date_display(date_start or 'Origine')} au {format_date_display(date_end or today_str)}"
    else:
        # Default: Monthly
        type = "monthly"
        year_month = f"{selected_year}-{selected_month}"
        m_name = next((name for num, name in MONTHS_FR if num == selected_month), selected_month)
        where_clause = "WHERE strftime('%Y-%m', date) = ?"
        params = [year_month]
        report_title = f"Comptes du Mois : {m_name} {selected_year}"

    # 1. Total Entrées & Sorties for selected period
    query_totals = f"""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'entree' THEN amount ELSE 0 END), 0) as total_entrees,
            COALESCE(SUM(CASE WHEN type = 'sortie' THEN amount ELSE 0 END), 0) as total_sorties
        FROM transactions
        {where_clause}
    """
    c.execute(query_totals, params)
    totals_row = c.fetchone()
    total_entrees = totals_row["total_entrees"]
    total_sorties = totals_row["total_sorties"]
    net_balance = total_entrees - total_sorties

    # 2. Entrées by category
    query_entrees_cat = f"""
        SELECT category_name, COUNT(*) as count, SUM(amount) as total
        FROM transactions
        {where_clause} {"AND" if where_clause else "WHERE"} type = 'entree'
        GROUP BY category_name
        ORDER BY total DESC
    """
    c.execute(query_entrees_cat, params)
    entrees_by_cat = [dict(r) for r in c.fetchall()]

    # 3. Sorties by category
    query_sorties_cat = f"""
        SELECT category_name, COUNT(*) as count, SUM(amount) as total
        FROM transactions
        {where_clause} {"AND" if where_clause else "WHERE"} type = 'sortie'
        GROUP BY category_name
        ORDER BY total DESC
    """
    c.execute(query_sorties_cat, params)
    sorties_by_cat = [dict(r) for r in c.fetchall()]

    # 4. Chart 1 (Timeline): if yearly -> 12 months; if monthly/daily -> days
    chart_labels = []
    chart_entrees = []
    chart_sorties = []

    if type == "yearly":
        # Monthly aggregates for the year
        c.execute("""
            SELECT 
                strftime('%m', date) as m,
                COALESCE(SUM(CASE WHEN type = 'entree' THEN amount ELSE 0 END), 0) as ent,
                COALESCE(SUM(CASE WHEN type = 'sortie' THEN amount ELSE 0 END), 0) as sor
            FROM transactions
            WHERE strftime('%Y', date) = ?
            GROUP BY m
            ORDER BY m ASC
        """, (selected_year,))
        month_data = {r["m"]: (r["ent"], r["sor"]) for r in c.fetchall()}
        for m_num, m_name in MONTHS_FR:
            chart_labels.append(m_name[:4])
            ent, sor = month_data.get(m_num, (0, 0))
            chart_entrees.append(ent)
            chart_sorties.append(sor)
    else:
        # Group by day
        query_timeline = f"""
            SELECT 
                date,
                COALESCE(SUM(CASE WHEN type = 'entree' THEN amount ELSE 0 END), 0) as ent,
                COALESCE(SUM(CASE WHEN type = 'sortie' THEN amount ELSE 0 END), 0) as sor
            FROM transactions
            {where_clause}
            GROUP BY date
            ORDER BY date ASC
        """
        c.execute(query_timeline, params)
        for r in c.fetchall():
            chart_labels.append(format_date_display(r["date"]))
            chart_entrees.append(r["ent"])
            chart_sorties.append(r["sor"])

    # 5. Top 6 Categories Doughnut Chart
    pie_labels = [row["category_name"] for row in entrees_by_cat[:6]]
    pie_data = [row["total"] for row in entrees_by_cat[:6]]

    # Years list for dropdown
    c.execute("SELECT DISTINCT strftime('%Y', date) as y FROM transactions ORDER BY y DESC")
    years_list = [r["y"] for r in c.fetchall() if r["y"]]
    if str(now.year) not in years_list:
        years_list.insert(0, str(now.year))

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={
            "active_page": "reports",
            "current_user": user,
            "report_type": type,
            "report_title": report_title,
            "selected_day": selected_day,
            "selected_month": selected_month,
            "selected_year": selected_year,
            "date_start": date_start,
            "date_end": date_end,
            "months_list": MONTHS_FR,
            "years_list": years_list,
            "today_str": today_str,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "net_balance": net_balance,
            "entrees_by_cat": entrees_by_cat,
            "sorties_by_cat": sorties_by_cat,
            "chart_labels": chart_labels,
            "chart_entrees": chart_entrees,
            "chart_sorties": chart_sorties,
            "pie_labels": pie_labels,
            "pie_data": pie_data,
        }
    )

@app.get("/categories", response_class=HTMLResponse)
async def categories_view(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login?error=Veuillez+entrer+votre+mot+de+passe", status_code=303)
    if user["role"] not in ["dg", "dg_adjoint"]:
        return RedirectResponse(
            url="/journal?message=Accès+refusé:+la+gestion+des+catégories+est+réservée+à+la+Direction+Générale&message_type=error",
            status_code=303
        )

    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name ASC")
    categories = [dict(r) for r in c.fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="categories.html",
        context={
            "active_page": "categories",
            "current_user": user,
            "categories": categories
        }
    )

@app.post("/categories/create")
async def create_category(
    request: Request,
    name: str = Form(...),
    operation_type: str = Form("both")
):
    user = get_current_user(request)
    if user["role"] not in ["dg", "dg_adjoint"]:
        return RedirectResponse(url="/journal?message=Action+non+autorisée&message_type=error", status_code=303)

    clean_name = name.strip()
    if not clean_name:
        return RedirectResponse(url="/categories?message=Nom+invalide&message_type=error", status_code=303)

    conn = database.get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name, operation_type) VALUES (?, ?)", (clean_name, operation_type))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return RedirectResponse(url="/categories?message=Cette+catégorie+existe+déjà&message_type=error", status_code=303)
    conn.close()

    return RedirectResponse(url=f"/categories?message=Catégorie+'{clean_name}'+ajoutée+avec+succès&message_type=success", status_code=303)

@app.post("/categories/delete/{id}")
async def delete_category(id: int, request: Request):
    user = get_current_user(request)
    if user["role"] not in ["dg", "dg_adjoint"]:
        return RedirectResponse(url="/journal?message=Action+non+autorisée&message_type=error", status_code=303)

    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/categories?message=Catégorie+supprimée&message_type=warning", status_code=303)

@app.get("/export/excel")
async def export_excel(
    request: Request,
    mode: Optional[str] = "journal",
    period: Optional[str] = "all",
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    search: Optional[str] = None,
    period_type: Optional[str] = None,
    year: Optional[str] = None,
    month: Optional[str] = None,
    day: Optional[str] = None
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login?error=Veuillez+entrer+votre+mot+de+passe", status_code=303)

    conn = database.get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM transactions ORDER BY date ASC, id ASC")
    all_raw = [dict(r) for r in c.fetchall()]
    conn.close()

    # Filter transactions based on query
    target_items = all_raw
    subtitle = "Historique Général"

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    if mode == "report":
        if period_type == "daily":
            target_day = day or today_str
            target_items = [t for t in all_raw if t["date"] == target_day]
            subtitle = f"Comptes du Jour : {format_date_display(target_day)}"
        elif period_type == "yearly":
            target_year = year or str(now.year)
            target_items = [t for t in all_raw if t["date"].startswith(target_year)]
            subtitle = f"Bilan Annuel {target_year}"
        elif period_type == "custom" and (date_start or date_end):
            target_items = [
                t for t in all_raw
                if (not date_start or t["date"] >= date_start) and (not date_end or t["date"] <= date_end)
            ]
            subtitle = f"Période du {format_date_display(date_start or 'Origine')} au {format_date_display(date_end or today_str)}"
        else:
            # Monthly
            target_year = year or str(now.year)
            target_month = month or now.strftime("%m")
            target_items = [t for t in all_raw if t["date"].startswith(f"{target_year}-{target_month}")]
            m_name = next((name for num, name in MONTHS_FR if num == target_month), target_month)
            subtitle = f"Comptes de {m_name} {target_year}"
    else:
        # Journal filter
        if period == "today":
            target_items = [t for t in all_raw if t["date"] == today_str]
            subtitle = f"Comptes du Jour ({format_date_display(today_str)})"
        elif period == "current_month":
            ym = now.strftime("%Y-%m")
            target_items = [t for t in all_raw if t["date"].startswith(ym)]
            subtitle = f"Mois en cours ({now.strftime('%m/%Y')})"
        elif period == "custom" and (date_start or date_end):
            target_items = [
                t for t in all_raw
                if (not date_start or t["date"] >= date_start) and (not date_end or t["date"] <= date_end)
            ]
            subtitle = f"Période du {format_date_display(date_start or 'Origine')} au {format_date_display(date_end or today_str)}"

        if search:
            s = search.lower().strip()
            target_items = [
                t for t in target_items
                if s in t["category_name"].lower() or s in (t.get("description") or "").lower()
            ]

    excel_bytes = generate_journal_excel(target_items, title="Cahier Journal de Caisse", subtitle=subtitle)

    filename = f"cahier_journal_carlo_acutis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

if __name__ == "__main__":
    import uvicorn
    print("Démarrage du Cahier Journal Carlo Acutis sur http://localhost:8000 ...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
