"""
pnl_engine.py — Conto Economico (P&L) con struttura A→M.

A. Ricavi (per tipologia)
B. COGS (costi diretti)
C. Margine Lordo
D. Spese Operative (costi indiretti)
E. EBITDA
F. Ammortamenti
G. EBIT
H. Oneri Finanziari
I. EBT
L. Imposte
M. Utile Netto + Cumulativo
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db


MESI_LABEL = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu',
              'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']


def calcola_pnl(anno: int = None) -> dict:
    """Calcola il P&L mensile completo (competenza economica)."""
    from datetime import date
    if anno is None:
        anno = date.today().year

    with get_db() as conn:
        # ─── A. RICAVI (per competenza = data_fattura) ───
        ricavi_per_tipo = {
            "Consulenza": [0.0] * 12,
            "Evento": [0.0] * 12,
            "Progetto Integrato": [0.0] * 12,
            "Altro": [0.0] * 12,
        }

        rows = conn.execute("""
            SELECT importo_netto, centro_ricavo, data_fattura
            FROM ciclo_attivo
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
              AND stato IN ('Confermato', 'Fatturato', 'Saldato')
        """, [anno]).fetchall()

        for r in rows:
            m = int(r["data_fattura"][5:7]) - 1
            tipo = r["centro_ricavo"]
            if tipo in ricavi_per_tipo:
                ricavi_per_tipo[tipo][m] += r["importo_netto"] or 0

        # Altre entrate
        rows_ae = conn.execute("""
            SELECT importo_netto, data_fattura
            FROM altre_entrate
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
              AND stato IN ('Confermato', 'Fatturato', 'Saldato')
        """, [anno]).fetchall()

        for r in rows_ae:
            m = int(r["data_fattura"][5:7]) - 1
            ricavi_per_tipo["Altro"][m] += r["importo_netto"] or 0

        # A. TOT RICAVI
        tot_ricavi = [sum(ricavi_per_tipo[t][m] for t in ricavi_per_tipo) for m in range(12)]

        # ─── B. COGS (per competenza) ───
        cogs_per_tipo = {
            "Consulenza": [0.0] * 12,
            "Evento": [0.0] * 12,
            "Progetto Integrato": [0.0] * 12,
            "Altro": [0.0] * 12,
        }

        rows = conn.execute("""
            SELECT importo_netto, centro_costo, data_fattura
            FROM ciclo_passivo
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
              AND stato IN ('Confermato', 'Fatturato', 'Saldato')
        """, [anno]).fetchall()

        for r in rows:
            m = int(r["data_fattura"][5:7]) - 1
            tipo = r["centro_costo"]
            if tipo in cogs_per_tipo:
                cogs_per_tipo[tipo][m] += r["importo_netto"] or 0

        tot_cogs = [sum(cogs_per_tipo[t][m] for t in cogs_per_tipo) for m in range(12)]

        # C. MARGINE LORDO
        margine_lordo = [round(tot_ricavi[m] - tot_cogs[m], 2) for m in range(12)]

        # ─── D. SPESE OPERATIVE (costi indiretti) ───
        spese_op_cat = {}
        cat_map = {
            "D. Personale": "D1. Compensi e Collaborazioni",
            "D. Sedi Operative": "D4. Affitto, Utenze, Manutenzioni",
            "D. Commerciale e Marketing": "D5. Spese Commerciali e Promozionali",
            "D. Servizi Professionali": "D6. Servizi Professionali",
            "D. Spese Operative": "D7. Gestione Ordinaria",
        }

        for cat_db, cat_label in cat_map.items():
            spese_op_cat[cat_label] = [0.0] * 12
            rows = conn.execute("""
                SELECT importo_netto, mese
                FROM costi_indiretti
                WHERE anno = ? AND categoria = ?
            """, [anno, cat_db]).fetchall()
            for r in rows:
                spese_op_cat[cat_label][r["mese"] - 1] += r["importo_netto"] or 0

        tot_spese_op = [sum(spese_op_cat[c][m] for c in spese_op_cat) for m in range(12)]

        # E. EBITDA
        ebitda = [round(margine_lordo[m] - tot_spese_op[m], 2) for m in range(12)]

        # ─── F. AMMORTAMENTI ───
        ammortamenti = [0.0] * 12
        rows = conn.execute("""
            SELECT importo_netto, mese
            FROM costi_indiretti
            WHERE anno = ? AND categoria = 'F. Licenze, Software, HW'
        """, [anno]).fetchall()
        for r in rows:
            ammortamenti[r["mese"] - 1] += r["importo_netto"] or 0

        # G. EBIT
        ebit = [round(ebitda[m] - ammortamenti[m], 2) for m in range(12)]

        # ─── H. ONERI FINANZIARI ───
        oneri_fin = [0.0] * 12
        rows = conn.execute("""
            SELECT importo_netto, mese
            FROM costi_indiretti
            WHERE anno = ? AND categoria = 'H. Oneri Finanziari'
        """, [anno]).fetchall()
        for r in rows:
            oneri_fin[r["mese"] - 1] += r["importo_netto"] or 0

        # I. EBT
        ebt = [round(ebit[m] - oneri_fin[m], 2) for m in range(12)]

        # ─── L. IMPOSTE ───
        imposte = [0.0] * 12
        rows = conn.execute("""
            SELECT importo_netto, mese
            FROM costi_indiretti
            WHERE anno = ? AND categoria = 'L. Imposte e Tasse'
        """, [anno]).fetchall()
        for r in rows:
            imposte[r["mese"] - 1] += r["importo_netto"] or 0

        # M. UTILE NETTO
        utile_netto = [round(ebt[m] - imposte[m], 2) for m in range(12)]

        # M. UTILE NETTO CUMULATIVO
        utile_cumulativo = []
        cumul = 0
        for m in range(12):
            cumul += utile_netto[m]
            utile_cumulativo.append(round(cumul, 2))

    return {
        "anno": anno,
        "mesi_label": MESI_LABEL,
        "ricavi_per_tipo": {t: [round(v, 2) for v in vals] for t, vals in ricavi_per_tipo.items()},
        "tot_ricavi": [round(v, 2) for v in tot_ricavi],
        "cogs_per_tipo": {t: [round(v, 2) for v in vals] for t, vals in cogs_per_tipo.items()},
        "tot_cogs": [round(v, 2) for v in tot_cogs],
        "margine_lordo": margine_lordo,
        "spese_operative": {c: [round(v, 2) for v in vals] for c, vals in spese_op_cat.items()},
        "tot_spese_operative": [round(v, 2) for v in tot_spese_op],
        "ebitda": ebitda,
        "ammortamenti": [round(v, 2) for v in ammortamenti],
        "ebit": ebit,
        "oneri_finanziari": [round(v, 2) for v in oneri_fin],
        "ebt": ebt,
        "imposte": [round(v, 2) for v in imposte],
        "utile_netto": utile_netto,
        "utile_cumulativo": utile_cumulativo,
    }
