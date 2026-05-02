import streamlit as st
from supabase import create_client
from datetime import datetime, date
import pandas as pd
from io import BytesIO
import openpyxl

# Page config
st.set_page_config(page_title="Dividers Tracker", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

# Supabase connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

LOW_STOCK_THRESHOLD = 50

# Dark mode toggle
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False


# ============ CUSTOM CSS ============
def load_css():
    dark = st.session_state.dark_mode
    
    if dark:
        bg_primary = "#1a1d24"
        bg_secondary = "#252932"
        text_primary = "#e4e6eb"
        text_secondary = "#b0b3b8"
        navbar_bg = "linear-gradient(90deg, #0d1117 0%, #161b22 100%)"
        border_color = "#3a3f4b"
        hover_bg = "#2d3139"
        card_shadow = "0 2px 10px rgba(0,0,0,0.4)"
        table_header_bg = "linear-gradient(90deg, #161b22 0%, #21262d 100%)"
    else:
        bg_primary = "#f5f7fa"
        bg_secondary = "#ffffff"
        text_primary = "#2c3e50"
        text_secondary = "#7f8c8d"
        navbar_bg = "linear-gradient(90deg, #1a2a3a 0%, #2c3e50 100%)"
        border_color = "#ecf0f1"
        hover_bg = "#f8f9fb"
        card_shadow = "0 2px 10px rgba(0,0,0,0.06)"
        table_header_bg = "linear-gradient(90deg, #2c3e50 0%, #34495e 100%)"
    
    st.markdown(f"""
    <style>
    * {{ font-family: 'Segoe UI', 'Tahoma', sans-serif; }}
    
    .stApp {{
        background: {bg_primary};
        color: {text_primary};
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {navbar_bg};
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label {{
        background: rgba(255,255,255,0.08);
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
        color: white !important;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        background: rgba(52, 152, 219, 0.3);
        transform: translateX(4px);
    }}
    
    /* Main Title */
    h1 {{
        color: {text_primary};
        font-weight: 700;
        position: relative;
        padding-bottom: 12px;
        margin-bottom: 25px;
    }}
    h1::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 80px;
        height: 4px;
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        border-radius: 2px;
    }}
    
    h2, h3 {{
        color: {text_primary};
        font-weight: 600;
    }}
    
    /* Metric cards */
    [data-testid="stMetric"] {{
        background: {bg_secondary};
        padding: 20px;
        border-radius: 12px;
        box-shadow: {card_shadow};
        border: 1px solid {border_color};
        transition: all 0.3s ease;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }}
    [data-testid="stMetricLabel"] {{
        color: {text_secondary};
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    [data-testid="stMetricValue"] {{
        color: {text_primary};
        font-weight: 700;
        font-size: 36px;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        padding: 10px 22px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(52, 152, 219, 0.5);
    }}
    
    .stFormSubmitButton > button {{
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        color: white;
        border: none;
        padding: 10px 22px;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
    }}
    .stFormSubmitButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(39, 174, 96, 0.5);
    }}
    
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #9b59b6 0%, #6c3483 100%);
        color: white;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input {{
        background: {bg_secondary};
        color: {text_primary};
        border-radius: 8px;
        border: 1.5px solid {border_color};
        padding: 10px 14px;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: #3498db;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
    }}
    
    .stSelectbox > div > div {{
        background: {bg_secondary};
        border-radius: 8px;
        border: 1.5px solid {border_color};
    }}
    
    /* Expander */
    [data-testid="stExpander"] {{
        background: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
        box-shadow: {card_shadow};
        margin-bottom: 12px;
    }}
    .streamlit-expanderHeader {{
        font-weight: 600;
        color: {text_primary};
    }}
    
    /* Form */
    [data-testid="stForm"] {{
        background: {bg_secondary};
        padding: 25px;
        border-radius: 12px;
        border: 1px solid {border_color};
        box-shadow: {card_shadow};
    }}
    
    /* DataFrame */
    [data-testid="stDataFrame"] {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: {card_shadow};
    }}
    
    /* Alerts */
    [data-testid="stAlert"] {{
        border-radius: 10px;
        padding: 16px 20px;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 5px solid;
    }}
    
    /* Hide Streamlit default items */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Custom divider cards */
    .divider-card {{
        background: {bg_secondary};
        padding: 20px;
        border-radius: 12px;
        border: 1px solid {border_color};
        box-shadow: {card_shadow};
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }}
    .divider-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }}
    
    .divider-30d {{
        border-left: 5px solid #3498db;
        background: linear-gradient(135deg, {bg_secondary} 0%, rgba(52, 152, 219, 0.08) 100%);
    }}
    .divider-40d {{
        border-left: 5px solid #e67e22;
        background: linear-gradient(135deg, {bg_secondary} 0%, rgba(230, 126, 34, 0.08) 100%);
    }}
    .divider-60d {{
        border-left: 5px solid #9b59b6;
        background: linear-gradient(135deg, {bg_secondary} 0%, rgba(155, 89, 182, 0.08) 100%);
    }}
    
    .divider-card h3 {{
        margin: 0 0 8px 0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {text_secondary};
    }}
    .divider-card h1 {{
        margin: 0;
        font-size: 42px;
        font-weight: 700;
        padding: 0;
        border: none;
    }}
    .divider-card h1::after {{ display: none; }}
    
    .color-30d {{ color: #3498db !important; }}
    .color-40d {{ color: #e67e22 !important; }}
    .color-60d {{ color: #9b59b6 !important; }}
    
    .badge {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 13px;
        margin-top: 10px;
    }}
    .badge-danger {{ background: #e74c3c; color: white; }}
    .badge-warning {{ background: #f39c12; color: white; }}
    .badge-success {{ background: #27ae60; color: white; }}
    
    /* Progress bar styling */
    .custom-progress {{
        background: {border_color};
        border-radius: 10px;
        overflow: hidden;
        height: 10px;
        margin-top: 10px;
    }}
    .custom-progress-bar {{
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: {bg_primary}; }}
    ::-webkit-scrollbar-thumb {{ background: {text_secondary}; border-radius: 5px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {text_primary}; }}
    </style>
    """, unsafe_allow_html=True)


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
            alerts.append(('danger', f'🚨 Critical! {dtype} shortage: Need to order {shortage} more units from vendor'))
        elif stock < threshold:
            alerts.append(('warning', f'⚠️ Low stock alert: {dtype} has only {stock} units left. Consider contacting vendor'))

    return alerts


def divider_color(dtype):
    return {'30D': '#3498db', '40D': '#e67e22', '60D': '#9b59b6'}.get(dtype, '#888')


def render_stock_card(dtype, qty, threshold):
    color_class = f"color-{dtype.lower()}"
    div_class = f"divider-{dtype.lower()}"
    
    if qty == 0:
        badge = '<span class="badge badge-danger">❌ Out of Stock</span>'
    elif qty < threshold:
        badge = '<span class="badge badge-warning">⚠️ Low Stock</span>'
    else:
        badge = '<span class="badge badge-success">✅ In Stock</span>'
    
    st.markdown(f"""
    <div class="divider-card {div_class}">
        <h3>{dtype} Stock</h3>
        <h1 class="{color_class}">{qty}</h1>
        {badge}
    </div>
    """, unsafe_allow_html=True)


def render_required_shipped_card(dtype, required, shipped, gap):
    color = divider_color(dtype)
    pct = (shipped / required * 100) if required > 0 else 0
    pct = min(pct, 100)
    gap_color = "#e74c3c" if gap > 0 else "#27ae60"
    
    st.markdown(f"""
    <div class="divider-card divider-{dtype.lower()}">
        <h3 class="color-{dtype.lower()}">{dtype}</h3>
        <p style="margin: 5px 0;"><strong>Required:</strong> {required}</p>
        <p style="margin: 5px 0;"><strong>Shipped:</strong> <span style="color:#27ae60">{shipped}</span></p>
        <p style="margin: 5px 0;"><strong>Gap:</strong> <span style="color:{gap_color}">{gap}</span></p>
        <div class="custom-progress">
            <div class="custom-progress-bar" style="width:{pct}%; background:{color};"></div>
        </div>
        <small style="color: #7f8c8d;">{pct:.0f}% completed</small>
    </div>
    """, unsafe_allow_html=True)


# ============ SIDEBAR ============
st.sidebar.markdown("# 📦 Dividers Tracker")
st.sidebar.markdown("---")

page = st.sidebar.radio("📍 Navigation", 
    ["📊 Dashboard", "🏪 Stores", "📦 Vendor Stock", "🚚 Shipments", "📈 Reports"],
    label_visibility="collapsed")

st.sidebar.markdown("---")

# Dark mode toggle
dark_label = "☀️ Light Mode" if st.session_state.dark_mode else "🌙 Dark Mode"
if st.sidebar.button(dark_label, use_container_width=True):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Dividers Tracker © 2025")


# ============ DASHBOARD ============
if "Dashboard" in page:
    st.title("📊 Dashboard")
    
    threshold = get_threshold()
    
    col_info, col_badge = st.columns([3, 1])
    with col_badge:
        st.markdown(f'<div style="text-align:right; padding-top:10px;"><span class="badge" style="background:#7f8c8d; color:white;">Threshold: {threshold} units</span></div>', unsafe_allow_html=True)

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

    # Summary stats
    c1, c2 = st.columns(2)
    c1.metric("🏪 Total Stores", len(stores_df))
    c2.metric("🚚 Total Shipments", len(shipments_df))

    st.markdown("### 📦 Vendor Stock")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)

    st.markdown("### 🎯 Required vs Shipped")
    c1, c2, c3 = st.columns(3)
    for idx, dtype in enumerate(['30D', '40D', '60D']):
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        gap = required - shipped
        with [c1, c2, c3][idx]:
            render_required_shipped_card(dtype, required, shipped, gap)

    # Charts
    st.markdown("### 📈 Overview Charts")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        chart_data = pd.DataFrame({
            'Type': ['30D', '40D', '60D'],
            'Vendor Stock': [stocks.get('30D', 0), stocks.get('40D', 0), stocks.get('60D', 0)],
            'Required': [
                int(stores_df['required_30d'].sum()) if not stores_df.empty else 0,
                int(stores_df['required_40d'].sum()) if not stores_df.empty else 0,
                int(stores_df['required_60d'].sum()) if not stores_df.empty else 0,
            ],
            'Shipped': [
                int(shipments_df['qty_30d'].sum()) if not shipments_df.empty else 0,
                int(shipments_df['qty_40d'].sum()) if not shipments_df.empty else 0,
                int(shipments_df['qty_60d'].sum()) if not shipments_df.empty else 0,
            ]
        })
        st.bar_chart(chart_data.set_index('Type'), color=['#3498db', '#f39c12', '#27ae60'])
    
    with c2:
        pie_data = pd.DataFrame({
            'Type': ['30D', '40D', '60D'],
            'Stock': [stocks.get('30D', 0), stocks.get('40D', 0), stocks.get('60D', 0)]
        })
        st.markdown("**Stock Distribution**")
        st.dataframe(pie_data, use_container_width=True, hide_index=True)


