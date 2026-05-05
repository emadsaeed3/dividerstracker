"""
Stores management page (no transportation field - moved to shipments)
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import (
    get_stores, add_store, update_store, delete_store,
    get_shipments, get_discrepancies
)
from components import render_section_title


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


def get_launch_status(launch_date, is_launched=False):
    if is_launched:
        return "✅", "Launched"

    launch_date = _to_date(launch_date)
    if not launch_date:
        return "", ""

    today = date.today()
    days_left = (launch_date - today).days

    if days_left < 0:
        return "⏰", "Launch date passed (" + str(abs(days_left)) + "d ago)"
    elif days_left == 0:
        return "🚀", "Launching TODAY!"
    elif days_left <= 2:
        return "🚨", str(days_left) + "d left - URGENT!"
    elif days_left <= 4:
        return "⚠️", str(days_left) + "d left"
    else:
        return "📅", str(days_left) + "d left"


def render_store_card(store, shipments_df):
    launch_date_val = store.get('launch_date')
    is_launched = bool(store.get('is_launched', False))
    emoji, status_msg = get_launch_status(launch_date_val, is_launched)

    store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()
    s30 = int(store_ships['qty_30d'].sum()) if not store_ships.empty else 0
    s40 = int(store_ships['qty_40d'].sum()) if not store_ships.empty else 0
    s60 = int(store_ships['qty_60d'].sum()) if not store_ships.empty else 0

    r30_req = int(store['required_30d'])
    r40_req = int(store['required_40d'])
    r60_req = int(store['required_60d'])

    rec_30 = int(store.get('received_30d', 0) or 0)
    rec_40 = int(store.get('received_40d', 0) or 0)
    rec_60 = int(store.get('received_60d', 0) or 0)

    launch_date_obj = _to_date(launch_date_val)
    if is_launched:
        status_color = '#27ae60'
        status_bg = 'rgba(39, 174, 96, 0.1)'
    elif launch_date_obj:
        days_left = (launch_date_obj - date.today()).days
        if days_left < 0:
            status_color = '#95a5a6'
            status_bg = 'rgba(149, 165, 166, 0.1)'
        elif days_left <= 2:
            status_color = '#e74c3c'
            status_bg = 'rgba(231, 76, 60, 0.1)'
        elif days_left <= 4:
            status_color = '#f39c12'
            status_bg = 'rgba(243, 156, 18, 0.1)'
        else:
            status_color = '#3498db'
            status_bg = 'rgba(52, 152, 219, 0.1)'
    else:
        status_color = '#7f8c8d'
        status_bg = 'rgba(127, 140, 141, 0.1)'

    status_text = status_msg if status_msg else "No Launch Date"
    status_badge = '<span style="background:' + status_color + '; color:white; padding:3px 9px; border-radius:10px; font-size:0.7rem; font-weight:600;">' + emoji + ' ' + status_text + '</span>'

    def qty_row(label, required, shipped, received, color):
        pending = max(0, required - shipped)
        if pending > 0:
            pending_txt = '<span style="color:#e74c3c;">(' + str(pending) + ' pending)</span>'
        else:
            pending_txt = '<span style="color:#27ae60;">✓</span>'

        if received > 0:
            received_txt = '<b style="color:#16a085;">' + str(received) + '</b>'
        else:
            received_txt = '<span style="opacity:0.5;">—</span>'

        row = (
            '<div style="display:flex; justify-content:space-between; align-items:center; '
            'padding:6px 10px; background:' + color + '15; border-radius:8px; '
            'margin-bottom:4px; font-size:0.82rem;">'
            '<span style="font-weight:700; color:' + color + '; min-width:40px;">' + label + '</span>'
            '<span style="opacity:0.85;">Req: <b>' + str(required) + '</b></span>'
            '<span style="opacity:0.85;">Ship: <b>' + str(shipped) + '</b></span>'
            '<span style="opacity:0.85;">Rec: ' + received_txt + '</span>'
            '<span style="font-size:0.75rem;">' + pending_txt + '</span>'
            '</div>'
        )
        return row

    qty_html = qty_row('🔵 30D', r30_req, s30, rec_30, '#3498db')
    qty_html += qty_row('🟠 40D', r40_req, s40, rec_40, '#e67e22')
    qty_html += qty_row('🟣 60D', r60_req, s60, rec_60, '#9b59b6')

    card_html = (
        '<div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, ' + status_bg + ' 100%);'
        'border-left: 5px solid ' + status_color + ';'
        'border-radius: 14px;'
        'padding: 18px 20px;'
        'margin-bottom: 14px;'
        'box-shadow: 0 4px 16px rgba(0,0,0,0.08);">'
        '<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap; gap:8px;">'
        '<div>'
        '<div style="font-size:1.15rem; font-weight:700;">🏪 ' + str(store['name']) + '</div>'
        '<div style="font-size:0.82rem; opacity:0.75; margin-top:2px;">📍 ' + str(store['location'] or 'N/A') + '</div>'
        '</div>'
        '<div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end;">'
        + status_badge +
        '</div>'
        '</div>'
        '<div style="margin-top:10px;">'
        + qty_html +
        '</div>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander("✏️ Edit **" + str(store['name']) + "**", expanded=False):
        with st.form("edit_" + str(store['id'])):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name", value=store['name'], key="n_" + str(store['id']))
            location = c2.text_input("Location", value=store['location'] or '', key="l_" + str(store['id']))

            c1, c2 = st.columns(2)
            current_launch = _to_date(launch_date_val)
            launch_date_edit = c1.date_input(
                "🚀 Launch Date",
                value=current_launch,
                key="ld_" + str(store['id'])
            )
            is_launched_edit = c2.checkbox(
                "✅ Already Launched",
                value=is_launched,
                key="il_" + str(store['id']),
                help="Tick if this store has already launched"
            )

            st.markdown("**📋 Required Quantities:**")
            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("🔵 Required 30D", min_value=0, value=r30_req, key="r30_" + str(store['id']))
            r40 = c2.number_input("🟠 Required 40D", min_value=0, value=r40_req, key="r40_" + str(store['id']))
            r60 = c3.number_input("🟣 Required 60D", min_value=0, value=r60_req, key="r60_" + str(store['id']))

            st.markdown("**📥 Actually Received at Store:**")
            st.caption("💡 Update these when the store confirms receipt of dividers")
            c1, c2, c3 = st.columns(3)
            rec30 = c1.number_input("🔵 Received 30D", min_value=0, value=rec_30, key="rec30_" + str(store['id']))
            rec40 = c2.number_input("🟠 Received 40D", min_value=0, value=rec_40, key="rec40_" + str(store['id']))
            rec60 = c3.number_input("🟣 Received 60D", min_value=0, value=rec_60, key="rec60_" + str(store['id']))

            c1, c2 = st.columns(2)
            update_btn = c1.form_submit_button("💾 Update", use_container_width=True)
            delete_btn = c2.form_submit_button("🗑️ Delete", use_container_width=True)

            if update_btn:
                update_store(
                    store['id'], name, location, r30, r40, r60,
                    launch_date_edit, is_launched_edit,
                    rec30, rec40, rec60
                )
                st.success("✅ Updated!")
                st.rerun()

            if delete_btn:
                delete_store(store['id'])
                st.warning("🗑️ Deleted!")
                st.rerun()


def render_discrepancy_card(row, kind):
    color = '#e67e22' if kind == 'excess' else '#e74c3c'
    icon = '📈' if kind == 'excess' else '📉'

    def diff_html(label, shipped, received, diff, dcolor):
        if diff == 0:
            return (
                '<div style="background:rgba(127,140,141,0.1); padding:8px 12px; border-radius:8px; flex:1; min-width:130px;">'
                '<div style="font-size:0.7rem; opacity:0.6;">' + label + '</div>'
                '<div style="font-size:0.75rem; opacity:0.7;">Ship: ' + str(shipped) + ' | Rec: ' + str(received) + '</div>'
                '<div style="font-weight:700; opacity:0.6;">—</div>'
                '</div>'
            )
        sign = '+' if diff > 0 else ''
        return (
            '<div style="background:' + dcolor + '20; padding:8px 12px; border-radius:8px; flex:1; min-width:130px; border:1.5px solid ' + dcolor + '60;">'
            '<div style="font-size:0.7rem; opacity:0.8; color:' + dcolor + ';"><b>' + label + '</b></div>'
            '<div style="font-size:0.72rem; opacity:0.8;">Ship: ' + str(shipped) + ' | Rec: ' + str(received) + '</div>'
            '<div style="font-weight:800; color:' + dcolor + '; font-size:1rem;">' + sign + str(diff) + '</div>'
            '</div>'
        )

    html_30 = diff_html('🔵 30D', row['shipped_30d'], row['received_30d'], row['diff_30d'], '#3498db')
    html_40 = diff_html('🟠 40D', row['shipped_40d'], row['received_40d'], row['diff_40d'], '#e67e22')
    html_60 = diff_html('🟣 60D', row['shipped_60d'], row['received_60d'], row['diff_60d'], '#9b59b6')

    card = (
        '<div style="background: rgba(255,255,255,0.02);'
        'border-left: 5px solid ' + color + ';'
        'border-radius: 12px;'
        'padding: 14px 18px;'
        'margin-bottom: 10px;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap;">'
        '<div>'
        '<span style="font-weight:700; font-size:1.05rem;">' + icon + ' 🏪 ' + str(row['name']) + '</span>'
        '<span style="opacity:0.7; font-size:0.85rem;"> — 📍 ' + str(row['location']) + '</span>'
        '</div>'
        '</div>'
        '<div style="display:flex; gap:8px; flex-wrap:wrap;">'
        + html_30 + html_40 + html_60 +
        '</div>'
        '</div>'
    )

    st.markdown(card, unsafe_allow_html=True)


def render_discrepancy_section(stores_df, shipments_df):
    disc_df = get_discrepancies(stores_df, shipments_df)

    if disc_df.empty:
        render_section_title("⚖️ Shipped vs Received")
        st.markdown(
            '<div style="background: rgba(39, 174, 96, 0.1); padding: 16px 20px; border-radius: 10px; '
            'border-left: 4px solid #27ae60; margin-bottom: 16px;">'
            '✅ <b>No discrepancies detected!</b> All received quantities match shipments '
            '(or no received data entered yet).'
            '</div>',
            unsafe_allow_html=True
        )
        return

    excess_stores = []
    shortage_stores = []

    for _, row in disc_df.iterrows():
        has_excess = row['diff_30d'] > 0 or row['diff_40d'] > 0 or row['diff_60d'] > 0
        has_shortage = row['diff_30d'] < 0 or row['diff_40d'] < 0 or row['diff_60d'] < 0

        if has_excess:
            excess_stores.append(row)
        if has_shortage:
            shortage_stores.append(row)

    render_section_title("⚖️ Shipped vs Received (" + str(len(disc_df)) + " discrepancies)")
    st.markdown(
        '<div style="background: rgba(243, 156, 18, 0.1); padding: 12px 18px; border-radius: 10px; '
        'border-left: 4px solid #f39c12; margin-bottom: 16px; font-size:0.9rem;">'
        '💡 These stores have differences between what was shipped and what was actually received.'
        '</div>',
        unsafe_allow_html=True
    )

    if excess_stores:
        st.markdown("### 📈 Excess — Received MORE than Shipped (" + str(len(excess_stores)) + ")")
        for row in excess_stores:
            render_discrepancy_card(row, 'excess')

    if shortage_stores:
        st.markdown("### 📉 Shortage — Received LESS than Shipped (" + str(len(shortage_stores)) + ")")
        for row in shortage_stores:
            render_discrepancy_card(row, 'shortage')


def render():
    st.markdown("# 🏪 Stores Management")

    with st.expander("➕ **Add New Store**", expanded=False):
        with st.form("add_store", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Store Name *")
            location = c2.text_input("Location")

            c1, c2 = st.columns(2)
            launch_date_input = c1.date_input("🚀 Launch Date (optional)", value=None)
            is_launched_new = c2.checkbox(
                "✅ Already Launched", value=False,
                help="Tick if this is an old store that has already launched"
            )

            st.markdown("**📋 Required Quantities:**")
            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("🔵 Required 30D", min_value=0, value=0)
            r40 = c2.number_input("🟠 Required 40D", min_value=0, value=0)
            r60 = c3.number_input("🟣 Required 60D", min_value=0, value=0)

            st.markdown("**📥 Actually Received (if already launched):**")
            c1, c2, c3 = st.columns(3)
            rec30_new = c1.number_input("🔵 Received 30D", min_value=0, value=0)
            rec40_new = c2.number_input("🟠 Received 40D", min_value=0, value=0)
            rec60_new = c3.number_input("🟣 Received 60D", min_value=0, value=0)

            submitted = st.form_submit_button("➕ Add Store", use_container_width=True)
            if submitted and name:
                add_store(
                    name, location, r30, r40, r60,
                    launch_date_input, is_launched_new,
                    rec30_new, rec40_new, rec60_new
                )
                st.success("✅ Store '" + name + "' added!")
                st.rerun()

    stores_df = get_stores()
    shipments_df = get_shipments()

    if stores_df.empty:
        st.info("📭 No stores added yet.")
        return

    render_discrepancy_section(stores_df, shipments_df)

    render_section_title("📊 Stores Overview")
    total_stores = len(stores_df)
    launched = len(stores_df[stores_df['is_launched'] == True]) if 'is_launched' in stores_df.columns else 0
    upcoming = total_stores - launched

    c1, c2, c3 = st.columns(3)
    c1.metric("🏪 Total Stores", total_stores)
    c2.metric("✅ Launched", launched)
    c3.metric("🚀 Upcoming", upcoming)

    render_section_title("📋 All Stores")

    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        status_filter = st.selectbox(
            "Filter",
            ['All', 'Launched only', 'Upcoming only'],
            key='store_filter',
            label_visibility="collapsed"
        )

    filtered_df = stores_df.copy()
    if status_filter == 'Launched only':
        filtered_df = filtered_df[filtered_df['is_launched'] == True]
    elif status_filter == 'Upcoming only':
        filtered_df = filtered_df[filtered_df['is_launched'] != True]

    if filtered_df.empty:
        st.info("📭 No stores match the filter.")
        return

    stores_list = list(filtered_df.iterrows())

    for i in range(0, len(stores_list), 2):
        c1, c2 = st.columns(2)
        with c1:
            render_store_card(stores_list[i][1], shipments_df)
        if i + 1 < len(stores_list):
            with c2:
                render_store_card(stores_list[i + 1][1], shipments_df)
