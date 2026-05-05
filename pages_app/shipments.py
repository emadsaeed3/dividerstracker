"""
Shipments management page
"""
import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
from database import (
    get_stores, get_shipments, add_shipment,
    delete_shipment, update_shipment_status, update_shipment_transport
)
from components import render_section_title


DELIVERY_STATUSES = ['Pending', 'In Transit', 'Delivered', 'Delayed']

STATUS_CONFIG = {
    'Pending':     {'emoji': '🟡', 'color': '#f39c12', 'bg': 'rgba(243, 156, 18, 0.08)'},
    'In Transit':  {'emoji': '🔵', 'color': '#3498db', 'bg': 'rgba(52, 152, 219, 0.08)'},
    'Delivered':   {'emoji': '🟢', 'color': '#27ae60', 'bg': 'rgba(39, 174, 96, 0.08)'},
    'Delayed':     {'emoji': '🔴', 'color': '#e74c3c', 'bg': 'rgba(231, 76, 60, 0.08)'},
}


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


def get_stores_with_pending_shipments(stores_df, shipments_df):
    if stores_df.empty:
        return pd.DataFrame()

    # Exclude launched stores
    if 'is_launched' in stores_df.columns:
        filtered = stores_df[stores_df['is_launched'] != True].copy()
    else:
        filtered = stores_df.copy()

    filtered = filtered[filtered['launch_date'].notna()]
    if filtered.empty:
        return pd.DataFrame()

    filtered['launch_date'] = pd.to_datetime(filtered['launch_date']).dt.date
    today = date.today()
    filtered = filtered[filtered['launch_date'] >= today]

    if filtered.empty:
        return pd.DataFrame()

    rows = []
    for _, store in filtered.iterrows():
        store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()

        s30 = int(store_ships['qty_30d'].sum()) if not store_ships.empty else 0
        s40 = int(store_ships['qty_40d'].sum()) if not store_ships.empty else 0
        s60 = int(store_ships['qty_60d'].sum()) if not store_ships.empty else 0

        p30 = max(0, int(store['required_30d']) - s30)
        p40 = max(0, int(store['required_40d']) - s40)
        p60 = max(0, int(store['required_60d']) - s60)

        if (p30 + p40 + p60) > 0:
            days_left = (store['launch_date'] - today).days
            ship_by = store['launch_date'] - timedelta(days=1)
            rows.append({
                'id': store['id'],
                'name': store['name'],
                'location': store['location'] or 'N/A',
                'launch_date': store['launch_date'],
                'ship_by': ship_by,
                'days_left': days_left,
                'pending_30d': p30,
                'pending_40d': p40,
                'pending_60d': p60,
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

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, {urgency_color}15 100%);
                border-left: 5px solid {urgency_color};
                border-radius: 14px;
                padding: 18px 20px;
                margin-bottom: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div>
                <div style="font-size:1.1rem; font-weight:700;">🏪 {row['name']}</div>
                <div style="font-size:0.85rem; opacity:0.7; margin-top:2px;">📍 {row['location']}</div>
            </div>
            <div style="background:{urgency_color}; color:white; padding:5px 12px; border-radius:20px; font-weight:700; font-size:0.75rem;">
                {urgency_icon} {row['days_left']}d left
            </div>
        </div>
        <div style="font-size:0.8rem; opacity:0.85; margin-bottom:8px;">
            🚀 Launch: <b>{row['launch_date']}</b> | 📆 Ship by: <b>{row['ship_by']}</b>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; padding-top:10px; border-top:1px dashed rgba(127,140,141,0.3);">
            <div style="background:rgba(52,152,219,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:80px;">
                <span style="font-size:0.7rem; opacity:0.7;">🔵 30D</span>
                <div style="font-weight:700; color:#3498db;">{row['pending_30d']}</div>
            </div>
            <div style="background:rgba(230,126,34,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:80px;">
                <span style="font-size:0.7rem; opacity:0.7;">🟠 40D</span>
                <div style="font-weight:700; color:#e67e22;">{row['pending_40d']}</div>
            </div>
            <div style="background:rgba(155,89,182,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:80px;">
                <span style="font-size:0.7rem; opacity:0.7;">🟣 60D</span>
                <div style="font-weight:700; color:#9b59b6;">{row['pending_60d']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"🚀 Create Shipment for **{row['name']}**", expanded=False):
        with st.form(f"quick_ship_{row['id']}_{idx}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ship_date = c1.date_input("📅 Shipment Date", value=date.today(), key=f"sd_{row['id']}_{idx}")
            scheduled = c2.date_input("📆 Scheduled Delivery", value=row['ship_by'], key=f"scd_{row['id']}_{idx}")

            c1, c2 = st.columns(2)
            status = c1.selectbox("🚚 Status", DELIVERY_STATUSES, key=f"st_{row['id']}_{idx}")
            transport_ready = c2.checkbox("🚛 Transportation Ready", value=False, key=f"tr_{row['id']}_{idx}")

            c1, c2, c3 = st.columns(3)
            q30 = c1.number_input("🔵 30D", min_value=0, value=int(row['pending_30d']), key=f"q30_{row['id']}_{idx}")
            q40 = c2.number_input("🟠 40D", min_value=0, value=int(row['pending_40d']), key=f"q40_{row['id']}_{idx}")
            q60 = c3.number_input("🟣 60D", min_value=0, value=int(row['pending_60d']), key=f"q60_{row['id']}_{idx}")

            notes = st.text_area("📝 Notes", key=f"nt_{row['id']}_{idx}")

            if st.form_submit_button("🚀 Create Shipment", use_container_width=True):
                add_shipment(row['id'], ship_date, q30, q40, q60, notes, status, scheduled, transport_ready)
                st.success(f"✅ Shipment created for {row['name']}!")
                st.rerun()


def render_shipment_card(ship, idx):
    status = ship.get('delivery_status') or 'Pending'
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG['Pending'])

    total = int(ship['qty_30d']) + int(ship['qty_40d']) + int(ship['qty_60d'])
    scheduled = ship.get('scheduled_date')
    scheduled_str = str(scheduled) if scheduled else '—'
    notes = ship.get('notes') or '—'
    transport_ready = bool(ship.get('transportation_ready', False))

    if transport_ready:
        transport_badge = '<span style="background:#27ae60; color:white; padding:3px 9px; border-radius:10px; font-size:0.7rem; font-weight:600; margin-top:4px; display:inline-block;">🚛 Transport Ready</span>'
    else:
        transport_badge = '<span style="background:#e74c3c; color:white; padding:3px 9px; border-radius:10px; font-size:0.7rem; font-weight:600; margin-top:4px; display:inline-block;">🚛 Transport Not Ready</span>'

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, {cfg['bg']} 100%);
                border-left: 5px solid {cfg['color']};
                border-radius: 14px;
                padding: 18px 20px;
                margin-bottom: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div>
                <div style="font-size:1.1rem; font-weight:700;">
                    🏪 {ship['store_name']}
                    <span style="opacity:0.5; font-weight:500; font-size:0.8rem;">#{ship['id']}</span>
                </div>
                <div style="font-size:0.8rem; opacity:0.85; margin-top:4px;">
                    📅 {ship['date']} | 📆 {scheduled_str}
                </div>
                <div style="margin-top:4px;">{transport_badge}</div>
            </div>
            <div style="background:{cfg['color']}; color:white; padding:5px 12px; border-radius:20px; font-weight:700; font-size:0.75rem;">
                {cfg['emoji']} {status}
            </div>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
            <div style="background:rgba(52,152,219,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:70px;">
                <span style="font-size:0.7rem; opacity:0.7;">🔵 30D</span>
                <div style="font-weight:700; color:#3498db;">{int(ship['qty_30d'])}</div>
            </div>
            <div style="background:rgba(230,126,34,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:70px;">
                <span style="font-size:0.7rem; opacity:0.7;">🟠 40D</span>
                <div style="font-weight:700; color:#e67e22;">{int(ship['qty_40d'])}</div>
            </div>
            <div style="background:rgba(155,89,182,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:70px;">
                <span style="font-size:0.7rem; opacity:0.7;">🟣 60D</span>
                <div style="font-weight:700; color:#9b59b6;">{int(ship['qty_60d'])}</div>
            </div>
            <div style="background:rgba(127,140,141,0.15); padding:6px 10px; border-radius:8px; flex:1; min-width:70px;">
                <span style="font-size:0.7rem; opacity:0.7;">📦 Total</span>
                <div style="font-weight:700;">{total}</div>
            </div>
        </div>
        <div style="padding-top:8px; border-top:1px dashed rgba(127,140,141,0.3); font-size:0.8rem; opacity:0.85;">
            📝 {notes}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Actions row 1: Status + Update + Delete
    c1, c2, c3 = st.columns([2, 1, 1])
    new_status = c1.selectbox(
        "Update Status",
        DELIVERY_STATUSES,
        index=DELIVERY_STATUSES.index(status) if status in DELIVERY_STATUSES else 0,
        key=f"status_sel_{ship['id']}_{idx}",
        label_visibility="collapsed"
    )
    if c2.button("💾", key=f"upd_{ship['id']}_{idx}", use_container_width=True, help="Update Status"):
        update_shipment_status(ship['id'], new_status)
        st.success("✅ Updated")
        st.rerun()
    if c3.button("🗑️", key=f"del_{ship['id']}_{idx}", use_container_width=True, help="Delete"):
        delete_shipment(ship['id'])
        st.warning("🗑️ Deleted")
        st.rerun()

    # Actions row 2: Transport toggle
    transport_label = "🚛 Mark Transport NOT Ready" if transport_ready else "🚛 Mark Transport READY"
    if st.button(transport_label, key=f"transp_{ship['id']}_{idx}", use_container_width=True):
        update_shipment_transport(ship['id'], not transport_ready)
        st.success("✅ Transport status updated")
        st.rerun()


