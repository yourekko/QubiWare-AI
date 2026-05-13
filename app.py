"""QubiWare AI - AI Control Tower for Warehouse, Inventory and Dispatch Operations."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

from utils.data_loader import load_all_data
from utils.analytics import (
    get_low_stock_items, get_overstock_items, get_dead_stock_items,
    get_fast_moving_skus, get_reorder_recommendations,
    get_delayed_orders, get_pending_orders, get_high_priority_delayed,
    get_delay_by_zone, get_delay_by_customer,
    get_zone_utilization, get_picking_errors_by_picker, get_dispatch_by_bay,
    get_inbound_mismatches, get_supplier_issues,
    compute_kpis, generate_inventory_action_plan, generate_dispatch_risk_summary,
    generate_dispatch_tab_report,
    df_to_styled_table,
    get_dead_stock_analysis, get_liquidation_strategies, get_resource_optimization,
    get_delay_root_causes, get_route_efficiency, get_zone_transport_analysis,
    get_customer_impact, get_picking_error_analysis, get_bay_optimization,
    generate_inventory_tab_report,
)
from utils.ai_helper import get_ai_response
from utils.report_generator import generate_pdf_report

# ─── Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="QubiWare AI",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%230F172A'/><text x='50' y='68' font-size='52' font-weight='bold' text-anchor='middle' fill='%232563EB'>Q</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit Community Cloud: keys from App → Secrets (TOML). Local: use .env via load_dotenv above.
try:
    for _secret_key in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
        if _secret_key in st.secrets:
            os.environ[_secret_key] = str(st.secrets[_secret_key])
except Exception:
    pass

# ─── Design Tokens ───────────────────────────────────────────────────
CHART_COLORS = ["#2563EB", "#06B6D4", "#10B981", "#F59E0B", "#EF4444",
                "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#6366F1"]

CHART_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, -apple-system, sans-serif", size=13, color="#374151"),
    title=dict(text=""),
    margin=dict(l=24, r=24, t=16, b=40),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#E2E8F0"),
    colorway=CHART_COLORS,
)

# ─── Global CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --primary: #0F172A;
    --accent: #2563EB;
    --cyan: #06B6D4;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --bg: #F8FAFC;
    --card: #FFFFFF;
    --border: #E2E8F0;
    --border-light: #F1F5F9;
    --text: #0F172A;
    --text-secondary: #475569;
    --text-muted: #94A3B8;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.05);
    --radius: 14px;
    --radius-lg: 18px;
}

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

/* ── Main Container ── */
.main .block-container {
    padding: 1.2rem 2rem 2rem 2rem;
    max-width: 1500px;
}
.stMarkdown, .stPlotlyChart, .stDataFrame { margin-bottom: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.4rem; }

/* ── Streamlit chrome: keep header (sidebar toggle) visible; hide overflow menu & deploy ── */
header[data-testid="stHeader"] {
    background: transparent !important;
    visibility: visible !important;
    min-height: 3rem !important;
}
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    width: 280px !important;
    min-width: 280px !important;
    max-width: 280px !important;
}
section[data-testid="stSidebar"][aria-expanded="true"] {
    display: block !important;
    width: 280px !important;
    min-width: 280px !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span { color: #374151 !important; }
section[data-testid="stSidebar"] hr {
    border-color: #F1F5F9 !important;
    margin: 0.7rem 0 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] { gap: 3px !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
    color: #475569 !important;
    padding: 0.55rem 0.9rem !important;
    border-radius: 10px !important;
    transition: all 0.15s ease !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    margin: 1px 0 !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
    background: transparent !important;
    border-left: 3px solid transparent !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
    background: #F8FAFC !important;
    color: #0F172A !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div,
section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked ~ div {
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    font-weight: 600 !important;
    border-left: 3px solid #2563EB !important;
}

/* ── Page Header ── */
.page-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%);
    padding: 38px 40px;
    border-radius: var(--radius-lg);
    margin-bottom: 26px;
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: '';
    position: absolute; top: -60px; right: -30px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(37,99,235,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header::after {
    content: '';
    position: absolute; bottom: -40px; left: 30%;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header h1 {
    color: #FFFFFF !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    margin: 0 0 8px 0 !important;
    letter-spacing: -0.5px;
    position: relative; z-index: 1;
}
.page-header p {
    color: #94A3B8 !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
    font-weight: 400;
    position: relative; z-index: 1;
}
.page-header .accent-bar {
    width: 50px; height: 3px;
    background: linear-gradient(90deg, #2563EB, #06B6D4);
    border-radius: 2px;
    margin-top: 16px;
    position: relative; z-index: 1;
}
.page-header .demo-badge {
    position: absolute; top: 22px; right: 28px;
    background: rgba(37,99,235,0.2);
    color: #93C5FD;
    font-size: 0.74rem;
    font-weight: 700;
    padding: 7px 16px;
    border-radius: 20px;
    letter-spacing: 0.3px;
    z-index: 2;
    border: 1px solid rgba(37,99,235,0.3);
}

/* ── KPI Cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 26px; }
.kpi-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 26px; }
.kpi-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 26px; }

.kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
}
.kpi-card.blue::before { background: linear-gradient(90deg, #2563EB, #3B82F6); }
.kpi-card.green::before { background: linear-gradient(90deg, #10B981, #34D399); }
.kpi-card.red::before { background: linear-gradient(90deg, #EF4444, #F87171); }
.kpi-card.amber::before { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.kpi-card.purple::before { background: linear-gradient(90deg, #8B5CF6, #A78BFA); }
.kpi-card.cyan::before { background: linear-gradient(90deg, #06B6D4, #22D3EE); }

.kpi-icon {
    width: 42px; height: 42px;
    border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 14px;
}
.kpi-icon.blue { background: #EFF6FF; color: #2563EB; }
.kpi-icon.green { background: #ECFDF5; color: #059669; }
.kpi-icon.red { background: #FEF2F2; color: #DC2626; }
.kpi-icon.amber { background: #FFFBEB; color: #D97706; }
.kpi-icon.purple { background: #F5F3FF; color: #7C3AED; }
.kpi-icon.cyan { background: #ECFEFF; color: #0891B2; }

.kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.1;
    margin-bottom: 5px;
    letter-spacing: -0.5px;
}
.kpi-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.4px;
    line-height: 1.3;
}
.kpi-helper {
    font-size: 0.74rem;
    color: var(--text-muted);
    margin-top: 8px;
    line-height: 1.3;
}

/* ── Section Headings ── */
.section-heading {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin: 30px 0 16px 0;
    display: flex; align-items: center; gap: 10px;
}
.section-heading .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    flex-shrink: 0;
}

/* ── Alert Cards ── */
.alert-card {
    padding: 16px 20px;
    border-radius: 12px;
    margin-bottom: 12px;
    border-left: 4px solid;
    font-size: 0.9rem;
    line-height: 1.6;
}
.alert-critical { background: #FEF2F2; border-left-color: #EF4444; color: #991B1B; }
.alert-warning { background: #FFFBEB; border-left-color: #F59E0B; color: #92400E; }
.alert-info { background: #EFF6FF; border-left-color: #2563EB; color: #1E40AF; }
.alert-success { background: #ECFDF5; border-left-color: #10B981; color: #065F46; }

/* ── Premium Alert Cards ── */
.premium-alert {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 4px solid;
    border-radius: var(--radius);
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: var(--shadow-sm);
}
.premium-alert.critical { border-left-color: #EF4444; }
.premium-alert.warning { border-left-color: #F59E0B; }
.premium-alert.info { border-left-color: #2563EB; }
.premium-alert .alert-badge {
    display: inline-block;
    font-size: 0.66rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 3px 10px;
    border-radius: 5px;
    margin-bottom: 8px;
}
.premium-alert.critical .alert-badge { background: #FEE2E2; color: #DC2626; }
.premium-alert.warning .alert-badge { background: #FEF3C7; color: #D97706; }
.premium-alert.info .alert-badge { background: #DBEAFE; color: #2563EB; }
.premium-alert .alert-title { font-size: 0.95rem; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.premium-alert .alert-msg { font-size: 0.88rem; color: #4B5563; line-height: 1.55; }
.premium-alert .alert-action { font-size: 0.82rem; color: var(--text-secondary); margin-top: 8px; font-style: italic; }

/* ── AI Summary Strip ── */
.ai-summary {
    background: linear-gradient(135deg, #EFF6FF, #F0F9FF);
    border: 1px solid #BFDBFE;
    border-radius: var(--radius);
    padding: 20px 26px;
    margin-bottom: 26px;
    display: flex; align-items: center; gap: 16px;
}
.ai-summary-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.ai-summary-text { font-size: 0.92rem; color: #1E3A5F; line-height: 1.6; }
.ai-summary-text strong { color: #1E40AF; font-weight: 700; }

/* ── Chart Card ── */
.chart-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 24px 8px 24px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-sm);
}
.chart-card-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 2px;
}
.chart-card-subtitle {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-bottom: 8px;
}

/* ── Buttons ── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    border: none !important;
    border-radius: 11px !important;
    padding: 11px 30px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: white !important;
    transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    transform: translateY(-1px);
}
div[data-testid="stVerticalBlock"] .stButton > button[kind="secondary"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 9px 16px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
    background: white !important;
    white-space: normal !important;
    line-height: 1.3 !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
div[data-testid="stVerticalBlock"] .stButton > button[kind="secondary"]:hover {
    background: #2563EB !important;
    color: white !important;
    border-color: #2563EB !important;
}
.stDownloadButton > button { border-radius: 11px !important; font-weight: 600 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px; background: var(--bg); padding: 5px; border-radius: 12px; border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] { border-radius: 9px; font-weight: 600; font-size: 0.88rem; padding: 9px 18px; }
.stTabs [aria-selected="true"] { background: white; box-shadow: var(--shadow-sm); }

/* ── Chat ── */
.chat-outer { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; }
.chat-header { background: linear-gradient(135deg, #0F172A, #1E293B); padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
.chat-header-dot { width: 10px; height: 10px; background: #10B981; border-radius: 50%; box-shadow: 0 0 6px rgba(16,185,129,0.5); }
.chat-header-text { color: white; font-size: 0.95rem; font-weight: 600; }
.chat-header-sub { color: #64748B; font-size: 0.78rem; }
[data-testid="stChatInput"] textarea { border-radius: var(--radius) !important; border-color: var(--border) !important; font-family: 'Inter', sans-serif !important; }

/* ── Recommendation Cards ── */
.rec-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; margin-bottom: 10px; display: flex; align-items: flex-start; gap: 12px; transition: transform 0.15s, box-shadow 0.15s; }
.rec-card:hover { transform: translateX(3px); box-shadow: var(--shadow); }
.rec-num { width: 28px; height: 28px; background: linear-gradient(135deg, #2563EB, #06B6D4); color: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; }
.rec-text { font-size: 0.9rem; color: var(--text); line-height: 1.55; }

/* ── Footer ── */
.qw-footer { text-align: center; padding: 24px; margin-top: 40px; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.8rem; }
.qw-footer strong { color: var(--text-secondary); }

/* ── Badge ── */
.badge { display: inline-block; font-size: 0.72rem; font-weight: 600; padding: 4px 11px; border-radius: 6px; letter-spacing: 0.2px; }
.badge-blue { background: #DBEAFE; color: #1D4ED8; }
.badge-cyan { background: #CFFAFE; color: #0E7490; }
.badge-green { background: #D1FAE5; color: #065F46; }
.badge-red { background: #FEE2E2; color: #991B1B; }
.badge-amber { background: #FEF3C7; color: #92400E; }
.badge-purple { background: #EDE9FE; color: #5B21B6; }
.badge-slate { background: #F1F5F9; color: #475569; }

/* ── Insight Panel ── */
.insight-panel { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow-sm); }

/* ── Responsive ── */
@media (max-width: 768px) {
    .kpi-grid, .kpi-grid-4 { grid-template-columns: repeat(2, 1fr); }
    .kpi-grid-3 { grid-template-columns: repeat(1, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# ─── Load Data ───────────────────────────────────────────────────────
@st.cache_data
def get_data():
    return load_all_data()

data = get_data()


# ─── SVG Icons ───────────────────────────────────────────────────────
SVG_ICONS = {
    "cube": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    "cart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
    "alert-triangle": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "archive": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>',
    "clock": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "truck": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    "timer": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 8 14"/></svg>',
    "building": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M8 10h.01M16 10h.01M12 10h.01M8 14h.01M16 14h.01M12 14h.01"/></svg>',
    "check-circle": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "x-circle": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    "zap": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "shield": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "target": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "bar-chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>',
}

KPI_HELPERS = {
    "Total SKUs": "Active inventory items tracked",
    "Total Orders": "Orders in current dataset",
    "Low Stock Items": "SKUs below reorder level",
    "Overstock Items": "SKUs occupying excess space",
    "Delayed Orders": "Beyond promised dispatch",
    "Pending Dispatches": "Awaiting dispatch",
    "Avg Delay Days": "Average across delayed orders",
    "Warehouse Utilization %": "Overall space usage",
    "Picking Accuracy %": "From picking records",
    "Inbound Mismatches": "Supplier qty mismatch cases",
}


# ─── Shared Components ───────────────────────────────────────────────
def render_header(title, subtitle, show_badge=True):
    badge = '<div class="demo-badge">Demo Mode &middot; CSV/WMS/ERP-ready</div>' if show_badge else ''
    st.markdown(f'<div class="page-header">{badge}<h1>{title}</h1><p>{subtitle}</p><div class="accent-bar"></div></div>', unsafe_allow_html=True)


def render_alert(message, level="warning"):
    st.markdown(f'<div class="alert-card alert-{level}">{message}</div>', unsafe_allow_html=True)


def render_premium_alert(level, title, message, action=""):
    action_html = f'<div class="alert-action">Recommended: {action}</div>' if action else ""
    st.markdown(f'<div class="premium-alert {level}"><div class="alert-badge">{level}</div><div class="alert-title">{title}</div><div class="alert-msg">{message}</div>{action_html}</div>', unsafe_allow_html=True)


def render_section(title):
    st.markdown(f'<div class="section-heading"><span class="dot"></span>{title}</div>', unsafe_allow_html=True)


def render_footer():
    st.markdown('<div class="qw-footer">Built by <strong>Qubithm Corporation LLP</strong> &middot; AI Solutions for Logistics &amp; Warehousing<br>QubiWare AI v1.0 &middot; Prototype uses demo data. Can be connected to live WMS, ERP, Excel, barcode or RFID exports during pilot.</div>', unsafe_allow_html=True)


def render_kpi_card(value, label, icon_name, color, helper=""):
    icon_svg = SVG_ICONS.get(icon_name, SVG_ICONS["cube"])
    helper_html = f'<div class="kpi-helper">{helper}</div>' if helper else ""
    return f'<div class="kpi-card {color}"><div class="kpi-icon {color}">{icon_svg}</div><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div>{helper_html}</div>'


def render_kpi_grid(items, columns=5):
    grid_class = {5: "kpi-grid", 4: "kpi-grid-4", 3: "kpi-grid-3"}.get(columns, "kpi-grid")
    html = f'<div class="{grid_class}">'
    for item in items:
        if len(item) == 4:
            value, label, icon, color = item
            helper = KPI_HELPERS.get(label, "")
        else:
            value, label, icon, color, helper = item
        html += render_kpi_card(value, label, icon, color, helper)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def chart_card_open(title, subtitle=""):
    sub_html = f'<div class="chart-card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="chart-card"><div class="chart-card-title">{title}</div>{sub_html}', unsafe_allow_html=True)


def chart_card_close():
    st.markdown('</div>', unsafe_allow_html=True)


def render_chart_card(title, subtitle=""):
    sub_html = f'<div class="chart-card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="chart-card"><div class="chart-card-title">{title}</div>{sub_html}</div>', unsafe_allow_html=True)


def render_recommendation(num, text):
    st.markdown(f'<div class="rec-card"><div class="rec-num">{num}</div><div class="rec-text">{text}</div></div>', unsafe_allow_html=True)


def render_badge(text, color="blue"):
    return f'<span class="badge badge-{color}">{text}</span>'


def styled_chart(fig, height=380):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, sans-serif", size=13, color="#374151"),
        title=dict(text=""), margin=dict(l=24, r=24, t=16, b=40),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#E2E8F0"),
        colorway=CHART_COLORS)
    return fig


def render_ai_summary(kpis, critical_zones_count):
    low = kpis["Low Stock Items"]
    delayed = kpis["Delayed Orders"]
    mismatch = kpis["Inbound Mismatch Count"]
    st.markdown(f'<div class="ai-summary"><div class="ai-summary-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div><div class="ai-summary-text">Today\'s warehouse health: <strong>{low} low-stock SKUs</strong>, <strong>{delayed} delayed orders</strong>, <strong>{critical_zones_count} congested zone(s)</strong>, and <strong>{mismatch} inbound mismatches</strong> require attention.</div></div>', unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    "Product Overview",
    "Executive Dashboard",
    "Inventory Intelligence",
    "Dispatch Intelligence",
    "Zone Intelligence",
    "AI CoPilot",
    "Daily AI Report",
]

with st.sidebar:
    st.markdown('<div style="text-align:center;padding:14px 0 16px 0;"><div style="display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;background:linear-gradient(135deg,#0F172A,#1E293B);border-radius:14px;margin-bottom:10px;box-shadow:0 4px 12px rgba(15,23,42,0.2);"><span style="font-size:1.35rem;font-weight:800;color:#2563EB;">Q</span></div><div style="font-size:1.1rem;font-weight:700;color:#0F172A;letter-spacing:-0.3px;">QubiWare AI</div><div style="font-size:0.7rem;color:#64748B;margin-top:3px;letter-spacing:0.8px;font-weight:600;text-transform:uppercase;">AI Control Tower</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigation",
        NAV_ITEMS,
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown('<div style="padding:16px;background:linear-gradient(135deg,#F8FAFC,#F1F5F9);border-radius:12px;border:1px solid #E2E8F0;"><div style="font-size:0.65rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;">Powered by</div><div style="font-size:0.85rem;font-weight:600;color:#0F172A;">Qubithm Corporation LLP</div><div style="font-size:0.72rem;color:#64748B;margin-top:3px;">AI Solutions for Logistics &amp; Warehousing</div></div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════
# PAGE: PRODUCT OVERVIEW
# ═════════════════════════════════════════════════════════════════════
if page == "Product Overview":

    # Hero section
    st.markdown('<div style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 40%,#0F172A 100%);padding:48px 44px;border-radius:20px;margin-bottom:28px;position:relative;overflow:hidden;"><div style="position:absolute;top:-80px;right:-40px;width:350px;height:350px;background:radial-gradient(circle,rgba(37,99,235,0.15) 0%,transparent 70%);border-radius:50%;"></div><div style="position:absolute;bottom:-60px;left:20%;width:250px;height:250px;background:radial-gradient(circle,rgba(6,182,212,0.1) 0%,transparent 70%);border-radius:50%;"></div><div style="position:relative;z-index:1;"><div style="font-size:0.7rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">AI-Powered Warehouse Intelligence</div><div style="font-size:2.2rem;font-weight:900;color:white;letter-spacing:-1px;line-height:1.1;margin-bottom:8px;">QubiWare AI</div><div style="font-size:1rem;color:#94A3B8;margin-bottom:20px;max-width:600px;line-height:1.6;">AI Control Tower for Warehouse, Inventory &amp; Dispatch Operations.<br>Turn warehouse data into alerts, decisions and reports.</div><div style="display:flex;flex-wrap:wrap;gap:8px;"><span style="background:rgba(37,99,235,0.15);color:#93C5FD;font-size:0.72rem;font-weight:600;padding:5px 14px;border-radius:20px;border:1px solid rgba(37,99,235,0.25);">AI CoPilot</span><span style="background:rgba(6,182,212,0.15);color:#67E8F9;font-size:0.72rem;font-weight:600;padding:5px 14px;border-radius:20px;border:1px solid rgba(6,182,212,0.25);">Warehouse Intelligence</span><span style="background:rgba(245,158,11,0.15);color:#FCD34D;font-size:0.72rem;font-weight:600;padding:5px 14px;border-radius:20px;border:1px solid rgba(245,158,11,0.25);">Inventory Alerts</span><span style="background:rgba(239,68,68,0.15);color:#FCA5A5;font-size:0.72rem;font-weight:600;padding:5px 14px;border-radius:20px;border:1px solid rgba(239,68,68,0.25);">Dispatch Risk</span><span style="background:rgba(16,185,129,0.15);color:#6EE7B7;font-size:0.72rem;font-weight:600;padding:5px 14px;border-radius:20px;border:1px solid rgba(16,185,129,0.25);">Daily Reports</span></div></div></div>', unsafe_allow_html=True)

    # Main pitch
    st.markdown('<div style="background:linear-gradient(135deg,#EFF6FF,#F0F9FF);border:1px solid #BFDBFE;border-radius:14px;padding:28px 32px;margin-bottom:28px;text-align:center;"><div style="font-size:0.68rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:10px;">Our Approach</div><div style="font-size:1.1rem;font-weight:700;color:#1E293B;max-width:700px;margin:0 auto;line-height:1.6;">&ldquo;We do not replace your WMS, ERP, barcode/RFID system, or Excel. We add an AI layer that gives insights, alerts, and reports from your existing data.&rdquo;</div></div>', unsafe_allow_html=True)

    # Problem > Solution
    render_section("From Problem to Solution")

    ps_col1, ps_col2, ps_col3 = st.columns(3)
    with ps_col1:
        st.markdown('<div style="background:white;border:1px solid #E5E7EB;border-radius:12px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.04);"><div style="font-size:0.65rem;font-weight:700;color:#EF4444;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Problem</div><div style="font-size:0.88rem;color:#4B5563;line-height:1.5;margin-bottom:14px;">Data scattered across Excel, WMS, ERP, barcode/RFID systems</div><div style="width:100%;height:1px;background:#F3F4F6;margin-bottom:14px;"></div><div style="font-size:0.65rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Solution</div><div style="font-size:0.88rem;color:#111827;font-weight:600;line-height:1.5;">Unified AI intelligence layer</div></div>', unsafe_allow_html=True)
    with ps_col2:
        st.markdown('<div style="background:white;border:1px solid #E5E7EB;border-radius:12px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.04);"><div style="font-size:0.65rem;font-weight:700;color:#EF4444;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Problem</div><div style="font-size:0.88rem;color:#4B5563;line-height:1.5;margin-bottom:14px;">Manual reports and delayed decisions</div><div style="width:100%;height:1px;background:#F3F4F6;margin-bottom:14px;"></div><div style="font-size:0.65rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Solution</div><div style="font-size:0.88rem;color:#111827;font-weight:600;line-height:1.5;">AI-generated summaries and action reports</div></div>', unsafe_allow_html=True)
    with ps_col3:
        st.markdown('<div style="background:white;border:1px solid #E5E7EB;border-radius:12px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.04);"><div style="font-size:0.65rem;font-weight:700;color:#EF4444;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Problem</div><div style="font-size:0.88rem;color:#4B5563;line-height:1.5;margin-bottom:14px;">Stockouts, delays, mismatch and congestion found late</div><div style="width:100%;height:1px;background:#F3F4F6;margin-bottom:14px;"></div><div style="font-size:0.65rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Solution</div><div style="font-size:0.88rem;color:#111827;font-weight:600;line-height:1.5;">Real-time risk alerts and recommended actions</div></div>', unsafe_allow_html=True)

    # Connects with
    render_section("Connects With Your Existing Systems")
    badges = ["Excel", "WMS", "ERP", "Barcode", "RFID", "IoT", "Dispatch Data", "Inbound Data", "Supplier Data"]
    badge_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px;">'
    for b in badges:
        badge_html += f'<span style="background:#F1F5F9;color:#475569;font-size:0.75rem;font-weight:600;padding:6px 14px;border-radius:8px;border:1px solid #E5E7EB;">{b}</span>'
    badge_html += '</div>'
    st.markdown(badge_html, unsafe_allow_html=True)

    # Ideal for
    render_section("Ideal For")
    segments = [
        ("Warehouse Operators", "building"), ("3PL Companies", "truck"), ("WMS Vendors", "cube"),
        ("Barcode/RFID Vendors", "target"), ("Logistics Companies", "cart"), ("Manufacturing Warehouses", "archive"),
    ]
    id_col1, id_col2, id_col3 = st.columns(3)
    for i, (name, icon) in enumerate(segments):
        svg = SVG_ICONS.get(icon, SVG_ICONS["cube"])
        col = [id_col1, id_col2, id_col3][i % 3]
        with col:
            st.markdown(f'<div style="background:white;border:1px solid #E5E7EB;border-radius:10px;padding:16px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 2px rgba(0,0,0,0.03);margin-bottom:12px;"><div style="width:36px;height:36px;background:#EFF6FF;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#2563EB;flex-shrink:0;">{svg}</div><div style="font-size:0.85rem;font-weight:600;color:#111827;">{name}</div></div>', unsafe_allow_html=True)

    # CTA
    st.markdown('<div style="background:linear-gradient(135deg,#0F172A,#1E293B);border-radius:14px;padding:28px 32px;text-align:center;"><div style="font-size:1rem;font-weight:700;color:white;margin-bottom:6px;">Ready to explore?</div><div style="font-size:0.85rem;color:#94A3B8;max-width:500px;margin:0 auto;">Start the demo from <strong style="color:#60A5FA;">Executive Dashboard</strong> to see live KPIs, AI risk alerts, intelligent insights and PDF reporting in action.</div></div>', unsafe_allow_html=True)

    with st.expander("Demo checklist — map stakeholder questions to the app", expanded=False):
        st.markdown(
            """
