"""
pages/analisi_clienti.py — Analisi Marginalità per Cliente e Progetto.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from execution.margin_analysis import analisi_margini


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 👥 Analisi Clienti")
    st.markdown(f"*Marginalità e profittabilità {anno}*")
    st.markdown("---")

    margini = analisi_margini(anno)

    # ─── KPI ───
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ricavi Totali", f"€{margini['totale_ricavi']:,.0f}")
    with col2:
        st.metric("Costi Diretti", f"€{margini['totale_costi_diretti']:,.0f}")
    with col3:
        st.metric("Margine Lordo", f"€{margini['totale_margine_lordo']:,.0f}")
    with col4:
        st.metric("EBITDA", f"€{margini['ebitda']:,.0f}")

    st.markdown("---")

    # ─── RANKING CLIENTI ───
    st.markdown('<div class="section-header">🏆 Ranking Clienti per Profittabilità</div>', unsafe_allow_html=True)

    if margini["clienti"]:
        clienti_attivi = [c for c in margini["clienti"] if c["ricavi"] > 0]

        if clienti_attivi:
            # Chart
            fig = go.Figure()
            nomi = [c["nome"] for c in clienti_attivi]
            ricavi = [c["ricavi"] for c in clienti_attivi]
            costi = [c["costi_diretti"] for c in clienti_attivi]
            margini_vals = [c["margine_lordo"] for c in clienti_attivi]

            fig.add_trace(go.Bar(
                x=nomi, y=ricavi,
                name="Ricavi", marker_color="#10b981",
            ))
            fig.add_trace(go.Bar(
                x=nomi, y=costi,
                name="Costi Diretti", marker_color="#ef4444",
            ))
            fig.add_trace(go.Scatter(
                x=nomi, y=margini_vals,
                name="Margine Lordo", mode="lines+markers+text",
                line=dict(color="#6366f1", width=3),
                marker=dict(size=10),
                text=[f"€{m:,.0f}" for m in margini_vals],
                textposition="top center",
                textfont=dict(size=11, color="#6366f1"),
            ))

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=400,
                barmode="group",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", y=1.08),
                yaxis=dict(gridcolor="rgba(99,102,241,0.1)", tickformat="€,.0f"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Table
            df_clienti = pd.DataFrame(clienti_attivi)
            df_clienti = df_clienti.rename(columns={
                "nome": "Cliente",
                "ricavi": "Ricavi €",
                "costi_diretti": "Costi Diretti €",
                "margine_lordo": "Margine Lordo €",
                "marginalita_pct": "Marginalità %",
            })
            df_clienti = df_clienti.drop(columns=["id"], errors="ignore")

            st.dataframe(
                df_clienti,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ricavi €": st.column_config.NumberColumn(format="€%.0f"),
                    "Costi Diretti €": st.column_config.NumberColumn(format="€%.0f"),
                    "Margine Lordo €": st.column_config.NumberColumn(format="€%.0f"),
                    "Marginalità %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                },
            )

            # Donut chart — distribuzione ricavi
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="section-header">📊 Distribuzione Ricavi</div>', unsafe_allow_html=True)
                fig_donut = go.Figure(data=[go.Pie(
                    labels=nomi, values=ricavi,
                    hole=0.55,
                    marker=dict(colors=["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#94a3b8"]),
                    textinfo="label+percent",
                )])
                fig_donut.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col2:
                st.markdown('<div class="section-header">📊 Distribuzione Margini</div>', unsafe_allow_html=True)
                fig_marg = go.Figure(data=[go.Pie(
                    labels=nomi,
                    values=[max(0, m) for m in margini_vals],
                    hole=0.55,
                    marker=dict(colors=["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#94a3b8"]),
                    textinfo="label+percent",
                )])
                fig_marg.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_marg, use_container_width=True)
        else:
            st.info("Nessun cliente con ricavi nel periodo selezionato.")

    # ─── ANALISI PROGETTI ───
    st.markdown("---")
    st.markdown('<div class="section-header">📁 Analisi per Progetto</div>', unsafe_allow_html=True)

    if margini["progetti"]:
        df_proj = pd.DataFrame(margini["progetti"])
        df_proj = df_proj.rename(columns={
            "progetto": "Progetto",
            "cliente": "Cliente",
            "ricavi": "Ricavi €",
            "costi": "Costi €",
            "margine": "Margine €",
            "marginalita_pct": "Marginalità %",
        })
        st.dataframe(
            df_proj,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ricavi €": st.column_config.NumberColumn(format="€%.0f"),
                "Costi €": st.column_config.NumberColumn(format="€%.0f"),
                "Margine €": st.column_config.NumberColumn(format="€%.0f"),
                "Marginalità %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            },
        )
    else:
        st.info("Nessun progetto con dati nel periodo.")

    # Summary box
    st.markdown("---")
    st.markdown(f"""
    ### 📊 Riepilogo {anno}
    | Voce | Importo |
    |------|---------|
    | **Ricavi Totali** | €{margini['totale_ricavi']:,.0f} |
    | **Costi Diretti** | €{margini['totale_costi_diretti']:,.0f} |
    | **Margine Lordo** | €{margini['totale_margine_lordo']:,.0f} ({margini['marginalita_media']:.1f}%) |
    | **Costi Indiretti** | €{margini['costi_indiretti']:,.0f} |
    | **EBITDA** | €{margini['ebitda']:,.0f} |
    """)
