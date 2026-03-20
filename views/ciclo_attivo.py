"""
pages/ciclo_attivo.py — Gestione Ciclo Attivo (Fatturazione).
Per-client invoice tracking con gestione stati.
"""
import streamlit as st
import pandas as pd
from database import get_db, insert_row, update_row, delete_row
from models import StatoPagamento, CentroRicavoCosto, calcola_mese_incasso
from datetime import date


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 📥 Ciclo Attivo — Fatturazione")
    st.markdown(f"*Gestione incassi e fatture emesse {anno}*")
    st.markdown("---")

    with get_db() as conn:
        clienti = conn.execute("SELECT * FROM clienti WHERE attivo = 1 ORDER BY nome").fetchall()
        rows = conn.execute("""
            SELECT ca.*, c.nome as cliente_nome
            FROM ciclo_attivo ca
            JOIN clienti c ON ca.cliente_id = c.id
            WHERE ca.data_fattura IS NOT NULL
              AND CAST(substr(ca.data_fattura, 1, 4) AS INTEGER) = ?
            ORDER BY ca.data_fattura
        """, [anno]).fetchall()

    client_map = {c["id"]: c["nome"] for c in clienti}

    # ─── FILTRO CLIENTE ───
    filtro_cliente = st.selectbox(
        "Filtra per cliente",
        options=["Tutti"] + [c["nome"] for c in clienti],
    )
    if filtro_cliente != "Tutti":
        rows = [r for r in rows if r["cliente_nome"] == filtro_cliente]

    # ─── METRICHE ───
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        tot = sum(r["importo_netto"] for r in rows)
        st.metric("Totale Netto", f"€{tot:,.0f}")
    with col2:
        saldato = sum(r["importo_netto"] for r in rows if r["stato"] == "Saldato")
        st.metric("Incassato", f"€{saldato:,.0f}")
    with col3:
        fatturato = sum(r["importo_netto"] for r in rows if r["stato"] == "Fatturato")
        st.metric("Fatturato (da incassare)", f"€{fatturato:,.0f}")
    with col4:
        prev = sum(r["importo_netto"] for r in rows if r["stato"] in ("Previsionale", "Confermato"))
        st.metric("Previsto/Confermato", f"€{prev:,.0f}")

    # ─── TABELLA ───
    if rows:
        data = []
        for r in rows:
            data.append({
                "ID": r["id"],
                "Cliente": r["cliente_nome"],
                "Dettaglio": r["dettaglio_ricavo"],
                "Centro Ricavo": r["centro_ricavo"],
                "Netto €": r["importo_netto"],
                "IVA %": r["iva_pct"],
                "Lordo €": r["importo_lordo"],
                "Data Fattura": r["data_fattura"],
                "Dilazione": f"{r['mesi_dilazione']} mesi",
                "Data Incasso": r["data_incasso_prevista"] or "—",
                "Stato": r["stato"],
                "N. Fattura": r["numero_fattura"] or "—",
            })

        df = pd.DataFrame(data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Netto €": st.column_config.NumberColumn(format="€%.0f"),
                "Lordo €": st.column_config.NumberColumn(format="€%.0f"),
                "IVA %": st.column_config.NumberColumn(format="%.0f%%"),
            },
        )
    else:
        st.info("Nessuna fattura attiva per questo periodo/cliente.")

    st.markdown("---")

    # ─── AZIONI ───
    tab1, tab2, tab3 = st.tabs(["➕ Nuova Fattura", "✏️ Aggiorna Stato", "🗑️ Elimina"])

    with tab1:
        with st.form("new_attivo", clear_on_submit=True):
            st.markdown("### Nuova Riga Ciclo Attivo")
            col1, col2 = st.columns(2)
            with col1:
                cliente_sel = st.selectbox("Cliente", [c["id"] for c in clienti],
                                           format_func=lambda x: client_map.get(x, ""), key="ca_cliente")
                centro = st.selectbox("Centro Ricavo", [e.value for e in CentroRicavoCosto], key="ca_centro")
                dettaglio = st.text_input("Dettaglio Ricavo", key="ca_dettaglio")
                progetto = st.text_input("Progetto", key="ca_progetto")
            with col2:
                importo = st.number_input("Importo Netto (€)", min_value=0.0, step=100.0, key="ca_importo")
                iva = st.number_input("IVA (%)", min_value=0.0, max_value=100.0, value=22.0, key="ca_iva")
                data_fatt = st.date_input("Data Fattura", value=date.today(), key="ca_data")
                dilazione = st.number_input("Mesi Dilazione", min_value=0, max_value=12, value=1, key="ca_dil")

            submitted = st.form_submit_button("💾 Salva", use_container_width=True)
            if submitted and dettaglio:
                data_inc = calcola_mese_incasso(data_fatt, dilazione)
                insert_row("ciclo_attivo", {
                    "cliente_id": cliente_sel,
                    "centro_ricavo": centro,
                    "dettaglio_ricavo": dettaglio,
                    "progetto": progetto,
                    "importo_netto": importo,
                    "iva_pct": iva,
                    "data_fattura": data_fatt.isoformat(),
                    "mesi_dilazione": dilazione,
                    "data_incasso_prevista": data_inc.isoformat(),
                    "stato": "Previsionale",
                })
                st.success("✅ Riga salvata!")
                st.rerun()

    with tab2:
        if rows:
            sel = st.selectbox(
                "Seleziona fattura",
                [r["id"] for r in rows],
                format_func=lambda x: next(
                    f"[{r['stato']}] {r['cliente_nome']} — {r['dettaglio_ricavo']} (€{r['importo_netto']:,.0f})"
                    for r in rows if r["id"] == x
                ),
                key="upd_ca_sel",
            )
            sel_row = next(r for r in rows if r["id"] == sel)
            stato_corrente = StatoPagamento(sel_row["stato"])
            transizioni = stato_corrente.transizioni_valide().get(stato_corrente, [])

            if transizioni:
                col1, col2 = st.columns(2)
                with col1:
                    nuovo_stato = st.selectbox("Nuovo Stato", [t.value for t in transizioni], key="upd_ca_stato")
                with col2:
                    num_fatt = st.text_input("Numero Fattura (opzionale)", value=sel_row["numero_fattura"] or "", key="upd_ca_nf")

                if st.button("🔄 Aggiorna", use_container_width=True, key="btn_upd_ca"):
                    data = {"stato": nuovo_stato}
                    if num_fatt:
                        data["numero_fattura"] = num_fatt
                    update_row("ciclo_attivo", sel, data)
                    st.success(f"✅ Stato aggiornato a '{nuovo_stato}'.")
                    st.rerun()
            else:
                st.info("Questa fattura è in stato finale (Saldato).")

    with tab3:
        if rows:
            del_sel = st.selectbox(
                "Seleziona da eliminare",
                [r["id"] for r in rows],
                format_func=lambda x: next(
                    f"{r['cliente_nome']} — {r['dettaglio_ricavo']}"
                    for r in rows if r["id"] == x
                ),
                key="del_ca_sel",
            )
            if st.button("🗑️ Elimina", type="secondary", use_container_width=True, key="btn_del_ca"):
                delete_row("ciclo_attivo", del_sel)
                st.success("Riga eliminata.")
                st.rerun()
