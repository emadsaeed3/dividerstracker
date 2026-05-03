"""
Dashboard page
"""
import streamlit as st
from database import get_threshold, get_stocks_dict, get_stores, get_shipments
from components import (
    render_stat_card, render_stock_card, render_progress_card,
    render_threshold_chip, render_section_title,
    render_bar_chart, render_pie_chart
)


def calculate_alerts(stocks, stores_df, shipments_df, threshold):
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


def render():
    """Render the Dashboard page"""
    # Title and threshold chip
    col_title, col_chip = st.columns([3, 1])
    with col_title:
        st.markdown("# 📊 Dashboard")
    with col_chip:
        threshold = get_threshold()
        render_threshold_chip(threshold)
    
    # Load data
    stocks = get_stocks_dict()
    stores_df = get_stores()
    shipments_df = get_shipments()
    
    # Alerts
    alerts = calculate_alerts(stocks, stores_df, shipments_df, threshold)
    if alerts:
        for level, msg in alerts:
            if level == 'danger':
                st.error(msg)
            else:
                st.warning(msg)
    
    # Overview section
    render_section_title("📌 Overview")
    c1, c2 = st.columns(2)
    with c1:
        render_stat_card("Total Stores", len(stores_df), "card-stores", "bi-shop")
    with c2:
        render_stat_card("Total Shipments", len(shipments_df), "card-shipments", "bi-truck")
    
    # Vendor Stock section
    render_section_title("📦 Vendor Stock")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)
    
    # Required vs Shipped section
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
    
    # Analytics section
    render_section_title("📊 Analytics")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        required_list = [req_shipped[t][0] for t in ['30D', '40D', '60D']]
        shipped_list = [req_shipped[t][1] for t in ['30D', '40D', '60D']]
        render_bar_chart(stocks, required_list, shipped_list)
    
    with c2:
        render_pie_chart(stocks)
