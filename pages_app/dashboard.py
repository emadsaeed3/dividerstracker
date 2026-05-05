"""
Dashboard page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from database import (
    get_threshold, get_stocks_dict, get_stores, get_shipments,
    get_upcoming_launches, get_magnet_stock, get_magnet_status_dict,
    get_stock_history, get_client
)
from components import (
    render_stat_card, render_stock_card, render_progress_card,
    render_magnet_status_card, render_threshold_chip, render_section_title,
    render_bar_chart, render_pie_chart
)
from styles import get_plotly_theme


def calculate_stock_alerts(stocks, stores_df, shipments_df, threshold):
    """Calculate stock alerts based on required vs shipped"""
    alerts = []

    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = stores_df[col].sum() if not stores_df.empty else 0
        shipped = shipments_df[ship_col].sum() if not shipments_df.empty else 0
        remaining_need = max(0, required - shipped)

        if stock < remaining_need:
            shortage = remaining_need - stock
            alerts.append(('danger', f'🚨 **Critical!** {dtype} shortage: Need to order **{shortage}** more units'))
        elif stock < threshold:
            alerts.append(('warning', f'⚠️ **Low stock:** {dtype} has only **{stock}** units left'))

    return alerts


def calculate_launch_alerts():
    """Calculate alerts for upcoming store launches"""
    alerts = []
    upcoming = get_upcoming_launches(days_ahead=4)

    if upcoming.empty:
        return alerts

    for _, store in upcoming.iterrows():
        days_left = store['days_left']
        name = store['name']
        location = store.get('location') or 'N/A'
        transport_ready = bool(store.get('transportation_ready', False))

        if days_left == 0:
            alerts.append(('danger', f'🚀 **LAUNCHING TODAY:** {name} ({location}) — Make sure everything is delivered!'))
        elif days_left == 1:
            alerts.append(('danger', f'🚨 **Launch Tomorrow:** {name} ({location}) — Shipment must be out NOW!'))
        elif days_left == 2:
            alerts.append(('warning', f'⚠️ **Launch in 2 days:** {name} ({location}) — Schedule shipment today!'))
            if not transport_ready:
                alerts.append(('warning', f'🚚 **Transportation NOT ready** for {name} — Arrange transport today!'))
        elif days_left <= 4:
            alerts.append(('info', f'📅 **Launch in {days_left} days:** {name} ({location}) — Prepare shipment soon.'))
            if not transport_ready and days_left <= 3:
                alerts.append(('warning', f'🚚 **Transportation not ready** for {name} — Arrange within 24h'))

    return alerts


def calculate_magnet_alerts(stocks):
    """Calculate magnet coverage alerts"""
    alerts = []
    strips = get_magnet_stock()
    magnet_status = get_magnet_status_dict()

    total_without = sum(
        magnet_status.get(t, {}).get('without_magnet', 0)
        for t in ['30D', '40D', '60D']
    )

    if total_without > 0 and strips < total_without:
        shortage = total_without - strips
        alerts.append((
            'warning',
            f'🧲 **Magnet shortage:** Need **{shortage}** more strips to cover all dividers ({total_without} dividers without magnet, only {strips} strips available)'
        ))

    return alerts


# ==================== TREND CHARTS ====================

def render_stock_trend_chart():
    """Render stock level changes over time"""
    # Get last 30 days of history
    supabase = get_client()
    try:
        res = supabase.table('stock_history').select('*').order('date', desc=False).limit(200).execute()
    except Exception:
        res = None

    if not res or not res.data:
        st.info("📊 No stock history yet. Start updating stock to see trends.")
        return

    df = pd.DataFrame(res.data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Filter to last 60 days
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=60)
    df = df[df['date'] >= cutoff]

    if df.empty:
        st.info("📊 No recent stock activity in the last 60 days.")
        return

    color_map = {'30D': '#3498db', '40D': '#e67e22', '60D': '#9b59b6'}
    fig = go.Figure()

    for dtype in ['30D', '40D', '60D']:
        sub = df[df['divider_type'] == dtype]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub['date'],
                y=sub['new_qty'],
                mode='lines+markers',
                name=dtype,
                line=dict(color=color_map[dtype], width=2.5),
                marker=dict(size=6)
            ))

    fig.update_layout(
        height=350,
        title=dict(text='<b>📈 Stock Level Trends (Last 60 Days)</b>', font=dict(size=15)),
        margin=dict(t=50, b=40, l=40, r=20),
        hovermode='x unified',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Quantity'),
        **get_plotly_theme()
    )

    st.plotly_chart(fig, use_container_width=True)


def render_shipments_per_week_chart(shipments_df):
    """Render shipments count per week"""
    if shipments_df.empty:
        st.info("📊 No shipments yet.")
        return

    df = shipments_df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Filter last 12 weeks
    cutoff = pd.Timestamp.now() - pd.Timedelta(weeks=12)
    df = df[df['date'] >= cutoff]

    if df.empty:
        st.info("📊 No shipments in the last 12 weeks.")
        return

    # Group by week
    df['week'] = df['date'].dt.to_period('W').dt.start_time
    weekly = df.groupby('week').size().reset_index(name='count')
    weekly['week_str'] = weekly['week'].dt.strftime('%d %b')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly['week_str'],
        y=weekly['count'],
        marker_color='#3498db',
        text=weekly['count'],
        textposition='outside'
    ))

    fig.update_layout(
        height=350,
        title=dict(text='<b>🚚 Shipments per Week (Last 12 Weeks)</b>', font=dict(size=15)),
        margin=dict(t=50, b=40, l=40, r=20),
        xaxis=dict(title='Week Starting'),
        yaxis=dict(title='Number of Shipments'),
        **get_plotly_theme()
    )

    st.plotly_chart(fig, use_container_width=True)


def render_delivery_status_trend(shipments_df):
    """Render delivery status over time"""
    if shipments_df.empty or 'delivery_status' not in shipments_df.columns:
        st.info("📊 No shipment status data.")
        return

    df = shipments_df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Last 30 days
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    df = df[df['date'] >= cutoff]

    if df.empty:
        st.info("📊 No recent shipments (last 30 days).")
        return

    # Group by date + status
    df['date_only'] = df['date'].dt.date
    grouped = df.groupby(['date_only', 'delivery_status']).size().reset_index(name='count')

    status_colors = {
        'Pending': '#f39c12',
        'In Transit': '#3498db',
        'Delivered': '#27ae60',
        'Delayed': '#e74c3c'
    }

    fig = go.Figure()

    for status in ['Pending', 'In Transit', 'Delivered', 'Delayed']:
        sub = grouped[grouped['delivery_status'] == status]
        if not sub.empty:
            fig.add_trace(go.Bar(
                name=status,
                x=sub['date_only'],
                y=sub['count'],
                marker_color=status_colors.get(status, '#7f8c8d')
            ))

    fig.update_layout(
        barmode='stack',
        height=350,
        title=dict(text='<b>📦 Shipments by Status (Last 30 Days)</b>', font=dict(size=15)),
        margin=dict(t=50, b=40, l=40, r=20),
        xaxis=dict(title='Date'),
        yaxis=dict(title='Shipments'),
        **get_plotly_theme()
    )

    st.plotly_chart(fig, use_container_width=True)


def render_launches_timeline(stores_df):
    """Render upcoming launches timeline"""
    if stores_df.empty or 'launch_date' not in stores_df.columns:
        st.info("📊 No stores with launch dates.")
        return

    df = stores_df.copy()
    df = df[df['launch_date'].notna()]

    if df.empty:
        st.info("📊 No launches scheduled.")
        return

    df['launch_date'] = pd.to_datetime(df['launch_date'])
    today = pd.Timestamp.now().normalize()

    # Next 60 days
    future_cutoff = today + pd.Timedelta(days=60)
    past_cutoff = today - pd.Timedelta(days=30)
    df = df[(df['launch_date'] >= past_cutoff) & (df['launch_date'] <= future_cutoff)]

    if df.empty:
        st.info("📊 No launches in the next 60 days or last 30.")
        return

    df = df.sort_values('launch_date')
    df['days_from_today'] = (df['launch_date'] - today).dt.days

    # Color by launched status
    colors = []
    for _, row in df.iterrows():
        if row.get('is_launched'):
            colors.append('#27ae60')
        elif row['days_from_today'] < 0:
            colors.append('#95a5a6')
        elif row['days_from_today'] <= 2:
            colors.append('#e74c3c')
        elif row['days_from_today'] <= 7:
            colors.append('#f39c12')
        else:
            colors.append('#3498db')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['launch_date'],
        y=df['name'],
        mode='markers+text',
        marker=dict(size=14, color=colors, line=dict(width=2, color='white')),
        text=df['days_from_today'].apply(lambda d: f'{d:+d}d' if d != 0 else 'Today'),
        textposition='top center',
        textfont=dict(size=10),
        hovertemplate='<b>%{y}</b><br>Launch: %{x|%d %b %Y}<br>%{text}<extra></extra>'
    ))

    # Today line
    fig.add_vline(
        x=today.timestamp() * 1000,
        line=dict(color='red', width=2, dash='dash'),
        annotation_text='Today',
        annotation_position='top'
    )

    fig.update_layout(
        height=max(300, 40 * len(df) + 100),
        title=dict(text='<b>🚀 Launches Timeline (Last 30d + Next 60d)</b>', font=dict(size=15)),
        margin=dict(t=50, b=40, l=40, r=20),
        xaxis=dict(title='Launch Date'),
        yaxis=dict(title='', autorange='reversed'),
        showlegend=False,
        **get_plotly_theme()
    )

    st.plotly_chart(fig, use_container_width=True)


# ==================== MAIN RENDER ====================

def render():
    """Render the Dashboard page"""
    col_title, col_chip = st.columns([3, 1])
    with col_title:
        st.markdown("# 📊 Dashboard")
    with col_chip:
        threshold = get_threshold()
        render_threshold_chip(threshold)

    stocks = get_stocks_dict()
    stores_df = get_stores()
    shipments_df = get_shipments()

    # Alerts
    stock_alerts = calculate_stock_alerts(stocks, stores_df, shipments_df, threshold)
    launch_alerts = calculate_launch_alerts()
    magnet_alerts = calculate_magnet_alerts(stocks)

    all_alerts = launch_alerts + stock_alerts + magnet_alerts

    if all_alerts:
        render_section_title("🔔 Alerts")
        for level, msg in all_alerts:
            if level == 'danger':
                st.error(msg)
            elif level == 'warning':
                st.warning(msg)
            else:
                st.info(msg)

    # Overview
    render_section_title("📌 Overview")

    pending_count = 0
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        pending_count = len(shipments_df[shipments_df['delivery_status'].isin(['Pending', 'In Transit'])])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card("Total Stores", len(stores_df), "card-stores", "bi-shop")
    with c2:
        render_stat_card("Total Shipments", len(shipments_df), "card-shipments", "bi-truck")
    with c3:
        render_stat_card("In Progress", pending_count, "card-40d", "bi-hourglass-split")
    with c4:
        upcoming = get_upcoming_launches(days_ahead=4)
        render_stat_card("Upcoming Launches", len(upcoming), "card-30d", "bi-rocket-takeoff")

    # Vendor Stock
    render_section_title("📦 Vendor Stock")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)

    # Required vs Shipped
    render_section_title("🎯 Required vs Shipped")
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

    # Magnet Status
    render_section_title("🧲 Dividers Magnet Status")
    magnet_status = get_magnet_status_dict()
    strips = get_magnet_stock()

    c1, c2, c3 = st.columns(3)
    for idx, dtype in enumerate(['30D', '40D', '60D']):
        status = magnet_status.get(dtype, {'with_magnet': 0, 'without_magnet': 0})
        with [c1, c2, c3][idx]:
            render_magnet_status_card(dtype, status['with_magnet'], status['without_magnet'])

    total_with = sum(magnet_status.get(t, {}).get('with_magnet', 0) for t in ['30D', '40D', '60D'])
    total_without = sum(magnet_status.get(t, {}).get('without_magnet', 0) for t in ['30D', '40D', '60D'])

    c1, c2, c3 = st.columns(3)
    with c1:
        render_stat_card("Magnet Strips", strips, "card-60d", "bi-layout-three-columns")
    with c2:
        render_stat_card("With Magnet 🧲", total_with, "card-shipments", "bi-check-circle-fill")
    with c3:
        render_stat_card("Without Magnet ⭕", total_without, "card-40d", "bi-x-circle")

    # Analytics (existing)
    render_section_title("📊 Analytics")
    c1, c2 = st.columns([2, 1])

    with c1:
        required_list = [req_shipped[t][0] for t in ['30D', '40D', '60D']]
        shipped_list = [req_shipped[t][1] for t in ['30D', '40D', '60D']]
        render_bar_chart(stocks, required_list, shipped_list)

    with c2:
        render_pie_chart(stocks)

    # ==================== TREND CHARTS ====================
    render_section_title("📈 Trends & Insights")

    # Row 1: Stock trend + Shipments per week
    c1, c2 = st.columns(2)
    with c1:
        render_stock_trend_chart()
    with c2:
        render_shipments_per_week_chart(shipments_df)

    # Row 2: Delivery status + Launches timeline
    c1, c2 = st.columns(2)
    with c1:
        render_delivery_status_trend(shipments_df)
    with c2:
        render_launches_timeline(stores_df)
