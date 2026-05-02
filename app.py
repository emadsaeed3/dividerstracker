import streamlit as st
from supabase import create_client
from datetime import datetime, date
import pandas as pd
from io import BytesIO
import openpyxl
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Dividers Tracker",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

LOW_STOCK_THRESHOLD = 50

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False


def load_css():
    dark = st.session_state.dark_mode
    
    if dark:
        bg_primary = "#1a1d24"
        bg_secondary = "#252932"
        text_primary = "#e4e6eb"
        text_secondary = "#b0b3b8"
        sidebar_bg = "linear-gradient(180deg, #0d1117 0%, #161b22 100%)"
        border_color = "#3a3f4b"
        card_shadow = "0 4px 20px rgba(0,0,0,0.4)"
        hover_shadow = "0 12px 35px rgba(0,0,0,0.6)"
    else:
        bg_primary = "#f5f7fa"
        bg_secondary = "#ffffff"
        text_primary = "#2c3e50"
        text_secondary = "#7f8c8d"
        sidebar_bg = "linear-gradient(180deg, #1a2a3a 0%, #2c3e50 100%)"
        border_color = "#ecf0f1"
        card_shadow = "0 4px 20px rgba(0,0,0,0.08)"
        hover_shadow = "0 12px 35px rgba(0,0,0,0.15)"
    
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined');
    
    * {{
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }}
    
    .stApp {{
        background: {bg_primary};
    }}
    
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}
    
    .stApp, .stApp p, .stApp label, .stApp span, .stMarkdown {{
        color: {text_primary};
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[kind="header"],
    button[kind="headerNoPadding"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    span.material-symbols-outlined,
    span.material-symbols-rounded,
    span.material-symbols-sharp,
    span.material-icons,
    span.material-icons-outlined,
    span.material-icons-round,
    span.material-icons-sharp {{
        font-family: 'Material Symbols Outlined', 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        display: inline-block !important;
        line-height: 1 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-wrap: normal !important;
        white-space: nowrap !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
        font-feature-settings: 'liga' !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: {sidebar_bg};
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: {sidebar_bg};
        padding-top: 1rem;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    [data-testid="stSidebar"] .stMarkdown h1 {{
        color: white !important;
        font-size: 1.4rem !important;
        padding-bottom: 0 !important;
        border: none !important;
        margin-bottom: 0 !important;
    }}
    [data-testid="stSidebar"] .stMarkdown h1::after {{
        display: none !important;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] {{
        gap: 8px;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] > label {{
        background: rgba(255,255,255,0.06);
        padding: 12px 16px !important;
        border-radius: 10px;
        margin: 0 !important;
        transition: all 0.3s ease;
        cursor: pointer;
        border-left: 3px solid transparent;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover {{
        background: rgba(52, 152, 219, 0.2);
        border-left: 3px solid #3498db;
        transform: translateX(4px);
    }}
    [data-testid="stSidebar"] [role="radiogroup"] > label[data-checked="true"] {{
        background: linear-gradient(90deg, rgba(52, 152, 219, 0.3) 0%, rgba(52, 152, 219, 0.1) 100%);
        border-left: 3px solid #3498db;
    }}
    [data-testid="stSidebar"] button {{
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease;
    }}
    [data-testid="stSidebar"] button:hover {{
        background: rgba(52, 152, 219, 0.3) !important;
        border-color: #3498db !important;
    }}
    
    h1 {{
        color: {text_primary} !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        position: relative;
        padding-bottom: 14px;
        margin-bottom: 28px !important;
        letter-spacing: -0.5px;
    }}
    h1::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 70px;
        height: 4px;
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        border-radius: 10px;
    }}
    
    h2, h3 {{
        color: {text_primary} !important;
        font-weight: 700 !important;
    }}
    
    .section-title {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {text_primary};
        margin: 25px 0 15px 0;
        padding-left: 12px;
        border-left: 4px solid #3498db;
    }}
    
    [data-testid="stMetric"] {{
        background: {bg_secondary};
        padding: 22px;
        border-radius: 14px;
        box-shadow: {card_shadow};
        border: 1px solid {border_color};
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
        position: relative;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-6px);
        box-shadow: {hover_shadow};
    }}
    [data-testid="stMetric"]::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
    }}
    [data-testid="stMetricLabel"] {{
        color: {text_secondary} !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }}
    [data-testid="stMetricValue"] {{
        color: {text_primary} !important;
        font-weight: 800 !important;
        font-size: 38px !important;
        line-height: 1.2 !important;
    }}
    
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
        border: none;
        padding: 11px 24px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.3px;
        font-size: 0.95rem;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white !important;
        box-shadow: 0 4px 14px rgba(52, 152, 219, 0.35);
    }}
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(52, 152, 219, 0.5);
    }}
    .stFormSubmitButton > button {{
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(39, 174, 96, 0.35);
    }}
    .stFormSubmitButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(39, 174, 96, 0.5);
    }}
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #9b59b6 0%, #6c3483 100%) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(155, 89, 182, 0.35);
    }}
    .stDownloadButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(155, 89, 182, 0.5);
    }}
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input {{
        background: {bg_secondary} !important;
        color: {text_primary} !important;
        border-radius: 10px !important;
        border: 1.5px solid {border_color} !important;
        padding: 11px 15px !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stDateInput > div > div > input:focus {{
        border-color: #3498db !important;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15) !important;
    }}
    
    .stSelectbox > div > div {{
        background: {bg_secondary} !important;
        border-radius: 10px !important;
        border: 1.5px solid {border_color} !important;
    }}
    
    [data-testid="stExpander"] {{
        background: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
        box-shadow: {card_shadow};
        margin-bottom: 14px;
        overflow: hidden;
        transition: all 0.3s ease;
    }}
    [data-testid="stExpander"]:hover {{
        box-shadow: {hover_shadow};
    }}
    .streamlit-expanderHeader {{
        font-weight: 600 !important;
        color: {text_primary} !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
    }}
    .streamlit-expanderHeader:hover {{
        background: rgba(52, 152, 219, 0.05);
    }}
    
    [data-testid="stForm"] {{
        background: {bg_secondary};
        padding: 28px;
        border-radius: 14px;
        border: 1px solid {border_color};
        box-shadow: {card_shadow};
    }}
    
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: {card_shadow};
        border: 1px solid {border_color};
    }}
    [data-testid="stDataFrame"] thead tr th {{
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px;
    }}
    
    [data-testid="stAlert"] {{
        border-radius: 12px !important;
        padding: 16px 22px !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        border-left: 5px solid !important;
        animation: slideIn 0.4s ease;
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateX(-20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .stat-card {{
        background: {bg_secondary};
        padding: 24px;
        border-radius: 14px;
        box-shadow: {card_shadow};
        border: 1px solid {border_color};
        margin-bottom: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.5s ease;
    }}
    .stat-card:hover {{
        transform: translateY(-6px);
        box-shadow: {hover_shadow};
    }}
    .stat-card .icon-bg {{
        position: absolute;
        top: 12px;
        right: 16px;
        font-size: 3.5rem;
        opacity: 0.12;
    }}
    .stat-card .stat-label {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: {text_secondary};
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .stat-card .stat-value {{
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
    }}
    
    .card-30d {{
        border-left: 5px solid #3498db;
        background: linear-gradient(135deg, {bg_secondary} 0%, rgba(52, 152, 219, 0.08) 100%);
    }}
    .card-30d .icon-bg {{ color: #3498db; }}
    .card-30d .stat-value {{ color: #3498db; }}
    
    .card-40d {{
        border-left: 5px solid #e67e22;
        background: linear-gradient(135deg, {bg_secondary} 0%, rgba(230, 126, 34, 0.08) 100%);
    }}
    .card-40d .icon-bg {{ color: #e67e22; }}
    .card-40d .stat-value {{ color: #e67e22; }}
    
    .card-60d {{
        border-left: 5px solid #9b59b6;
        background: linear-gradient(135deg, {bg_secondary} 0%, rgba(155, 89, 182, 0.08) 100%);
    }}
    .card-60d .icon-bg {{ color: #9b59b6; }}
    .card-60d .stat-value {{ color: #9b59b6; }}
    
    .card-stores {{
        border-left: 5px solid #3498db;
    }}
    .card-stores .icon-bg {{ color: #3498db; }}
    .card-stores .stat-value {{ color: {text_primary}; }}
    
    .card-shipments {{
        border-left: 5px solid #27ae60;
    }}
    .card-shipments .icon-bg {{ color: #27ae60; }}
    .card-shipments .stat-value {{ color: {text_primary}; }}
    
    .badge-stock {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        margin-top: 12px;
        letter-spacing: 0.3px;
    }}
    .badge-danger {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; }}
    .badge-warning {{ background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); color: white; }}
    .badge-success {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; }}
    
    .progress-container {{
        background: {border_color};
        border-radius: 20px;
        overflow: hidden;
        height: 10px;
        margin-top: 12px;
    }}
    .progress-fill {{
        height: 100%;
        border-radius: 20px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .threshold-chip {{
        display: inline-block;
        background: linear-gradient(135deg, #7f8c8d 0%, #636e72 100%);
        color: white;
        padding: 8px 18px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }}
    
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: {bg_primary}; }}
    ::-webkit-scrollbar-thumb {{ 
        background: linear-gradient(180deg, #3498db 0%, #2980b9 100%);
        border-radius: 10px;
    }}
    
hr {{
        border: none;
        height: 1px;
        background: {border_color};
        margin: 24px 0;
    }}
    
    /* Hide expander arrow text and replace with custom arrow */
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary span {{
        display: none !important;
    }}
    
    [data-testid="stExpander"] summary::after {{
        content: "▼" !important;
        color: #3498db !important;
        font-size: 14px !important;
        margin-left: auto !important;
        transition: transform 0.3s ease;
    }}
    
    [data-testid="stExpander"] details[open] summary::after {{
        content: "▲" !important;
    }}
    
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


load_css()



# ============ DATABASE FUNCTIONS ============
def get_threshold():
    try:
        res = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
        if res.data:
            return int(res.data[0]['value'])
    except:
        pass
    return LOW_STOCK_THRESHOLD


def set_threshold(val):
    existing = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
    if existing.data:
        supabase.table('settings').update({'value': str(val)}).eq('key', 'low_stock_threshold').execute()
    else:
        supabase.table('settings').insert({'key': 'low_stock_threshold', 'value': str(val)}).execute()


def get_stocks():
    res = supabase.table('vendor_stock').select('*').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['divider_type', 'quantity'])


def get_stores():
    res = supabase.table('stores').select('*').order('name').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


def get_shipments():
    res = supabase.table('shipments').select('*, stores(name)').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df['store_name'] = df['stores'].apply(lambda x: x['name'] if x else 'Unknown')
    return df


def calculate_alerts():
    alerts = []
    threshold = get_threshold()
    stocks_df = get_stocks()
    stores_df = get_stores()
    shipments_df = get_shipments()

    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}

    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = stores_df[col].sum() if not stores_df.empty else 0
        shipped = shipments_df[ship_col].sum() if not shipments_df.empty else 0
        remaining_need = max(0, required - shipped)

        if stock < remaining_need:
            shortage = remaining_need - stock
            alerts.append(('danger', f'🚨 **Critical!** {dtype} shortage: Need to order **{shortage}** more units from vendor'))
        elif stock < threshold:
            alerts.append(('warning', f'⚠️ **Low stock alert:** {dtype} has only **{stock}** units left. Consider contacting vendor'))

    return alerts


def render_stat_card(label, value, card_class, icon):
    st.markdown(f"""
    <div class="stat-card {card_class}">
        <i class="bi {icon} icon-bg"></i>
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stock_card(dtype, qty, threshold):
    card_class = f"card-{dtype.lower()}"
    
    if qty == 0:
        badge = '<span class="badge-stock badge-danger">❌ Out of Stock</span>'
    elif qty < threshold:
        badge = '<span class="badge-stock badge-warning">⚠️ Low Stock</span>'
    else:
        badge = '<span class="badge-stock badge-success">✅ In Stock</span>'
    
    st.markdown(f"""
    <div class="stat-card {card_class}">
        <i class="bi bi-box-seam icon-bg"></i>
        <div class="stat-label">{dtype} Stock</div>
        <div class="stat-value">{qty}</div>
        {badge}
    </div>
    """, unsafe_allow_html=True)


def render_progress_card(dtype, required, shipped, gap):
    color_map = {'30D': '#3498db', '40D': '#e67e22', '60D': '#9b59b6'}
    color = color_map[dtype]
    pct = min((shipped / required * 100) if required > 0 else 0, 100)
    gap_color = "#e74c3c" if gap > 0 else "#27ae60"
    gap_icon = "⚠️" if gap > 0 else "✅"
    
    st.markdown(f"""
    <div class="stat-card card-{dtype.lower()}">
        <i class="bi bi-bar-chart-fill icon-bg"></i>
        <div class="stat-label" style="color:{color};">{dtype} Progress</div>
        <div style="margin-top: 12px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-size:0.9rem;"><b>Required:</b> {required}</span>
                <span style="font-size:0.9rem; color:#27ae60;"><b>Shipped:</b> {shipped}</span>
            </div>
            <div class="progress-container">
                <div class="progress-fill" style="width:{pct}%; background:{color};"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:10px;">
                <span style="font-size:0.85rem;">{pct:.0f}% complete</span>
                <span style="font-weight:700; color:{gap_color};">{gap_icon} Gap: {gap}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <i class="bi bi-box-seam" style="font-size:2.5rem; color:#3498db;"></i>
        <h1 style="margin:8px 0 0 0;">Dividers Tracker</h1>
        <p style="font-size:0.8rem; opacity:0.7; margin:0;">Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    page = st.radio("Navigation",
        ["📊  Dashboard", "🏪  Stores", "📦  Vendor Stock", "🚚  Shipments", "📈  Reports"],
        label_visibility="collapsed")
    
    st.markdown("---")
    
    dark_label = "☀️ Switch to Light" if st.session_state.dark_mode else "🌙 Switch to Dark"
    if st.button(dark_label, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; font-size:0.75rem; opacity:0.6; padding:10px;">
        <i class="bi bi-heart-fill" style="color:#e74c3c;"></i> Built with Streamlit<br>
        © 2025
    </div>
    """, unsafe_allow_html=True)


def get_plotly_theme():
    if st.session_state.dark_mode:
        return dict(
            paper_bgcolor='#252932',
            plot_bgcolor='#252932',
            font=dict(color='#e4e6eb')
        )
    return dict(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(color='#2c3e50')
    )


# ============ DASHBOARD ============
if "Dashboard" in page:
    col_title, col_chip = st.columns([3, 1])
    with col_title:
        st.markdown("# 📊 Dashboard")
    with col_chip:
        threshold = get_threshold()
        st.markdown(f'<div style="text-align:right; padding-top:12px;"><span class="threshold-chip">⚙️ Threshold: {threshold}</span></div>', unsafe_allow_html=True)

    alerts = calculate_alerts()
    if alerts:
        for level, msg in alerts:
            if level == 'danger':
                st.error(msg)
            else:
                st.warning(msg)

    stocks_df = get_stocks()
    stores_df = get_stores()
    shipments_df = get_shipments()

    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}

    st.markdown('<div class="section-title">📌 Overview</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        render_stat_card("Total Stores", len(stores_df), "card-stores", "bi-shop")
    with c2:
        render_stat_card("Total Shipments", len(shipments_df), "card-shipments", "bi-truck")

    st.markdown('<div class="section-title">📦 Vendor Stock</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)

    st.markdown('<div class="section-title">🎯 Required vs Shipped</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    req_shipped = {}
    for idx, dtype in enumerate(['30D', '40D', '60D']):
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        gap = required - shipped
        req_shipped[dtype] = (required, shipped, gap)
        with [c1, c2, c3][idx]:
            render_progress_card(dtype, required, shipped, gap)

    st.markdown('<div class="section-title">📊 Analytics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    
    with c1:
        fig = go.Figure()
        types = ['30D', '40D', '60D']
        fig.add_trace(go.Bar(name='Vendor Stock', x=types, 
                             y=[stocks.get(t, 0) for t in types],
                             marker_color='#3498db'))
        fig.add_trace(go.Bar(name='Required', x=types,
                             y=[req_shipped[t][0] for t in types],
                             marker_color='#f39c12'))
        fig.add_trace(go.Bar(name='Shipped', x=types,
                             y=[req_shipped[t][1] for t in types],
                             marker_color='#27ae60'))
        fig.update_layout(
            barmode='group',
            height=380,
            title=dict(text='<b>Stock Overview by Divider Type</b>', font=dict(size=16)),
            margin=dict(t=50, b=40, l=40, r=20),
            **get_plotly_theme()
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        total = sum(stocks.get(t, 0) for t in types)
        if total > 0:
            fig = go.Figure(data=[go.Pie(
                labels=types,
                values=[stocks.get(t, 0) for t in types],
                hole=0.55,
                marker=dict(colors=['#3498db', '#e67e22', '#9b59b6'])
            )])
            fig.update_layout(
                height=380,
                title=dict(text='<b>Stock Distribution</b>', font=dict(size=16)),
                margin=dict(t=50, b=40, l=20, r=20),
                **get_plotly_theme()
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No stock data to visualize yet.")


# ============ STORES ============
elif "Stores" in page:
    st.markdown("# 🏪 Stores Management")

    with st.expander("➕ **Add New Store**", expanded=False):
        with st.form("add_store", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Store Name *", placeholder="e.g., Smouha Store")
            location = c2.text_input("Location", placeholder="e.g., Alexandria")
            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("🔵 Required 30D", min_value=0, value=0)
            r40 = c2.number_input("🟠 Required 40D", min_value=0, value=0)
            r60 = c3.number_input("🟣 Required 60D", min_value=0, value=0)
            submitted = st.form_submit_button("➕ Add Store")
            if submitted and name:
                supabase.table('stores').insert({
                    'name': name, 'location': location,
                    'required_30d': r30, 'required_40d': r40, 'required_60d': r60
                }).execute()
                st.success(f"✅ Store '{name}' added successfully!")
                st.rerun()

    st.markdown('<div class="section-title">📋 All Stores</div>', unsafe_allow_html=True)
    stores_df = get_stores()
    if stores_df.empty:
        st.info("📭 No stores added yet.")
    else:
        for _, store in stores_df.iterrows():
            with st.expander(f"🏪 **{store['name']}** — 📍 {store['location'] or 'N/A'}"):
                with st.form(f"edit_{store['id']}"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Name", value=store['name'], key=f"n_{store['id']}")
                    location = c2.text_input("Location", value=store['location'] or '', key=f"l_{store['id']}")
                    c1, c2, c3 = st.columns(3)
                    r30 = c1.number_input("🔵 Required 30D", min_value=0, value=int(store['required_30d']), key=f"r30_{store['id']}")
                    r40 = c2.number_input("🟠 Required 40D", min_value=0, value=int(store['required_40d']), key=f"r40_{store['id']}")
                    r60 = c3.number_input("🟣 Required 60D", min_value=0, value=int(store['required_60d']), key=f"r60_{store['id']}")
                    c1, c2 = st.columns(2)
                    update = c1.form_submit_button("💾 Update")
                    delete = c2.form_submit_button("🗑️ Delete")
                    if update:
                        supabase.table('stores').update({
                            'name': name, 'location': location,
                            'required_30d': r30, 'required_40d': r40, 'required_60d': r60
                        }).eq('id', store['id']).execute()
                        st.success("✅ Updated!")
                        st.rerun()
                    if delete:
                        supabase.table('stores').delete().eq('id', store['id']).execute()
                        st.warning("🗑️ Deleted!")
                        st.rerun()


# ============ VENDOR STOCK ============
elif "Vendor Stock" in page:
    st.markdown("# 📦 Vendor Stock Management")

    threshold = get_threshold()
    
    with st.expander("⚙️ **Low Stock Threshold Settings**"):
        st.info(f"💡 Current threshold: **{threshold}** units")
        c1, c2 = st.columns([3, 1])
        new_threshold = c1.number_input("Threshold (units)", min_value=0, value=threshold, label_visibility="collapsed")
        if c2.button("💾 Save"):
            set_threshold(new_threshold)
            st.success(f"✅ Threshold updated to {new_threshold}")
            st.rerun()

    st.markdown('<div class="section-title">📊 Current Stock Levels</div>', unsafe_allow_html=True)
    stocks_df = get_stocks()
    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}
    
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)

    st.markdown('<div class="section-title">🔄 Update Stock</div>', unsafe_allow_html=True)
    with st.form("update_stock", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        dtype = c1.selectbox("Divider Type", ['30D', '40D', '60D'])
        qty = c2.number_input("New Quantity", min_value=0, value=0)
        note = st.text_input("Note (optional)")
        if st.form_submit_button("🔄 Update Stock"):
            res = supabase.table('vendor_stock').select('*').eq('divider_type', dtype).execute()
            old_qty = res.data[0]['quantity'] if res.data else 0
            supabase.table('vendor_stock').update({
                'quantity': qty,
                'last_updated': datetime.utcnow().isoformat()
            }).eq('divider_type', dtype).execute()
            supabase.table('stock_history').insert({
                'divider_type': dtype, 'old_qty': old_qty, 'new_qty': qty,
                'change': qty - old_qty, 'note': note
            }).execute()
            st.success(f"✅ {dtype} stock updated!")
            st.rerun()

    st.markdown('<div class="section-title">📜 Stock History</div>', unsafe_allow_html=True)
    res = supabase.table('stock_history').select('*').order('date', desc=True).limit(20).execute()
    if res.data:
        hist_df = pd.DataFrame(res.data)
        hist_df = hist_df[['date', 'divider_type', 'old_qty', 'new_qty', 'change', 'note']]
        hist_df.columns = ['Date', 'Type', 'Old Qty', 'New Qty', 'Change', 'Note']
        hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No history yet.")


# ============ SHIPMENTS ============
elif "Shipments" in page:
    st.markdown("# 🚚 Shipments")

    stores_df = get_stores()
    if stores_df.empty:
        st.warning("⚠️ Please add a store first.")
    else:
        with st.expander("➕ **Record New Shipment**", expanded=False):
            with st.form("add_shipment", clear_on_submit=True):
                store_options = {f"{row['name']} ({row['location'] or 'N/A'})": row['id'] for _, row in stores_df.iterrows()}
                c1, c2 = st.columns(2)
                selected = c1.selectbox("🏪 Store", list(store_options.keys()))
                ship_date = c2.date_input("📅 Date", value=date.today())
                c1, c2, c3 = st.columns(3)
                q30 = c1.number_input("🔵 Qty 30D", min_value=0, value=0)
                q40 = c2.number_input("🟠 Qty 40D", min_value=0, value=0)
                q60 = c3.number_input("🟣 Qty 60D", min_value=0, value=0)
                notes = st.text_area("📝 Notes")
                if st.form_submit_button("💾 Record Shipment"):
                    store_id = store_options[selected]
                    supabase.table('shipments').insert({
                        'store_id': store_id, 'date': ship_date.isoformat(),
                        'qty_30d': q30, 'qty_40d': q40, 'qty_60d': q60, 'notes': notes
                    }).execute()
                    for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
                        if qty > 0:
                            res = supabase.table('vendor_stock').select('*').eq('divider_type', dtype).execute()
                            if res.data:
                                old_qty = res.data[0]['quantity']
                                new_qty = max(0, old_qty - qty)
                                supabase.table('vendor_stock').update({
                                    'quantity': new_qty,
                                    'last_updated': datetime.utcnow().isoformat()
                                }).eq('divider_type', dtype).execute()
                                supabase.table('stock_history').insert({
                                    'divider_type': dtype, 'old_qty': old_qty, 'new_qty': new_qty,
                                    'change': -qty, 'note': f'Shipped to store #{store_id}'
                                }).execute()
                    st.success("✅ Shipment recorded!")
                    st.rerun()

    st.markdown('<div class="section-title">📋 All Shipments</div>', unsafe_allow_html=True)
    shipments_df = get_shipments()
    if shipments_df.empty:
        st.info("📭 No shipments yet.")
    else:
        display_df = shipments_df[['id', 'store_name', 'date', 'qty_30d', 'qty_40d', 'qty_60d', 'notes']].copy()
        display_df.columns = ['ID', 'Store', 'Date', '30D', '40D', '60D', 'Notes']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        c1, c2 = st.columns([1, 3])
        del_id = c1.number_input("Shipment ID", min_value=0, value=0)
        if c2.button("🗑️ Delete Shipment"):
            if del_id > 0:
                supabase.table('shipments').delete().eq('id', del_id).execute()
                st.warning(f"🗑️ Shipment #{del_id} deleted.")
                st.rerun()


# ============ REPORTS ============
elif "Reports" in page:
    st.markdown("# 📈 Reports")

    stores_df = get_stores()
    shipments_df = get_shipments()

    if stores_df.empty:
        st.info("📭 No data to display.")
    else:
        report_rows = []
        for _, store in stores_df.iterrows():
            store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()
            s30 = store_ships['qty_30d'].sum() if not store_ships.empty else 0
            s40 = store_ships['qty_40d'].sum() if not store_ships.empty else 0
            s60 = store_ships['qty_60d'].sum() if not store_ships.empty else 0
            report_rows.append({
                'Store': store['name'],
                'Location': store['location'] or '-',
                'Req 30D': store['required_30d'],
                'Ship 30D': int(s30),
                'Gap 30D': store['required_30d'] - int(s30),
                'Req 40D': store['required_40d'],
                'Ship 40D': int(s40),
                'Gap 40D': store['required_40d'] - int(s40),
                'Req 60D': store['required_60d'],
                'Ship 60D': int(s60),
                'Gap 60D': store['required_60d'] - int(s60),
            })
        report_df = pd.DataFrame(report_rows)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_stat_card("Total Stores", len(report_df), "card-stores", "bi-shop")
        with c2:
            total_req = report_df[['Req 30D', 'Req 40D', 'Req 60D']].sum().sum()
            render_stat_card("Total Required", int(total_req), "card-30d", "bi-clipboard-check")
        with c3:
            total_ship = report_df[['Ship 30D', 'Ship 40D', 'Ship 60D']].sum().sum()
            render_stat_card("Total Shipped", int(total_ship), "card-shipments", "bi-truck")
        with c4:
            total_gap = report_df[['Gap 30D', 'Gap 40D', 'Gap 60D']].sum().sum()
            render_stat_card("Total Gap", int(total_gap), "card-40d", "bi-exclamation-triangle")

        st.markdown('<div class="section-title">📊 Detailed Report</div>', unsafe_allow_html=True)
        
        def style_gap(val):
            try:
                v = int(val)
                if v > 0:
                    return 'color: #e74c3c; font-weight: 700;'
                elif v == 0:
                    return 'color: #27ae60; font-weight: 600;'
            except:
                pass
            return ''
        
        styled = report_df.style.map(style_gap, subset=['Gap 30D', 'Gap 40D', 'Gap 60D'])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        output = BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Stores Report"
        ws.append(list(report_df.columns))
        for _, row in report_df.iterrows():
            ws.append(list(row))
        wb.save(output)
        output.seek(0)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.download_button(
                label="📥 Download Excel Report",
                data=output,
                file_name=f"dividers_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
