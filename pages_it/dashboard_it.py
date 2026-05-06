"""
4M IT Equipment Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from database_it import (
    IT_EQUIPMENT_TYPES, IT_ICONS,
    get_it_stock_dict, get_rdcs, get_it_shipments,
    get_upcoming_rdc_launches, get_total_requirements,
    get_rdc_requirements_dict, get_shipped_totals_per_rdc,
    get_all_shipment_items
)
from database import get_threshold
from components import (
    render_stat_card, render_it_stock_card,
    render_section_title
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


def calculate_launch_alerts():
    alerts = []
    upcoming = get_upcoming_rdc_launches(days_ahead=4)

    if upcoming.empty:
        return alerts

    for _, rdc in upcoming.iterrows():
        days_left = rdc['days_left']
        name = rdc['name']
        location = rdc.get('location') or 'N/A'

        if days_left == 0:
            alerts.append(('danger', f'🚀 **LAUNCHING TODAY:** {name} ({location})'))
        elif days_left == 1:
            alerts.append(('danger', f'🚨 **Launch Tomorrow:** {name} ({location}) — Ship NOW!'))
        elif days_left == 2:
            alerts.append(('warning', f'⚠️ **Launch in 2 days:** {name} ({location}) — Schedule shipment today!'))
        elif days_left <= 4:
            alerts.append(('info', f'📅 **Launch in {days_left} days:** {name} ({location})'))

    return alerts


def calculate_transport_alerts(shipments_df):
    """Alerts for IT shipments without transportation"""
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
        rdc_name = ship.get('rdc_name', 'Unknown')
        ship_id = ship.get('id')

        if days < 0:
            alerts.append(('danger', f'🚛 **Transport NOT arranged** for IT shipment #{ship_id} to {rdc_name} (was due {abs(days)}d ago)'))
        elif days <= 1:
            alerts.append(('danger', f'🚛 **Transport NOT ready** for IT shipment #{ship_id} to {rdc_name} — delivers tomorrow!'))
        elif days <= 2:
            alerts.append(('warning', f'🚛 **Arrange transport** for IT shipment #{ship_id} to {rdc_name} ({days}d)'))

    return alerts


def calculate_stock_alerts(stocks, requirements, threshold):
    alerts = []
    for item in IT_EQUIPMENT_TYPES:
        stock = stocks.get(item, 0)
        req = requirements.get(item, 0)

        if req > 0 and stock < req:
            shortage = req - stock
            alerts.append((
                'danger',
                f'🚨 **{item} shortage:** Need **{shortage}** more units (Stock: {stock} / Required: {req})'
            ))
        elif 0 < stock < threshold:
            alerts.append((
                'warning',
                f'⚠️ **Low stock on {item}:** Only **{stock}** units left'
            ))
    return alerts


def render_bar_chart_it(stocks, requirements, shipped):
    items = IT_EQUIPMENT_TYPES
    short_labels = [
        item.replace('Wireless Scanner - ', 'WS-')
            .replace('Charger Wireless Scanner - ', 'Charger ')
            .replace('Yubikey - Security Key', 'Yubikey')
            .replace('Zebra ZD621', 'Zebra')
        for item in items
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Stock', x=short_labels,
        y=[stocks.get(t, 0) for t in items],
        marker_color='#3498db'
    ))
    fig.add_trace(go.Bar(
        name='Required', x=short_labels,
        y=[requirements.get(t, 0) for t in items],
        marker_color='#f39c12'
    ))
    fig.add_trace(go.Bar(
        name='Shipped', x=short_labels,
        y=[shipped.get(t, 0) for t in items],
        marker_color='#27ae60'
    ))

    fig.update_layout(
        barmode='group', height=420,
        title=dict(text='<b>📊 Equipment Stock Overview</b>', font=dict(size=16)),
        margin=dict(t=60, b=80, l=40, r=20),
        xaxis=dict(tickangle=-30),
        **get_plotly_theme()
    )
    st.plotly_chart(fig, use_container_width=True)


def render_status_pie(shipments_df):
    if shipments_df.empty or 'delivery_status' not in shipments_df.columns:
        st.info("📊 No shipments yet.")
        return

    counts = shipments_df['delivery_status'].value_counts()
    if counts.empty:
        st.info("📊 No shipments yet.")
        return

    color_map = {
        'Pending': '#f39c12', 'In Transit': '#3498db',
        'Delivered': '#27ae60', 'Delayed': '#e74c3c'
    }
    colors = [color_map.get(s, '#95a5a6') for s in counts.index]

    fig = go.Figure(data=[go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.55, marker=dict(colors=colors)
    )])
    fig.update_layout(
        height=420,
        title=dict(text='<b>🚚 Shipment Statuses</b>', font=dict(size=16)),
        margin=dict(t=60, b=40, l=20, r=20),
        **get_plotly_theme()
    )
    st.plotly_chart(fig, use_container_width=True)


def render_rdc_progress_table(rdcs_df):
    if rdcs_df.empty:
        return

    rows = []
    for _, rdc in rdcs_df.iterrows():
        requirements = get_rdc_requirements_dict(rdc['id'])
        shipped = get_shipped_totals_per_rdc(rdc['id'])

        total_req = sum(requirements.values())
        total_ship = sum(shipped.values())
        total_pending = max(0, total_req - total_ship)
        pct = (total_ship / total_req * 100) if total_req > 0 else 0

        launch = rdc.get('launch_date')
        launch_str = str(launch) if launch else '—'

        status_icon = '✅' if pct >= 100 else ('🟡' if pct > 0 else '🔴')

        rows.append({
            'Status': status_icon,
            'RDC': rdc['name'],
            'Location': rdc['location'] or '-',
            'Launch Date': launch_str,
            'Required': total_req,
            'Shipped': total_ship,
            'Pending': total_pending,
            'Progress': f"{pct:.0f}%"
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render():
    st.markdown("# 📊 4M IT Equipment Dashboard")
    st.caption("Overview of all IT equipment, RDCs, and shipments")

    threshold = get_threshold()
    stocks = get_it_stock_dict()
    requirements = get_total_requirements()
    rdcs_df = get_rdcs()
    shipments_df = get_it_shipments()

    all_items = get_all_shipment_items()
    shipped_totals = {t: 0 for t in IT_EQUIPMENT_TYPES}
    if not all_items.empty:
        for t in IT_EQUIPMENT_TYPES:
            shipped_totals[t] = int(all_items[all_items['equipment_type'] == t]['quantity'].sum())

    # Alerts
    launch_alerts = calculate_launch_alerts()
    transport_alerts = calculate_transport_alerts(shipments_df)
    stock_alerts = calculate_stock_alerts(stocks, requirements, threshold)
    all_alerts = launch_alerts + transport_alerts + stock_alerts

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

    pending_ships = 0
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        pending_ships = len(shipments_df[shipments_df['delivery_status'].isin(['Pending', 'In Transit'])])

    upcoming = get_upcoming_rdc_launches(days_ahead=4)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card("Total RDCs", len(rdcs_df), "card-stores", "bi-building")
    with c2:
        render_stat_card("Total Shipments", len(shipments_df), "card-shipments", "bi-truck")
    with c3:
        render_stat_card("In Progress", pending_ships, "card-40d", "bi-hourglass-split")
    with c4:
        render_stat_card("Upcoming Launches", len(upcoming), "card-30d", "bi-rocket-takeoff")

    # Totals
    total_stock = sum(stocks.values())
    total_required = sum(requirements.values())
    total_shipped = sum(shipped_totals.values())
    total_pending = max(0, total_required - total_shipped)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card("Total Stock", total_stock, "card-30d", "bi-box-seam-fill")
    with c2:
        render_stat_card("Total Required", total_required, "card-40d", "bi-clipboard-check")
    with c3:
        render_stat_card("Total Shipped", total_shipped, "card-shipments", "bi-check-circle-fill")
    with c4:
        render_stat_card("Total Pending", total_pending, "card-60d", "bi-hourglass-split")

    # Equipment Stock
    render_section_title("💻 IT Equipment Stock")
    cols = st.columns(3)
    for idx, item in enumerate(IT_EQUIPMENT_TYPES):
        with cols[idx % 3]:
            render_it_stock_card(
                item, stocks.get(item, 0), threshold,
                icon=IT_ICONS.get(item, 'bi-cpu')
            )

    # Analytics
    render_section_title("📊 Analytics")
    c1, c2 = st.columns([2, 1])
    with c1:
        render_bar_chart_it(stocks, requirements, shipped_totals)
    with c2:
        render_status_pie(shipments_df)

    # RDC Progress
    if not rdcs_df.empty:
        render_section_title("🏢 RDCs Progress")
        render_rdc_progress_table(rdcs_df)

    # Upcoming launches details
    if not upcoming.empty:
        render_section_title("🚀 Upcoming Launches")
        upcoming_display = upcoming[['name', 'location', 'launch_date', 'days_left']].copy()
        upcoming_display.columns = ['RDC', 'Location', 'Launch Date', 'Days Left']
        st.dataframe(upcoming_display, use_container_width=True, hide_index=True)
