"""
pages/forecast.py — Gestione Forecast / Pipeline Commerciale.
CRUD per opportunità con cambio stato e generazione ciclo attivo.
"""
import streamlit as st
import json
import pandas as pd
from database import get_db, insert_row, update_row, delete_row, fetch_all
from models import StatoForecast, CentroRicavoCosto


STATO_BADGE = {
    "Forecast": "badge-forecast",
    "Opportunità": "badge-opportunita",
    "Chiuso Vinto": "badge-vinto",
    "Chiuso Perso": "badge-perso",
    "Abbandonato": "badge-perso",
}


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 🎯 Forecast — Pipeline Commerciale")
    st.markdown(f"*Gestione opportunità e previsioni {anno}*")
    st.markdown("---")

    # Load clients and actors
    with get_db() as conn:
        clienti = conn.execute("SELECT * FROM clienti WHERE attivo = 1 ORDER BY nome").fetchall()
        attori = conn.execute("SELECT * FROM attori WHERE attivo = 1 ORDER BY nome").fetchall()
        forecasts = conn.execute("""
            SELECT f.*, c.nome as cliente_nome, a.nome as attore_nome
            FROM forecast f
            JOIN clienti c ON f.cliente_id = c.id
            LEFT JOIN attori a ON f.attore_id = a.id
            ORDER BY f.stato, f.win_probability DESC
        """).fetchall()

    client_map = {c["id"]: c["nome"] for c in clienti}
    attori_map = {a["id"]: a["nome"] for a in attori}

    # ─── TABELLA PIPELINE ───
    if forecasts:
        st.markdown('<div class="section-header">📋 Pipeline Attiva</div>', unsafe_allow_html=True)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        attive = [f for f in forecasts if f["stato"] in ("Forecast", "Opportunità")]
        with col1:
            st.metric("Opportunità Attive", len(attive))
        with col2:
            budget_tot = sum(f["budget"] for f in attive)
            st.metric("Budget Totale", f"€{budget_tot:,.0f}")
        with col3:
            pesato = sum(f["budget"] * (f["win_probability"] or 0) / 100 for f in attive)
            st.metric("Valore Pesato", f"€{pesato:,.0f}")
        with col4:
            vinti = len([f for f in forecasts if f["stato"] == "Chiuso Vinto"])
            totali = len([f for f in forecasts if f["stato"] in ("Chiuso Vinto", "Chiuso Perso")])
            wr = (vinti / totali * 100) if totali > 0 else 0
            st.metric("Win Rate", f"{wr:.0f}%")

        # Table
        rows_data = []
        for f in forecasts:
            rows_data.append({
                "ID": f["id"],
                "Cliente": f["cliente_nome"],
                "Attore": f["attore_nome"] or "N/A",
                "Progetto": f["nome_progetto"],
                "Tipologia": f["tipologia"],
                "Budget €": f["budget"],
                "Costi €": f["costi_previsti"],
                "Margine %": f["marginalita_attesa"],
                "Win %": f["win_probability"],
                "Valore Pesato €": round(f["budget"] * (f["win_probability"] or 0) / 100, 2),
                "Stato": f["stato"],
            })

        df = pd.DataFrame(rows_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Budget €": st.column_config.NumberColumn(format="€%.0f"),
                "Costi €": st.column_config.NumberColumn(format="€%.0f"),
                "Margine %": st.column_config.NumberColumn(format="%.0f%%"),
                "Win %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
                "Valore Pesato €": st.column_config.NumberColumn(format="€%.0f"),
            },
        )
    else:
        st.info("Nessuna opportunità nel forecast. Aggiungine una qui sotto.")

    st.markdown("---")

    # ─── AZIONI ───
    tab1, tab2, tab3 = st.tabs(["➕ Nuova Opportunità", "✏️ Modifica Stato", "🗑️ Elimina"])

    with tab1:
        with st.form("new_forecast", clear_on_submit=True):
            st.markdown("### Nuova Opportunità")
            col1, col2 = st.columns(2)
            with col1:
                cliente_sel = st.selectbox("Cliente", options=[c["id"] for c in clienti],
                                           format_func=lambda x: client_map.get(x, ""))
                attore_sel = st.selectbox("Attore / Owner", options=[a["id"] for a in attori],
                                          format_func=lambda x: attori_map.get(x, ""))
                nome_progetto = st.text_input("Nome Progetto")
                tipologia = st.selectbox("Tipologia", [e.value for e in CentroRicavoCosto])
                budget = st.number_input("Budget (€)", min_value=0.0, step=1000.0)
            with col2:
                costi = st.number_input("Costi Previsti (€)", min_value=0.0, step=1000.0)
                margine = st.number_input("Marginalità Attesa (%)", min_value=0.0, max_value=100.0, value=30.0)
                wp = st.slider("Win Probability (%)", 0, 100, 20)
                stato_init = st.selectbox("Stato Iniziale", ["Forecast", "Opportunità"])

            st.markdown("### Pianificazione Finanziaria")
            split_fatt = st.text_input(
                "Split Fatturazione (formato JSON)",
                value="{}",
                placeholder='Es: {"2025-06": 50000, "2025-09": 50000}',
                help='Inserisci un JSON con le mensilità (YYYY-MM). Esempio: {"2025-06": 50000, "2025-09": 50000}'
            )
            split_cost = st.text_input(
                "Split Costi (formato JSON)",
                value="{}",
                placeholder='Es: {"2025-06": 10000}',
                help='Inserisci un JSON con i costi per mensilità. Esempio: {"2025-06": 10000}'
            )

            submitted = st.form_submit_button("💾 Salva Opportunità", use_container_width=True)
            if submitted and nome_progetto:
                try:
                    json.loads(split_fatt)
                    json.loads(split_cost)
                except json.JSONDecodeError:
                    st.error("JSON non valido per gli split.")
                else:
                    insert_row("forecast", {
                        "cliente_id": cliente_sel,
                        "attore_id": attore_sel,
                        "nome_progetto": nome_progetto,
                        "tipologia": tipologia,
                        "budget": budget,
                        "costi_previsti": costi,
                        "marginalita_attesa": margine,
                        "win_probability": wp,
                        "stato": stato_init,
                        "split_fatturazione": split_fatt,
                        "split_costi": split_cost,
                    })
                    st.success(f"✅ Opportunità '{nome_progetto}' salvata!")
                    st.rerun()

    with tab2:
        if forecasts:
            attive = [f for f in forecasts if f["stato"] in ("Forecast", "Opportunità")]
            if attive:
                sel = st.selectbox(
                    "Seleziona opportunità",
                    options=[f["id"] for f in attive],
                    format_func=lambda x: next(f"{f['cliente_nome']} — {f['nome_progetto']} [{f['stato']}]"
                                                for f in attive if f["id"] == x),
                    key="mod_stato_sel",
                )
                sel_forecast = next(f for f in attive if f["id"] == sel)
                stato_corrente = StatoForecast(sel_forecast["stato"])
                transizioni = stato_corrente.transizioni_valide().get(stato_corrente, [])

                if transizioni:
                    nuovo_stato = st.selectbox("Nuovo Stato", [t.value for t in transizioni])

                    col1, col2 = st.columns(2)
                    with col1:
                        new_wp = st.slider("Aggiorna Win %", 0, 100,
                                           int(sel_forecast["win_probability"]), key="upd_wp")

                    if st.button("🔄 Aggiorna Stato", use_container_width=True):
                        update_row("forecast", sel, {"stato": nuovo_stato, "win_probability": new_wp})

                        # Se Chiuso Vinto → genera righe in Ciclo Attivo
                        if nuovo_stato == "Chiuso Vinto":
                            split_fatt = json.loads(sel_forecast["split_fatturazione"] or "{}")
                            for mese_key, importo in split_fatt.items():
                                insert_row("ciclo_attivo", {
                                    "cliente_id": sel_forecast["cliente_id"],
                                    "forecast_id": sel_forecast["id"],
                                    "centro_ricavo": sel_forecast["tipologia"],
                                    "dettaglio_ricavo": f"{sel_forecast['nome_progetto']} — {mese_key}",
                                    "progetto": sel_forecast["nome_progetto"],
                                    "importo_netto": importo,
                                    "iva_pct": sel_forecast["iva_pct"] or 22,
                                    "data_fattura": f"{mese_key}-15",
                                    "mesi_dilazione": 1,
                                    "data_incasso_prevista": None,  # Will be calculated
                                    "stato": "Previsionale",
                                })
                            st.success(f"✅ Stato aggiornato a '{nuovo_stato}'. Righe generate nel Ciclo Attivo!")
                        else:
                            st.success(f"✅ Stato aggiornato a '{nuovo_stato}'.")
                        st.rerun()
                else:
                    st.info("Questa opportunità è in uno stato finale.")
            else:
                st.info("Nessuna opportunità modificabile.")

    with tab3:
        if forecasts:
            del_sel = st.selectbox(
                "Seleziona opportunità da eliminare",
                options=[f["id"] for f in forecasts],
                format_func=lambda x: next(f"{f['cliente_nome']} — {f['nome_progetto']}"
                                            for f in forecasts if f["id"] == x),
                key="del_forecast_sel",
            )
            if st.button("🗑️ Elimina", type="secondary", use_container_width=True):
                delete_row("forecast", del_sel)
                st.success("Opportunità eliminata.")
                st.rerun()
