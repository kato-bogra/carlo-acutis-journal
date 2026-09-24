"""
Excel export module for Boutique Carlo Acutis Foundation
Uses xlsxwriter to generate a beautifully styled journal matching the original workbook.
"""

import io
from datetime import datetime
import xlsxwriter

def generate_journal_excel(transactions: list, title: str = "Cahier Journal", subtitle: str = "") -> bytes:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Cahier Journal")
    
    # Page setup
    worksheet.set_paper(9) # A4
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 0)
    
    # Formats
    title_fmt = workbook.add_format({
        'bold': True, 'font_size': 16, 'font_name': 'Calibri',
        'font_color': '#1E3A8A', 'align': 'center', 'valign': 'vcenter'
    })
    sub_fmt = workbook.add_format({
        'italic': True, 'font_size': 10, 'font_name': 'Calibri',
        'font_color': '#64748B', 'align': 'center', 'valign': 'vcenter'
    })
    
    header_date = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#E2E8F0', 'font_color': '#1E293B',
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    header_op = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#E2E8F0', 'font_color': '#1E293B',
        'align': 'left', 'valign': 'vcenter', 'border': 1
    })
    header_entree = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#D9E1F2', 'font_color': '#1E3A8A',
        'align': 'right', 'valign': 'vcenter', 'border': 1
    })
    header_sortie = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#FFF2CC', 'font_color': '#854D0E',
        'align': 'right', 'valign': 'vcenter', 'border': 1
    })
    header_solde = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#E2EFDA', 'font_color': '#166534',
        'align': 'right', 'valign': 'vcenter', 'border': 1
    })
    header_note = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#E2E8F0', 'font_color': '#1E293B',
        'align': 'left', 'valign': 'vcenter', 'border': 1
    })

    # Data row formats
    date_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    op_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'align': 'left', 'valign': 'vcenter', 'border': 1
    })
    entree_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'align': 'right', 'valign': 'vcenter',
        'bg_color': '#EEF2FF', 'num_format': '#,##0', 'border': 1
    })
    sortie_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'align': 'right', 'valign': 'vcenter',
        'bg_color': '#FEFCE8', 'num_format': '#,##0', 'border': 1
    })
    solde_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'bold': True, 'align': 'right', 'valign': 'vcenter',
        'bg_color': '#F0FDF4', 'font_color': '#166534', 'num_format': '#,##0', 'border': 1
    })
    note_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 9, 'color': '#475569', 'align': 'left', 'valign': 'vcenter', 'border': 1
    })

    total_label_fmt = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#CBD5E1', 'align': 'right', 'valign': 'vcenter', 'border': 1
    })
    total_entree_fmt = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#BFDBFE', 'font_color': '#1E3A8A',
        'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0', 'border': 1
    })
    total_sortie_fmt = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#FEF08A', 'font_color': '#854D0E',
        'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0', 'border': 1
    })
    total_solde_fmt = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#BBF7D0', 'font_color': '#166534',
        'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0', 'border': 1
    })

    header_nature = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#E2E8F0', 'font_color': '#1E293B',
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    nature_service_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 9, 'bold': True, 'align': 'center', 'valign': 'vcenter',
        'bg_color': '#DBEAFE', 'font_color': '#1D4ED8', 'border': 1
    })
    nature_vente_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 9, 'bold': True, 'align': 'center', 'valign': 'vcenter',
        'bg_color': '#F3E8FF', 'font_color': '#7E22CE', 'border': 1
    })
    nature_depense_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 9, 'bold': True, 'align': 'center', 'valign': 'vcenter',
        'bg_color': '#FEF3C7', 'font_color': '#B45309', 'border': 1
    })

    # Set column widths
    worksheet.set_column('A:A', 13) # Date
    worksheet.set_column('B:B', 30) # Opération
    worksheet.set_column('C:C', 15) # Nature / Activité
    worksheet.set_column('D:D', 16) # Entrée
    worksheet.set_column('E:E', 16) # Sortie
    worksheet.set_column('F:F', 18) # Solde
    worksheet.set_column('G:G', 25) # Remarques / Auteur

    # Header Titles
    worksheet.merge_range('A1:G1', 'BOUTIQUE CARLO ACUTIS FOUNDATION', title_fmt)
    subtitle_text = subtitle or f"Document extrait le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    worksheet.merge_range('A2:G2', f"{title} — {subtitle_text}", sub_fmt)
    worksheet.set_row(0, 26)
    worksheet.set_row(1, 18)
    worksheet.set_row(3, 24)

    # Column Headers
    headers = [
        ("Date", header_date),
        ("Opération / Libellé", header_op),
        ("Nature / Activité", header_nature),
        ("Entrée (FCFA)", header_entree),
        ("Sortie (FCFA)", header_sortie),
        ("Solde Cumulé", header_solde),
        ("Observation / Saisi par", header_note),
    ]
    for col_idx, (text, fmt) in enumerate(headers):
        worksheet.write(3, col_idx, text, fmt)

    # Helper function to classify
    def classify_act(cat_name, op_type):
        if op_type == 'sortie':
            return ('depense', 'Dépense', nature_depense_fmt)
        c_l = (cat_name or '').lower().strip()
        if c_l.startswith('vente ') and 'wifi' not in c_l:
            return ('vente', 'Vente', nature_vente_fmt)
        if any(k in c_l for k in ['livret', 'livre', 'article']) and not c_l.startswith('reliure'):
            return ('vente', 'Vente', nature_vente_fmt)
        return ('service', 'Prestation', nature_service_fmt)

    # Write Transactions
    current_row = 4
    cumulative_solde = 0.0
    total_entrees = 0.0
    total_sorties = 0.0
    total_services = 0.0
    total_ventes = 0.0

    for t in transactions:
        t_date = t['date']
        t_cat = t['category_name']
        t_type = t['type']
        t_amount = float(t['amount'])
        t_note = t.get('description') or ''
        t_user = t.get('created_by_user') or ''
        user_info = f"{t_note} ({t_user})".strip() if t_user else t_note

        act_code, act_label, act_fmt = classify_act(t_cat, t_type)

        if t_type == 'entree':
            entree_val = t_amount
            sortie_val = None
            cumulative_solde += t_amount
            total_entrees += t_amount
            if act_code == 'service':
                total_services += t_amount
            else:
                total_ventes += t_amount
        else:
            entree_val = None
            sortie_val = t_amount
            cumulative_solde -= t_amount
            total_sorties += t_amount

        worksheet.write(current_row, 0, t_date, date_fmt)
        worksheet.write(current_row, 1, t_cat, op_fmt)
        worksheet.write(current_row, 2, act_label, act_fmt)
        worksheet.write(current_row, 3, entree_val if entree_val else "", entree_fmt)
        worksheet.write(current_row, 4, sortie_val if sortie_val else "", sortie_fmt)
        worksheet.write(current_row, 5, cumulative_solde, solde_fmt)
        worksheet.write(current_row, 6, user_info, note_fmt)
        current_row += 1

    # Total Row
    worksheet.merge_range(current_row, 0, current_row, 2, "TOTAUX & SOLDE FINAL", total_label_fmt)
    worksheet.write(current_row, 3, total_entrees, total_entree_fmt)
    worksheet.write(current_row, 4, total_sorties, total_sortie_fmt)
    worksheet.write(current_row, 5, cumulative_solde, total_solde_fmt)
    worksheet.write(current_row, 6, "", total_label_fmt)
    worksheet.set_row(current_row, 22)

    # Summary Analysis Block (Services vs Ventes)
    current_row += 2
    sum_title_fmt = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': '#1E3A8A', 'font_color': '#FFFFFF',
        'align': 'left', 'valign': 'vcenter'
    })
    sum_label_fmt = workbook.add_format({
        'bold': True, 'font_size': 10, 'bg_color': '#F8FAFC', 'border': 1
    })
    sum_val_fmt = workbook.add_format({
        'bold': True, 'font_size': 10, 'num_format': '#,##0 "FCFA"', 'align': 'right', 'border': 1
    })
    sum_pct_fmt = workbook.add_format({
        'italic': True, 'font_size': 10, 'align': 'center', 'border': 1
    })

    pct_services = (total_services / total_entrees * 100) if total_entrees > 0 else 0
    pct_ventes = (total_ventes / total_entrees * 100) if total_entrees > 0 else 0

    worksheet.merge_range(current_row, 0, current_row, 3, "SYNTHÈSE : PRESTATIONS DE SERVICES VS VENTES", sum_title_fmt)
    current_row += 1

    worksheet.merge_range(current_row, 0, current_row, 1, "🛠️ Prestations de Services (Photocopies, Impressions, etc.)", sum_label_fmt)
    worksheet.write(current_row, 2, total_services, sum_val_fmt)
    worksheet.write(current_row, 3, f"{pct_services:.1f}% des recettes", sum_pct_fmt)
    current_row += 1

    worksheet.merge_range(current_row, 0, current_row, 1, "🛍️ Ventes de Produits & Livres (Articles, Livrets)", sum_label_fmt)
    worksheet.write(current_row, 2, total_ventes, sum_val_fmt)
    worksheet.write(current_row, 3, f"{pct_ventes:.1f}% des recettes", sum_pct_fmt)
    current_row += 1

    worksheet.merge_range(current_row, 0, current_row, 1, "TOTAL DES RECETTES (SERVICES + VENTES)", sum_label_fmt)
    worksheet.write(current_row, 2, total_entrees, sum_val_fmt)
    worksheet.write(current_row, 3, "100.0%", sum_pct_fmt)

    workbook.close()
    output.seek(0)
    return output.getvalue()
