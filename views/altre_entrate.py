"""
pages/altre_entrate.py — Gestione Altre Entrate (ricavi non da clienti).
"""
import streamlit as st
import pandas as pd
from database import get_db, insert_row, update_row, delete_row
from models import StatoPagamento, calcola_mese_incasso
from datetime import date


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 💵 Altre Entrate")
    st.markdown(f"*Entrate extra non legate a progetti {anno}*")
    st.markdown("---")

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM altre_entrate
            WHERE data_fattura IS NOT NULL
              AND CAST(substr(data_fattura, 1, 4) AS INTEGER) = ?
            ORDER BY data_fattura
        """, [anno]).fetchall()

    # Metriche
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale", f"€{sum(r['importo_netto'] for r in rows):,.0f}")
    with col2:
        st.metric("Incassato", f"€{sum(r['importo_netto'] for r in rows if r['stato'] == 'Saldato'):,.0f}")
    with col3:
        st.metric("Da Incassare", f"€{sum(r['importo_netto'] for r in rows if r['stato'] != 'Saldato'):,.0f}")

    # Table
    if rows:
        data = [{
            "ID": r["id"],
            "Descrizione": r["descrizione"],
            "Netto €": r["importo_netto"],
            "IVA %": r["iva_pct"],
            "Lordo €": r["importo_lordo"],
            "Data": r["data_fattura"],
            "Incasso Previsto": r["data_incasso_prevista"] or "—",
            "Stato": r["stato"],
        } for r in rows]
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "Netto €": st.column_config.NumberColumn(format="€%.0f"),
                         "Lordo €": st.column_config.NumberColumn(format="€%.0f"),
                     })

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["➕ Nuova Entrata", "✏️ Aggiorna Stato", "🗑️ Elimina"])

    with tab1:
        with st.form("new_ae", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                desc = st.text_input("Descrizione")
                importo = st.number_input("Importo Netto (€)", min_value=0.0, step=100.0)
            with col2:
                iva = st.number_input("IVA (%)", min_value=0.0, value=0.0)
                data_fatt = st.date_input("Data", value=date.today())
                dilazione = st.number_input("Mesi Dilazione", min_value=0, max_value=12, value=0)

            if st.form_submit_button("💾 Salva", use_container_width=True):
                if desc:
                    data_inc = calcola_mese_incasso(data_fatt, dilazione)
                    insert_row("altre_entrate", {
                        "descrizione": desc,
                        "importo_netto": importo,
                        "iva_pct": iva,
                        "data_fattura": data_fatt.isoformat(),
                        "mesi_dilazione": dilazione,
                        "data_incasso_prevista": data_inc.isoformat(),
                        "stato": "Previsionale",
                    })
                    st.success("✅ Entrata salvata!")
                    st.rerun()

    with tab2:
        if rows:
            sel = st.selectbox("Seleziona entrata",
                               [r["id"] for r in rows],
                               format_func=lambda x: next(f"[{r['stato']}] {r['descrizione']}" for r in rows if r["id"] == x),
                               key="upd_ae_sel")
            sel_row = next(r for r in rows if r["id"] == sel)
            stato = StatoPagamento(sel_row["stato"])
            trans = stato.transizioni_valide().get(stato, [])
            if trans:
                nuovo = st.selectbox("Nuovo Stato", [t.value for t in trans], key="upd_ae_stato")
                if st.button("🔄 Aggiorna", use_container_width=True, key="btn_upd_ae"):
                    update_row("altre_entrate", sel, {"stato": nuovo})
                    st.success(f"✅ Aggiornato a '{nuovo}'.")
                    st.rerun()
            else:
                st.info("Stato finale.")

    with tab3:
        if rows:
            del_sel = st.selectbox("Seleziona da eliminare",
                                   [r["id"] for r in rows],
                                   format_func=lambda x: next(r["descrizione"] for r in rows if r["id"] == x),
                                   key="del_ae_sel")
            if st.button("🗑️ Elimina", type="secondary", use_container_width=True, key="btn_del_ae"):
                delete_row("altre_entrate", del_sel)
                st.success("Eliminato.")
                st.rerun()
