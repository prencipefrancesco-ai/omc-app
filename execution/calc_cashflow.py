"""
calc_cashflow.py — Calcolo Cashflow a 3 scenari (Reale, Opportunità, Forecast).

Logica:
- REALE: Solo flussi con stato Confermato/Fatturato/Saldato
- OPPORTUNITÀ: Reale + Forecast con stato "Opportunità" pesato per Win Probability
- FORECAST: Opportunità + Forecast con stato "Forecast" pesato per Win Probability
"""
import json
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db, get_config


def calcola_cashflow(anno: int = None) -> dict:
    """
    Calcola i tre scenari di cashflow su base mensile.
    Returns dict with keys: mesi, reale, opportunita, forecast, saldo_iniziale, soglia
    """
    if anno is None:
        anno = date.today().year

    saldo_iniziale = float(get_config("saldo_iniziale", "0"))
    soglia = float(get_config("soglia_minima_liquidita", "50000"))

    mesi = []
    for m in range(1, 13):
        mesi.append(f"{anno}-{m:02d}")

    # Initialize monthly arrays
    cash_in_reale = [0.0] * 12
    cash_out_reale = [0.0] * 12
    cash_in_opp = [0.0] * 12
    cash_out_opp = [0.0] * 12
    cash_in_forecast = [0.0] * 12
    cash_out_forecast = [0.0] * 12

    with get_db() as conn:
        # ─── 1. CICLO ATTIVO (Cash In) ───
        rows = conn.execute("""
            SELECT importo_lordo, data_incasso_prevista, stato
            FROM ciclo_attivo
            WHERE data_incasso_prevista IS NOT NULL
              AND CAST(substr(data_incasso_prevista, 1, 4) AS INTEGER) = ?
        """, [anno]).fetchall()

        for r in rows:
            mese_idx = int(r["data_incasso_prevista"][5:7]) - 1
            if r["stato"] in ("Confermato", "Fatturato", "Saldato"):
                cash_in_reale[mese_idx] += r["importo_lordo"] or 0

        # ─── 2. CICLO PASSIVO (Cash Out) ───
        rows = conn.execute("""
            SELECT importo_lordo, data_pagamento_prevista, stato
            FROM ciclo_passivo
            WHERE data_pagamento_prevista IS NOT NULL
              AND CAST(substr(data_pagamento_prevista, 1, 4) AS INTEGER) = ?
        """, [anno]).fetchall()

        for r in rows:
            mese_idx = int(r["data_pagamento_prevista"][5:7]) - 1
            if r["stato"] in ("Confermato", "Fatturato", "Saldato"):
                cash_out_reale[mese_idx] += r["importo_lordo"] or 0

        # ─── 3. COSTI INDIRETTI (Cash Out - always real) ───
        rows = conn.execute("""
            SELECT importo_netto, iva_pct, mese
            FROM costi_indiretti
            WHERE anno = ?
        """, [anno]).fetchall()

        for r in rows:
            mese_idx = r["mese"] - 1
            lordo = r["importo_netto"] * (1 + (r["iva_pct"] or 0) / 100)
            cash_out_reale[mese_idx] += lordo

        # ─── 4. ALTRE ENTRATE (Cash In) ───
        rows = conn.execute("""
            SELECT importo_lordo, data_incasso_prevista, stato
            FROM altre_entrate
            WHERE data_incasso_prevista IS NOT NULL
              AND CAST(substr(data_incasso_prevista, 1, 4) AS INTEGER) = ?
        """, [anno]).fetchall()

        for r in rows:
            mese_idx = int(r["data_incasso_prevista"][5:7]) - 1
            if r["stato"] in ("Confermato", "Fatturato", "Saldato"):
                cash_in_reale[mese_idx] += r["importo_lordo"] or 0

        # ─── 5. FORECAST - OPPORTUNITÀ (pesato per WP) ───
        rows = conn.execute("""
            SELECT budget, costi_previsti, win_probability, iva_pct,
                   split_fatturazione, split_costi, stato
            FROM forecast
            WHERE stato = 'Opportunità'
        """).fetchall()

        for r in rows:
            wp = (r["win_probability"] or 0) / 100
            iva_mult = 1 + (r["iva_pct"] or 22) / 100

            # Ricavi ponderati
            split_fatt = json.loads(r["split_fatturazione"] or "{}")
            for mese_key, importo in split_fatt.items():
                try:
                    y, m = mese_key.split("-")
                    if int(y) == anno:
                        cash_in_opp[int(m) - 1] += importo * wp * iva_mult
                except (ValueError, IndexError):
                    pass

            # Costi ponderati
            split_costi = json.loads(r["split_costi"] or "{}")
            for mese_key, importo in split_costi.items():
                try:
                    y, m = mese_key.split("-")
                    if int(y) == anno:
                        cash_out_opp[int(m) - 1] += importo * wp * iva_mult
                except (ValueError, IndexError):
                    pass

        # ─── 6. FORECAST - FORECAST (pesato per WP) ───
        rows = conn.execute("""
            SELECT budget, costi_previsti, win_probability, iva_pct,
                   split_fatturazione, split_costi, stato
            FROM forecast
            WHERE stato = 'Forecast'
        """).fetchall()

        for r in rows:
            wp = (r["win_probability"] or 0) / 100
            iva_mult = 1 + (r["iva_pct"] or 22) / 100

            split_fatt = json.loads(r["split_fatturazione"] or "{}")
            for mese_key, importo in split_fatt.items():
                try:
                    y, m = mese_key.split("-")
                    if int(y) == anno:
                        cash_in_forecast[int(m) - 1] += importo * wp * iva_mult
                except (ValueError, IndexError):
                    pass

            split_costi = json.loads(r["split_costi"] or "{}")
            for mese_key, importo in split_costi.items():
                try:
                    y, m = mese_key.split("-")
                    if int(y) == anno:
                        cash_out_forecast[int(m) - 1] += importo * wp * iva_mult
                except (ValueError, IndexError):
                    pass

    # ─── CALCOLO SALDI CUMULATIVI ───
    saldo_reale = []
    saldo_opp = []
    saldo_fc = []
    running_reale = saldo_iniziale
    running_opp = saldo_iniziale
    running_fc = saldo_iniziale

    for i in range(12):
        # Reale
        delta_reale = cash_in_reale[i] - cash_out_reale[i]
        running_reale += delta_reale
        saldo_reale.append(round(running_reale, 2))

        # Opportunità = Reale + Opp
        delta_opp = delta_reale + (cash_in_opp[i] - cash_out_opp[i])
        running_opp += delta_opp - delta_reale  # avoid double counting
        running_opp += delta_reale
        # Ricalcolo pulito
        pass

    # Ricalcolo pulito con accumulo separato
    saldo_reale = []
    saldo_opp = []
    saldo_fc = []
    s_r = saldo_iniziale
    s_o = saldo_iniziale
    s_f = saldo_iniziale

    for i in range(12):
        net_reale = cash_in_reale[i] - cash_out_reale[i]
        net_opp = cash_in_opp[i] - cash_out_opp[i]
        net_fc = cash_in_forecast[i] - cash_out_forecast[i]

        s_r += net_reale
        s_o += net_reale + net_opp
        s_f += net_reale + net_opp + net_fc

        saldo_reale.append(round(s_r, 2))
        saldo_opp.append(round(s_o, 2))
        saldo_fc.append(round(s_f, 2))

    return {
        "mesi": mesi,
        "mesi_label": [f"{['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'][i]} {anno}" for i in range(12)],
        "saldo_reale": saldo_reale,
        "saldo_opportunita": saldo_opp,
        "saldo_forecast": saldo_fc,
        "cash_in_reale": [round(x, 2) for x in cash_in_reale],
        "cash_out_reale": [round(x, 2) for x in cash_out_reale],
        "cash_in_opp": [round(x, 2) for x in cash_in_opp],
        "cash_out_opp": [round(x, 2) for x in cash_out_opp],
        "cash_in_forecast": [round(x, 2) for x in cash_in_forecast],
        "cash_out_forecast": [round(x, 2) for x in cash_out_forecast],
        "saldo_iniziale": saldo_iniziale,
        "soglia_minima": soglia,
        "anno": anno,
    }
