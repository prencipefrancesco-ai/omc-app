"""
pages/ciclo_passivo.py — Gestione Ciclo Passivo (Costi Fornitori).
"""
import streamlit as st
import pandas as pd
from database import get_db, insert_row, update_row, delete_row
from models import StatoPagamento, CentroRicavoCosto, calcola_mese_incasso
from datetime import date


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 📤 Ciclo Passivo — Costi Fornitori")
    st.markdown(f"*Gestione pagamenti e fatture ricevute {anno}*")
    st.markdown("---")

    with get_db() as conn:
        clienti = conn.execute("SELECT * FROM clienti WHERE attivo = 1 ORDER BY nome").fetchall()
        rows = conn.execute("""
            SELECT cp.*, c.nome as cliente_nome
            FROM ciclo_passivo cp
            JOIN clienti c ON cp.cliente_id = c.id
            WHERE cp.data_fattura IS NOT NULL
              AND CAST(substr(cp.data_fattura, 1, 4) AS INTEGER) = ?
            ORDER BY cp.data_fattura
        """, [anno]).fetchall()

    client_map = {c["id"]: c["nome"] for c in clienti}

    # Filtro
    filtro_cliente = st.selectbox("Filtra per cliente", ["Tutti"] + [c["nome"] for c in clienti], key="cp_filter")
    if filtro_cliente != "Tutti":
        rows = [r for r in rows if r["cliente_nome"] == filtro_cliente]

    # Metriche
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Totale Costi Netto", f"€{sum(r['importo_netto'] for r in rows):,.0f}")
    with col2:
        st.metric("Pagati", f"€{sum(r['importo_netto'] for r in rows if r['stato'] == 'Saldato'):,.0f}")
    with col3:
        st.metric("Fatturati (da pagare)", f"€{sum(r['importo_netto'] for r in rows if r['stato'] == 'Fatturato'):,.0f}")
    with col4:
        st.metric("Previsti/Confermati", f"€{sum(r['importo_netto'] for r in rows if r['stato'] in ('Previsionale', 'Confermato')):,.0f}")

    # Table
    if rows:
        data = []
        for r in rows:
            data.append({
                "ID": r["id"],
                "Cliente (Progetto)": r["cliente_nome"],
                "Dettaglio": r["dettaglio_costo"],
                "Fornitore": r["fornitore"] or "—",
                "Centro Costo": r["centro_costo"],
                "Netto €": r["importo_netto"],
                "IVA %": r["iva_pct"],
                "Lordo €": r["importo_lordo"],
                "Data Fattura": r["data_fattura"],
                "Dilazione": f"{r['mesi_dilazione']} mesi",
                "Data Pagamento": r["data_pagamento_prevista"] or "—",
                "Stato": r["stato"],
                "N. Fattura": r["numero_fattura"] or "—",
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "Netto €": st.column_config.NumberColumn(format="€%.0f"),
                         "Lordo €": st.column_config.NumberColumn(format="€%.0f"),
                     })
    else:
        st.info("Nessun costo passivo per questo periodo.")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["➕ Nuovo Costo", "✏️ Aggiorna Stato", "🗑️ Elimina"])

    with tab1:
        with st.form("new_passivo", clear_on_submit=True):
            st.markdown("### Nuovo Costo Fornitore")
            col1, col2 = st.columns(2)
            with col1:
                cliente_sel = st.selectbox("Cliente/Progetto", [c["id"] for c in clienti],
                                           format_func=lambda x: client_map.get(x, ""), key="cp_cliente")
                centro = st.selectbox("Centro Costo", [e.value for e in CentroRicavoCosto], key="cp_centro")
                dettaglio = st.text_input("Dettaglio Costo", key="cp_dettaglio")
                fornitore = st.text_input("Fornitore", key="cp_fornitore")
            with col2:
                importo = st.number_input("Importo Netto (€)", min_value=0.0, step=100.0, key="cp_importo")
                iva = st.number_input("IVA (%)", min_value=0.0, max_value=100.0, value=22.0, key="cp_iva")
                data_fatt = st.date_input("Data Fattura", value=date.today(), key="cp_data")
                dilazione = st.number_input("Mesi Dilazione", min_value=0, max_value=12, value=1, key="cp_dil")

            submitted = st.form_submit_button("💾 Salva", use_container_width=True)
            if submitted and dettaglio:
                data_pag = calcola_mese_incasso(data_fatt, dilazione)
                insert_row("ciclo_passivo", {
                    "cliente_id": cliente_sel,
                    "centro_costo": centro,
                    "dettaglio_costo": dettaglio,
                    "fornitore": fornitore,
                    "importo_netto": importo,
                    "iva_pct": iva,
                    "data_fattura": data_fatt.isoformat(),
                    "mesi_dilazione": dilazione,
                    "data_pagamento_prevista": data_pag.isoformat(),
                    "stato": "Previsionale",
                })
                st.success("✅ Costo salvato!")
                st.rerun()

    with tab2:
        if rows:
            sel = st.selectbox(
                "Seleziona costo",
                [r["id"] for r in rows],
                format_func=lambda x: next(
                    f"[{r['stato']}] {r['fornitore'] or r['cliente_nome']} — {r['dettaglio_costo']} (€{r['importo_netto']:,.0f})"
                    for r in rows if r["id"] == x
                ),
                key="upd_cp_sel",
            )
            sel_row = next(r for r in rows if r["id"] == sel)
            stato_corrente = StatoPagamento(sel_row["stato"])
            transizioni = stato_corrente.transizioni_valide().get(stato_corrente, [])

            if transizioni:
                col1, col2 = st.columns(2)
                with col1:
                    nuovo_stato = st.selectbox("Nuovo Stato", [t.value for t in transizioni], key="upd_cp_stato")
                with col2:
                    num_fatt = st.text_input("N. Fattura Fornitore", value=sel_row["numero_fattura"] or "", key="upd_cp_nf")

                if st.button("🔄 Aggiorna", use_container_width=True, key="btn_upd_cp"):
                    data = {"stato": nuovo_stato}
                    if num_fatt:
                        data["numero_fattura"] = num_fatt
                    update_row("ciclo_passivo", sel, data)
                    st.success(f"✅ Stato aggiornato a '{nuovo_stato}'.")
                    st.rerun()
            else:
                st.info("Stato finale raggiunto.")

    with tab3:
        if rows:
            del_sel = st.selectbox(
                "Seleziona da eliminare",
                [r["id"] for r in rows],
                format_func=lambda x: next(
                    f"{r['fornitore'] or r['cliente_nome']} — {r['dettaglio_costo']}"
                    for r in rows if r["id"] == x
                ),
                key="del_cp_sel",
            )
            if st.button("🗑️ Elimina", type="secondary", use_container_width=True, key="btn_del_cp"):
                delete_row("ciclo_passivo", del_sel)
                st.success("Eliminato.")
                st.rerun()