def render():
    st.markdown("# 🚚 Shipments")

    stores_df = get_stores()
    shipments_df = get_shipments()

    if stores_df.empty:
        st.warning("⚠️ Add a store first.")
        return

    # SCHEDULED SHIPMENTS
    scheduled_df = get_stores_with_pending_shipments(stores_df, shipments_df)

    if not scheduled_df.empty:
        render_section_title(f"📅 Scheduled Shipments — Based on Launch Dates ({len(scheduled_df)})")
        st.markdown("""
        <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                    border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
            💡 Auto-suggested shipments for stores with upcoming launches. <b>Ship by = Launch Date - 1 day</b>
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

    # MANUAL ADD
    render_section_title("➕ Manual Shipment Entry")
    with st.expander("**Record a new shipment manually**", expanded=False):
        with st.form("add_shipment_manual", clear_on_submit=True):
            store_options = {
                f"{row['name']} ({row['location'] or 'N/A'})": row['id']
                for _, row in stores_df.iterrows()
            }

            c1, c2 = st.columns(2)
            selected = c1.selectbox("🏪 Store", list(store_options.keys()))
            ship_date = c2.date_input("📅 Shipment Date", value=date.today())

            c1, c2 = st.columns(2)
            scheduled_date = c1.date_input(
                "📆 Scheduled Delivery",
                value=date.today() + timedelta(days=1)
            )
            delivery_status = c2.selectbox("🚚 Delivery Status", DELIVERY_STATUSES)

            transport_ready = st.checkbox("🚛 Transportation Ready", value=False)

            c1, c2, c3 = st.columns(3)
            q30 = c1.number_input("🔵 Qty 30D", min_value=0, value=0)
            q40 = c2.number_input("🟠 Qty 40D", min_value=0, value=0)
            q60 = c3.number_input("🟣 Qty 60D", min_value=0, value=0)
            notes = st.text_area("📝 Notes")

            if st.form_submit_button("💾 Record Shipment", use_container_width=True):
                store_id = store_options[selected]
                add_shipment(
                    store_id, ship_date, q30, q40, q60,
                    notes, delivery_status, scheduled_date, transport_ready
                )
                st.success("✅ Shipment recorded!")
                st.rerun()

    # ALL SHIPMENTS with Filter
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
            key='status_filter',
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
