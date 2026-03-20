"""
forecast_engine.py — Pipeline analysis and weighted probability calculations.
"""
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db


def analisi_pipeline(anno: int = None) -> dict:
    """
    Analizza la pipeline commerciale.
    Returns: dict with pipeline stats, by tipologia, by stato, conversion rates.
    """
    from datetime import date
    if anno is None:
        anno = date.today().year

    with get_db() as conn:
        rows = conn.execute("SELECT * FROM forecast").fetchall()

    totale_budget = 0
    totale_pesato = 0
    totale_costi = 0
    per_tipologia = {}
    per_stato = {}
    per_cliente = {}
    opportunita_list = []

    for r in rows:
        budget = r["budget"] or 0
        wp = (r["win_probability"] or 0) / 100
        costi = r["costi_previsti"] or 0
        stato = r["stato"]
        tipo = r["tipologia"]

        totale_budget += budget
        totale_pesato += budget * wp
        totale_costi += costi * wp

        # Per tipologia
        if tipo not in per_tipologia:
            per_tipologia[tipo] = {"budget": 0, "pesato": 0, "count": 0}
        per_tipologia[tipo]["budget"] += budget
        per_tipologia[tipo]["pesato"] += budget * wp
        per_tipologia[tipo]["count"] += 1

        # Per stato
        if stato not in per_stato:
            per_stato[stato] = {"budget": 0, "pesato": 0, "count": 0}
        per_stato[stato]["budget"] += budget
        per_stato[stato]["pesato"] += budget * wp
        per_stato[stato]["count"] += 1

        # Per cliente
        cid = r["cliente_id"]
        if cid not in per_cliente:
            per_cliente[cid] = {"budget": 0, "pesato": 0, "count": 0}
        per_cliente[cid]["budget"] += budget
        per_cliente[cid]["pesato"] += budget * wp
        per_cliente[cid]["count"] += 1

        opportunita_list.append({
            "id": r["id"],
            "cliente_id": r["cliente_id"],
            "nome_progetto": r["nome_progetto"],
            "tipologia": tipo,
            "budget": budget,
            "costi_previsti": costi,
            "marginalita_attesa": r["marginalita_attesa"],
            "win_probability": r["win_probability"],
            "stato": stato,
            "valore_pesato": round(budget * wp, 2),
        })

    # Win rate
    totale_items = len([r for r in rows if r["stato"] in ("Chiuso Vinto", "Chiuso Perso")])
    vinti = len([r for r in rows if r["stato"] == "Chiuso Vinto"])
    win_rate = (vinti / totale_items * 100) if totale_items > 0 else 0

    return {
        "totale_budget": round(totale_budget, 2),
        "totale_pesato": round(totale_pesato, 2),
        "totale_costi_pesati": round(totale_costi, 2),
        "margine_pesato": round(totale_pesato - totale_costi, 2),
        "num_opportunita": len(rows),
        "win_rate": round(win_rate, 1),
        "per_tipologia": per_tipologia,
        "per_stato": per_stato,
        "per_cliente": per_cliente,
        "opportunita": opportunita_list,
    }
