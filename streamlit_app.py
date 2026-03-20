"""
app.py — Entry point for the OMC Financial Management System.
Streamlit multipage app with sidebar navigation.
"""
import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from seed_data import seed
from database import init_database

# ─── Page Config ───
st.set_page_config(
    page_title="OMC — Controllo di Gestione",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialize DB ───
init_database()
seed()

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ═══ Global text & font ═══ */
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #0f0f23 !important;
    }
    /* Force dark background on all content containers */
    .main, .main .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        background-color: #0f0f23 !important;
    }
    /* Force all main-area text to light color */
    .stApp .stMarkdown, .stApp .stMarkdown p, .stApp .stMarkdown li,
    .stApp .stMarkdown span, .stApp .stMarkdown td, .stApp .stMarkdown th,
    .stApp .stMarkdown h1, .stApp .stMarkdown h2, .stApp .stMarkdown h3,
    .stApp .stMarkdown h4, .stApp .stMarkdown h5, .stApp .stMarkdown h6 {
        color: #f1f5f9 !important;
    }
    .stApp label, .stApp .stSelectbox label, .stApp .stTextInput label,
    .stApp .stNumberInput label, .stApp .stDateInput label,
    .stApp .stTextArea label, .stApp .stMultiSelect label,
    .stApp .stRadio label, .stApp .stCheckbox label {
        color: #e2e8f0 !important;
    }

    /* ═══ Sidebar ═══ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: #e2e8f0 !important;
    }

    /* ═══ KPI Cards (custom HTML) ═══ */
    .kpi-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #2d2d5e 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #e2e8f0 !important;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #a5b4fc !important;
        margin-bottom: 4px;
    }
    .kpi-value.positive { color: #6ee7b7 !important; }
    .kpi-value.negative { color: #fca5a5 !important; }
    .kpi-value.warning  { color: #fcd34d !important; }
    .kpi-delta {
        font-size: 0.8rem;
        color: #94a3b8 !important;
    }

    /* ═══ Section headers ═══ */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9 !important;
        padding: 12px 0;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        margin-bottom: 16px;
        letter-spacing: 0.5px;
    }

    /* ═══ Status badges ═══ */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-previsionale { background: rgba(148, 163, 184, 0.2); color: #cbd5e1 !important; border: 1px solid rgba(148, 163, 184, 0.3); }
    .badge-confermato   { background: rgba(59, 130, 246, 0.2);  color: #93c5fd !important; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-fatturato    { background: rgba(251, 191, 36, 0.2);  color: #fde68a !important; border: 1px solid rgba(251, 191, 36, 0.3); }
    .badge-saldato      { background: rgba(34, 197, 94, 0.2);   color: #86efac !important; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-forecast     { background: rgba(148, 163, 184, 0.15);color: #cbd5e1 !important; border: 1px solid rgba(148, 163, 184, 0.2); }
    .badge-opportunita  { background: rgba(251, 191, 36, 0.15); color: #fde68a !important; border: 1px solid rgba(251, 191, 36, 0.2); }
    .badge-vinto        { background: rgba(34, 197, 94, 0.15);  color: #86efac !important; border: 1px solid rgba(34, 197, 94, 0.2); }
    .badge-perso        { background: rgba(239, 68, 68, 0.15);  color: #fca5a5 !important; border: 1px solid rgba(239, 68, 68, 0.2); }

    /* ═══ Tables ═══ */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ═══ Tabs ═══ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        color: #cbd5e1 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #f1f5f9 !important;
    }

    /* ═══ Native st.metric ═══ */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e3f 0%, #2d2d5e 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #e2e8f0 !important;
        font-weight: 600;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #94a3b8 !important;
    }

    /* ═══ Forms ═══ */
    .stForm {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 24px;
    }
    .stForm label, .stForm p, .stForm span,
    .stForm h1, .stForm h2, .stForm h3, .stForm h4 {
        color: #e2e8f0 !important;
    }

    /* ═══ Expanders ═══ */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        color: #f1f5f9 !important;
        font-weight: 600;
    }

    /* ═══ Selectbox / Input text inside widgets ═══ */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        color: #f1f5f9 !important;
    }

    /* ═══ Info / Warning / Error boxes ═══ */
    .stAlert p, .stAlert span {
        color: #f1f5f9 !important;
    }

    /* ═══ FORCE bright text on ALL content ═══ */
    /* Page titles (h1-h6 rendered by st.markdown("# ...")) */
    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4,
    .main .block-container h5,
    .main .block-container h6,
    [data-testid="stMainBlockContainer"] h1,
    [data-testid="stMainBlockContainer"] h2,
    [data-testid="stMainBlockContainer"] h3 {
        color: #ffffff !important;
    }
    /* Paragraph, italic, bold and all body text */
    .main .block-container p,
    .main .block-container em,
    .main .block-container strong,
    .main .block-container span,
    .main .block-container li,
    .main .block-container td,
    .main .block-container th,
    .main .block-container div,
    [data-testid="stMainBlockContainer"] p,
    [data-testid="stMainBlockContainer"] em,
    [data-testid="stMainBlockContainer"] span {
        color: #e2e8f0 !important;
    }
    /* Captions and small text */
    .main .block-container .stCaption,
    [data-testid="stCaptionContainer"] {
        color: #94a3b8 !important;
    }
    /* Tab text override with higher specificity */
    [data-testid="stMainBlockContainer"] [data-baseweb="tab"] {
        color: #cbd5e1 !important;
    }
    [data-testid="stMainBlockContainer"] [data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar Navigation ───
with st.sidebar:
    st.markdown("# 💰 OMC System")
    st.markdown("*Controllo di Gestione*")
    st.markdown("---")

    page = st.radio(
        "Navigazione",
        [
            "📊 Dashboard",
            "🎯 Forecast",
            "📥 Ciclo Attivo",
            "📤 Ciclo Passivo",
            "🏢 Costi Indiretti",
            "💵 Altre Entrate",
            "📋 Controllo di Gestione",
            "👥 Analisi Clienti",
            "👥 Gestione Attori",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    anno = st.selectbox("Anno di riferimento", [2024, 2025, 2026, 2027], index=1)
    st.session_state["anno"] = anno

    st.markdown("---")
    st.markdown(
        '<p style="color:#64748b; font-size:0.7rem; text-align:center;">'
        'OMC System v1.0<br>Powered by Streamlit</p>',
        unsafe_allow_html=True,
    )


# ─── Page Router ───
if page == "📊 Dashboard":
    from views.dashboard import render
    render()
elif page == "🎯 Forecast":
    from views.forecast import render
    render()
elif page == "📥 Ciclo Attivo":
    from views.ciclo_attivo import render
    render()
elif page == "📤 Ciclo Passivo":
    from views.ciclo_passivo import render
    render()
elif page == "🏢 Costi Indiretti":
    from views.costi_indiretti import render
    render()
elif page == "💵 Altre Entrate":
    from views.altre_entrate import render
    render()
elif page == "📋 Controllo di Gestione":
    from views.controllo_gestione import render
    render()
elif page == "👥 Analisi Clienti":
    from views.analisi_clienti import render
    render()
elif page == "👥 Gestione Attori":
    from views.attori import render
    render()