# ============ STORES ============
elif "Stores" in page:
    st.title("🏪 Stores Management")

    with st.expander("➕ Add New Store", expanded=False):
        with st.form("add_store"):
            name = st.text_input("Store Name *")
            location = st.text_input("Location")
            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("Required 30D 🔵", min_value=0, value=0)
            r40 = c2.number_input("Required 40D 🟠", min_value=0, value=0)
            r60 = c3.number_input("Required 60D 🟣", min_value=0, value=0)
            submitted = st.form_submit_button("➕ Add Store")
            if submitted and name:
                supabase.table('stores').insert({
                    'name': name, 'location': location,
                    'required_30d': r30, 'required_40d': r40, 'required_60d': r60
                }).execute()
                st.success(f"✅ Store '{name}' added!")
                st.rerun()

    st.markdown("### All Stores")
    stores_df = get_stores()
    if stores_df.empty:
        st.info("📭 No stores added yet. Add your first store above!")
    else:
        for _, store in stores_df.iterrows():
            with st.expander(f"🏪 **{store['name']}** — {store['location'] or 'N/A'}"):
                with st.form(f"edit_{store['id']}"):
                    name = st.text_input("Name", value=store['name'], key=f"n_{store['id']}")
                    location = st.text_input("Location", value=store['location'] or '', key=f"l_{store['id']}")
                    c1, c2, c3 = st.columns(3)
                    r30 = c1.number_input("Required 30D 🔵", min_value=0, value=int(store['required_30d']), key=f"r30_{store['id']}")
                    r40 = c2.number_input("Required 40D 🟠", min_value=0, value=int(store['required_40d']), key=f"r40_{store['id']}")
                    r60 = c3.number_input("Required 60D 🟣", min_value=0, value=int(store['required_60d']), key=f"r60_{store['id']}")
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
    st.title("📦 Vendor Stock Management")

    threshold = get_threshold()
    
    with st.expander("⚙️ Settings - Low Stock Threshold"):
        st.info(f"💡 You'll get warnings when stock goes below this number (currently: **{threshold}**)")
        new_threshold = st.number_input("Threshold (units)", min_value=0, value=threshold)
        if st.button("💾 Update Threshold"):
            set_threshold(new_threshold)
            st.success(f"✅ Threshold updated to {new_threshold}")
            st.rerun()

    st.markdown("### Current Stock")
    stocks_df = get_stocks()
    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}
    
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)

    st.markdown("### 🔄 Update Stock")
    with st.form("update_stock"):
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

    st.markdown("### 📜 Stock History (Last 20)")
    res = supabase.table('stock_history').select('*').order('date', desc=True).limit(20).execute()
    if res.data:
        hist_df = pd.DataFrame(res.data)
        hist_df = hist_df[['date', 'divider_type', 'old_qty', 'new_qty', 'change', 'note']]
        hist_df.columns = ['Date', 'Type', 'Old Qty', 'New Qty', 'Change', 'Note']
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No history yet.")


