"""
views/attori.py — Gestione Attori (Proprietari Forecast).
CRUD operations for 'attori' table.
"""
import streamlit as st
import pandas as pd
from database import get_db, insert_row, update_row, delete_row

def render():
    st.markdown("# 👥 Gestione Attori")
    st.markdown("*Gestione assegnatari per le opportunità a Forecast*")
    st.markdown("---")

    # Load actors
    with get_db() as conn:
        attori = conn.execute("SELECT * FROM attori ORDER BY nome").fetchall()
    
    # --- TABLE ---
    if attori:
        st.markdown('<div class="section-header">Elenco Attori</div>', unsafe_allow_html=True)
        
        rows_data = []
        for a in attori:
            rows_data.append({
                "ID": a["id"],
                "Nome": a["nome"],
                "Ruolo": a["ruolo"] or "-",
                "Attivo": "Sì" if a["attivo"] == 1 else "No",
            })
        
        df = pd.DataFrame(rows_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nessun attore presente nel sistema. Aggiungine uno qui sotto.")

    st.markdown("---")

    # --- ACTIONS ---
    tab1, tab2, tab3 = st.tabs(["➕ Nuovo Attore", "✏️ Modifica", "🗑️ Elimina"])

    with tab1:
        with st.form("new_actor", clear_on_submit=True):
            st.markdown("### Aggiungi Attore")
            nome = st.text_input("Nome")
            ruolo = st.text_input("Ruolo (opzionale)")
            attivo = st.checkbox("Attivo", value=True)
            
            submitted = st.form_submit_button("💾 Salva", use_container_width=True)
            if submitted and nome:
                # Check for uniqueness
                if any(a["nome"].lower() == nome.lower() for a in attori):
                    st.error(f"Errore: Esiste già un attore con il nome '{nome}'.")
                else:
                    insert_row("attori", {
                        "nome": nome,
                        "ruolo": ruolo,
                        "attivo": 1 if attivo else 0
                    })
                    st.success(f"✅ Attore '{nome}' aggiunto con successo!")
                    st.rerun()

    with tab2:
        if attori:
            sel_id = st.selectbox(
                "Seleziona Attore",
                options=[a["id"] for a in attori],
                format_func=lambda x: next(a["nome"] for a in attori if a["id"] == x),
                key="mod_actor_sel"
            )
            actor_to_mod = next(a for a in attori if a["id"] == sel_id)
            
            with st.form("mod_actor"):
                st.markdown("### Modifica Attore")
                nuovo_nome = st.text_input("Nome", value=actor_to_mod["nome"])
                nuovo_ruolo = st.text_input("Ruolo (opzionale)", value=actor_to_mod["ruolo"] or "")
                nuovo_attivo = st.checkbox("Attivo", value=bool(actor_to_mod["attivo"]))
                
                submitted = st.form_submit_button("🔄 Aggiorna", use_container_width=True)
                if submitted and nuovo_nome:
                    if nuovo_nome.lower() != actor_to_mod["nome"].lower() and any(a["nome"].lower() == nuovo_nome.lower() for a in attori):
                        st.error(f"Errore: Esiste già un attore con il nome '{nuovo_nome}'.")
                    else:
                        update_row("attori", sel_id, {
                            "nome": nuovo_nome,
                            "ruolo": nuovo_ruolo,
                            "attivo": 1 if nuovo_attivo else 0
                        })
                        st.success(f"✅ Attore aggiornato!")
                        st.rerun()
        else:
            st.info("Nessun attore modificabile.")

    with tab3:
        if attori:
            del_id = st.selectbox(
                "Seleziona Attore da Eliminare",
                options=[a["id"] for a in attori],
                format_func=lambda x: next(a["nome"] for a in attori if a["id"] == x),
                key="del_actor_sel"
            )
            st.warning("⚠️ Attenzione: Se l'attore è assegnato a un Forecast, l'eliminazione fallirà (vincolo di sicurezza). Si consiglia, in quel caso, di impostarlo come 'Non attivo' anziché eliminarlo.")
            if st.button("🗑️ Elimina", type="primary", use_container_width=True):
                try:
                    delete_row("attori", del_id)
                    st.success("Attore eliminato.")
                    st.rerun()
                except Exception as e:
                    if "FOREIGN KEY constraint failed" in str(e):
                        st.error("❌ Impossibile eliminare l'attore: è attualmente assegnato a uno o più Forecast. Ti consigliamo di modificarlo e deselezionare la spunta 'Attivo'.")
                    else:
                        st.error(f"❌ Errore durante l'eliminazione: {e}")
