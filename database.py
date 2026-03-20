"""
database.py — SQLite database schema and connection management for the OMC system.
"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "omc.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database operations."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Create all tables if they don't exist."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)


# ─── SCHEMA ────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- Anagrafica Clienti
CREATE TABLE IF NOT EXISTS clienti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    partita_iva TEXT,
    indirizzo TEXT,
    note TEXT,
    attivo INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Attori (Assegnatari Opportunità)
CREATE TABLE IF NOT EXISTS attori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    ruolo TEXT,
    attivo INTEGER DEFAULT 1
);

-- Forecast / Pipeline Commerciale
CREATE TABLE IF NOT EXISTS forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    attore_id INTEGER REFERENCES attori(id),
    nome_progetto TEXT NOT NULL,
    tipologia TEXT NOT NULL CHECK(tipologia IN ('Consulenza', 'Evento', 'Progetto Integrato', 'Altro')),
    budget REAL NOT NULL DEFAULT 0,
    costi_previsti REAL NOT NULL DEFAULT 0,
    marginalita_attesa REAL DEFAULT 0,  -- percentuale
    win_probability REAL DEFAULT 10,     -- percentuale 0-100
    stato TEXT NOT NULL DEFAULT 'Forecast' CHECK(stato IN ('Forecast', 'Opportunità', 'Chiuso Vinto', 'Chiuso Perso', 'Abbandonato')),
    iva_pct REAL DEFAULT 22,
    -- Split fatturazione per mese (JSON: {"2026-01": 30000, "2026-03": 70000})
    split_fatturazione TEXT DEFAULT '{}',
    -- Split costi per mese
    split_costi TEXT DEFAULT '{}',
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (cliente_id) REFERENCES clienti(id)
);

-- Ciclo Attivo (Fatturazione)
CREATE TABLE IF NOT EXISTS ciclo_attivo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    forecast_id INTEGER,
    centro_ricavo TEXT NOT NULL CHECK(centro_ricavo IN ('Consulenza', 'Evento', 'Progetto Integrato', 'Altro')),
    dettaglio_ricavo TEXT NOT NULL,
    progetto TEXT,
    importo_netto REAL NOT NULL DEFAULT 0,
    iva_pct REAL DEFAULT 22,
    importo_iva REAL GENERATED ALWAYS AS (ROUND(importo_netto * iva_pct / 100, 2)) STORED,
    importo_lordo REAL GENERATED ALWAYS AS (ROUND(importo_netto * (1 + iva_pct / 100), 2)) STORED,
    data_fattura TEXT,  -- data emissione o prevista
    mesi_dilazione INTEGER DEFAULT 0,
    data_incasso_prevista TEXT,  -- calcolato: data_fattura + dilazione
    stato TEXT NOT NULL DEFAULT 'Previsionale' CHECK(stato IN ('Previsionale', 'Confermato', 'Fatturato', 'Saldato')),
    numero_fattura TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (cliente_id) REFERENCES clienti(id),
    FOREIGN KEY (forecast_id) REFERENCES forecast(id)
);

-- Ciclo Passivo (Costi Fornitori)
CREATE TABLE IF NOT EXISTS ciclo_passivo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,  -- cliente di riferimento (progetto)
    forecast_id INTEGER,
    centro_costo TEXT NOT NULL CHECK(centro_costo IN ('Consulenza', 'Evento', 'Progetto Integrato', 'Altro')),
    dettaglio_costo TEXT NOT NULL,
    fornitore TEXT,
    importo_netto REAL NOT NULL DEFAULT 0,
    iva_pct REAL DEFAULT 22,
    importo_iva REAL GENERATED ALWAYS AS (ROUND(importo_netto * iva_pct / 100, 2)) STORED,
    importo_lordo REAL GENERATED ALWAYS AS (ROUND(importo_netto * (1 + iva_pct / 100), 2)) STORED,
    data_fattura TEXT,
    mesi_dilazione INTEGER DEFAULT 0,
    data_pagamento_prevista TEXT,
    stato TEXT NOT NULL DEFAULT 'Previsionale' CHECK(stato IN ('Previsionale', 'Confermato', 'Fatturato', 'Saldato')),
    numero_fattura TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (cliente_id) REFERENCES clienti(id),
    FOREIGN KEY (forecast_id) REFERENCES forecast(id)
);

-- Costi Indiretti (Overhead mensile)
CREATE TABLE IF NOT EXISTS costi_indiretti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL CHECK(categoria IN (
        'D. Personale', 'D. Sedi Operative', 'D. Commerciale e Marketing',
        'D. Servizi Professionali', 'D. Spese Operative',
        'F. Licenze, Software, HW', 'H. Oneri Finanziari', 'L. Imposte e Tasse'
    )),
    sottocategoria TEXT NOT NULL,
    descrizione TEXT,
    importo_netto REAL NOT NULL DEFAULT 0,
    iva_pct REAL DEFAULT 22,
    anno INTEGER NOT NULL,
    mese INTEGER NOT NULL CHECK(mese BETWEEN 1 AND 12),
    ricorrente INTEGER DEFAULT 0,  -- 1 = costo fisso mensile
    note TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Altre Entrate (non legate a clienti)
CREATE TABLE IF NOT EXISTS altre_entrate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descrizione TEXT NOT NULL,
    importo_netto REAL NOT NULL DEFAULT 0,
    iva_pct REAL DEFAULT 22,
    importo_iva REAL GENERATED ALWAYS AS (ROUND(importo_netto * iva_pct / 100, 2)) STORED,
    importo_lordo REAL GENERATED ALWAYS AS (ROUND(importo_netto * (1 + iva_pct / 100), 2)) STORED,
    data_fattura TEXT,
    mesi_dilazione INTEGER DEFAULT 0,
    data_incasso_prevista TEXT,
    stato TEXT NOT NULL DEFAULT 'Previsionale' CHECK(stato IN ('Previsionale', 'Confermato', 'Fatturato', 'Saldato')),
    numero_fattura TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Saldo Cassa Iniziale (configurazione)
CREATE TABLE IF NOT EXISTS configurazione (
    chiave TEXT PRIMARY KEY,
    valore TEXT NOT NULL
);
"""


