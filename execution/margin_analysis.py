"""
margin_analysis.py — Calcolo marginalità per cliente e commessa.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db


def analisi_margini(anno: int = None) -> dict:
    """
    Calcola margini per ogni cliente e per progetto.
    Returns dict with per-client and per-project margin data.
    """
    from datetime import date
    if anno is None:
        anno = date.today().year

    with get_db() as conn:
        clienti = conn.execute("SELECT * FROM clienti WHERE attivo = 1").fetchall()

        risultati_clienti = []
        for c in clienti:
            # Ricavi da ciclo attivo (per competenza = data_fattura nell'anno)
            ricavi = conn.execute("""
                SELECT COALESCE(SUM(importo_netto), 0) as totale
                FROM ciclo_attivo
                WHERE cliente_id = ?
                  AND data_fattura IS NOT NULL
                  AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
                  AND stato IN ('Confermato', 'Fatturato', 'Saldato')
            """, [c["id"], anno]).fetchone()["totale"]

            # Costi da ciclo passivo
            costi = conn.execute("""
                SELECT COALESCE(SUM(importo_netto), 0) as totale
                FROM ciclo_passivo
                WHERE cliente_id = ?
                  AND data_fattura IS NOT NULL
                  AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
                  AND stato IN ('Confermato', 'Fatturato', 'Saldato')
            """, [c["id"], anno]).fetchone()["totale"]

            margine = ricavi - costi
            pct = (margine / ricavi * 100) if ricavi > 0 else 0

            risultati_clienti.append({
                "id": c["id"],
                "nome": c["nome"],
                "ricavi": round(ricavi, 2),
                "costi_diretti": round(costi, 2),
                "margine_lordo": round(margine, 2),
                "marginalita_pct": round(pct, 1),
            })

        # Sort by margine lordo descending
        risultati_clienti.sort(key=lambda x: x["margine_lordo"], reverse=True)

        # Totali
        totale_ricavi = sum(c["ricavi"] for c in risultati_clienti)
        totale_costi = sum(c["costi_diretti"] for c in risultati_clienti)
        totale_margine = totale_ricavi - totale_costi
        pct_totale = (totale_margine / totale_ricavi * 100) if totale_ricavi > 0 else 0

        # Costi indiretti totali
        costi_indiretti = conn.execute("""
            SELECT COALESCE(SUM(importo_netto), 0) as totale
            FROM costi_indiretti
            WHERE anno = ?
        """, [anno]).fetchone()["totale"]

        ebitda = totale_margine - costi_indiretti

        # Per progetto (aggregato per dettaglio_ricavo + cliente)
        progetti = conn.execute("""
            SELECT
                ca.progetto,
                cl.nome as cliente,
                SUM(ca.importo_netto) as ricavi
            FROM ciclo_attivo ca
            JOIN clienti cl ON ca.cliente_id = cl.id
            WHERE ca.data_fattura IS NOT NULL
              AND CAST(substr(ca.data_fattura, 1, 4) AS INTEGER) = ?
              AND ca.stato IN ('Confermato', 'Fatturato', 'Saldato')
              AND ca.progetto IS NOT NULL
            GROUP BY ca.progetto, cl.nome
        """, [anno]).fetchall()

        risultati_progetti = []
        for p in progetti:
            costi_p = conn.execute("""
                SELECT COALESCE(SUM(cp.importo_netto), 0) as totale
                FROM ciclo_passivo cp
                JOIN clienti cl ON cp.cliente_id = cl.id
                WHERE cl.nome = ?
                  AND cp.data_fattura IS NOT NULL
                  AND CAST(substr(cp.data_fattura, 1, 4) AS INTEGER) = ?
                  AND cp.stato IN ('Confermato', 'Fatturato', 'Saldato')
            """, [p["cliente"], anno]).fetchone()["totale"]

            ric = p["ricavi"] or 0
            mar = ric - costi_p
            pct_p = (mar / ric * 100) if ric > 0 else 0

            risultati_progetti.append({
                "progetto": p["progetto"],
                "cliente": p["cliente"],
                "ricavi": round(ric, 2),
                "costi": round(costi_p, 2),
                "margine": round(mar, 2),
                "marginalita_pct": round(pct_p, 1),
            })

    return {
        "clienti": risultati_clienti,
        "progetti": risultati_progetti,
        "totale_ricavi": round(totale_ricavi, 2),
        "totale_costi_diretti": round(totale_costi, 2),
        "totale_margine_lordo": round(totale_margine, 2),
        "marginalita_media": round(pct_totale, 1),
        "costi_indiretti": round(costi_indiretti, 2),
        "ebitda": round(ebitda, 2),
        "anno": anno,
    }
