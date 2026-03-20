"""
pages/costi_indiretti.py — Gestione Costi Indiretti (Overhead).
8 categorie con input mensile.
"""
import streamlit as st
import pandas as pd
from database import get_db, insert_row, delete_row
from models import CategoriaIndiretti


CATEGORIA_ICON = {
    "D. Personale": "👤",
    "D. Sedi Operative": "🏢",
    "D. Commerciale e Marketing": "📢",
    "D. Servizi Professionali": "⚖️",
    "D. Spese Operative": "📋",
    "F. Licenze, Software, HW": "💻",
    "H. Oneri Finanziari": "🏦",
    "L. Imposte e Tasse": "📊",
}

MESI = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 🏢 Costi Indiretti — Overhead")
    st.markdown(f"*Costi di struttura {anno}*")
    st.markdown("---")

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM costi_indiretti
            WHERE anno = ?
            ORDER BY categoria, sottocategoria, mese
        """, [anno]).fetchall()

    # ─── RIEPILOGO PER CATEGORIA ───
    totali_cat = {}
    for cat in CategoriaIndiretti:
        cat_rows = [r for r in rows if r["categoria"] == cat.value]
        totale = sum(r["importo_netto"] for r in cat_rows)
        totali_cat[cat.value] = totale

    totale_generale = sum(totali_cat.values())
    media_mensile = totale_generale / 12 if totale_generale > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale Annuo", f"€{totale_generale:,.0f}")
    with col2:
        st.metric("Media Mensile", f"€{media_mensile:,.0f}")
    with col3:
        st.metric("Categorie Attive", f"{sum(1 for v in totali_cat.values() if v > 0)}")

    st.markdown("---")

    # ─── TAB PER CATEGORIA ───
    tab_labels = [f"{CATEGORIA_ICON.get(cat.value, '')} {cat.value}" for cat in CategoriaIndiretti]
    tabs = st.tabs(tab_labels)

    for i, cat in enumerate(CategoriaIndiretti):
        with tabs[i]:
            cat_rows = [r for r in rows if r["categoria"] == cat.value]

            if cat_rows:
                # Pivot: sottocategoria × mese
                sottocategorie = sorted(set(r["sottocategoria"] for r in cat_rows))
                pivot_data = []
                for sotto in sottocategorie:
                    row_data = {"Sottocategoria": sotto}
                    for m in range(1, 13):
                        val = sum(r["importo_netto"] for r in cat_rows
                                  if r["sottocategoria"] == sotto and r["mese"] == m)
                        row_data[MESI[m-1]] = val
                    row_data["TOTALE"] = sum(row_data[MESI[m-1]] for m in range(1, 13))
                    pivot_data.append(row_data)

                # Riga totale
                totale_row = {"Sottocategoria": "TOTALE"}
                for m in range(1, 13):
                    totale_row[MESI[m-1]] = sum(d[MESI[m-1]] for d in pivot_data)
                totale_row["TOTALE"] = sum(totale_row[MESI[m-1]] for m in range(1, 13))
                pivot_data.append(totale_row)

                df = pd.DataFrame(pivot_data)
                col_config = {MESI[m-1]: st.column_config.NumberColumn(format="€%.0f") for m in range(1, 13)}
                col_config["TOTALE"] = st.column_config.NumberColumn(format="€%.0f")
                st.dataframe(df, use_container_width=True, hide_index=True, column_config=col_config)
            else:
                st.info(f"Nessun costo per {cat.value}.")

            # Form per aggiungere
            with st.expander("➕ Aggiungi costo"):
                with st.form(f"add_ci_{cat.value}", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        sotto = st.text_input("Sottocategoria", key=f"ci_sotto_{cat.value}")
                        importo = st.number_input("Importo Netto (€/mese)", min_value=0.0, step=100.0,
                                                  key=f"ci_imp_{cat.value}")
                    with col2:
                        iva = st.number_input("IVA (%)", min_value=0.0, value=22.0 if "Personale" not in cat.value and "Imposte" not in cat.value and "Oneri" not in cat.value else 0.0,
                                              key=f"ci_iva_{cat.value}")
                        ricorrente = st.checkbox("Ricorrente (tutti i mesi)", value=True, key=f"ci_ric_{cat.value}")

                    if not ricorrente:
                        mese_sel = st.selectbox("Mese", list(range(1, 13)),
                                                format_func=lambda x: MESI[x-1],
                                                key=f"ci_mese_{cat.value}")
                    else:
                        mese_sel = None

                    if st.form_submit_button("💾 Salva", use_container_width=True):
                        if sotto and importo > 0:
                            mesi_to_insert = list(range(1, 13)) if ricorrente else [mese_sel]
                            for m in mesi_to_insert:
                                insert_row("costi_indiretti", {
                                    "categoria": cat.value,
                                    "sottocategoria": sotto,
                                    "importo_netto": importo,
                                    "iva_pct": iva,
                                    "anno": anno,
                                    "mese": m,
                                    "ricorrente": 1 if ricorrente else 0,
                                })
                            st.success(f"✅ Costo aggiunto per {'tutti i mesi' if ricorrente else MESI[mese_sel-1]}!")
                            st.rerun()
