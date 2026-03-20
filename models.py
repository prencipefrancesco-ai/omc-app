"""
models.py — Enums, state machine, and data validation for the OMC system.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ─── STATE ENUMS ───────────────────────────────────────────────────

class StatoForecast(str, Enum):
    """Stati del Forecast / Pipeline commerciale."""
    FORECAST = "Forecast"
    OPPORTUNITA = "Opportunità"
    CHIUSO_VINTO = "Chiuso Vinto"
    CHIUSO_PERSO = "Chiuso Perso"
    ABBANDONATO = "Abbandonato"

    # Transizioni valide
    @classmethod
    def transizioni_valide(cls):
        return {
            cls.FORECAST: [cls.OPPORTUNITA, cls.ABBANDONATO],
            cls.OPPORTUNITA: [cls.CHIUSO_VINTO, cls.CHIUSO_PERSO, cls.ABBANDONATO],
            cls.CHIUSO_VINTO: [],  # stato finale
            cls.CHIUSO_PERSO: [],  # stato finale
            cls.ABBANDONATO: [],   # stato finale
        }

    def puo_transitare_a(self, nuovo_stato: 'StatoForecast') -> bool:
        return nuovo_stato in self.transizioni_valide().get(self, [])


class StatoPagamento(str, Enum):
    """Stati del ciclo attivo/passivo e altre entrate."""
    PREVISIONALE = "Previsionale"
    CONFERMATO = "Confermato"
    FATTURATO = "Fatturato"
    SALDATO = "Saldato"

    @classmethod
    def transizioni_valide(cls):
        return {
            cls.PREVISIONALE: [cls.CONFERMATO],
            cls.CONFERMATO: [cls.FATTURATO],
            cls.FATTURATO: [cls.SALDATO],
            cls.SALDATO: [],  # stato finale
        }

    def puo_transitare_a(self, nuovo_stato: 'StatoPagamento') -> bool:
        return nuovo_stato in self.transizioni_valide().get(self, [])

    # Helpers for cashflow scenario filtering
    @classmethod
    def stati_reali(cls):
        """Stati inclusi nel cashflow REALE."""
        return [cls.CONFERMATO, cls.FATTURATO, cls.SALDATO]

    @classmethod
    def stati_certi(cls):
        """Stati certi (fatturato + saldato) per calcoli."""
        return [cls.FATTURATO, cls.SALDATO]


class CentroRicavoCosto(str, Enum):
    """Tipologia progetto / centro di ricavo-costo."""
    CONSULENZA = "Consulenza"
    EVENTO = "Evento"
    PROGETTO_INTEGRATO = "Progetto Integrato"
    ALTRO = "Altro"


class CategoriaIndiretti(str, Enum):
    """Categorie costi indiretti — Tab del foglio Costi_indiretti."""
    D_PERSONALE = "D. Personale"
    D_SEDI = "D. Sedi Operative"
    D_COMMERCIALE = "D. Commerciale e Marketing"
    D_SERVIZI = "D. Servizi Professionali"
    D_SPESE_OPERATIVE = "D. Spese Operative"
    F_LICENZE = "F. Licenze, Software, HW"
    H_ONERI = "H. Oneri Finanziari"
    L_IMPOSTE = "L. Imposte e Tasse"


# ─── TRIMESTRE IVA ─────────────────────────────────────────────────

TRIMESTRI_IVA = {
    "Q1": {"mesi": [1, 2, 3], "liquidazione_mese": 5, "label": "Gen-Mar"},
    "Q2": {"mesi": [4, 5, 6], "liquidazione_mese": 8, "label": "Apr-Giu"},
    "Q3": {"mesi": [7, 8, 9], "liquidazione_mese": 11, "label": "Lug-Set"},
    "Q4": {"mesi": [10, 11, 12], "liquidazione_mese": 1, "label": "Ott-Dic"},  # +1 anno
}


def get_trimestre(mese: int) -> str:
    """Dato un mese (1-12), restituisce il trimestre IVA (Q1-Q4)."""
    for q, info in TRIMESTRI_IVA.items():
        if mese in info["mesi"]:
            return q
    return "Q1"


# ─── UTILITIES ─────────────────────────────────────────────────────

def calcola_mese_incasso(data_fattura: date, mesi_dilazione: int) -> date:
    """Calcola la data di incasso/pagamento prevista."""
    mese = data_fattura.month + mesi_dilazione
    anno = data_fattura.year + (mese - 1) // 12
    mese = ((mese - 1) % 12) + 1
    # Ultimo giorno del mese calcolato (approssimato al 28 per sicurezza)
    giorno = min(data_fattura.day, 28)
    return date(anno, mese, giorno)


def calcola_importo_iva(importo_netto: float, iva_pct: float) -> float:
    """Calcola l'importo IVA."""
    return round(importo_netto * iva_pct / 100, 2)


def calcola_importo_lordo(importo_netto: float, iva_pct: float) -> float:
    """Calcola l'importo IVA inclusa."""
    return round(importo_netto * (1 + iva_pct / 100), 2)
