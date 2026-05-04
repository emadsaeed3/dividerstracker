"""
Components module - Reusable UI components
"""
import os
import base64
import streamlit as st
import plotly.graph_objects as go
from styles import get_plotly_theme


# ==================== LOGO HELPER ====================

def get_logo_base64(force_white=False):
    """Load the appropriate logo based on dark/light mode"""
    is_dark = st.session_state.get('dark_mode', False)

    if force_white or is_dark:
        logo_file = "Now-PrimaryLogo-White.png"
    else:
        logo_file = "Now-PrimaryLogo-Squid.png"

    try:
        if os.path.exists(logo_file):
            with open(logo_file, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return None


# ==================== SIDEBAR ====================

def render_sidebar():
    """Render sidebar with section switcher + navigation"""
    # Initialize session state
    if 'section' not in st.session_state:
        st.session_state.section = None  # None = no section chosen yet

    with st.sidebar:
        # Logo
        logo_b64 = get_logo_base64(force_white=True)
        if logo_b64:
            st.markdown(f"""
            <div style="text-align:center; padding: 10px 0 15px 0;">
                <img src="data:image/png;base64,{logo_b64}" 
                     style="max-width: 160px; height: auto; margin-bottom: 8px;" />
                <h1 style="margin:8px 0 0 0; font-size:1.25rem !important;">Launch Team Tracker</h1>
                <p style="font-size:0.75rem; opacity:0.85; margin:4px 0 0 0;">
                    Launch Team • Amazon Now
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding: 10px 0 15px 0;">
                <i class="bi bi-box-seam" style="font-size:2.5rem; color:#3498db;"></i>
                <h1 style="margin:8px 0 0 0;">Launch Team Tracker</h1>
                <p style="font-size:0.75rem; opacity:0.85; margin:4px 0 0 0;">
                    Launch Team • Amazon Now
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Section Switcher (Stacked - one above the other)
        st.markdown("""
        <div style="font-size:0.7rem; opacity:0.75; text-transform:uppercase; 
                    letter-spacing:1.2px; font-weight:700; margin-bottom:8px;">
            🔄 Select Section
        </div>
        """, unsafe_allow_html=True)

        dividers_active = st.session_state.section == 'dividers'
        if st.button(
            "📦 Dividers",
            use_container_width=True,
            key="btn_dividers",
            type="primary" if dividers_active else "secondary"
        ):
            st.session_state.section = 'dividers'
            st.rerun()

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        it_active = st.session_state.section == 'it'
        if st.button(
            "💻 4M IT Equipment",
            use_container_width=True,
            key="btn_it",
            type="primary" if it_active else "secondary"
        ):
            st.session_state.section = 'it'
            st.rerun()

        # Navigation only shows AFTER a section is selected
        page = None
        if st.session_state.section is not None:
            st.markdown("---")
            st.markdown("""
            <div style="font-size:0.7rem; opacity:0.75; text-transform:uppercase; 
                        letter-spacing:1.2px; font-weight:700; margin-bottom:8px;">
                📍 Navigation
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.section == 'dividers':
                page = st.radio(
                    "Navigation",
                    [
                        "📊  Dashboard",
                        "🏪  Stores",
                        "📦  Vendor Stock",
                        "🧲  Magnets",
                        "🚚  Shipments",
                        "📈  Reports"
                    ],
                    label_visibility="collapsed",
                    key="nav_dividers"
                )
            else:
                page = st.radio(
                    "Navigation",
                    [
                        "📊  Dashboard",
                        "🏢  RDCs",
                        "💻  IT Stock",
                        "🚚  Shipments",
                        "📈  Reports"
                    ],
                    label_visibility="collapsed",
                    key="nav_it"
                )

        st.markdown("---")

        # Dark mode toggle
        dark_label = "☀️ Switch to Light" if st.session_state.dark_mode else "🌙 Switch to Dark"
        if st.button(dark_label, use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

        # Footer
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; font-size:0.7rem; opacity:0.65; padding:10px;">
            <i class="bi bi-heart-fill" style="color:#e74c3c;"></i> Built with Streamlit<br>
            <b>Launch Team</b> © 2025
        </div>
        """, unsafe_allow_html=True)

        return page


# ==================== CARDS ====================

def render_stat_card(label, value, card_class, icon):
    """Render a general statistics card"""
    st.markdown(f"""
    <div class="stat-card {card_class}">
        <i class="bi {icon} icon-bg"></i>
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stock_card(dtype, qty, threshold):
    """Render a stock card with status badge"""
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
    """Render a progress card showing Required vs Shipped"""
    color_map = {'30D': '#3498db', '40D': '#e67e22', '60D': '#9b59b6'}
    color = color_map.get(dtype, '#3498db')
    pct = min((shipped / required * 100) if required > 0 else 0, 100)
    gap_color = "#e74c3c" if gap > 0 else "#27ae60"
    gap_icon = "⚠️" if gap > 0 else "✅"
    gap_label = "Pending" if gap > 0 else "Complete"

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
                <span style="font-weight:700; color:{gap_color};">{gap_icon} {gap_label}: {gap}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_magnet_status_card(dtype, with_magnet, without_magnet):
    """Render a magnet status card for a divider type"""
    color_map = {'30D': '#3498db', '40D': '#e67e22', '60D': '#9b59b6'}
    color = color_map.get(dtype, '#3498db')

    total = with_magnet + without_magnet
    pct = (with_magnet / total * 100) if total > 0 else 0

    st.markdown(f"""
    <div class="stat-card card-{dtype.lower()}">
        <i class="bi bi-magnet icon-bg"></i>
        <div class="stat-label" style="color:{color};">{dtype} Magnet Status</div>
        <div style="margin-top: 14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:0.95rem;">🧲 <b>With:</b> <span style="color:#27ae60; font-weight:700;">{with_magnet}</span></span>
                <span style="font-size:0.95rem;">⭕ <b>Without:</b> <span style="color:#e74c3c; font-weight:700;">{without_magnet}</span></span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; padding-top:8px; border-top:1px solid rgba(0,0,0,0.1);">
                <span style="font-size:0.85rem;"><b>Total:</b> {total}</span>
                <span style="font-size:0.85rem; font-weight:700; color:{color};">{pct:.0f}%</span>
            </div>
            <div class="progress-container" style="margin-top:8px;">
                <div class="progress-fill" style="width:{pct}%; background:{color};"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_it_stock_card(item_name, qty, threshold, icon="bi-cpu"):
    """Render IT equipment stock card"""
    if qty == 0:
        badge = '<span class="badge-stock badge-danger">❌ Out of Stock</span>'
        border_color = '#e74c3c'
    elif qty < threshold:
        badge = '<span class="badge-stock badge-warning">⚠️ Low Stock</span>'
        border_color = '#f39c12'
    else:
        badge = '<span class="badge-stock badge-success">✅ In Stock</span>'
        border_color = '#27ae60'

    st.markdown(f"""
    <div class="stat-card" style="border-left: 5px solid {border_color};">
        <i class="bi {icon} icon-bg" style="color:{border_color};"></i>
        <div class="stat-label">{item_name}</div>
        <div class="stat-value" style="font-size:2.2rem;">{qty}</div>
        {badge}
    </div>
    """, unsafe_allow_html=True)


def render_threshold_chip(threshold):
    """Render the threshold chip displayed on Dashboard"""
    st.markdown(
        f'<div style="text-align:right; padding-top:12px;">'
        f'<span class="threshold-chip">⚙️ Threshold: {threshold}</span>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_section_title(title):
    """Render a section title with left border"""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


# ==================== CHARTS ====================

def render_bar_chart(stocks_data, required_data, shipped_data):
    """Render grouped bar chart: Stock vs Required vs Shipped"""
    types = ['30D', '40D', '60D']
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Vendor Stock',
        x=types,
        y=[stocks_data.get(t, 0) for t in types],
        marker_color='#3498db'
    ))
    fig.add_trace(go.Bar(
        name='Required',
        x=types,
        y=required_data,
        marker_color='#f39c12'
    ))
    fig.add_trace(go.Bar(
        name='Shipped',
        x=types,
        y=shipped_data,
        marker_color='#27ae60'
    ))

    fig.update_layout(
        barmode='group',
        height=380,
        title=dict(text='<b>Stock Overview</b>', font=dict(size=16)),
        margin=dict(t=50, b=40, l=40, r=20),
        **get_plotly_theme()
    )

    st.plotly_chart(fig, use_container_width=True)


def render_pie_chart(stocks_data):
    """Render pie chart for stock distribution"""
    types = ['30D', '40D', '60D']
    values = [stocks_data.get(t, 0) for t in types]
    total = sum(values)

    if total == 0:
        st.info("📊 No stock data yet.")
        return

    fig = go.Figure(data=[go.Pie(
        labels=types,
        values=values,
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
