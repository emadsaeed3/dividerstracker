"""
Dashboard page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from coverage_helper import calculate_coverage
from database import (
    get_threshold, get_stocks_dict, get_stores, get_shipments,
    get_upcoming_launches, get_magnet_stock, get_magnet_status_dict,
    get_client
)
from components import (
    render_stat_card, render_stock_card, render_progress_card,
    render_magnet_status_card, render_threshold_chip, render_section_title,
    render_bar_chart, render_pie_chart
)
from styles import get_plotly_theme


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            try:
                return pd.to_datetime(value).date()
            except Exception:
                return None
    return None


def calculate_stock_alerts(stocks, stores_df, shipments_df, threshold):
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
    alerts = []
    upcoming = get_upcoming_launches(days_ahead=4)

    if upcoming.empty:
        return alerts

    for _, store in upcoming.iterrows():
        days_left = store['days_left']
        name = store['name']
        location = store.get('location') or 'N/A'

        if days_left == 0:
            alerts.append(('danger', f'🚀 **LAUNCHING TODAY:** {name} ({location})'))
        elif days_left == 1:
            alerts.append(('danger', f'🚨 **Launch Tomorrow:** {name} ({location}) — Shipment must be out NOW!'))
        elif days_left == 2:
            alerts.append(('warning', f'⚠️ **Launch in 2 days:** {name} ({location}) — Schedule shipment today!'))
        elif days_left <= 4:
            alerts.append(('info', f'📅 **Launch in {days_left} days:** {name} ({location})'))

    return alerts


def calculate_transport_alerts(shipments_df):
    """Alerts for shipments without transportation arranged"""
    alerts = []
    today = date.today()

    if shipments_df.empty:
        return alerts

    for _, ship in shipments_df.iterrows():
        status = ship.get('delivery_status') or 'Pending'
        if status not in ('Pending', 'In Transit'):
            continue

        if bool(ship.get('transportation_ready', False)):
            continue

        scheduled = _to_date(ship.get('scheduled_date'))
        if not scheduled:
            continue

        days = (scheduled - today).days
        store_name = ship.get('store_name', 'Unknown')
        ship_id = ship.get('id')

        if days < 0:
            alerts.append(('danger', f'🚛 **Transport NOT arranged** for shipment #{ship_id} to {store_name} (was due {abs(days)}d ago)'))
        elif days <= 1:
            alerts.append(('danger', f'🚛 **Transport NOT ready** for shipment #{ship_id} to {store_name} — delivers tomorrow!'))
        elif days <= 2:
            alerts.append(('warning', f'🚛 **Arrange transport** for shipment #{ship_id} to {store_name} ({days}d)'))

    return alerts


def calculate_magnet_alerts(stocks):
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
            f'🧲 **Magnet shortage:** Need **{shortage}** more strips ({total_without} dividers without magnet, only {strips} strips available)'
        ))

    return alerts


# ==================== COVERAGE SUMMARY ====================

def render_coverage_summary():
    """Quick coverage summary for dashboard"""
    coverage = calculate_coverage()
    demand = coverage['demand']

    if demand['stores_count'] == 0:
        return  # Don't show if no demand

    cov = coverage['coverage']
    short = coverage['shortages']

    if cov['overall_status'] == 'covered':
        color = '#27ae60'
        bg = 'rgba(39,174,96,0.1)'
        icon = '✅'
        msg = f"All {demand['stores_count']} stores can be fully covered with current supply!"
    elif cov['overall_status'] == 'partial':
        color = '#f39c12'
        bg = 'rgba(243,156,18,0.1)'
        icon = '⚠️'
        msg = f"Partial coverage for {demand['stores_count']} stores. Shortage: {short['total_shortage']} dividers."
    else:
        color = '#e74c3c'
        bg = 'rgba(231,76,60,0.1)'
        icon = '🚨'
        msg = f"Critical! {demand['stores_count']} stores need supply. Shortage: {short['total_shortage']} dividers."

    st.markdown(
        f'<div style="background:{bg}; padding:16px 20px; border-radius:12px; '
        f'border-left:5px solid {color}; margin-bottom:16px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">'
        f'<div>'
        f'<div style="font-size:1rem; font-weight:700;">{icon} Coverage Status</div>'
        f'<div style="font-size:0.88rem; opacity:0.9; margin-top:4px;">{msg}</div>'
        f'</div>'
        f'<div style="display:flex; gap:12px;">'
        f'<div style="text-align:center;">'
        f'<div style="font-size:0.7rem; opacity:0.7;">🔵 30D</div>'
        f'<div style="font-size:1.1rem; font-weight:700;">{cov["pct_30d"]:.0f}%</div>'
        f'</div>'
        f'<div style="text-align:center;">'
        f'<div style="font-size:0.7rem; opacity:0.7;">🟠 40D</div>'
        f'<div style="font-size:1.1rem; font-weight:700;">{cov["pct_40d"]:.0f}%</div>'
        f'</div>'
        f'<div style="text-align:center;">'
        f'<div style="font-size:0.7rem; opacity:0.7;">🟣 60D</div>'
        f'<div style="font-size:1.1rem; font-weight:700;">{cov["pct_60d"]:.0f}%</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="font-size:0.78rem; opacity:0.8; margin-top:8px;">'
        f'💡 Visit <b>Vendor Stock → Coverage Analysis</b> for full details'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# ==================== TREND CHARTS ====================

def render_stock_trend_chart():
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

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=60)
    df = df[df['date'] >= cutoff]

    if df.empty:
        st.info("📊 No recent stock activity.")
        return

    color_map = {'30D': '#3498db', '40D': '#e67e22', '60D': '#9b59b6'}
    fig = go.Figure()

    for dtype in ['30D', '40D', '60D']:
        sub = df[df['divider_type'] == dtype]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub['date'], y=sub['new_qty'],
                mode='lines+markers', name=dtype,
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
    if shipments_df.empty:
        st.info("📊 No shipments yet.")
        return

    df = shipments_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    cutoff = pd.Timestamp.now() - pd.Timedelta(weeks=12)
    df = df[df['date'] >= cutoff]

    if df.empty:
        st.info("📊 No shipments in the last 12 weeks.")
        return

    df['week'] = df['date'].dt.to_period('W').dt.start_time
    weekly = df.groupby('week').size().reset_index(name='count')
    weekly['week_str'] = weekly['week'].dt.strftime('%d %b')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly['week_str'], y=weekly['count'],
        marker_color='#3498db',
        text=weekly['count'], textposition='outside'
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
    if shipments_df.empty or 'delivery_status' not in shipments_df.columns:
        st.info("📊 No shipment status data.")
        return

    df = shipments_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    df = df[df['date'] >= cutoff]

    if df.empty:
        st.info("📊 No recent shipments (last 30 days).")
        return

    df['date_only'] = df['date'].dt.date
    grouped = df.groupby(['date_only', 'delivery_status']).size().reset_index(name='count')

    status_colors = {
        'Pending': '#f39c12', 'In Transit': '#3498db',
        'Delivered': '#27ae60', 'Delayed': '#e74c3c'
    }

    fig = go.Figure()
    for status in ['Pending', 'In Transit', 'Delivered', 'Delayed']:
        sub = grouped[grouped['delivery_status'] == status]
        if not sub.empty:
            fig.add_trace(go.Bar(
                name=status, x=sub['date_only'], y=sub['count'],
                marker_color=status_colors.get(status, '#7f8c8d')
            ))

    fig.update_layout(
        barmode='stack', height=350,
        title=dict(text='<b>📦 Shipments by Status (Last 30 Days)</b>', font=dict(size=15)),
        margin=dict(t=50, b=40, l=40, r=20),
        xaxis=dict(title='Date'), yaxis=dict(title='Shipments'),
        **get_plotly_theme()
    )
    st.plotly_chart(fig, use_container_width=True)


def render_launches_timeline(stores_df):
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
    future_cutoff = today + pd.Timedelta(days=60)
    past_cutoff = today - pd.Timedelta(days=30)
    df = df[(df['launch_date'] >= past_cutoff) & (df['launch_date'] <= future_cutoff)]

    if df.empty:
        st.info("📊 No launches in window.")
        return

    df = df.sort_values('launch_date')
    df['days_from_today'] = (df['launch_date'] - today).dt.days

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
        x=df['launch_date'], y=df['name'],
        mode='markers+text',
        marker=dict(size=14, color=colors, line=dict(width=2, color='white')),
        text=df['days_from_today'].apply(lambda d: f'{d:+d}d' if d != 0 else 'Today'),
        textposition='top center', textfont=dict(size=10),
        hovertemplate='<b>%{y}</b><br>Launch: %{x|%d %b %Y}<br>%{text}<extra></extra>'
    ))

    fig.add_vline(
        x=today.timestamp() * 1000,
        line=dict(color='red', width=2, dash='dash'),
        annotation_text='Today', annotation_position='top'
    )

    fig.update_layout(
        height=max(300, 40 * len(df) + 100),
        title=dict(text='<b>🚀 Launches Timeline</b>', font=dict(size=15)),
        margin=dict(t=50, b=40, l=40, r=20),
        xaxis=dict(title='Launch Date'),
        yaxis=dict(title='', autorange='reversed'),
        showlegend=False,
        **get_plotly_theme()
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== MAIN RENDER ====================

def render():
    col_title, col_chip = st.columns([3, 1])
    with col_title:
        st.markdown("# 📊 Dashboard")
    with col_chip:
        threshold = get_threshold()
        render_threshold_chip(threshold)

    stocks = get_stocks_dict()
    stores_df = get_stores()
    shipments_df = get_shipments()

    # 🆕 Coverage Summary (shows at the top)
    render_coverage_summary()

    # Alerts
    stock_alerts = calculate_stock_alerts(stocks, stores_df, shipments_df, threshold)
    launch_alerts = calculate_launch_alerts()
    transport_alerts = calculate_transport_alerts(shipments_df)
    magnet_alerts = calculate_magnet_alerts(stocks)

    all_alerts = launch_alerts + transport_alerts + stock_alerts + magnet_alerts

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

    # Analytics
    render_section_title("📊 Analytics")
    c1, c2 = st.columns([2, 1])

    with c1:
        required_list = [req_shipped[t][0] for t in ['30D', '40D', '60D']]
        shipped_list = [req_shipped[t][1] for t in ['30D', '40D', '60D']]
        render_bar_chart(stocks, required_list, shipped_list)

    with c2:
        render_pie_chart(stocks)

    # Trends
    render_section_title("📈 Trends & Insights")

    c1, c2 = st.columns(2)
    with c1:
        render_stock_trend_chart()
    with c2:
        render_shipments_per_week_chart(shipments_df)

    c1, c2 = st.columns(2)
    with c1:
        render_delivery_status_trend(shipments_df)
    with c2:
        render_launches_timeline(stores_df)
