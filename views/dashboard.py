"""
pages/dashboard.py — Dashboard Overview con KPI, Cashflow chart, e alerts.
"""
import streamlit as st
import plotly.graph_objects as go
from execution.calc_cashflow import calcola_cashflow
from execution.forecast_engine import analisi_pipeline
from execution.margin_analysis import analisi_margini


def format_euro(value):
    """Format number as Euro currency."""
    if abs(value) >= 1_000_000:
        return f"€{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"€{value/1_000:.0f}K"
    return f"€{value:,.0f}"


def render():
    anno = st.session_state.get("anno", 2025)

    st.markdown("# 📊 Dashboard Overview")
    st.markdown(f"*Anno {anno} — Vista d'insieme del sistema finanziario*")
    st.markdown("---")

    # Load data
    cf = calcola_cashflow(anno)
    pipeline = analisi_pipeline(anno)
    margini = analisi_margini(anno)

    # ─── KPI CARDS ───
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        saldo_attuale = cf["saldo_reale"][-1] if cf["saldo_reale"] else 0
        cls = "positive" if saldo_attuale > 0 else "negative"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">💰 Saldo Cassa (Reale)</div>
            <div class="kpi-value {cls}">{format_euro(saldo_attuale)}</div>
            <div class="kpi-delta">Saldo iniziale: {format_euro(cf['saldo_iniziale'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        ebitda = margini.get("ebitda", 0)
        cls = "positive" if ebitda > 0 else "negative"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">📈 EBITDA</div>
            <div class="kpi-value {cls}">{format_euro(ebitda)}</div>
            <div class="kpi-delta">Margine: {margini.get('marginalita_media', 0):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        pip_val = pipeline.get("totale_pesato", 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🎯 Pipeline (Pesata)</div>
            <div class="kpi-value warning">{format_euro(pip_val)}</div>
            <div class="kpi-delta">{pipeline.get('num_opportunita', 0)} opportunità in corso</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        ricavi = margini.get("totale_ricavi", 0)
        cls = "positive" if ricavi > 0 else ""
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">💵 Ricavi Totali</div>
            <div class="kpi-value {cls}">{format_euro(ricavi)}</div>
            <div class="kpi-delta">Costi diretti: {format_euro(margini.get('totale_costi_diretti', 0))}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── CASHFLOW CHART (3 scenari) ───
    st.markdown('<div class="section-header">📉 Cash Flow — 3 Scenari</div>', unsafe_allow_html=True)

    fig = go.Figure()

    # Soglia minima liquidità
    fig.add_trace(go.Scatter(
        x=cf["mesi_label"],
        y=[cf["soglia_minima"]] * 12,
        mode="lines",
        name="Soglia Minima",
        line=dict(color="rgba(239, 68, 68, 0.5)", width=2, dash="dot"),
        fill=None,
    ))

    # Cashflow Reale
    fig.add_trace(go.Scatter(
        x=cf["mesi_label"],
        y=cf["saldo_reale"],
        mode="lines+markers",
        name="🟢 Reale",
        line=dict(color="#10b981", width=3),
        marker=dict(size=8, color="#10b981"),
        hovertemplate="<b>%{x}</b><br>Saldo Reale: €%{y:,.0f}<extra></extra>",
    ))

    # Cashflow Opportunità
    fig.add_trace(go.Scatter(
        x=cf["mesi_label"],
        y=cf["saldo_opportunita"],
        mode="lines+markers",
        name="🟡 Opportunità",
        line=dict(color="#f59e0b", width=2, dash="dash"),
        marker=dict(size=6, color="#f59e0b"),
        hovertemplate="<b>%{x}</b><br>Saldo Opportunità: €%{y:,.0f}<extra></extra>",
    ))

    # Cashflow Forecast
    fig.add_trace(go.Scatter(
        x=cf["mesi_label"],
        y=cf["saldo_forecast"],
        mode="lines+markers",
        name="🔵 Forecast",
        line=dict(color="#6366f1", width=2, dash="dot"),
        marker=dict(size=6, color="#6366f1"),
        hovertemplate="<b>%{x}</b><br>Saldo Forecast: €%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=12),
        ),
        yaxis=dict(
            title="Saldo Cassa (€)",
            gridcolor="rgba(99, 102, 241, 0.1)",
            tickformat="€,.0f",
        ),
        xaxis=dict(gridcolor="rgba(99, 102, 241, 0.1)"),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ─── ALERTS ───
    mesi_critici = []
    for i, saldo in enumerate(cf["saldo_reale"]):
        if saldo < cf["soglia_minima"]:
            mesi_critici.append((cf["mesi_label"][i], saldo))

    if mesi_critici:
        st.markdown('<div class="section-header">⚠️ Alert — Mesi Critici</div>', unsafe_allow_html=True)
        for mese, saldo in mesi_critici:
            st.error(f"🚨 **{mese}**: Saldo previsto **{format_euro(saldo)}** sotto la soglia minima di {format_euro(cf['soglia_minima'])}")

    # ─── BOTTOM ROW ───
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">🎯 Pipeline per Tipologia</div>', unsafe_allow_html=True)
        if pipeline["per_tipologia"]:
            labels = list(pipeline["per_tipologia"].keys())
            values = [v["pesato"] for v in pipeline["per_tipologia"].values()]
            counts = [v["count"] for v in pipeline["per_tipologia"].values()]

            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=["#6366f1", "#f59e0b", "#10b981", "#94a3b8"]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Valore: €%{value:,.0f}<br>%{percent}<extra></extra>",
            )])
            fig_pie.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nessuna opportunità nel forecast.")

    with col2:
        st.markdown('<div class="section-header">👥 Top Clienti per Margine</div>', unsafe_allow_html=True)
        if margini["clienti"]:
            for i, c in enumerate(margini["clienti"][:5]):
                if c["ricavi"] > 0:
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.markdown(f"**{i+1}. {c['nome']}**")
                    with col_b:
                        st.markdown(f"Ricavi: {format_euro(c['ricavi'])}")
                    with col_c:
                        color = "🟢" if c["marginalita_pct"] > 30 else "🟡" if c["marginalita_pct"] > 15 else "🔴"
                        st.markdown(f"{color} Margine: {c['marginalita_pct']:.0f}%")
        else:
            st.info("Nessun dato clienti disponibile.")