| Topic | Where in QubiWare AI |
|------|----------------------|
| Why dead stock, expensive / unreliable / bulk, perishable loss, storage cost | **Inventory Intelligence** → tabs *Dead Stock Analysis*, *Liquidation*, *Resource & charges* |
| Break-even / discount / return / bulk clearance | **Liquidation** tab + **AI CoPilot** (e.g. “what to do with dead stock”) |
| Reduce warehouse resources & charges | **Resource & charges** tab + **AI CoPilot** (“reduce warehouse cost”, “energy cost”) |
| Why delivery delayed, pending orders, picking errors | **Dispatch Intelligence** → *Delayed*, *Pending*, *Picking Errors*, *Delay Root Causes* |
| Best bays, routes, efficiency, cost | **Dispatch** → *Route & Bay Optimization* |
| Zones causing delay, customer impact | **Dispatch** → charts + *Customer Impact*; **Zone Intelligence** for congestion |
| Critical / warning / normal zones, vehicles, until when critical, revenue | **Zone Intelligence** → KPIs, charts, *Zone Transport & Revenue* table |
| Daily narrative & actions | **Daily AI Report** + **AI CoPilot** |
            """
        )

    render_footer()


# ═════════════════════════════════════════════════════════════════════
# PAGE: EXECUTIVE DASHBOARD
# ═════════════════════════════════════════════════════════════════════
elif page == "Executive Dashboard":
    render_header("Executive Dashboard", "Real-time warehouse KPIs, risk alerts and operational intelligence")

    kpis = compute_kpis(data)
    zone_util = get_zone_utilization(data["zones"])
    critical_zones = zone_util[zone_util["status"] == "Critical"]

    # AI Summary Strip
    render_ai_summary(kpis, len(critical_zones))

    # KPI Row 1
    render_kpi_grid([
        (f"{kpis['Total SKUs']:,}", "Total SKUs", "cube", "blue"),
        (f"{kpis['Total Orders']:,}", "Total Orders", "cart", "blue"),
        (kpis["Low Stock Items"], "Low Stock Items", "alert-triangle", "red"),
        (kpis["Overstock Items"], "Overstock Items", "archive", "amber"),
        (kpis["Delayed Orders"], "Delayed Orders", "clock", "red"),
    ], 5)

    # KPI Row 2
    render_kpi_grid([
        (kpis["Pending Dispatches"], "Pending Dispatches", "truck", "amber"),
        (kpis["Avg Delay Days"], "Avg Delay Days", "timer", "red"),
        (f"{kpis['Warehouse Utilization %']}%", "Warehouse Utilization %", "building", "purple"),
        (f"{kpis['Picking Accuracy %']}%", "Picking Accuracy %", "check-circle", "green"),
        (kpis["Inbound Mismatch Count"], "Inbound Mismatches", "x-circle", "amber"),
    ], 5)

    # AI Risk Alerts
    render_section("AI Risk Alerts")
    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        if kpis["Low Stock Items"] > 0:
            render_premium_alert("critical", "Low Stock Alert",
                f"{kpis['Low Stock Items']} SKUs are below reorder level.",
                "Start procurement review today.")
        if kpis["Overstock Items"] > 0:
            render_premium_alert("warning", "Overstock Alert",
                f"{kpis['Overstock Items']} SKUs are occupying excess warehouse space.",
                "Review for redistribution or promotional clearance.")
        if kpis["Inbound Mismatch Count"] > 0:
            render_premium_alert("info", "Inbound Mismatch Alert",
                f"{kpis['Inbound Mismatch Count']} inbound shipments have quantity mismatch.",
                "Escalate to procurement and supplier management.")

    with alert_col2:
        if kpis["Delayed Orders"] > 0:
            render_premium_alert("critical", "Dispatch Delay Alert",
                f"{kpis['Delayed Orders']} orders are delayed beyond promised dispatch date.",
                "Prioritize high-priority orders for immediate dispatch.")
        for _, z in critical_zones.iterrows():
            render_premium_alert("warning", "Zone Congestion",
                f"{z['zone_name']} at {z['utilization_pct']}% utilization. Picking delays likely.",
                "Move slow stock out and redistribute.")
        picker_errors = get_picking_errors_by_picker(data["picking"])
        top_picker = picker_errors.iloc[0] if len(picker_errors) > 0 else None
        if top_picker is not None and top_picker["total_errors"] > 5:
            render_premium_alert("info", "Picking Accuracy Alert",
                f"{top_picker['picker_name']} has {int(top_picker['total_errors'])} picking errors this period.",
                "Schedule retraining and review picking zone assignment.")

    # Charts
    render_section("Warehouse Intelligence Overview")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        chart_card_open("Inventory by Category", "Stock volume distribution across product categories")
        inv_by_cat = data["inventory"].groupby("category")["current_stock"].sum().reset_index().sort_values("current_stock", ascending=True)
        fig = go.Figure(go.Bar(
            y=inv_by_cat["category"], x=inv_by_cat["current_stock"],
            orientation='h',
            marker=dict(color=inv_by_cat["current_stock"], colorscale=[[0, "#93C5FD"], [1, "#2563EB"]], cornerradius=4),
            text=inv_by_cat["current_stock"].apply(lambda x: f"{x:,}"),
            textposition="outside", textfont=dict(size=11, color="#374151"),
        ))
        fig = styled_chart(fig, 340)
        fig.update_layout(xaxis=dict(showticklabels=False, showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    with chart_col2:
        chart_card_open("Orders by Status", "Current order fulfillment status breakdown")
        orders_status = data["orders"]["status"].value_counts().reset_index()
        orders_status.columns = ["status", "count"]
        color_map = {"Delivered": "#10B981", "Dispatched": "#2563EB", "Pending": "#F59E0B", "Delayed": "#EF4444", "Cancelled": "#9CA3AF"}
        fig = go.Figure(go.Pie(
            labels=orders_status["status"], values=orders_status["count"],
            hole=0.55,
            marker=dict(colors=[color_map.get(s, "#8B5CF6") for s in orders_status["status"]]),
            textinfo="label+percent", textfont=dict(size=13),
        ))
        fig = styled_chart(fig, 340)
        fig.update_layout(showlegend=False,
            annotations=[dict(text=f"<b>{len(data['orders'])}</b><br>Orders", x=0.5, y=0.5, font_size=15, showarrow=False, font=dict(color="#111827"))])
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        chart_card_open("Zone Utilization", "Capacity usage by warehouse zone with threshold markers")
        zone_color = {"Critical": "#EF4444", "Warning": "#F59E0B", "Normal": "#10B981"}
        fig = go.Figure(go.Bar(
            x=zone_util["zone_id"], y=zone_util["utilization_pct"],
            marker=dict(color=[zone_color[s] for s in zone_util["status"]], cornerradius=6),
            text=zone_util["utilization_pct"].apply(lambda x: f"{x}%"),
            textposition="outside", textfont=dict(size=11, weight="bold"),
        ))
        fig.add_hline(y=90, line_dash="dot", line_color="#EF4444", line_width=1.5,
            annotation_text="Critical 90%", annotation_font_color="#EF4444", annotation_font_size=10)
        fig.add_hline(y=75, line_dash="dot", line_color="#F59E0B", line_width=1.5,
            annotation_text="Warning 75%", annotation_font_color="#D97706", annotation_font_size=10)
        fig = styled_chart(fig, 340)
        fig.update_layout(yaxis_range=[0, 115], showlegend=False)
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    with chart_col4:
        chart_card_open("Top 10 Most Delayed Orders", "Orders with the longest dispatch delay in days")
        delayed_orders = get_delayed_orders(data["orders"])
        if len(delayed_orders) > 0:
            top_delayed = delayed_orders.nlargest(10, "delay_days")
            fig = go.Figure(go.Bar(
                x=top_delayed["sku_id"], y=top_delayed["delay_days"],
                marker=dict(color=top_delayed["delay_days"], colorscale=[[0, "#FBBF24"], [0.5, "#F97316"], [1, "#EF4444"]], cornerradius=4),
                text=top_delayed["delay_days"].apply(lambda x: f"{x}d"),
                textposition="outside", textfont=dict(size=10),
            ))
            fig = styled_chart(fig, 340)
            fig.update_layout(yaxis_title="Delay (days)")
            st.plotly_chart(fig, width="stretch")
        chart_card_close()

    chart_col5, chart_col6 = st.columns(2)

    with chart_col5:
        chart_card_open("Top 10 Fast Moving SKUs", "Highest average daily sales velocity")
        fast = get_fast_moving_skus(data["inventory"], 10)
        fig = go.Figure(go.Bar(
            x=fast["sku_id"], y=fast["avg_daily_sales"],
            marker=dict(color=fast["avg_daily_sales"], colorscale=[[0, "#A5B4FC"], [1, "#2563EB"]], cornerradius=4),
            text=fast["avg_daily_sales"].apply(lambda x: f"{x:.0f}"),
            textposition="outside", textfont=dict(size=10),
        ))
        fig = styled_chart(fig, 340)
        fig.update_layout(yaxis_title="Avg Daily Sales")
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    with chart_col6:
        chart_card_open("Pending Dispatches by Zone", "Orders awaiting dispatch grouped by warehouse zone")
        pending_by_zone = data["orders"][data["orders"]["status"] == "Pending"].groupby("warehouse_zone").size().reset_index(name="count").sort_values("count", ascending=True)
        fig = go.Figure(go.Bar(
            y=pending_by_zone["warehouse_zone"], x=pending_by_zone["count"],
            orientation='h',
            marker=dict(color="#EF4444", cornerradius=4),
            text=pending_by_zone["count"], textposition="outside", textfont=dict(size=11),
        ))
        fig = styled_chart(fig, 340)
        fig.update_layout(xaxis=dict(showticklabels=False, showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    render_footer()


# ═════════════════════════════════════════════════════════════════════
# PAGE: INVENTORY INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════
elif page == "Inventory Intelligence":
    render_header("Inventory Intelligence", "Low stock, overstock, dead stock and reorder recommendations")

    inv = data["inventory"]
    low_stock = get_low_stock_items(inv)
    overstock = get_overstock_items(inv)
    dead_stock = get_dead_stock_items(inv)
    fast_moving = get_fast_moving_skus(inv, 20)
    reorder = get_reorder_recommendations(inv)
    est_cost = f"INR {reorder['estimated_cost'].sum():,.0f}" if len(reorder) > 0 else "N/A"

    def _inventory_tab_report_ui(tab_key: str):
        """Scoped HTML report for the active tab only (not the old global mixed plan)."""
        if st.button("Generate report for this tab", key=f"inv_gen_{tab_key}"):
            st.session_state[f"inv_rep_{tab_key}"] = generate_inventory_tab_report(inv, data, tab_key)
        html = st.session_state.get(f"inv_rep_{tab_key}")
        if html:
            st.caption(
                "Report matches **this tab only**. Regenerate anytime; with the same CSV data the tables stay in the same order (no random shuffling)."
            )
            st.markdown(html, unsafe_allow_html=True)

    render_kpi_grid([
        (len(low_stock), "Low Stock", "alert-triangle", "red", "Below reorder level"),
        (len(overstock), "Overstock", "archive", "amber", "Above 85% max capacity"),
        (len(dead_stock), "Dead Stock", "clock", "purple", "No movement > 60 days"),
        (len(fast_moving), "Fast Moving", "zap", "green", "Top by daily sales"),
        (est_cost, "Est. Reorder Investment", "cart", "blue", "For low-stock items"),
    ], 5)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        ["Low Stock", "Overstock", "Dead Stock", "Fast Moving", "Reorder", "Dead Stock Analysis", "Liquidation", "Resource & charges"]
    )

    with tab1:
        render_section("Low Stock Items")
        st.caption("SKUs where current stock is at or below reorder level")
        if len(low_stock) > 0:
            render_alert(f"<strong>{len(low_stock)} SKUs</strong> are at critical low stock. Immediate reorder required.", "critical")
            df_ls = low_stock[["sku_id", "product_name", "category", "warehouse_zone", "current_stock", "reorder_level", "max_stock", "supplier_name"]].copy()
            df_ls.columns = ["SKU", "Product", "Category", "Zone", "Stock", "Reorder Lvl", "Max Stock", "Supplier"]
            st.markdown(df_to_styled_table(df_ls, "Low Stock Items", f"{len(low_stock)} SKUs below reorder level", highlight_cols={"Stock": "#EF4444", "SKU": "#111827"}), unsafe_allow_html=True)
        else:
            render_alert("No low stock items detected.", "success")
        _inventory_tab_report_ui("low_stock")

    with tab2:
        render_section("Overstock Items")
        st.caption("SKUs at or above 85% of maximum stock capacity")
        if len(overstock) > 0:
            render_alert(f"<strong>{len(overstock)} SKUs</strong> are overstocked and occupying excess space.", "warning")
            df_os = overstock[["sku_id", "product_name", "category", "warehouse_zone", "current_stock", "max_stock", "unit_price"]].copy()
            df_os.columns = ["SKU", "Product", "Category", "Zone", "Stock", "Max Stock", "Unit Price"]
            st.markdown(df_to_styled_table(df_os, "Overstock Items", f"{len(overstock)} SKUs above 85% max capacity", highlight_cols={"Stock": "#F59E0B", "SKU": "#111827"}), unsafe_allow_html=True)
        else:
            render_alert("No overstock items detected.", "success")
        _inventory_tab_report_ui("overstock")

    with tab3:
        render_section("Dead Stock Items")
        st.caption("SKUs with no movement in over 60 days")
        if len(dead_stock) > 0:
            dead_display = dead_stock.copy()
            dead_display["days_inactive"] = (datetime.now() - dead_display["last_movement_date"]).dt.days
            render_alert(f"<strong>{len(dead_stock)} SKUs</strong> have had no movement for over 60 days.", "warning")
            df_ds = dead_display[["sku_id", "product_name", "category", "warehouse_zone", "current_stock", "days_inactive", "unit_price"]].copy()
            df_ds.columns = ["SKU", "Product", "Category", "Zone", "Stock", "Days Inactive", "Unit Price"]
            st.markdown(df_to_styled_table(df_ds, "Dead Stock Items", f"{len(dead_stock)} SKUs with no movement > 60 days", highlight_cols={"Days Inactive": "#8B5CF6", "SKU": "#111827"}), unsafe_allow_html=True)
        else:
            render_alert("No dead stock items detected.", "success")
        _inventory_tab_report_ui("dead_stock")

    with tab4:
        render_section("Fast Moving SKUs")
        st.caption("Top SKUs by average daily sales velocity")
        df_fm = fast_moving[["sku_id", "product_name", "category", "warehouse_zone", "avg_daily_sales", "current_stock", "reorder_level"]].copy()
        df_fm.columns = ["SKU", "Product", "Category", "Zone", "Avg Daily Sales", "Stock", "Reorder Lvl"]
        df_fm["Avg Daily Sales"] = df_fm["Avg Daily Sales"].round(1)
        st.markdown(df_to_styled_table(df_fm, "Fast Moving SKUs", "Top SKUs by daily sales velocity", max_rows=20, highlight_cols={"Avg Daily Sales": "#10B981", "SKU": "#111827"}), unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=fast_moving["sku_id"].head(15), y=fast_moving["avg_daily_sales"].head(15),
            marker=dict(color=fast_moving["avg_daily_sales"].head(15), colorscale=[[0, "#A5B4FC"], [1, "#2563EB"]], cornerradius=4),
            text=fast_moving["avg_daily_sales"].head(15).apply(lambda x: f"{x:.1f}"), textposition="outside",
        ))
        fig = styled_chart(fig, 350)
        fig.update_layout(yaxis_title="Avg Daily Sales")
        st.plotly_chart(fig, width="stretch")
        _inventory_tab_report_ui("fast_moving")

    with tab5:
        render_section("Reorder Recommendations")
        if len(reorder) > 0:
            df_ro = reorder[["sku_id", "product_name", "current_stock", "reorder_level", "max_stock", "recommended_reorder_qty", "estimated_cost", "supplier_name"]].copy()
            df_ro.columns = ["SKU", "Product", "Stock", "Reorder Lvl", "Max", "Reorder Qty", "Est. Cost", "Supplier"]
            df_ro["Est. Cost"] = df_ro["Est. Cost"].apply(lambda x: f"INR {x:,.0f}")
            df_ro["Reorder Qty"] = df_ro["Reorder Qty"].astype(int)
            st.markdown(df_to_styled_table(df_ro, "Reorder Recommendations", f"{len(reorder)} SKUs recommended for reorder", max_rows=15, highlight_cols={"Reorder Qty": "#2563EB", "Est. Cost": "#8B5CF6", "SKU": "#111827"}), unsafe_allow_html=True)
            render_kpi_grid([
                (len(reorder), "SKUs to Reorder", "alert-triangle", "red"),
                (f"{reorder['recommended_reorder_qty'].sum():,.0f}", "Total Units Needed", "cube", "amber"),
                (f"INR {reorder['estimated_cost'].sum():,.0f}", "Estimated Investment", "cart", "purple"),
            ], 3)
        _inventory_tab_report_ui("reorder")

    with tab6:
        render_section("Dead Stock Root Cause Analysis")
        st.caption("Understanding why products are not selling and the financial impact")
        dead_analysis = get_dead_stock_analysis(inv)
        if len(dead_analysis) > 0:
            total_storage = dead_analysis["total_storage_cost"].sum() if "total_storage_cost" in dead_analysis.columns else 0
            total_inv_value = dead_analysis["inventory_value"].sum() if "inventory_value" in dead_analysis.columns else 0
            expired_count = int(dead_analysis["is_expired"].sum()) if "is_expired" in dead_analysis.columns else 0
            perishable_loss = dead_analysis["perishable_loss"].sum() if "perishable_loss" in dead_analysis.columns else 0
            render_kpi_grid([
                (len(dead_analysis), "Dead Stock SKUs", "archive", "purple"),
                (f"INR {total_storage:,.0f}", "Storage Cost Wasted", "timer", "red"),
                (f"INR {total_inv_value:,.0f}", "Tied-Up Inventory Value", "cart", "amber"),
                (expired_count, "Expired Perishable Items", "x-circle", "red"),
                (f"INR {perishable_loss:,.0f}", "Perishable Loss", "alert-triangle", "red"),
            ], 5)
            if "dead_stock_reason" in dead_analysis.columns:
                reason_counts = dead_analysis["dead_stock_reason"].value_counts().reset_index()
                reason_counts.columns = ["Reason", "Count"]
                render_alert(f"<strong>Top reasons for dead stock:</strong> {', '.join(reason_counts.head(3)['Reason'].tolist())}", "warning")
                st.markdown(df_to_styled_table(reason_counts, "Dead Stock by Reason", "Why products are not selling", highlight_cols={"Count": "#8B5CF6", "Reason": "#111827"}), unsafe_allow_html=True)
            cols_show = ["sku_id", "product_name", "current_stock", "days_inactive", "storage_cost_per_day", "total_storage_cost", "is_perishable", "dead_stock_reason"]
            cols_avail = [c for c in cols_show if c in dead_analysis.columns]
            df_da = dead_analysis[cols_avail].copy()
            df_da.columns = [c.replace("_", " ").title() for c in df_da.columns]
            if "Total Storage Cost" in df_da.columns:
                df_da["Total Storage Cost"] = df_da["Total Storage Cost"].apply(lambda x: f"INR {x:,.0f}")
            st.markdown(df_to_styled_table(df_da, "Dead Stock Detail", f"{len(dead_analysis)} items with full cost analysis", max_rows=15, highlight_cols={"Total Storage Cost": "#EF4444", "Sku Id": "#111827"}), unsafe_allow_html=True)
        else:
            render_alert("No dead stock items detected.", "success")
        _inventory_tab_report_ui("dead_stock_analysis")

    with tab7:
        render_section("Liquidation Strategies")
        st.caption("Recommended strategies to recover value from dead stock")
        strategies = get_liquidation_strategies(inv)
        if len(strategies) > 0:
            import pandas as pd
            df_strat = pd.DataFrame(strategies)
            total_recovery = df_strat["recovery"].sum()
            total_value = df_strat["inventory_value"].sum()
            total_storage = df_strat["storage_cost"].sum()
            render_kpi_grid([
                (f"INR {total_value:,.0f}", "Dead Stock Value", "archive", "red"),
                (f"INR {total_recovery:,.0f}", "Potential Recovery", "check-circle", "green"),
                (f"INR {total_storage:,.0f}", "Ongoing Storage Cost", "timer", "amber"),
                (f"{(total_recovery/max(total_value,1)*100):.0f}%", "Recovery Rate", "zap", "blue"),
            ], 4)
            strategy_counts = df_strat["strategy"].value_counts().reset_index()
            strategy_counts.columns = ["Strategy", "Items"]
            render_alert(f"<strong>Recovery plan:</strong> {len(df_strat)} items analyzed. Potential to recover <strong>INR {total_recovery:,.0f}</strong> ({(total_recovery/max(total_value,1)*100):.0f}% of tied-up value).", "info")
            df_show = df_strat[["sku_id", "product_name", "stock", "reason", "strategy", "inventory_value", "recovery"]].copy()
            df_show["inventory_value"] = df_show["inventory_value"].apply(lambda x: f"INR {x:,.0f}")
            df_show["recovery"] = df_show["recovery"].apply(lambda x: f"INR {x:,.0f}")
            df_show.columns = ["SKU", "Product", "Stock", "Dead Reason", "Strategy", "Inv. Value", "Est. Recovery"]
            st.markdown(df_to_styled_table(df_show, "Liquidation Plan", "Strategy per dead stock item", max_rows=20, highlight_cols={"Strategy": "#2563EB", "Est. Recovery": "#10B981", "SKU": "#111827"}), unsafe_allow_html=True)
            st.markdown(df_to_styled_table(strategy_counts, "Strategy Distribution", "Breakdown by liquidation method", highlight_cols={"Items": "#8B5CF6", "Strategy": "#111827"}), unsafe_allow_html=True)
        else:
            render_alert("No dead stock items to liquidate.", "success")
        _inventory_tab_report_ui("liquidation")

    with tab8:
        render_section("Resource optimization & warehouse charges")
        st.caption("Tie dead stock, faster throughput, and zone energy to cost — answers: reduce resources, close/consolidate zones, cut holding cost")
        opt = get_resource_optimization(data)
        render_kpi_grid([
            (f"INR {opt['dead_storage_cost']:,.0f}", "Est. dead-stock holding cost", "timer", "red", "Storage tied to inactive SKUs"),
            (f"INR {opt['total_energy_cost']:,.0f}", "Monthly energy (all zones)", "zap", "amber", "From zone energy × 30 days"),
            (f"{opt['potential_space_freed']:,}", "Units in dead stock", "archive", "purple", "Units to free if liquidated"),
            (opt["critical_zones"], "Critical zones", "alert-triangle", "red", ">90% utilization"),
        ], 4)
        zb = opt["zone_breakdown"]
        df_zb = zb[["zone_name", "utilization_pct", "energy_cost_monthly", "dead_stock_units", "potential_space_freed_pct", "status"]].copy()
        df_zb["energy_cost_monthly"] = df_zb["energy_cost_monthly"].apply(lambda x: f"INR {float(x):,.0f}")
        df_zb["utilization_pct"] = df_zb["utilization_pct"].apply(lambda x: f"{x}%")
        df_zb["potential_space_freed_pct"] = df_zb["potential_space_freed_pct"].apply(lambda x: f"{x}%")
        df_zb.columns = ["Zone", "Utilization", "Energy / month", "Dead stock units", "Dead as % of used", "Status"]
        st.markdown(df_to_styled_table(df_zb, "Where cost hides", "Per zone: utilization, monthly energy estimate, dead units", highlight_cols={"Dead stock units": "#8B5CF6", "Zone": "#111827"}, status_col="Status"), unsafe_allow_html=True)
        render_recommendation(1, "Clear <strong>dead stock units</strong> first to recover space and reduce per-day storage and climate cost.")
        render_recommendation(2, "Speed <strong>dispatch and picking</strong> in high-energy zones (for example cold storage) so fewer SKU-days are held under expensive conditions.")
        render_recommendation(3, "When utilization allows, <strong>consolidate SKUs</strong> out of critical zones to defer expansion and overtime.")
        _inventory_tab_report_ui("resource")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Full consolidated inventory plan (all topics in one report)", expanded=False):
        st.caption("Optional: single report covering reorder, overstock, and dead stock together—not tied to a single tab above.")
        if st.button("Generate full inventory action plan", key="inv_gen_full_plan"):
            st.session_state["inv_rep_full"] = generate_inventory_action_plan(inv)
        if st.session_state.get("inv_rep_full"):
            st.markdown(st.session_state["inv_rep_full"], unsafe_allow_html=True)

    render_footer()


# ═════════════════════════════════════════════════════════════════════
# PAGE: DISPATCH INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════
elif page == "Dispatch Intelligence":
    render_header("Dispatch Intelligence", "Delay monitoring, priority risks, loading bay bottlenecks and picking errors")

    st.info(
        "Scroll tabs right for **Delay Root Causes**, **Route & Bay Optimization**, and **Customer Impact**. "
        "Use **Generate report for this tab** inside each tab for a scoped PDF-style summary; the **consolidated** all-in-one report is in the expander at the bottom."
    )

    orders = data["orders"]
    picking = data["picking"]
    delayed = get_delayed_orders(orders)
    pending = get_pending_orders(orders)
    high_priority = get_high_priority_delayed(orders)
    bay_stats = get_dispatch_by_bay(picking)
    worst_zone = delayed.groupby("warehouse_zone").size().idxmax() if len(delayed) > 0 else "N/A"
    slowest_bay = bay_stats.iloc[0]["loading_bay"] if len(bay_stats) > 0 else "N/A"

    def _dispatch_tab_report_ui(tab_key: str):
        if st.button("Generate report for this tab", key=f"dis_gen_{tab_key}"):
            st.session_state[f"dis_rep_{tab_key}"] = generate_dispatch_tab_report(data, tab_key)
        html = st.session_state.get(f"dis_rep_{tab_key}")
        if html:
            st.caption("This PDF-style block matches **this tab only**. Use **Consolidated dispatch summary** below for the all-in-one view.")
            st.markdown(html, unsafe_allow_html=True)

    render_kpi_grid([
        (len(delayed), "Delayed Orders", "clock", "red", "Beyond promised dispatch"),
        (len(pending), "Pending Orders", "truck", "amber", "Awaiting dispatch"),
        (len(high_priority), "High Priority Delays", "alert-triangle", "red", "High-priority delayed"),
        (worst_zone, "Worst Zone", "building", "purple", "Most delayed orders"),
        (slowest_bay, "Slowest Bay", "timer", "cyan", "Highest avg dispatch time"),
    ], 5)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Delayed Orders", "Pending Orders", "Picking Errors", "Loading Bay Analysis", "Delay Root Causes", "Route & Bay Optimization", "Customer Impact"])

    with tab1:
        render_section("Delayed Orders")
        if len(delayed) > 0:
            render_alert(f"<strong>{len(delayed)} orders</strong> are delayed. <strong>{len(high_priority)}</strong> are high-priority.", "critical")
            priority_filter = st.multiselect("Filter by Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
            filtered = delayed[delayed["priority"].isin(priority_filter)]
            df_dl = filtered[["order_id", "customer_name", "sku_id", "order_quantity", "promised_dispatch_date", "delay_days", "warehouse_zone", "priority"]].sort_values("delay_days", ascending=False).copy()
            df_dl["promised_dispatch_date"] = df_dl["promised_dispatch_date"].dt.strftime("%Y-%m-%d")
            df_dl.columns = ["Order", "Customer", "SKU", "Qty", "Promised Date", "Delay (days)", "Zone", "Priority"]
            st.markdown(df_to_styled_table(df_dl, "Delayed Orders", f"{len(filtered)} orders behind schedule", highlight_cols={"Delay (days)": "#EF4444", "Order": "#111827"}, status_col="Priority"), unsafe_allow_html=True)
        _dispatch_tab_report_ui("delayed")

    with tab2:
        render_section("Pending Orders")
        if len(pending) > 0:
            df_pn = pending[["order_id", "customer_name", "sku_id", "order_quantity", "order_date", "promised_dispatch_date", "warehouse_zone", "priority"]].copy()
            df_pn["order_date"] = df_pn["order_date"].dt.strftime("%Y-%m-%d")
            df_pn["promised_dispatch_date"] = df_pn["promised_dispatch_date"].dt.strftime("%Y-%m-%d")
            df_pn.columns = ["Order", "Customer", "SKU", "Qty", "Order Date", "Promised Date", "Zone", "Priority"]
            st.markdown(df_to_styled_table(df_pn, "Pending Orders", f"{len(pending)} orders awaiting dispatch", highlight_cols={"Order": "#111827"}, status_col="Priority"), unsafe_allow_html=True)
        else:
            render_alert("No pending orders at this time.", "success")
        _dispatch_tab_report_ui("pending")

    with tab3:
        render_section("Picking Error Summary")
        picker_errors = get_picking_errors_by_picker(picking)
        df_pe = picker_errors.round(2).copy()
        df_pe.columns = [c.replace("_", " ").title() for c in df_pe.columns]
        st.markdown(df_to_styled_table(df_pe, "Picking Error Summary", "Error rates by picker", highlight_cols={"Total Errors": "#EF4444", "Picker Name": "#111827"}), unsafe_allow_html=True)
        _dispatch_tab_report_ui("picking_errors")

    with tab4:
        render_section("Loading Bay Performance")
        df_bay = bay_stats.round(1).copy()
        df_bay.columns = [c.replace("_", " ").title() for c in df_bay.columns]
        st.markdown(df_to_styled_table(df_bay, "Loading Bay Performance", "Dispatch metrics by loading bay", highlight_cols={"Avg Time": "#8B5CF6", "Loading Bay": "#111827", "Total Errors": "#EF4444"}), unsafe_allow_html=True)
        _dispatch_tab_report_ui("loading_bay")

    with tab5:
        render_section("Delay Root Cause Analysis")
        st.caption("Understanding why deliveries are delayed and how to fix them")
        delay_causes = get_delay_root_causes(orders)
        if len(delay_causes) > 0:
            render_alert(f"<strong>{len(delay_causes)} distinct delay reasons</strong> identified across {len(delayed)+len(pending)} affected orders.", "warning")
            cols_show = [c for c in ["delay_reason", "count", "avg_delay", "max_delay"] if c in delay_causes.columns]
            df_dc = delay_causes[cols_show].copy()
            df_dc.columns = [c.replace("_", " ").title() for c in df_dc.columns]
            if "Avg Delay" in df_dc.columns:
                df_dc["Avg Delay"] = df_dc["Avg Delay"].apply(lambda x: f"{x:.1f} days")
            if "Max Delay" in df_dc.columns:
                df_dc["Max Delay"] = df_dc["Max Delay"].apply(lambda x: f"{int(x)} days")
            st.markdown(df_to_styled_table(df_dc, "Delay Reasons Breakdown", "Root causes for all delayed and pending orders", highlight_cols={"Count": "#EF4444", "Delay Reason": "#111827"}), unsafe_allow_html=True)
            render_recommendation(1, "Address <strong>top delay reasons</strong> with targeted action plans for each root cause.")
            render_recommendation(2, "Add picking resources and staffing to zones with <strong>Picker Shortage</strong> delays.")
            render_recommendation(3, "Fix <strong>Loading Bay Bottleneck</strong> issues with load redistribution and equipment upgrades.")
        else:
            render_alert("No delay data available for analysis.", "info")
        error_analysis = get_picking_error_analysis(picking)
        if len(error_analysis) > 0:
            render_section("Picking Error Types")
            df_err = error_analysis.copy()
            df_err.columns = [c.replace("_", " ").title() for c in df_err.columns]
            st.markdown(df_to_styled_table(df_err, "Error Type Analysis", "Types of picking errors and their frequency", highlight_cols={"Total Errors": "#EF4444", "Error Type": "#111827"}), unsafe_allow_html=True)
        _dispatch_tab_report_ui("delay_root_causes")

    with tab6:
        render_section("Route & Bay Optimization")
        st.caption("Identifying the best routes, bays, and vehicles for maximum efficiency")
        bay_opt = get_bay_optimization(picking)
        if len(bay_opt) > 0 and "efficiency_score" in bay_opt.columns:
            best_bay = bay_opt.iloc[0]
            render_kpi_grid([
                (best_bay["loading_bay"], "Best Bay", "check-circle", "green", f"Efficiency: {best_bay['efficiency_score']}"),
                (f"{best_bay['avg_time']:.0f} min", "Avg Time (Best)", "timer", "blue"),
                (f"INR {best_bay['cost_per_dispatch']:.0f}", "Cost/Dispatch (Best)", "cart", "green"),
            ], 3)
            df_bo = bay_opt[["loading_bay", "avg_time", "total_dispatches", "total_errors", "cost_per_dispatch", "efficiency_score"]].round(1).copy()
            df_bo.columns = ["Bay", "Avg Time (min)", "Dispatches", "Errors", "Cost/Dispatch (INR)", "Efficiency Score"]
            st.markdown(df_to_styled_table(df_bo, "Bay Efficiency Ranking", "Sorted by efficiency score (higher is better)", highlight_cols={"Efficiency Score": "#10B981", "Bay": "#111827", "Cost/Dispatch (INR)": "#8B5CF6"}), unsafe_allow_html=True)
        route_eff = get_route_efficiency(data)
        if len(route_eff) > 0:
            render_section("Route Performance")
            cols_show = [c for c in ["route_id", "route_name", "route_type", "orders", "avg_distance", "avg_cost", "delayed", "delay_pct", "congestion_level", "best_vehicle"] if c in route_eff.columns]
            df_re = route_eff[cols_show].copy()
            df_re.columns = [c.replace("_", " ").title() for c in df_re.columns]
            if "Avg Cost" in df_re.columns:
                df_re["Avg Cost"] = df_re["Avg Cost"].apply(lambda x: f"INR {x:,.0f}")
            if "Avg Distance" in df_re.columns:
                df_re["Avg Distance"] = df_re["Avg Distance"].apply(lambda x: f"{x:.0f} km")
            if "Delay Pct" in df_re.columns:
                df_re["Delay Pct"] = df_re["Delay Pct"].apply(lambda x: f"{x}%")
            st.markdown(df_to_styled_table(df_re, "Route Performance Analysis", "Route costs, delays, and recommended vehicles", max_rows=12, highlight_cols={"Route Id": "#111827", "Delay Pct": "#EF4444", "Avg Cost": "#8B5CF6"}), unsafe_allow_html=True)
        _dispatch_tab_report_ui("route_bay")

    with tab7:
        render_section("Customer Impact Analysis")
        st.caption("Customers most affected by delivery delays and recommended recovery actions")
        customer_imp = get_customer_impact(orders)
        if len(customer_imp) > 0:
            render_alert(f"<strong>{len(customer_imp)} customers</strong> impacted by delivery delays. Top affected: <strong>{customer_imp.iloc[0]['customer_name']}</strong> with {int(customer_imp.iloc[0]['delayed_orders'])} delayed orders.", "critical")
            df_ci = customer_imp.copy()
            df_ci["avg_delay"] = df_ci["avg_delay"].apply(lambda x: f"{x:.1f} days")
            df_ci.columns = ["Customer", "Delayed Orders", "Total Delay Days", "Avg Delay", "Total Qty Affected"]
            st.markdown(df_to_styled_table(df_ci, "Customer Delay Impact", f"{len(customer_imp)} affected customers ranked by severity", max_rows=20, highlight_cols={"Delayed Orders": "#EF4444", "Customer": "#111827", "Total Delay Days": "#8B5CF6"}), unsafe_allow_html=True)
            render_recommendation(1, "Send <strong>proactive communications</strong> to top-impacted customers with revised delivery timelines.")
            render_recommendation(2, "<strong>Expedite pending orders</strong> for customers with 3+ delayed orders to prevent churn.")
            render_recommendation(3, "Offer <strong>discount or priority shipping</strong> on next order as goodwill recovery.")
        else:
            render_alert("No customer delay impact data available.", "success")
        _dispatch_tab_report_ui("customer_impact")

    st.caption("Charts below are **fleet-wide** (not tab-specific).")

    render_section("Dispatch Analytics")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        chart_card_open("Delayed Orders by Zone", "Delay distribution across warehouse zones")
        if len(delayed) > 0:
            delay_zone = delayed.groupby("warehouse_zone").size().reset_index(name="count").sort_values("count")
            fig = go.Figure(go.Bar(
                y=delay_zone["warehouse_zone"], x=delay_zone["count"], orientation='h',
                marker=dict(color=delay_zone["count"], colorscale=[[0, "#FBBF24"], [1, "#EF4444"]], cornerradius=4),
                text=delay_zone["count"], textposition="outside",
            ))
            fig = styled_chart(fig, 320)
            fig.update_layout(xaxis=dict(showticklabels=False, showgrid=False), yaxis=dict(showgrid=False))
            st.plotly_chart(fig, width="stretch")
        chart_card_close()

    with chart_col2:
        chart_card_open("Orders by Priority", "High / Medium / Low priority breakdown")
        priority_dist = orders["priority"].value_counts().reset_index()
        priority_dist.columns = ["priority", "count"]
        fig = go.Figure(go.Pie(
            labels=priority_dist["priority"], values=priority_dist["count"], hole=0.55,
            marker=dict(colors=["#EF4444", "#F59E0B", "#10B981"]),
            textinfo="label+percent", textfont=dict(size=13),
        ))
        fig = styled_chart(fig, 320)
        fig.update_layout(showlegend=False,
            annotations=[dict(text="<b>Priority</b>", x=0.5, y=0.5, font_size=14, showarrow=False, font=dict(color="#111827"))])
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        chart_card_open("Dispatch Status Distribution", "Completed / In Progress / Pending")
        status_dist = picking["status"].value_counts().reset_index()
        status_dist.columns = ["status", "count"]
        scolor = {"Completed": "#10B981", "In Progress": "#2563EB", "Pending": "#F59E0B"}
        fig = go.Figure(go.Pie(
            labels=status_dist["status"], values=status_dist["count"], hole=0.55,
            marker=dict(colors=[scolor.get(s, "#8B5CF6") for s in status_dist["status"]]),
            textinfo="label+percent", textfont=dict(size=13),
        ))
        fig = styled_chart(fig, 320)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    with chart_col4:
        chart_card_open("Picking Errors by Picker", "Error count per warehouse picker")
        picker_err = get_picking_errors_by_picker(picking).head(10)
        fig = go.Figure(go.Bar(
            x=picker_err["picker_name"], y=picker_err["total_errors"],
            marker=dict(color=picker_err["total_errors"], colorscale=[[0, "#FBBF24"], [1, "#EF4444"]], cornerradius=4),
            text=picker_err["total_errors"].astype(int), textposition="outside",
        ))
        fig = styled_chart(fig, 320)
        fig.update_layout(yaxis_title="Total Errors")
        st.plotly_chart(fig, width="stretch")
        chart_card_close()

    chart_card_open("Average Dispatch Time by Loading Bay", "Minutes per dispatch by loading bay location")
    fig = go.Figure(go.Bar(
        x=bay_stats["loading_bay"], y=bay_stats["avg_time"],
        marker=dict(color=bay_stats["avg_time"], colorscale=[[0, "#93C5FD"], [0.5, "#F97316"], [1, "#EF4444"]], cornerradius=6),
        text=bay_stats["avg_time"].apply(lambda x: f"{x:.0f} min"), textposition="outside",
    ))
    fig = styled_chart(fig, 340)
    fig.update_layout(yaxis_title="Minutes")
    st.plotly_chart(fig, width="stretch")
    chart_card_close()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Consolidated dispatch risk summary (all topics in one report)", expanded=False):
        st.caption("Optional: same content zones + customers + bays + priorities together—independent from each tab’s report above.")
        if st.button("Generate consolidated summary", key="dis_gen_full"):
            st.session_state["dis_rep_full"] = generate_dispatch_risk_summary(orders, picking)
        if st.session_state.get("dis_rep_full"):
            st.markdown(st.session_state["dis_rep_full"], unsafe_allow_html=True)

    render_footer()


# ═════════════════════════════════════════════════════════════════════
# PAGE: ZONE INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════
elif page == "Zone Intelligence":
    render_header("Zone Intelligence", "Space utilization, congestion risk and warehouse zone performance")

    st.info(
        "**Critical / Warning / Normal** zones, allowed vehicles, **expected critical-until** dates, throughput and **revenue potential** are in the table below — this maps to “which transport can pass”, “until when critical”, and profit-oriented routing."
    )

    zones = data["zones"]
    zone_util = get_zone_utilization(zones)
    inv = data["inventory"]
    orders = data["orders"]
    picking = data["picking"]

    critical_zones = zone_util[zone_util["status"] == "Critical"]
    warning_zones = zone_util[zone_util["status"] == "Warning"]
    normal_zones = zone_util[zone_util["status"] == "Normal"]
    total_avail = int((zone_util["capacity_units"] - zone_util["used_units"]).sum())

    render_kpi_grid([
        (len(critical_zones), "Critical Zones", "alert-triangle", "red", "Above 90% capacity"),
        (len(warning_zones), "Warning Zones", "archive", "amber", "75-90% capacity"),
        (len(normal_zones), "Normal Zones", "check-circle", "green", "Below 75% capacity"),
        (f"{zone_util['utilization_pct'].mean():.1f}%", "Avg Utilization", "building", "purple", "Across all zones"),
        (f"{total_avail:,}", "Available Capacity", "cube", "blue", "Total remaining units"),
    ], 5)

    chart_card_open("Zone Utilization Overview", "Capacity usage with critical and warning thresholds")
    zone_color = {"Critical": "#EF4444", "Warning": "#F59E0B", "Normal": "#10B981"}
    fig = go.Figure(go.Bar(
        x=zone_util["zone_name"], y=zone_util["utilization_pct"],
        marker=dict(color=[zone_color[s] for s in zone_util["status"]], cornerradius=6),
        text=zone_util["utilization_pct"].apply(lambda x: f"{x}%"),
        textposition="outside", textfont=dict(size=12, weight="bold"),
    ))
    fig.add_hline(y=90, line_dash="dot", line_color="#EF4444", line_width=1.5,
        annotation_text="Critical 90%", annotation_font_color="#EF4444", annotation_font_size=10)
    fig.add_hline(y=75, line_dash="dot", line_color="#F59E0B", line_width=1.5,
        annotation_text="Warning 75%", annotation_font_color="#D97706", annotation_font_size=10)
    fig = styled_chart(fig, 400)
    fig.update_layout(yaxis_range=[0, 115], showlegend=False)
    st.plotly_chart(fig, width="stretch")
    chart_card_close()

    col1, col2 = st.columns(2)

    with col1:
        render_section("Critical & Warning Zones")
        if len(critical_zones) > 0:
            for _, z in critical_zones.iterrows():
                render_premium_alert("critical", z["zone_name"],
                    f"{z['utilization_pct']}% utilized &mdash; {z['used_units']:,} / {z['capacity_units']:,} units &middot; Manager: {z['manager_name']}")
        if len(warning_zones) > 0:
            for _, z in warning_zones.iterrows():
                render_premium_alert("warning", z["zone_name"],
                    f"{z['utilization_pct']}% utilized &mdash; {z['used_units']:,} / {z['capacity_units']:,} units &middot; Manager: {z['manager_name']}")
        if len(critical_zones) == 0 and len(warning_zones) == 0:
            render_alert("All zones operating within normal limits.", "success")

    with col2:
        render_section("Available Capacity")
        avail = zone_util.copy()
        avail["available_units"] = avail["capacity_units"] - avail["used_units"]
        fig = go.Figure(go.Bar(
            x=avail["zone_name"], y=avail["available_units"],
            marker=dict(color=[zone_color[s] for s in avail["status"]], cornerradius=4),
            text=avail["available_units"].apply(lambda x: f"{x:,}"), textposition="outside",
        ))
        fig = styled_chart(fig, 320)
        fig.update_layout(yaxis_title="Units")
        st.plotly_chart(fig, width="stretch")

    render_section("Zone-wise Analysis")
    tab1, tab2, tab3 = st.tabs(["Stock by Zone", "Delayed Orders by Zone", "Picking Errors by Zone"])

    with tab1:
        zone_stock = inv.groupby("warehouse_zone")["current_stock"].agg(["count", "sum"]).reset_index()
        zone_stock.columns = ["warehouse_zone", "sku_count", "total_stock"]
        fig = go.Figure(go.Bar(
            x=zone_stock["warehouse_zone"], y=zone_stock["total_stock"],
            marker=dict(color=zone_stock["total_stock"], colorscale=[[0, "#A5B4FC"], [1, "#0F172A"]], cornerradius=4),
            text=zone_stock["total_stock"].apply(lambda x: f"{x:,}"), textposition="outside",
        ))
        fig = styled_chart(fig, 350)
        fig.update_layout(yaxis_title="Stock Units")
        st.plotly_chart(fig, width="stretch")

    with tab2:
        delayed_by_zone = orders[orders["status"].isin(["Delayed", "Pending"])].groupby("warehouse_zone").size().reset_index(name="delayed_count")
        fig = go.Figure(go.Bar(
            x=delayed_by_zone["warehouse_zone"], y=delayed_by_zone["delayed_count"],
            marker=dict(color="#EF4444", cornerradius=4),
            text=delayed_by_zone["delayed_count"], textposition="outside",
        ))
        fig = styled_chart(fig, 350)
        fig.update_layout(yaxis_title="Count")
        st.plotly_chart(fig, width="stretch")

    with tab3:
        errors_by_zone = picking.groupby("warehouse_zone")["picking_errors"].sum().reset_index()
        fig = go.Figure(go.Bar(
            x=errors_by_zone["warehouse_zone"], y=errors_by_zone["picking_errors"],
            marker=dict(color="#F59E0B", cornerradius=4),
            text=errors_by_zone["picking_errors"], textposition="outside",
        ))
        fig = styled_chart(fig, 350)
        fig.update_layout(yaxis_title="Total Errors")
        st.plotly_chart(fig, width="stretch")

    render_section("Zone Optimization Recommendations")
    zone_rec_html = '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.07);">'
    zone_rec_html += '<div style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);padding:18px 24px;"><div style="font-size:0.6rem;font-weight:700;color:#06B6D4;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;">AI Recommendations</div><div style="font-size:1rem;font-weight:700;color:white;">Zone Optimization Action Plan</div></div>'
    zone_rec_html += '<div style="padding:12px 0 16px 0;">'
    from utils.analytics import _html_action_item
    zone_rec_html += _html_action_item(1, "<strong>Move slow-moving inventory</strong> from critical zones to zones with available capacity to relieve congestion and prevent picking delays.", "#EF4444")
    zone_rec_html += _html_action_item(2, "<strong>Rebalance fast-moving SKUs</strong> into Zone A (Fast Moving) for optimal picking speed and reduced travel time across the warehouse floor.", "#2563EB")
    zone_rec_html += _html_action_item(3, "<strong>Improve picker-to-zone allocation</strong> in congested zones and introduce batch picking methodology to reduce errors and increase throughput.", "#F59E0B")
    zone_rec_html += _html_action_item(4, "<strong>Prioritize dispatch scheduling</strong> from congested zones to free up capacity before next inbound shipments arrive at receiving docks.", "#8B5CF6")
    zone_rec_html += '</div>'
    zone_rec_html += '<div style="background:#F8FAFC;padding:10px 24px;border-top:1px solid #E5E7EB;font-size:0.7rem;color:#9CA3AF;">QubiWare AI &middot; Zone Intelligence Engine</div></div>'
    st.markdown(zone_rec_html, unsafe_allow_html=True)

    render_section("Zone Transport & Revenue Analysis")
    transport = get_zone_transport_analysis(data)
    if len(transport) > 0:
        cols_show = [c for c in ["zone_name", "utilization_pct", "status", "allowed_vehicle_types", "max_vehicle_capacity_tons", "congestion_reason", "expected_critical_until", "energy_cost_per_day", "zone_throughput_rate", "revenue_potential_per_day", "utilization_trend"] if c in transport.columns]
        if len(cols_show) > 3:
            df_zt = transport[cols_show].copy()
            if "utilization_pct" in df_zt.columns:
                df_zt["utilization_pct"] = df_zt["utilization_pct"].apply(lambda x: f"{x}%")
            if "energy_cost_per_day" in df_zt.columns:
                df_zt["energy_cost_per_day"] = df_zt["energy_cost_per_day"].apply(lambda x: f"INR {x:,.0f}")
            if "revenue_potential_per_day" in df_zt.columns:
                df_zt["revenue_potential_per_day"] = df_zt["revenue_potential_per_day"].apply(lambda x: f"INR {x:,.0f}")
            df_zt.columns = [c.replace("_", " ").title() for c in df_zt.columns]
            st.markdown(df_to_styled_table(df_zt, "Zone Transport & Revenue Intelligence", "Vehicle restrictions, congestion reasons, throughput, and revenue potential per zone", max_rows=10, highlight_cols={"Zone Name": "#111827", "Status": "#8B5CF6"}), unsafe_allow_html=True)
            render_recommendation(1, "Assign <strong>right-sized vehicles</strong> based on allowed types and max capacity per zone to avoid damage and delays.")
            render_recommendation(2, "<strong>Redirect dispatch routes</strong> through zones with highest revenue potential and lowest congestion.")
            render_recommendation(3, "Monitor <strong>utilization trends</strong> to predict when zones will become critical and pre-allocate resources.")

    render_section("Zone Master Data")
    df_zm = zone_util[["zone_id", "zone_name", "capacity_units", "used_units", "utilization_pct", "status", "manager_name"]].copy()
    df_zm["utilization_pct"] = df_zm["utilization_pct"].apply(lambda x: f"{x}%")
    df_zm.columns = ["Zone ID", "Zone Name", "Capacity", "Used", "Utilization", "Status", "Manager"]
    st.markdown(df_to_styled_table(df_zm, "Zone Master Data", "Complete zone overview with utilization and status", highlight_cols={"Zone ID": "#111827", "Utilization": "#8B5CF6"}, status_col="Status"), unsafe_allow_html=True)

    render_footer()


# ═════════════════════════════════════════════════════════════════════
# PAGE: AI COPILOT
# ═════════════════════════════════════════════════════════════════════
elif page == "AI CoPilot":
    render_header("AI CoPilot", "Ask natural-language questions about warehouse, inventory and dispatch operations")

    suggestions = [
        "Which SKUs are at low-stock risk?",
        "Which warehouse zone is most congested?",
        "Which orders are delayed today?",
        "Which supplier has mismatch issues?",
        "Generate a warehouse performance summary",
        "Which loading bay is causing delay?",
        "Why is dead stock not selling and what is the perishable loss?",
        "How do we reduce warehouse charges and energy cost?",
        "What are the best routes and bays for low cost dispatch?",
        "What should we do with dead stock at break-even or low margin?",
    ]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown('<div class="chat-outer"><div class="chat-header"><div class="chat-header-dot"></div><div><div class="chat-header-text">QubiWare AI CoPilot</div><div class="chat-header-sub">Warehouse intelligence engine &middot; Ask anything</div></div></div></div>', unsafe_allow_html=True)

    if len(st.session_state.messages) == 0:
        st.markdown('<div style="text-align:center;padding:28px 20px 8px 20px;"><div style="display:inline-flex;align-items:center;justify-content:center;width:50px;height:50px;background:linear-gradient(135deg,#2563EB,#06B6D4);border-radius:14px;margin-bottom:12px;"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg></div><h4 style="color:#111827;margin:0 0 6px 0;font-weight:700;font-size:1.05rem;">How can I help you today?</h4><p style="color:#64748B;font-size:0.82rem;max-width:460px;margin:0 auto;line-height:1.5;">Ask QubiWare AI questions like: Which SKUs need reorder? Which zone is congested? Which orders are delayed?</p></div>', unsafe_allow_html=True)

        row1 = st.columns(5)
        row2 = st.columns(5)
        all_cols = [*row1, *row2]

        for i, s in enumerate(suggestions):
            if i < len(all_cols):
                with all_cols[i]:
                    if st.button(s, key=f"suggestion_{i}"):
                        st.session_state.messages.append({"role": "user", "content": s})
                        with st.spinner("Analyzing..."):
                            response = get_ai_response(s, data)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(f'<div style="font-size:0.65rem; font-weight:700; color:#2563EB; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">QubiWare AI CoPilot</div>', unsafe_allow_html=True)
            st.markdown(msg["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("Ask about inventory, orders, zones, dispatch, suppliers..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            st.markdown('<div style="font-size:0.65rem; font-weight:700; color:#2563EB; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">QubiWare AI CoPilot</div>', unsafe_allow_html=True)
            with st.spinner("Analyzing warehouse data..."):
                response = get_ai_response(prompt, data)
            st.markdown(response, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": response})

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if gemini_key:
            st.markdown(f'<span style="font-size:0.72rem; color:#10B981;">{render_badge("Gemini API Connected", "green")}</span>', unsafe_allow_html=True)
        elif openai_key:
            st.markdown(f'<span style="font-size:0.72rem; color:#10B981;">{render_badge("OpenAI API Connected", "green")}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="font-size:0.72rem;">{render_badge("Rule-based Engine", "slate")} Add API key to .env for enhanced AI</span>', unsafe_allow_html=True)
    with col3:
        if len(st.session_state.messages) > 0:
            if st.button("Clear Chat", type="primary"):
                st.session_state.messages = []
                st.rerun()

    render_footer()


# ═════════════════════════════════════════════════════════════════════
# PAGE: DAILY AI REPORT
# ═════════════════════════════════════════════════════════════════════
elif page == "Daily AI Report":
    render_header("Daily AI Report", "Generate management-ready warehouse performance reports")

    st.markdown('<div style="background:linear-gradient(135deg,#EFF6FF,#F0F9FF);border:1px solid #BFDBFE;border-radius:12px;padding:22px 26px;margin-bottom:24px;"><div style="font-weight:700;color:#1E40AF;margin-bottom:6px;font-size:0.92rem;">About this report</div><div style="color:#1E40AF;font-size:0.85rem;opacity:0.85;line-height:1.6;">Generate a complete daily warehouse performance report including executive summary, risk analysis across inventory, dispatch, and zones, KPI tracking, supplier issues, picking accuracy analysis, and recommended actions with an email draft for the operations manager.</div></div>', unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        generate_clicked = st.button("Generate Daily Warehouse Report", type="primary")

    if generate_clicked:
        with st.spinner("Generating comprehensive report..."):
            st.session_state["report_ready"] = True
            try:
                pdf_bytes = generate_pdf_report(data)
                st.session_state["daily_report_pdf"] = pdf_bytes
            except Exception:
                st.session_state["daily_report_pdf"] = None

    if st.session_state.get("report_ready"):
        kpis = compute_kpis(data)
        low_stock = get_low_stock_items(data["inventory"])
        overstock = get_overstock_items(data["inventory"])
        dead_stock = get_dead_stock_items(data["inventory"])
        delayed = get_delayed_orders(data["orders"])
        pending = get_pending_orders(data["orders"])
        high_priority = get_high_priority_delayed(data["orders"])
        zone_util_r = get_zone_utilization(data["zones"])
        picker_errors = get_picking_errors_by_picker(data["picking"])
        mismatches = get_inbound_mismatches(data["inbound"])
        supplier_issues_r = get_supplier_issues(data["inbound"])
        critical_zones = zone_util_r[zone_util_r["status"] == "Critical"]

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            pdf_data = st.session_state.get("daily_report_pdf")
            if pdf_data:
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_data,
                    file_name=f"QubiWare_Daily_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    type="primary",
                )

        render_section("Executive Summary")
        render_alert(
            f"Today's operations show <strong>{len(low_stock)} SKUs at critical low stock</strong>, "
            f"<strong>{len(delayed)} delayed orders</strong> ({len(high_priority)} high-priority), "
            f"and warehouse utilization averaging <strong>{kpis['Warehouse Utilization %']}%</strong>. "
            f"There are <strong>{len(critical_zones)} zone(s) in critical state</strong>. "
            f"Picking accuracy: <strong>{kpis['Picking Accuracy %']}%</strong>. "
            f"Inbound mismatches: <strong>{len(mismatches)}</strong>.",
            "info"
        )

        render_section("Key Performance Indicators")
        render_kpi_grid([
            (f"{kpis['Total SKUs']:,}", "Total SKUs", "cube", "blue"),
            (f"{kpis['Total Orders']:,}", "Total Orders", "cart", "blue"),
            (kpis['Low Stock Items'], "Low Stock", "alert-triangle", "red"),
            (kpis['Overstock Items'], "Overstock", "archive", "amber"),
            (kpis['Delayed Orders'], "Delayed Orders", "clock", "red"),
        ], 5)
        render_kpi_grid([
            (kpis['Pending Dispatches'], "Pending Dispatch", "truck", "amber"),
            (kpis['Avg Delay Days'], "Avg Delay Days", "timer", "red"),
            (f"{kpis['Warehouse Utilization %']}%", "Utilization", "building", "purple"),
            (f"{kpis['Picking Accuracy %']}%", "Pick Accuracy", "check-circle", "green"),
            (kpis['Inbound Mismatch Count'], "Inbound Mismatches", "x-circle", "amber"),
        ], 5)

        from utils.analytics import _html_report_header, _html_kpi_strip, _html_section, _html_table, _html_action_item

        report_ts = datetime.now().strftime('%d %b %Y, %H:%M')

        # --- Full Report Panel ---
        rp = '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.07);margin-bottom:24px;">'
        rp += _html_report_header("Daily Warehouse Performance Report", "QubiWare AI Intelligence Engine", report_ts)

        # KPI Strip
        rp += _html_kpi_strip([
            (f"{kpis['Total SKUs']:,}", "Total SKUs", "#2563EB"),
            (kpis['Low Stock Items'], "Low Stock", "#EF4444"),
            (kpis['Delayed Orders'], "Delayed Orders", "#EF4444"),
            (f"{kpis['Warehouse Utilization %']}%", "Utilization", "#8B5CF6"),
            (f"{kpis['Picking Accuracy %']}%", "Pick Accuracy", "#10B981"),
        ])

        # Inventory Risks
        rp += _html_section("Inventory Risk Analysis", f"{len(low_stock)} Low / {len(overstock)} Over / {len(dead_stock)} Dead", "#EF4444")
        inv_rows = []
        for _, r in low_stock[["sku_id", "product_name", "current_stock", "reorder_level", "supplier_name"]].head(8).iterrows():
            inv_rows.append([r['sku_id'], str(r['product_name'])[:28], int(r['current_stock']), int(r['reorder_level']), str(r['supplier_name'])[:20]])
        if inv_rows:
            rp += _html_table(["SKU", "Product", "Stock", "Reorder Lvl", "Supplier"], inv_rows, ['#111827', '#4B5563', '#EF4444', '#64748B', '#64748B'])

        # Dispatch Risks
        rp += _html_section("Dispatch Risk Analysis", f"{len(delayed)} Delayed / {len(high_priority)} Critical", "#F59E0B")
        rp += '<div style="display:flex;gap:0;border-bottom:1px solid #F3F4F6;border-top:1px solid #F3F4F6;">'
        for val, lab, col in [(len(delayed), "Delayed", "#EF4444"), (len(pending), "Pending", "#F59E0B"), (len(high_priority), "High Priority", "#DC2626"), (f"{kpis['Avg Delay Days']}d", "Avg Delay", "#8B5CF6")]:
            rp += f'<div style="flex:1;padding:12px 16px;text-align:center;border-right:1px solid #F3F4F6;"><div style="font-size:1.15rem;font-weight:800;color:{col};">{val}</div><div style="font-size:0.6rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;">{lab}</div></div>'
        rp += '</div>'
        zone_delay = delayed.groupby("warehouse_zone")["delay_days"].count().sort_values(ascending=False).reset_index()
        zone_delay.columns = ["Zone", "Delayed Orders"]
        zd_rows = [[r['Zone'], int(r['Delayed Orders'])] for _, r in zone_delay.head(5).iterrows()]
        if zd_rows:
            rp += _html_table(["Zone", "Delayed Orders"], zd_rows, ['#111827', '#EF4444'])

        # Zone Status
        rp += _html_section("Warehouse Zone Status", f"{len(critical_zones)} Critical Zone(s)", "#8B5CF6")
        zone_display = zone_util_r[["zone_name", "utilization_pct", "used_units", "capacity_units", "status"]].sort_values("utilization_pct", ascending=False)
        zs_rows = []
        for _, r in zone_display.iterrows():
            status = r['status']
            status_col = '#EF4444' if status == 'Critical' else '#F59E0B' if status == 'Warning' else '#10B981'
            status_badge = f'<span style="background:{status_col}15;color:{status_col};font-size:0.65rem;font-weight:700;padding:2px 8px;border-radius:4px;">{status}</span>'
            zs_rows.append([r['zone_name'], f"{r['utilization_pct']:.0f}%", int(r['used_units']), int(r['capacity_units']), status_badge])
        rp += _html_table(["Zone", "Utilization", "Used", "Capacity", "Status"], zs_rows, ['#111827', '#8B5CF6', '#64748B', '#64748B', None])

        # Supplier Issues
        rp += _html_section("Supplier / Inbound Issues", f"{len(mismatches)} Mismatches", "#D97706")
        if len(supplier_issues_r) > 0:
            si_rows = []
            for _, r in supplier_issues_r[["supplier_name", "mismatch_count", "total_shortage"]].head(5).iterrows():
                si_rows.append([str(r['supplier_name'])[:24], int(r['mismatch_count']), int(r['total_shortage'])])
            rp += _html_table(["Supplier", "Mismatches", "Shortage (units)"], si_rows, ['#111827', '#F59E0B', '#EF4444'])
        else:
            rp += '<div style="padding:10px 32px;font-size:0.82rem;color:#10B981;">No supplier issues detected.</div>'

        # Picking Accuracy
        rp += _html_section("Picking Accuracy Analysis", f"{kpis['Picking Accuracy %']}% Overall", "#10B981")
        pe_rows = []
        for _, r in picker_errors[["picker_name", "total_errors", "total_picks", "avg_errors_per_pick"]].head(6).iterrows():
            err_rate = round(r['avg_errors_per_pick'], 2)
            rate_color = '#EF4444' if err_rate > 0.15 else '#F59E0B' if err_rate > 0.08 else '#10B981'
            pe_rows.append([r['picker_name'], int(r['total_errors']), int(r['total_picks']), f'<span style="color:{rate_color};font-weight:700;">{err_rate}</span>'])
        rp += _html_table(["Picker", "Errors", "Picks", "Error Rate"], pe_rows, ['#111827', '#EF4444', '#64748B', None])

        # Recommended Actions
        rp += _html_section("Recommended Actions")
        rp += '<div style="padding:8px 32px 0 32px;"><div style="font-size:0.62rem;font-weight:700;color:#DC2626;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:flex;align-items:center;gap:6px;"><div style="width:8px;height:8px;background:#DC2626;border-radius:50%;"></div>Immediate &mdash; Today</div></div>'
        rp += _html_action_item(1, f"<strong>Initiate procurement</strong> for {len(low_stock)} critical low-stock SKUs to prevent stockouts", "#EF4444")
        rp += _html_action_item(2, f"<strong>Dispatch {len(high_priority)} high-priority delayed orders</strong> immediately to avoid SLA breaches", "#DC2626")
        rp += _html_action_item(3, f"<strong>Reassign resources</strong> to decongest {len(critical_zones)} critical warehouse zone(s)", "#EF4444")
        rp += '<div style="padding:12px 32px 0 32px;"><div style="font-size:0.62rem;font-weight:700;color:#D97706;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:flex;align-items:center;gap:6px;"><div style="width:8px;height:8px;background:#D97706;border-radius:50%;"></div>Short-Term &mdash; This Week</div></div>'
        rp += _html_action_item(4, f"<strong>Review {len(overstock)} overstock items</strong> for redistribution or promotional clearance", "#F59E0B")
        rp += _html_action_item(5, f"<strong>Conduct dead stock audit</strong> on {len(dead_stock)} items with no movement &gt; 60 days", "#8B5CF6")
        rp += _html_action_item(6, "<strong>Retrain pickers</strong> with high error rates and escalate supplier mismatches", "#D97706")
        rp += '<div style="padding:12px 32px 0 32px;"><div style="font-size:0.62rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:flex;align-items:center;gap:6px;"><div style="width:8px;height:8px;background:#2563EB;border-radius:50%;"></div>Medium-Term &mdash; This Month</div></div>'
        rp += _html_action_item(7, "<strong>Rebalance warehouse zone allocation</strong> across all zones based on demand patterns", "#2563EB")
        rp += _html_action_item(8, "<strong>Review reorder levels</strong> based on recent demand trends and optimize picking routes", "#06B6D4")
        rp += '<div style="height:16px;"></div>'

        # Email Draft
        rp += '<div style="border-top:2px solid #E5E7EB;padding:24px 32px;">'
        rp += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;"><div style="width:28px;height:28px;background:linear-gradient(135deg,#2563EB,#06B6D4);border-radius:6px;display:flex;align-items:center;justify-content:center;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg></div><div style="font-size:0.88rem;font-weight:700;color:#111827;">Email Draft to Operations Manager</div></div>'
        report_date = datetime.now().strftime('%d %B %Y')
        rp += f'<div style="background:#F8FAFC;border:1px solid #E5E7EB;border-radius:10px;padding:20px 24px;font-size:0.82rem;line-height:1.7;color:#374151;">'
        rp += f'<div style="font-weight:700;color:#111827;margin-bottom:12px;font-size:0.84rem;border-bottom:1px solid #E5E7EB;padding-bottom:8px;">Subject: Daily Warehouse Performance Report &mdash; {report_date}</div>'
        rp += '<p style="margin:0 0 10px 0;">Dear Operations Manager,</p>'
        rp += '<p style="margin:0 0 10px 0;">Please find below the key highlights from today\'s warehouse performance:</p>'
        rp += '<p style="margin:0 0 6px 0;font-weight:700;color:#111827;">Critical Alerts:</p>'
        rp += f'<ul style="margin:4px 0 14px 0;padding-left:20px;"><li style="margin-bottom:4px;">{len(low_stock)} SKUs below reorder level (stockout risk)</li><li style="margin-bottom:4px;">{len(delayed)} orders delayed ({len(high_priority)} high-priority)</li><li style="margin-bottom:4px;">{len(critical_zones)} zone(s) at critical capacity (&gt;90%)</li><li style="margin-bottom:4px;">{len(mismatches)} inbound shipments with quantity mismatch</li></ul>'
        rp += f'<div style="background:white;border:1px solid #E5E7EB;border-radius:8px;padding:12px 16px;margin:10px 0;display:flex;gap:16px;flex-wrap:wrap;">'
        rp += f'<div><span style="font-weight:700;color:#111827;">Utilization:</span> {kpis["Warehouse Utilization %"]}%</div>'
        rp += f'<div><span style="font-weight:700;color:#111827;">Pick Accuracy:</span> {kpis["Picking Accuracy %"]}%</div>'
        rp += f'<div><span style="font-weight:700;color:#111827;">Avg Delay:</span> {kpis["Avg Delay Days"]} days</div>'
        rp += f'<div><span style="font-weight:700;color:#111827;">Pending:</span> {kpis["Pending Dispatches"]}</div>'
        rp += '</div>'
        rp += '<p style="margin:10px 0;">Please review the full report for detailed analysis and recommendations.</p>'
        rp += '<p style="margin:0;">Best regards,<br><strong>QubiWare AI Intelligence Engine</strong><br><span style="color:#9CA3AF;">Qubithm Corporation LLP</span></p>'
        rp += '</div></div>'

        # Footer
        rp += '<div style="background:#F8FAFC;padding:12px 32px;border-top:1px solid #E5E7EB;font-size:0.7rem;color:#9CA3AF;display:flex;justify-content:space-between;">Generated by QubiWare AI &middot; Qubithm Corporation LLP<span>AI-powered warehouse intelligence</span></div>'
        rp += '</div>'

        st.markdown(rp, unsafe_allow_html=True)

    render_footer()
