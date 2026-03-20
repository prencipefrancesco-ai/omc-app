"""
iva_engine.py — Stima IVA trimestrale.

IVA a Debito (su vendite cicli attivi + forecast ponderato)
IVA a Credito (su acquisti cicli passivi + costi indiretti)
IVA Netta = Debito - Credito
"""
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db
from models import TRIMESTRI_IVA


def calcola_iva_trimestrale(anno: int = None) -> dict:
    """Calcola IVA trimestrale con dettaglio debito/credito."""
    from datetime import date
    if anno is None:
        anno = date.today().year

    iva_debito_mensile = [0.0] * 12
    iva_credito_mensile = [0.0] * 12

    with get_db() as conn:
        # ─── IVA a DEBITO (Cicli Attivi) ───
        rows = conn.execute("""
            SELECT importo_iva, data_fattura, stato
            FROM ciclo_attivo
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
              AND stato IN ('Confermato', 'Fatturato', 'Saldato')
        """, [anno]).fetchall()

        for r in rows:
            m = int(r["data_fattura"][5:7]) - 1
            iva_debito_mensile[m] += r["importo_iva"] or 0

        # IVA Debito da Altre Entrate
        rows = conn.execute("""
            SELECT importo_iva, data_fattura
            FROM altre_entrate
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
              AND stato IN ('Confermato', 'Fatturato', 'Saldato')
              AND iva_pct > 0
        """, [anno]).fetchall()

        for r in rows:
            m = int(r["data_fattura"][5:7]) - 1
            iva_debito_mensile[m] += r["importo_iva"] or 0

        # ─── IVA a CREDITO (Cicli Passivi) ───
        rows = conn.execute("""
            SELECT importo_iva, data_fattura, stato
            FROM ciclo_passivo
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
              AND stato IN ('Confermato', 'Fatturato', 'Saldato')
        """, [anno]).fetchall()

        for r in rows:
            m = int(r["data_fattura"][5:7]) - 1
            iva_credito_mensile[m] += r["importo_iva"] or 0

        # IVA Credito da Costi Indiretti
        rows = conn.execute("""
            SELECT importo_netto, iva_pct, mese
            FROM costi_indiretti
            WHERE anno = ? AND iva_pct > 0
        """, [anno]).fetchall()

        for r in rows:
            m = r["mese"] - 1
            iva = r["importo_netto"] * (r["iva_pct"] or 0) / 100
            iva_credito_mensile[m] += iva

        # ─── IVA da FORECAST (ponderata) ───
        iva_debito_forecast = [0.0] * 12
        iva_credito_forecast = [0.0] * 12

        rows = conn.execute("""
            SELECT budget, costi_previsti, win_probability, iva_pct,
                   split_fatturazione, split_costi
            FROM forecast
            WHERE stato IN ('Opportunità', 'Forecast')
        """).fetchall()

        for r in rows:
            wp = (r["win_probability"] or 0) / 100
            iva_pct = r["iva_pct"] or 22

            split_fatt = json.loads(r["split_fatturazione"] or "{}")
            for k, v in split_fatt.items():
                try:
                    y, m = k.split("-")
                    if int(y) == anno:
                        iva_debito_forecast[int(m) - 1] += v * iva_pct / 100 * wp
                except (ValueError, IndexError):
                    pass

            split_costi = json.loads(r["split_costi"] or "{}")
            for k, v in split_costi.items():
                try:
                    y, m = k.split("-")
                    if int(y) == anno:
                        iva_credito_forecast[int(m) - 1] += v * iva_pct / 100 * wp
                except (ValueError, IndexError):
                    pass

    # ─── Calcolo per trimestre ───
    trimestri = {}
    for q, info in TRIMESTRI_IVA.items():
        debito = sum(iva_debito_mensile[m - 1] for m in info["mesi"])
        credito = sum(iva_credito_mensile[m - 1] for m in info["mesi"])
        debito_fc = sum(iva_debito_forecast[m - 1] for m in info["mesi"])
        credito_fc = sum(iva_credito_forecast[m - 1] for m in info["mesi"])
        netta = debito - credito
        netta_con_forecast = (debito + debito_fc) - (credito + credito_fc)

        liq_mese = info["liquidazione_mese"]
        liq_anno = anno if liq_mese > info["mesi"][-1] else anno + 1

        trimestri[q] = {
            "label": info["label"],
            "iva_debito": round(debito, 2),
            "iva_credito": round(credito, 2),
            "iva_netta": round(netta, 2),
            "iva_debito_forecast": round(debito_fc, 2),
            "iva_credito_forecast": round(credito_fc, 2),
            "iva_netta_con_forecast": round(netta_con_forecast, 2),
            "mese_liquidazione": liq_mese,
            "anno_liquidazione": liq_anno,
        }

    return {
        "anno": anno,
        "trimestri": trimestri,
        "iva_debito_mensile": [round(v, 2) for v in iva_debito_mensile],
        "iva_credito_mensile": [round(v, 2) for v in iva_credito_mensile],
        "iva_debito_forecast_mensile": [round(v, 2) for v in iva_debito_forecast],
        "iva_credito_forecast_mensile": [round(v, 2) for v in iva_credito_forecast],
    }
