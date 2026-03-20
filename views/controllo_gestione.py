"""
pages/controllo_gestione.py — Controllo di Gestione con 5 tab:
1. Dettaglio CF (Cashflow aggregato)
2. Stima IVA Trimestrale
3. Dettaglio R&C (Ricavi e Costi per competenza)
4. P&L (Conto Economico A→M)
5. Grafico Cashflow Multi-Scenario
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from execution.calc_cashflow import calcola_cashflow
from execution.pnl_engine import calcola_pnl
from execution.iva_engine import calcola_iva_trimestrale

MESI = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']


def format_row(label, values, bold=False):
    """Create a row dict for a P&L table."""
    row = {"Voce": f"**{label}**" if bold else label}
    for i, v in enumerate(values):
        row[MESI[i]] = v
    row["TOTALE"] = sum(values)
    return row


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 📋 Controllo di Gestione")
    st.markdown(f"*Analisi finanziaria ed economica {anno}*")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Dettaglio CF",
        "🧾 Stima IVA",
        "📊 Dettaglio R&C",
        "💼 P&L",
        "📉 Cashflow Chart",
    ])

    # ─── TAB 1: Dettaglio Cashflow ───
    with tab1:
        cf = calcola_cashflow(anno)
        st.markdown("### Dettaglio Cashflow Mensile")
        st.markdown("*Analisi entrate/uscite per mese con 3 scenari*")

        data = []
        data.append(format_row("📥 Cash In (Reale)", cf["cash_in_reale"], bold=True))
        data.append(format_row("📤 Cash Out (Reale)", cf["cash_out_reale"], bold=True))
        net_reale = [cf["cash_in_reale"][i] - cf["cash_out_reale"][i] for i in range(12)]
        data.append(format_row("💰 Netto Reale", net_reale, bold=True))
        data.append(format_row("", [0]*12))
        data.append(format_row("📥 Cash In (Opportunità)", cf["cash_in_opp"]))
        data.append(format_row("📤 Cash Out (Opportunità)", cf["cash_out_opp"]))
        data.append(format_row("📥 Cash In (Forecast)", cf["cash_in_forecast"]))
        data.append(format_row("📤 Cash Out (Forecast)", cf["cash_out_forecast"]))
        data.append(format_row("", [0]*12))
        data.append(format_row("🟢 Saldo Reale", cf["saldo_reale"], bold=True))
        data.append(format_row("🟡 Saldo Opportunità", cf["saldo_opportunita"], bold=True))
        data.append(format_row("🔵 Saldo Forecast", cf["saldo_forecast"], bold=True))

        df = pd.DataFrame(data)
        col_config = {MESI[i]: st.column_config.NumberColumn(format="€%.0f") for i in range(12)}
        col_config["TOTALE"] = st.column_config.NumberColumn(format="€%.0f")
        st.dataframe(df, use_container_width=True, hide_index=True, column_config=col_config)

        st.info(f"💰 Saldo iniziale: €{cf['saldo_iniziale']:,.0f}  |  🚨 Soglia minima: €{cf['soglia_minima']:,.0f}")

    # ─── TAB 2: Stima IVA ───
    with tab2:
        iva = calcola_iva_trimestrale(anno)
        st.markdown("### Stima IVA Trimestrale")

        for q, info in iva["trimestri"].items():
            with st.expander(f"📅 {q} ({info['label']}) — IVA Netta: €{info['iva_netta']:,.0f}", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("IVA a Debito", f"€{info['iva_debito']:,.0f}")
                with col2:
                    st.metric("IVA a Credito", f"€{info['iva_credito']:,.0f}")
                with col3:
                    color = "normal" if info['iva_netta'] >= 0 else "inverse"
                    st.metric("IVA Netta da Versare", f"€{info['iva_netta']:,.0f}")

                if info['iva_debito_forecast'] > 0 or info['iva_credito_forecast'] > 0:
                    st.markdown(f"*Con Forecast: IVA Netta €{info['iva_netta_con_forecast']:,.0f}*")

                liq_mese_label = MESI[info['mese_liquidazione'] - 1]
                st.caption(f"Liquidazione: {liq_mese_label} {info['anno_liquidazione']}")

        # Tabella mensile
        st.markdown("---")
        st.markdown("#### Dettaglio Mensile IVA")
        iva_data = []
        iva_data.append(format_row("IVA Debito (Reale)", iva["iva_debito_mensile"]))
        iva_data.append(format_row("IVA Credito (Reale)", iva["iva_credito_mensile"]))
        netta_m = [iva["iva_debito_mensile"][i] - iva["iva_credito_mensile"][i] for i in range(12)]
        iva_data.append(format_row("IVA Netta Mensile", netta_m, bold=True))
        iva_data.append(format_row("IVA Debito (Forecast)", iva["iva_debito_forecast_mensile"]))
        iva_data.append(format_row("IVA Credito (Forecast)", iva["iva_credito_forecast_mensile"]))

        df_iva = pd.DataFrame(iva_data)
        st.dataframe(df_iva, use_container_width=True, hide_index=True, column_config=col_config)

    # ─── TAB 3: Dettaglio R&C ───
    with tab3:
        pnl = calcola_pnl(anno)
        st.markdown("### Dettaglio Ricavi e Costi (Competenza)")

        data_rc = []
        data_rc.append(format_row("A. RICAVI", pnl["tot_ricavi"], bold=True))
        for tipo, vals in pnl["ricavi_per_tipo"].items():
            if sum(vals) > 0:
                data_rc.append(format_row(f"   {tipo}", vals))
        data_rc.append(format_row("", [0]*12))
        data_rc.append(format_row("B. COSTI DIRETTI (COGS)", pnl["tot_cogs"], bold=True))
        for tipo, vals in pnl["cogs_per_tipo"].items():
            if sum(vals) > 0:
                data_rc.append(format_row(f"   {tipo}", vals))
        data_rc.append(format_row("", [0]*12))
        data_rc.append(format_row("C. MARGINE LORDO", pnl["margine_lordo"], bold=True))

        # Marginalità %
        marg_pct = []
        for i in range(12):
            if pnl["tot_ricavi"][i] > 0:
                marg_pct.append(round(pnl["margine_lordo"][i] / pnl["tot_ricavi"][i] * 100, 1))
            else:
                marg_pct.append(0)
        data_rc.append(format_row("   Marginalità %", marg_pct))

        df_rc = pd.DataFrame(data_rc)
        st.dataframe(df_rc, use_container_width=True, hide_index=True, column_config=col_config)

    # ─── TAB 4: P&L Completo ───
    with tab4:
        pnl = calcola_pnl(anno)
        st.markdown("### Conto Economico (P&L)")
        st.markdown(f"*Ricavi e Costi {anno} — Actual + Forecast*")

        data_pnl = []
        data_pnl.append(format_row("A. RICAVI", pnl["tot_ricavi"], bold=True))
        for tipo, vals in pnl["ricavi_per_tipo"].items():
            if sum(vals) > 0:
                data_pnl.append(format_row(f"   A. {tipo}", vals))

        data_pnl.append(format_row("B. COSTO DEL VENDUTO", pnl["tot_cogs"], bold=True))
        for tipo, vals in pnl["cogs_per_tipo"].items():
            if sum(vals) > 0:
                data_pnl.append(format_row(f"   B. {tipo}", vals))

        data_pnl.append(format_row("C. MARGINE LORDO", pnl["margine_lordo"], bold=True))
        data_pnl.append(format_row("", [0]*12))

        data_pnl.append(format_row("D. SPESE OPERATIVE", pnl["tot_spese_operative"], bold=True))
        for cat, vals in pnl["spese_operative"].items():
            if sum(vals) > 0:
                data_pnl.append(format_row(f"   {cat}", vals))

        data_pnl.append(format_row("E. EBITDA", pnl["ebitda"], bold=True))
        data_pnl.append(format_row("", [0]*12))
        data_pnl.append(format_row("F. AMMORTAMENTI", pnl["ammortamenti"], bold=True))
        data_pnl.append(format_row("G. EBIT", pnl["ebit"], bold=True))
        data_pnl.append(format_row("", [0]*12))
        data_pnl.append(format_row("H. ONERI FINANZIARI", pnl["oneri_finanziari"], bold=True))
        data_pnl.append(format_row("I. EBT", pnl["ebt"], bold=True))
        data_pnl.append(format_row("", [0]*12))
        data_pnl.append(format_row("L. IMPOSTE", pnl["imposte"], bold=True))
        data_pnl.append(format_row("M. UTILE NETTO", pnl["utile_netto"], bold=True))
        data_pnl.append(format_row("M. UTILE CUMULATIVO", pnl["utile_cumulativo"], bold=True))

        df_pnl = pd.DataFrame(data_pnl)
        st.dataframe(df_pnl, use_container_width=True, hide_index=True, column_config=col_config)

        # Chart P&L summary
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Bar(
            x=MESI, y=pnl["tot_ricavi"],
            name="Ricavi", marker_color="#10b981",
        ))
        fig_pnl.add_trace(go.Bar(
            x=MESI, y=[-v for v in pnl["tot_cogs"]],
            name="COGS", marker_color="#ef4444",
        ))
        fig_pnl.add_trace(go.Scatter(
            x=MESI, y=pnl["ebitda"],
            name="EBITDA", mode="lines+markers",
            line=dict(color="#6366f1", width=3),
        ))
        fig_pnl.add_trace(go.Scatter(
            x=MESI, y=pnl["utile_cumulativo"],
            name="Utile Cumulativo", mode="lines+markers",
            line=dict(color="#f59e0b", width=2, dash="dash"),
        ))
        fig_pnl.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            barmode="relative",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", y=1.1),
            yaxis=dict(gridcolor="rgba(99,102,241,0.1)", tickformat="€,.0f"),
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

    # ─── TAB 5: Cashflow Chart ───
    with tab5:
        cf = calcola_cashflow(anno)
        st.markdown("### Cashflow Finanziario — 3 Scenari")

        fig = go.Figure()

        # Soglia
        fig.add_trace(go.Scatter(
            x=cf["mesi_label"], y=[cf["soglia_minima"]]*12,
            mode="lines", name="🚨 Soglia Minima",
            line=dict(color="rgba(239,68,68,0.5)", width=2, dash="dot"),
            fill="tozeroy", fillcolor="rgba(239,68,68,0.05)",
        ))

        fig.add_trace(go.Scatter(
            x=cf["mesi_label"], y=cf["saldo_reale"],
            mode="lines+markers", name="🟢 Reale",
            line=dict(color="#10b981", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>€%{y:,.0f}<extra>Reale</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=cf["mesi_label"], y=cf["saldo_opportunita"],
            mode="lines+markers", name="🟡 Opportunità",
            line=dict(color="#f59e0b", width=2, dash="dash"),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>€%{y:,.0f}<extra>Opportunità</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=cf["mesi_label"], y=cf["saldo_forecast"],
            mode="lines+markers", name="🔵 Forecast",
            line=dict(color="#6366f1", width=2, dash="dot"),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>€%{y:,.0f}<extra>Forecast</extra>",
        ))

        # Delta band between Reale and Forecast
        fig.add_trace(go.Scatter(
            x=cf["mesi_label"] + cf["mesi_label"][::-1],
            y=cf["saldo_reale"] + cf["saldo_forecast"][::-1],
            fill="toself",
            fillcolor="rgba(99,102,241,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", y=1.08, xanchor="right", x=1),
            yaxis=dict(title="Saldo Cassa (€)", gridcolor="rgba(99,102,241,0.1)", tickformat="€,.0f"),
            xaxis=dict(gridcolor="rgba(99,102,241,0.1)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Delta table
        st.markdown("#### Delta tra Scenari")
        delta_data = []
        for i in range(12):
            delta_data.append({
                "Mese": MESI[i],
                "Reale €": cf["saldo_reale"][i],
                "Opportunità €": cf["saldo_opportunita"][i],
                "Forecast €": cf["saldo_forecast"][i],
                "Delta Opp-Reale €": cf["saldo_opportunita"][i] - cf["saldo_reale"][i],
                "Delta FC-Reale €": cf["saldo_forecast"][i] - cf["saldo_reale"][i],
            })
        df_delta = pd.DataFrame(delta_data)
        st.dataframe(df_delta, use_container_width=True, hide_index=True,
                     column_config={k: st.column_config.NumberColumn(format="€%.0f")
                                    for k in df_delta.columns if "€" in k})