# ─── CRUD HELPERS ──────────────────────────────────────────────────

def insert_row(table: str, data: dict) -> int:
    """Insert a row and return its ID."""
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with get_db() as conn:
        cursor = conn.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            list(data.values())
        )
        return cursor.lastrowid


def update_row(table: str, row_id: int, data: dict):
    """Update a row by ID."""
    sets = ", ".join([f"{k} = ?" for k in data.keys()])
    with get_db() as conn:
        conn.execute(
            f"UPDATE {table} SET {sets}, updated_at = datetime('now') WHERE id = ?",
            list(data.values()) + [row_id]
        )


def delete_row(table: str, row_id: int):
    """Delete a row by ID."""
    with get_db() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", [row_id])


def fetch_all(table: str, where: str = "", params: list = None) -> list:
    """Fetch all rows from a table."""
    query = f"SELECT * FROM {table}"
    if where:
        query += f" WHERE {where}"
    with get_db() as conn:
        return conn.execute(query, params or []).fetchall()


def fetch_one(table: str, row_id: int) -> dict:
    """Fetch a single row by ID."""
    with get_db() as conn:
        return conn.execute(f"SELECT * FROM {table} WHERE id = ?", [row_id]).fetchone()


def get_config(chiave: str, default: str = "0") -> str:
    """Get a configuration value."""
    with get_db() as conn:
        row = conn.execute("SELECT valore FROM configurazione WHERE chiave = ?", [chiave]).fetchone()
        return row["valore"] if row else default


def set_config(chiave: str, valore: str):
    """Set a configuration value."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO configurazione (chiave, valore) VALUES (?, ?) "
            "ON CONFLICT(chiave) DO UPDATE SET valore = ?",
            [chiave, valore, valore]
        )
