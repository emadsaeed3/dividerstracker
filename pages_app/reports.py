"""
Reports page (Dividers)
"""
import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
from datetime import datetime
from database import (
    get_stores, get_shipments, get_stocks_dict, get_threshold,
    get_magnet_stock, get_magnet_status_dict, get_upcoming_launches,
    get_discrepancies
)
from components import render_stat_card, render_section_title
from email_drafts import generate_dividers_mailto


def build_report_data(stores_df, shipments_df):
    """Build the report data from stores and shipments"""
    report_rows = []

    for _, store in stores_df.iterrows():
        store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()
        s30 = store_ships['qty_30d'].sum() if not store_ships.empty else 0
        s40 = store_ships['qty_40d'].sum() if not store_ships.empty else 0
        s60 = store_ships['qty_60d'].sum() if not store_ships.empty else 0

        launch = store.get('launch_date')
        launch_str = str(launch) if launch else '-'
        transport = '✅' if store.get('transportation_ready') else '❌'
        launched = '✅' if store.get('is_launched') else '❌'

        rec30 = int(store.get('received_30d', 0) or 0)
        rec40 = int(store.get('received_40d', 0) or 0)
        rec60 = int(store.get('received_60d', 0) or 0)

        report_rows.append({
            'Store': store['name'],
            'Location': store['location'] or '-',
            'Launch Date': launch_str,
            'Launched': launched,
            'Transport Ready': transport,
            'Req 30D': store['required_30d'],
            'Ship 30D': int(s30),
            'Rec 30D': rec30,
            'Pending 30D': max(0, store['required_30d'] - int(s30)),
            'Req 40D': store['required_40d'],
            'Ship 40D': int(s40),
            'Rec 40D': rec40,
            'Pending 40D': max(0, store['required_40d'] - int(s40)),
            'Req 60D': store['required_60d'],
            'Ship 60D': int(s60),
            'Rec 60D': rec60,
            'Pending 60D': max(0, store['required_60d'] - int(s60)),
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


def style_pending(val):
    """Style pending cells based on value"""
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
        total_pending = report_df[['Pending 30D', 'Pending 40D', 'Pending 60D']].sum().sum()
        render_stat_card("Total Pending", int(total_pending), "card-40d", "bi-hourglass-split")

    # === EMAIL DRAFT SECTION ===
    render_section_title("📧 Email Daily Report")
    
    st.markdown("""
    <div style="background: rgba(52, 152, 219, 0.1); padding: 14px 18px; border-radius: 10px; 
                border-left: 4px solid #3498db; margin-bottom: 16px;">
        💡 Click the button below to open your default email app with a pre-filled daily report.
        <br>You can review and edit before sending.
    </div>
    """, unsafe_allow_html=True)

    # Gather data for email
    stocks = get_stocks_dict()
    threshold = get_threshold()
    magnet_stock = get_magnet_stock()
    magnet_status = get_magnet_status_dict()
    upcoming_launches = get_upcoming_launches(days_ahead=4)
    discrepancies_df = get_discrepancies(stores_df, shipments_df)

    mailto_link = generate_dividers_mailto(
        stocks, threshold, stores_df, shipments_df,
        magnet_stock, magnet_status, upcoming_launches, discrepancies_df
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # Styled link that looks like a button
        st.markdown(
            f'''
            <a href="{mailto_link}" style="
                display: block;
                text-align: center;
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                color: white !important;
                padding: 12px 24px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 700;
                box-shadow: 0 4px 14px rgba(52, 152, 219, 0.35);
                transition: all 0.3s ease;
                margin: 10px 0;
            " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(52, 152, 219, 0.5)';"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 14px rgba(52, 152, 219, 0.35)';">
                📧 Generate Dividers Report Email
            </a>
            ''',
            unsafe_allow_html=True
        )

    # Detailed report
    render_section_title("📊 Detailed Report")

    pending_cols = ['Pending 30D', 'Pending 40D', 'Pending 60D']
    available_pending = [c for c in pending_cols if c in report_df.columns]

    styled = report_df.style.map(style_pending, subset=available_pending)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Excel download
    render_section_title("📥 Export")
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
