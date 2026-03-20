"""
seed_data.py — Demo data for the OMC system to show functionality immediately.
"""
import json
from database import init_database, insert_row, set_config, get_connection


def seed():
    """Populate database with demo data."""
    init_database()

    conn = get_connection()
    # Check if already seeded
    count = conn.execute("SELECT COUNT(*) FROM clienti").fetchone()[0]
    conn.close()
    if count > 0:
        return  # Already seeded

    # ─── Saldo iniziale ───
    set_config("saldo_iniziale", "150000")
    set_config("soglia_minima_liquidita", "50000")
    set_config("anno_inizio", "2025")

    # ─── Clienti ───
    clienti = [
        {"nome": "4Ward", "partita_iva": "IT01234567890", "note": "Cliente storico"},
        {"nome": "Be Team", "partita_iva": "IT09876543210", "note": "Sede principale"},
        {"nome": "Cohesity", "partita_iva": "IT11223344556", "note": "Enterprise"},
        {"nome": "Digital Corp", "partita_iva": "IT66778899001", "note": "Nuovo cliente"},
        {"nome": "EuroTech", "partita_iva": "IT55443322110", "note": "Medio cliente"},
    ]
    client_ids = {}
    for c in clienti:
        cid = insert_row("clienti", c)
        client_ids[c["nome"]] = cid

    # ─── Forecast (Pipeline Commerciale) ───
    forecasts = [
        {
            "cliente_id": client_ids["Digital Corp"],
            "nome_progetto": "Digital Transformation Q2",
            "tipologia": "Consulenza",
            "budget": 80000,
            "costi_previsti": 48000,
            "marginalita_attesa": 40,
            "win_probability": 60,
            "stato": "Opportunità",
            "iva_pct": 22,
            "split_fatturazione": json.dumps({"2025-04": 30000, "2025-06": 50000}),
            "split_costi": json.dumps({"2025-04": 18000, "2025-06": 30000}),
        },
        {
            "cliente_id": client_ids["EuroTech"],
            "nome_progetto": "Evento Product Launch Q3",
            "tipologia": "Evento",
            "budget": 100000,
            "costi_previsti": 70000,
            "marginalita_attesa": 30,
            "win_probability": 50,
            "stato": "Opportunità",
            "iva_pct": 22,
            "split_fatturazione": json.dumps({"2025-07": 40000, "2025-09": 60000}),
            "split_costi": json.dumps({"2025-07": 28000, "2025-09": 42000}),
        },
        {
            "cliente_id": client_ids["4Ward"],
            "nome_progetto": "Cloud Migration Phase 2",
            "tipologia": "Progetto Integrato",
            "budget": 150000,
            "costi_previsti": 90000,
            "marginalita_attesa": 40,
            "win_probability": 30,
            "stato": "Forecast",
            "iva_pct": 22,
            "split_fatturazione": json.dumps({"2025-09": 50000, "2025-11": 50000, "2026-01": 50000}),
            "split_costi": json.dumps({"2025-09": 30000, "2025-11": 30000, "2026-01": 30000}),
        },
        {
            "cliente_id": client_ids["Cohesity"],
            "nome_progetto": "Security Audit 2025",
            "tipologia": "Consulenza",
            "budget": 45000,
            "costi_previsti": 22500,
            "marginalita_attesa": 50,
            "win_probability": 80,
            "stato": "Opportunità",
            "iva_pct": 22,
            "split_fatturazione": json.dumps({"2025-03": 20000, "2025-05": 25000}),
            "split_costi": json.dumps({"2025-03": 10000, "2025-05": 12500}),
        },
    ]
    for f in forecasts:
        insert_row("forecast", f)

    # ─── Ciclo Attivo (Fatture emesse / previste) ───
    attivi = [
        # 4Ward — progetto già vinto
        {
            "cliente_id": client_ids["4Ward"],
            "centro_ricavo": "Consulenza",
            "dettaglio_ricavo": "Consulenza IT Q1 2025 - Acconto",
            "progetto": "IT Consulting Annuale",
            "importo_netto": 25000,
            "iva_pct": 22,
            "data_fattura": "2025-01-15",
            "mesi_dilazione": 1,
            "data_incasso_prevista": "2025-02-15",
            "stato": "Saldato",
            "numero_fattura": "FT-2025-001",
        },
        {
            "cliente_id": client_ids["4Ward"],
            "centro_ricavo": "Consulenza",
            "dettaglio_ricavo": "Consulenza IT Q1 2025 - Saldo",
            "progetto": "IT Consulting Annuale",
            "importo_netto": 25000,
            "iva_pct": 22,
            "data_fattura": "2025-03-15",
            "mesi_dilazione": 1,
            "data_incasso_prevista": "2025-04-15",
            "stato": "Fatturato",
            "numero_fattura": "FT-2025-005",
        },
        # Be Team
        {
            "cliente_id": client_ids["Be Team"],
            "centro_ricavo": "Evento",
            "dettaglio_ricavo": "Organizzazione Evento Corporate - Acconto 40%",
            "progetto": "Evento Corporate 2025",
            "importo_netto": 32000,
            "iva_pct": 22,
            "data_fattura": "2025-02-01",
            "mesi_dilazione": 0,
            "data_incasso_prevista": "2025-02-01",
            "stato": "Saldato",
            "numero_fattura": "FT-2025-003",
        },
        {
            "cliente_id": client_ids["Be Team"],
            "centro_ricavo": "Evento",
            "dettaglio_ricavo": "Organizzazione Evento Corporate - Saldo 60%",
            "progetto": "Evento Corporate 2025",
            "importo_netto": 48000,
            "iva_pct": 22,
            "data_fattura": "2025-04-15",
            "mesi_dilazione": 1,
            "data_incasso_prevista": "2025-05-15",
            "stato": "Confermato",
        },
        # Cohesity
        {
            "cliente_id": client_ids["Cohesity"],
            "centro_ricavo": "Progetto Integrato",
            "dettaglio_ricavo": "Data Platform Setup",
            "progetto": "Cohesity Data Platform",
            "importo_netto": 60000,
            "iva_pct": 22,
            "data_fattura": "2025-01-20",
            "mesi_dilazione": 2,
            "data_incasso_prevista": "2025-03-20",
            "stato": "Saldato",
            "numero_fattura": "FT-2025-002",
        },
        {
            "cliente_id": client_ids["Cohesity"],
            "centro_ricavo": "Progetto Integrato",
            "dettaglio_ricavo": "Data Platform Maintenance Q2",
            "progetto": "Cohesity Data Platform",
            "importo_netto": 15000,
            "iva_pct": 22,
            "data_fattura": "2025-05-01",
            "mesi_dilazione": 1,
            "data_incasso_prevista": "2025-06-01",
            "stato": "Previsionale",
        },
    ]
    for a in attivi:
        insert_row("ciclo_attivo", a)

    # ─── Ciclo Passivo (Costi Fornitori) ───
    passivi = [
        # 4Ward
        {
            "cliente_id": client_ids["4Ward"],
            "centro_costo": "Consulenza",
            "dettaglio_costo": "Consulente Senior - Gennaio",
            "fornitore": "TechPeople Srl",
            "importo_netto": 8000,
            "iva_pct": 22,
            "data_fattura": "2025-01-31",
            "mesi_dilazione": 1,
            "data_pagamento_prevista": "2025-02-28",
            "stato": "Saldato",
            "numero_fattura": "FRN-001",
        },
        {
            "cliente_id": client_ids["4Ward"],
            "centro_costo": "Consulenza",
            "dettaglio_costo": "Consulente Senior - Marzo",
            "fornitore": "TechPeople Srl",
            "importo_netto": 8000,
            "iva_pct": 22,
            "data_fattura": "2025-03-31",
            "mesi_dilazione": 1,
            "data_pagamento_prevista": "2025-04-30",
            "stato": "Confermato",
        },
        # Be Team
        {
            "cliente_id": client_ids["Be Team"],
            "centro_costo": "Evento",
            "dettaglio_costo": "Location + Allestimento Evento",
            "fornitore": "EventiMax Spa",
            "importo_netto": 22000,
            "iva_pct": 22,
            "data_fattura": "2025-02-10",
            "mesi_dilazione": 0,
            "data_pagamento_prevista": "2025-02-10",
            "stato": "Saldato",
            "numero_fattura": "FRN-005",
        },
        {
            "cliente_id": client_ids["Be Team"],
            "centro_costo": "Evento",
            "dettaglio_costo": "Catering e Servizi Evento",
            "fornitore": "GustoFine Srl",
            "importo_netto": 12000,
            "iva_pct": 10,
            "data_fattura": "2025-04-20",
            "mesi_dilazione": 1,
            "data_pagamento_prevista": "2025-05-20",
            "stato": "Previsionale",
        },
        # Cohesity
        {
            "cliente_id": client_ids["Cohesity"],
            "centro_costo": "Progetto Integrato",
            "dettaglio_costo": "Licenze Software Annuali",
            "fornitore": "SoftVendor Inc",
            "importo_netto": 18000,
            "iva_pct": 22,
            "data_fattura": "2025-01-15",
            "mesi_dilazione": 0,
            "data_pagamento_prevista": "2025-01-15",
            "stato": "Saldato",
            "numero_fattura": "FRN-003",
        },
        {
            "cliente_id": client_ids["Cohesity"],
            "centro_costo": "Progetto Integrato",
            "dettaglio_costo": "DevOps Specialist Q2",
            "fornitore": "CloudOps Srl",
            "importo_netto": 15000,
            "iva_pct": 22,
            "data_fattura": "2025-05-15",
            "mesi_dilazione": 1,
            "data_pagamento_prevista": "2025-06-15",
            "stato": "Previsionale",
        },
    ]
    for p in passivi:
        insert_row("ciclo_passivo", p)

    # ─── Costi Indiretti (mensili, 12 mesi) ───
    costi_fissi = [
        ("D. Personale", "Stipendi Dipendenti", 28000),
        ("D. Personale", "Oneri Sociali (INPS/INAIL)", 9000),
        ("D. Personale", "Collaboratori P.IVA", 6000),
        ("D. Personale", "Accantonamento TFR", 2500),
        ("D. Sedi Operative", "Affitto Sede Imola", 2200),
        ("D. Sedi Operative", "Affitto Sede Cusano", 1800),
        ("D. Sedi Operative", "Utenze (Luce/Gas/Acqua)", 800),
        ("D. Commerciale e Marketing", "Marketing e ADV", 1500),
        ("D. Commerciale e Marketing", "Trasferte Commerciali", 1000),
        ("D. Servizi Professionali", "Commercialista/Fiscale", 1200),
        ("D. Servizi Professionali", "IT e Cybersecurity", 800),
        ("D. Spese Operative", "Spese Bancarie", 300),
        ("D. Spese Operative", "Materiale Consumo e Cancelleria", 200),
        ("D. Spese Operative", "Rimborsi Chilometrici", 600),
        ("F. Licenze, Software, HW", "Licenze SaaS (Microsoft/Google)", 1800),
        ("F. Licenze, Software, HW", "Infrastruttura Cloud", 1200),
        ("H. Oneri Finanziari", "Interessi Passivi Mutuo", 500),
    ]
    for mese in range(1, 13):
        for cat, sotto, importo in costi_fissi:
            insert_row("costi_indiretti", {
                "categoria": cat,
                "sottocategoria": sotto,
                "importo_netto": importo,
                "iva_pct": 22 if cat not in ("D. Personale", "H. Oneri Finanziari", "L. Imposte e Tasse") else 0,
                "anno": 2025,
                "mese": mese,
                "ricorrente": 1,
            })

    # Imposte (trimestrali)
    for mese in [3, 6, 9, 12]:
        insert_row("costi_indiretti", {
            "categoria": "L. Imposte e Tasse",
            "sottocategoria": "IRES/IRAP Acconto",
            "importo_netto": 8000,
            "iva_pct": 0,
            "anno": 2025,
            "mese": mese,
            "ricorrente": 0,
        })

    # ─── Altre Entrate ───
    insert_row("altre_entrate", {
        "descrizione": "Rimborso assicurativo",
        "importo_netto": 5000,
        "iva_pct": 0,
        "data_fattura": "2025-02-15",
        "mesi_dilazione": 0,
        "data_incasso_prevista": "2025-02-15",
        "stato": "Saldato",
    })
    insert_row("altre_entrate", {
        "descrizione": "Contributo formazione regionale",
        "importo_netto": 8000,
        "iva_pct": 0,
        "data_fattura": "2025-06-01",
        "mesi_dilazione": 2,
        "data_incasso_prevista": "2025-08-01",
        "stato": "Confermato",
    })

    print("✅ Database inizializzato con dati demo!")


if __name__ == "__main__":
    seed()
