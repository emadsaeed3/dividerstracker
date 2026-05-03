"""
Reports page
"""
import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
from datetime import datetime
from database import get_stores, get_shipments
from components import render_stat_card, render_section_title


def build_report_data(stores_df, shipments_df):
    """Build the report data from stores and shipments"""
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
    
    return pd.DataFrame(report_rows)


def export_to_excel(report_df):
    """Export report to Excel file"""
    output = BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stores Report"
    ws.append(list(report_df.columns))
    for _, row in report_df.iterrows():
        ws.append(list(row))
    wb.save(output)
    output.seek(0)
    return output


def style_gap(val):
    """Style gap cells based on value"""
    try:
        v = int(val)
        if v > 0:
            return 'color: #e74c3c; font-weight: 700;'
        elif v == 0:
            return 'color: #27ae60; font-weight: 600;'
    except (ValueError, TypeError):
        pass
    return ''


def render():
    """Render the Reports page"""
    st.markdown("# 📈 Reports")
    
    stores_df = get_stores()
    shipments_df = get_shipments()
    
    if stores_df.empty:
        st.info("📭 No data to display.")
        return
    
    # Build report
    report_df = build_report_data(stores_df, shipments_df)
    
    # Summary cards
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
    
    # Detailed report table
    render_section_title("📊 Detailed Report")
    styled = report_df.style.map(style_gap, subset=['Gap 30D', 'Gap 40D', 'Gap 60D'])
    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    # Excel download
    output = export_to_excel(report_df)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.download_button(
            label="📥 Download Excel Report",
            data=output,
            file_name=f"dividers_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
