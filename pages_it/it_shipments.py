"""
IT Equipment Shipments Management
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database_it import (
    IT_EQUIPMENT_TYPES,
    get_rdcs, get_it_shipments, get_it_shipment_items,
    add_it_shipment, delete_it_shipment, update_it_shipment_status,
    update_it_shipment_transport,
    get_rdc_requirements_dict, get_shipped_totals_per_rdc,
    get_it_stock_dict
)
from components import render_section_title


DELIVERY_STATUSES = ['Pending', 'In Transit', 'Delivered', 'Delayed']

STATUS_CONFIG = {
    'Pending':    {'emoji': '🟡', 'color': '#f39c12', 'bg': 'rgba(243, 156, 18, 0.08)'},
    'In Transit': {'emoji': '🔵', 'color': '#3498db', 'bg': 'rgba(52, 152, 219, 0.08)'},
    'Delivered':  {'emoji': '🟢', 'color': '#27ae60', 'bg': 'rgba(39, 174, 96, 0.08)'},
    'Delayed':    {'emoji': '🔴', 'color': '#e74c3c', 'bg': 'rgba(231, 76, 60, 0.08)'},
}


def get_rdcs_with_pending(rdcs_df):
    if rdcs_df.empty:
        return pd.DataFrame()

    filtered = rdcs_df[rdcs_df['launch_date'].notna()].copy()
    if filtered.empty:
        return pd.DataFrame()

    filtered['launch_date'] = pd.to_datetime(filtered['launch_date']).dt.date
    today = date.today()
    filtered = filtered[filtered['launch_date'] >= today]

    if filtered.empty:
        return pd.DataFrame()

    rows = []
    for _, rdc in filtered.iterrows():
        requirements = get_rdc_requirements_dict(rdc['id'])
        shipped = get_shipped_totals_per_rdc(rdc['id'])

        pending = {}
        total_pending = 0
        for item in IT_EQUIPMENT_TYPES:
            p = max(0, requirements.get(item, 0) - shipped.get(item, 0))
            pending[item] = p
            total_pending += p

        if total_pending > 0:
            days_left = (rdc['launch_date'] - today).days
            ship_by = rdc['launch_date'] - timedelta(days=1)
            rows.append({
                'id': rdc['id'],
                'name': rdc['name'],
                'location': rdc['location'] or 'N/A',
                'launch_date': rdc['launch_date'],
                'ship_by': ship_by,
                'days_left': days_left,
                'pending': pending,
                'total_pending': total_pending,
            })

    return pd.DataFrame(rows).sort_values('days_left') if rows else pd.DataFrame()


def render_scheduled_card(row, idx):
    days_left = row['days_left']

    if days_left <= 1:
        urgency_color = '#e74c3c'
        urgency_icon = '🚨'
    elif days_left <= 3:
        urgency_color = '#f39c12'
        urgency_icon = '⚠️'
    else:
        urgency_color = '#3498db'
        urgency_icon = '📅'

    pending_chips = ""
    for item, qty in row['pending'].items():
        if qty > 0:
            short = item.replace('Wireless Scanner - ', 'WS-').replace('Charger Wireless Scanner - ', 'Chrg-').replace('Yubikey - Security Key', 'Yubikey').replace('Zebra ZD621', 'Zebra')
            pending_chips += f"""
            <div style="background:rgba(52,152,219,0.15); padding:4px 8px; border-radius:6px; font-size:0.72rem;">
                <b>{short}:</b> <span style="color:#3498db; font-weight:700;">{qty}</span>
            </div>
            """

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, {urgency_color}15 100%);
                border-left: 5px solid {urgency_color};
                border-radius: 14px;
                padding: 16px 18px;
                margin-bottom: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; flex-wrap:wrap; gap:8px;">
            <div>
                <div style="font-size:1.05rem; font-weight:700;">🏢 {row['name']}</div>
                <div style="font-size:0.8rem; opacity:0.7; margin-top:2px;">📍 {row['location']}</div>
            </div>
            <div style="background:{urgency_color}; color:white; padding:4px 10px; border-radius:20px; font-weight:700; font-size:0.72rem;">
                {urgency_icon} {row['days_left']}d left
            </div>
        </div>
        <div style="font-size:0.78rem; opacity:0.85; margin-bottom:8px;">
            🚀 Launch: <b>{row['launch_date']}</b> | 📆 Ship by: <b>{row['ship_by']}</b> | 📦 <b>{row['total_pending']}</b> items
        </div>
        <div style="display:flex; gap:6px; flex-wrap:wrap; padding-top:10px; border-top:1px dashed rgba(127,140,141,0.3);">
            {pending_chips}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"🚀 Create Shipment for **{row['name']}**", expanded=False):
        with st.form(f"quick_ship_it_{row['id']}_{idx}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ship_date = c1.date_input("📅 Shipment Date", value=date.today(), key=f"sd_{row['id']}_{idx}")
            scheduled = c2.date_input("📆 Scheduled Delivery", value=row['ship_by'], key=f"scd_{row['id']}_{idx}")

            c1, c2 = st.columns(2)
            receiver_name = c1.text_input("👤 Receiver Name", key=f"rn_{row['id']}_{idx}")
            receiver_contact = c2.text_input("📞 Receiver Contact", key=f"rc_{row['id']}_{idx}")

            c1, c2 = st.columns(2)
            status = c1.selectbox("🚚 Status", DELIVERY_STATUSES, key=f"st_{row['id']}_{idx}")
            transport_ready = c2.checkbox("🚛 Transportation Ready", value=False, key=f"tr_{row['id']}_{idx}")

            st.markdown("**📦 Items to Ship:**")
            items_to_ship = {}
            for item in IT_EQUIPMENT_TYPES:
                pending_qty = int(row['pending'].get(item, 0))
                items_to_ship[item] = st.number_input(
                    f"{item} (Pending: {pending_qty})",
                    min_value=0, value=pending_qty,
                    key=f"item_{row['id']}_{idx}_{item}"
                )

            notes = st.text_area("📝 Notes", key=f"nt_{row['id']}_{idx}")

            if st.form_submit_button("🚀 Create Shipment", use_container_width=True):
                total_items = sum(items_to_ship.values())
                if total_items == 0:
                    st.error("❌ Add at least one item to ship!")
                else:
                    add_it_shipment(
                        row['id'], ship_date, items_to_ship,
                        notes, status, scheduled,
                        receiver_name, receiver_contact, transport_ready
                    )
                    st.success(f"✅ Shipment created for {row['name']}!")
                    st.rerun()


def render_shipment_card(ship, idx):
    status = ship.get('delivery_status') or 'Pending'
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG['Pending'])

    scheduled = ship.get('scheduled_date')
    scheduled_str = str(scheduled) if scheduled else '—'
    notes = ship.get('notes') or '—'
    receiver = ship.get('receiver_name') or '—'
    contact = ship.get('receiver_contact') or ''
    transport_ready = bool(ship.get('transportation_ready', False))

    items_df = get_it_shipment_items(ship['id'])
    total_items = int(items_df['quantity'].sum()) if not items_df.empty else 0

    items_chips = ""
    if not items_df.empty:
        for _, it in items_df.iterrows():
            short = it['equipment_type'].replace('Wireless Scanner - ', 'WS-').replace('Charger Wireless Scanner - ', 'Chrg-').replace('Yubikey - Security Key', 'Yubikey').replace('Zebra ZD621', 'Zebra')
            items_chips += f"""
            <div style="background:rgba(52,152,219,0.15); padding:5px 10px; border-radius:8px; font-size:0.72rem;">
                <b>{short}:</b> <span style="color:#3498db; font-weight:700;">{int(it['quantity'])}</span>
            </div>
            """
    else:
        items_chips = '<div style="opacity:0.6; font-size:0.75rem;">No items</div>'

    receiver_line = f"👤 <b>{receiver}</b>"
    if contact:
        receiver_line += f" | 📞 {contact}"

    if transport_ready:
        transport_badge = '<span style="background:#27ae60; color:white; padding:3px 9px; border-radius:10px; font-size:0.7rem; font-weight:600; margin-top:4px; display:inline-block;">🚛 Transport Ready</span>'
    else:
        transport_badge = '<span style="background:#e74c3c; color:white; padding:3px 9px; border-radius:10px; font-size:0.7rem; font-weight:600; margin-top:4px; display:inline-block;">🚛 Transport Not Ready</span>'

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, {cfg['bg']} 100%);
                border-left: 5px solid {cfg['color']};
                border-radius: 14px;
                padding: 16px 18px;
                margin-bottom: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div>
                <div style="font-size:1.05rem; font-weight:700;">
                    🏢 {ship['rdc_name']}
                    <span style="opacity:0.5; font-weight:500; font-size:0.78rem;">#{ship['id']}</span>
                </div>
                <div style="font-size:0.78rem; opacity:0.85; margin-top:3px;">
                    📅 {ship['date']} | 📆 {scheduled_str}
                </div>
                <div style="font-size:0.78rem; opacity:0.85; margin-top:2px;">
                    {receiver_line}
                </div>
                <div style="margin-top:4px;">{transport_badge}</div>
            </div>
            <div style="background:{cfg['color']}; color:white; padding:4px 10px; border-radius:20px; font-weight:700; font-size:0.72rem;">
                {cfg['emoji']} {status}
            </div>
        </div>
        <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px;">
            {items_chips}
            <div style="background:rgba(127,140,141,0.15); padding:5px 10px; border-radius:8px; font-size:0.72rem;">
                <b>Total:</b> <span style="font-weight:700;">{total_items}</span>
            </div>
        </div>
        <div style="padding-top:8px; border-top:1px dashed rgba(127,140,141,0.3); font-size:0.78rem; opacity:0.85;">
            📝 {notes}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    new_status = c1.selectbox(
        "Update Status",
        DELIVERY_STATUSES,
        index=DELIVERY_STATUSES.index(status) if status in DELIVERY_STATUSES else 0,
        key=f"it_status_{ship['id']}_{idx}",
        label_visibility="collapsed"
    )
    if c2.button("💾", key=f"it_upd_{ship['id']}_{idx}", use_container_width=True, help="Update Status"):
        update_it_shipment_status(ship['id'], new_status)
        st.success("✅ Updated")
        st.rerun()
    if c3.button("🗑️", key=f"it_del_{ship['id']}_{idx}", use_container_width=True, help="Delete"):
        delete_it_shipment(ship['id'])
        st.warning("🗑️ Deleted")
        st.rerun()

    transport_label = "🚛 Mark Transport NOT Ready" if transport_ready else "🚛 Mark Transport READY"
    if st.button(transport_label, key=f"it_transp_{ship['id']}_{idx}", use_container_width=True):
        update_it_shipment_transport(ship['id'], not transport_ready)
        st.success("✅ Transport status updated")
        st.rerun()


def render():
    st.markdown("# 🚚 IT Equipment Shipments")

    rdcs_df = get_rdcs()
    shipments_df = get_it_shipments()

    if rdcs_df.empty:
        st.warning("⚠️ Add an RDC first.")
        return

    scheduled_df = get_rdcs_with_pending(rdcs_df)

    if not scheduled_df.empty:
        render_section_title(f"📅 Scheduled Shipments — Based on Launch Dates ({len(scheduled_df)})")
        st.markdown("""
        <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                    border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
            💡 Auto-suggested shipments for RDCs with upcoming launch dates. <b>Ship by = Launch Date - 1 day</b>
        </div>
        """, unsafe_allow_html=True)

        scheduled_list = list(scheduled_df.iterrows())
        for i in range(0, len(scheduled_list), 2):
            c1, c2 = st.columns(2)
            with c1:
                render_scheduled_card(scheduled_list[i][1], i)
            if i + 1 < len(scheduled_list):
                with c2:
                    render_scheduled_card(scheduled_list[i + 1][1], i + 1)

    render_section_title("➕ Manual Shipment Entry")
    with st.expander("**Record a new shipment manually**", expanded=False):
        with st.form("add_it_shipment", clear_on_submit=True):
            rdc_options = {
                f"{row['name']} ({row['location'] or 'N/A'})": row['id']
                for _, row in rdcs_df.iterrows()
            }

            c1, c2 = st.columns(2)
            selected = c1.selectbox("🏢 RDC", list(rdc_options.keys()))
            ship_date = c2.date_input("📅 Shipment Date", value=date.today())

            c1, c2 = st.columns(2)
            scheduled_date = c1.date_input(
                "📆 Scheduled Delivery",
                value=date.today() + timedelta(days=1)
            )
            delivery_status = c2.selectbox("🚚 Status", DELIVERY_STATUSES)

            c1, c2 = st.columns(2)
            receiver_name = c1.text_input("👤 Receiver Name")
            receiver_contact = c2.text_input("📞 Receiver Contact")

            transport_ready = st.checkbox("🚛 Transportation Ready", value=False)

            st.markdown("**📦 Items to Ship:**")
            items_to_ship = {}
            stocks = get_it_stock_dict()
            cols = st.columns(2)
            for i, item in enumerate(IT_EQUIPMENT_TYPES):
                with cols[i % 2]:
                    stock_qty = stocks.get(item, 0)
                    items_to_ship[item] = st.number_input(
                        f"{item} (Stock: {stock_qty})",
                        min_value=0, value=0, key=f"manual_{item}"
                    )

            notes = st.text_area("📝 Notes")

            if st.form_submit_button("💾 Record Shipment", use_container_width=True):
                total = sum(items_to_ship.values())
                if total == 0:
                    st.error("❌ Add at least one item to ship!")
                else:
                    rdc_id = rdc_options[selected]
                    add_it_shipment(
                        rdc_id, ship_date, items_to_ship,
                        notes, delivery_status, scheduled_date,
                        receiver_name, receiver_contact, transport_ready
                    )
                    st.success("✅ Shipment recorded!")
                    st.rerun()

    if shipments_df.empty:
        render_section_title("📋 All Shipments")
        st.info("📭 No shipments yet.")
        return

    col_title, col_filter = st.columns([2, 1])
    with col_title:
        render_section_title(f"📋 All Shipments ({len(shipments_df)})")
    with col_filter:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        status_filter = st.selectbox(
            "Filter by Status",
            ['All'] + DELIVERY_STATUSES,
            key='it_status_filter',
            label_visibility="collapsed"
        )

    pending = len(shipments_df[shipments_df['delivery_status'] == 'Pending']) if 'delivery_status' in shipments_df.columns else 0
    transit = len(shipments_df[shipments_df['delivery_status'] == 'In Transit']) if 'delivery_status' in shipments_df.columns else 0
    delivered = len(shipments_df[shipments_df['delivery_status'] == 'Delivered']) if 'delivery_status' in shipments_df.columns else 0
    delayed = len(shipments_df[shipments_df['delivery_status'] == 'Delayed']) if 'delivery_status' in shipments_df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🟡 Pending", pending)
    c2.metric("🔵 In Transit", transit)
    c3.metric("🟢 Delivered", delivered)
    c4.metric("🔴 Delayed", delayed)

    st.markdown("<br>", unsafe_allow_html=True)

    filtered_df = shipments_df.copy()
    if status_filter != 'All':
        filtered_df = filtered_df[filtered_df['delivery_status'] == status_filter]

    if filtered_df.empty:
        st.info(f"📭 No shipments with status '{status_filter}'.")
        return

    ships_list = list(filtered_df.iterrows())
    for i in range(0, len(ships_list), 2):
        c1, c2 = st.columns(2)
        with c1:
            render_shipment_card(ships_list[i][1], i)
        if i + 1 < len(ships_list):
            with c2:
                render_shipment_card(ships_list[i + 1][1], i + 1)