# ============ SHIPMENTS ============
elif "Shipments" in page:
    st.title("🚚 Shipments")

    stores_df = get_stores()
    if stores_df.empty:
        st.warning("⚠️ Add a store first before recording shipments.")
    else:
        with st.expander("➕ Record New Shipment", expanded=False):
            with st.form("add_shipment"):
                store_options = {f"{row['name']} ({row['location'] or 'N/A'})": row['id'] for _, row in stores_df.iterrows()}
                selected = st.selectbox("Store", list(store_options.keys()))
                ship_date = st.date_input("Date", value=date.today())
                c1, c2, c3 = st.columns(3)
                q30 = c1.number_input("Qty 30D 🔵", min_value=0, value=0)
                q40 = c2.number_input("Qty 40D 🟠", min_value=0, value=0)
                q60 = c3.number_input("Qty 60D 🟣", min_value=0, value=0)
                notes = st.text_area("Notes")
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

    st.markdown("### All Shipments")
    shipments_df = get_shipments()
    if shipments_df.empty:
        st.info("📭 No shipments yet.")
    else:
        display_df = shipments_df[['id', 'store_name', 'date', 'qty_30d', 'qty_40d', 'qty_60d', 'notes']].copy()
        display_df.columns = ['ID', 'Store', 'Date', '30D 🔵', '40D 🟠', '60D 🟣', 'Notes']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        c1, c2 = st.columns([1, 3])
        del_id = c1.number_input("Shipment ID to Delete", min_value=0, value=0)
        if c2.button("🗑️ Delete Shipment"):
            if del_id > 0:
                supabase.table('shipments').delete().eq('id', del_id).execute()
                st.warning(f"🗑️ Shipment #{del_id} deleted.")
                st.rerun()


# ============ REPORTS ============
elif "Reports" in page:
    st.title("📈 Reports")

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
                'Location': store['location'] or '',
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
        
        # Color-coded styling
        def highlight_gaps(val, col_name):
            if 'Gap' in col_name and isinstance(val, (int, float)):
                if val > 0:
                    return 'color: #e74c3c; font-weight: 700;'
                elif val == 0:
                    return 'color: #27ae60; font-weight: 600;'
            return ''
        
        styled = report_df.style.apply(lambda row: [highlight_gaps(v, c) for v, c in zip(row, report_df.columns)], axis=1)
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
        st.download_button(
            label="📥 Download Excel Report",
            data=output,
            file_name=f"dividers_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
