"""
Dashboard page
"""
import streamlit as st
from datetime import date
from database import (
    get_threshold, get_stocks_dict, get_stores, get_shipments,
    get_upcoming_launches, get_magnet_stock, get_magnet_status_dict
)
from components import (
    render_stat_card, render_stock_card, render_progress_card,
    render_magnet_status_card, render_threshold_chip, render_section_title,
    render_bar_chart, render_pie_chart
)


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

    # Magnet Status (visible on Dashboard)
    render_section_title("🧲 Dividers Magnet Status")
    magnet_status = get_magnet_status_dict()
    strips = get_magnet_stock()

    c1, c2, c3 = st.columns(3)
    for idx, dtype in enumerate(['30D', '40D', '60D']):
        status = magnet_status.get(dtype, {'with_magnet': 0, 'without_magnet': 0})
        with [c1, c2, c3][idx]:
            render_magnet_status_card(dtype, status['with_magnet'], status['without_magnet'])

    # Magnet Overview
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
