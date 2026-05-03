"""
Components module - Reusable UI components
"""
import streamlit as st
import plotly.graph_objects as go
from styles import get_plotly_theme


# ==================== SIDEBAR ====================

def render_sidebar():
    """Render sidebar with navigation and dark mode toggle"""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align:center; padding: 10px 0 20px 0;">
            <i class="bi bi-box-seam" style="font-size:2.5rem; color:#3498db;"></i>
            <h1 style="margin:8px 0 0 0;">Dividers Tracker</h1>
            <p style="font-size:0.8rem; opacity:0.7; margin:0;">Management Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📊  Dashboard", "🏪  Stores", "📦  Vendor Stock", "🚚  Shipments", "📈  Reports"],
            label_visibility="collapsed"
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
        <div style="text-align:center; font-size:0.75rem; opacity:0.6; padding:10px;">
            <i class="bi bi-heart-fill" style="color:#e74c3c;"></i> Built with Streamlit<br>
            © 2025
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
