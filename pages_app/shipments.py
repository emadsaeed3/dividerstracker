"""
Shipments management page
"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
from database import (
    get_stores, get_shipments, add_shipment,
    delete_shipment, update_shipment_status
)
from components import render_section_title


DELIVERY_STATUSES = ['Pending', 'In Transit', 'Delivered', 'Delayed']

STATUS_CONFIG = {
    'Pending':     {'emoji': '🟡', 'color': '#f39c12', 'bg': 'rgba(243, 156, 18, 0.08)'},
    'In Transit':  {'emoji': '🔵', 'color': '#3498db', 'bg': 'rgba(52, 152, 219, 0.08)'},
    'Delivered':   {'emoji': '🟢', 'color': '#27ae60', 'bg': 'rgba(39, 174, 96, 0.08)'},
    'Delayed':     {'emoji': '🔴', 'color': '#e74c3c', 'bg': 'rgba(231, 76, 60, 0.08)'},
}


def get_stores_with_pending_shipments(stores_df, shipments_df):
    """Return stores with launch dates that still have pending quantities"""
    if stores_df.empty:
        return pd.DataFrame()
    
    filtered = stores_df[stores_df['launch_date'].notna()].copy()
    if filtered.empty:
        return pd.DataFrame()
    
    filtered['launch_date'] = pd.to_datetime(filtered['launch_date']).dt.date
    today = date.today()
    filtered = filtered[filtered['launch_date'] >= today]
    
    if filtered.empty:
        return pd.DataFrame()
    
    # Calculate remaining qty per store
    rows = []
    for _, store in filtered.iterrows():
        store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()
        
        s30 = int(store_ships['qty_30d'].sum()) if not store_ships.empty else 0
        s40 = int(store_ships['qty_40d'].sum()) if not store_ships.empty else 0
        s60 = int(store_ships['qty_60d'].sum()) if not store_ships.empty else 0
        
        p30 = max(0, int(store['required_30d']) - s30)
        p40 = max(0, int(store['required_40d']) - s40)
        p60 = max(0, int(store['required_60d']) - s60)
        
        if (p30 + p40 + p60) > 0:  # Has pending
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
                'transportation_ready': bool(store.get('transportation_ready', False)),
            })
    
    return pd.DataFrame(rows).sort_values('days_left') if rows else pd.DataFrame()


def render_scheduled_card(row, idx):
    """Render a scheduled shipment card (suggested based on launch date)"""
    days_left = row['days_left']
    
    if days_left <= 1:
        urgency_color = '#e74c3c'
        urgency_icon = '🚨'
        urgency_label = 'URGENT'
    elif days_left <= 3:
        urgency_color = '#f39c12'
        urgency_icon = '⚠️'
        urgency_label = 'SOON'
    else:
        urgency_color = '#3498db'
        urgency_icon = '📅'
        urgency_label = 'UPCOMING'
    
    transport_badge = (
        '<span style="background:#27ae60; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600;">✅ Transport Ready</span>'
        if row['transportation_ready']
        else '<span style="background:#e74c3c; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600;">❌ Transport NOT Ready</span>'
    )
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, {urgency_color}15 100%);
                border-left: 5px solid {urgency_color};
                border-radius: 14px;
                padding: 20px 24px;
                margin-bottom: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
            <div>
                <div style="font-size:1.25rem; font-weight:700;">
                    🏪 {row['name']} <span style="opacity:0.6; font-weight:500; font-size:1rem;">• 📍 {row['location']}</span>
                </div>
                <div style="margin-top:6px; font-size:0.85rem; opacity:0.85;">
                    🚀 Launch: <b>{row['launch_date']}</b> &nbsp;|&nbsp; 📆 Ship by: <b>{row['ship_by']}</b>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="background:{urgency_color}; color:white; padding:6px 14px; border-radius:20px; font-weight:700; font-size:0.85rem;">
                    {urgency_icon} {urgency_label} • {row['days_left']} day(s) left
                </div>
                <div style="margin-top:8px;">{transport_badge}</div>
            </div>
        </div>
        <div style="display:flex; gap:14px; flex-wrap:wrap; margin-top:10px; padding-top:12px; border-top:1px dashed rgba(127,140,141,0.3);">
            <div style="background:rgba(52,152,219,0.15); padding:8px 14px; border-radius:10px;">
                <span style="font-size:0.75rem; opacity:0.7;">🔵 30D Pending</span>
                <div style="font-weight:700; font-size:1.1rem; color:#3498db;">{row['pending_30d']}</div>
            </div>
            <div style="background:rgba(230,126,34,0.15); padding:8px 14px; border-radius:10px;">
                <span style="font-size:0.75rem; opacity:0.7;">🟠 40D Pending</span>
                <div style="font-weight:700; font-size:1.1rem; color:#e67e22;">{row['pending_40d']}</div>
            </div>
            <div style="background:rgba(155,89,182,0.15); padding:8px 14px; border-radius:10px;">
                <span style="font-size:0.75rem; opacity:0.7;">🟣 60D Pending</span>
                <div style="font-weight:700; font-size:1.1rem; color:#9b59b6;">{row['pending_60d']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick shipment form
    with st.expander(f"🚀 Create Shipment for **{row['name']}**", expanded=False):
        with st.form(f"quick_ship_{row['id']}_{idx}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ship_date = c1.date_input("📅 Shipment Date", value=date.today(), key=f"sd_{row['id']}_{idx}")
            scheduled = c2.date_input("📆 Scheduled Delivery", value=row['ship_by'], key=f"scd_{row['id']}_{idx}")
            
            c1, c2, c3 = st.columns(3)
            q30 = c1.number_input("🔵 30D", min_value=0, value=int(row['pending_30d']), key=f"q30_{row['id']}_{idx}")
            q40 = c2.number_input("🟠 40D", min_value=0, value=int(row['pending_40d']), key=f"q40_{row['id']}_{idx}")
            q60 = c3.number_input("🟣 60D", min_value=0, value=int(row['pending_60d']), key=f"q60_{row['id']}_{idx}")
            
            status = st.selectbox("🚚 Status", DELIVERY_STATUSES, key=f"st_{row['id']}_{idx}")
            notes = st.text_area("📝 Notes", key=f"nt_{row['id']}_{idx}")
            
            if st.form_submit_button("🚀 Create Shipment", use_container_width=True):
                add_shipment(row['id'], ship_date, q30, q40, q60, notes, status, scheduled)
                st.success(f"✅ Shipment created for {row['name']}!")
                st.rerun()


def render_shipment_card(ship, idx):
    """Render a full-width shipment card"""
    status = ship.get('delivery_status') or 'Pending'
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG['Pending'])
    
    total = int(ship['qty_30d']) + int(ship['qty_40d']) + int(ship['qty_60d'])
    scheduled = ship.get('scheduled_date')
    scheduled_str = str(scheduled) if scheduled else '—'
    notes = ship.get('notes') or '—'
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, {cfg['bg']} 100%);
                border-left: 5px solid {cfg['color']};
                border-radius: 14px;
                padding: 20px 24px;
                margin-bottom: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
            <div>
                <div style="font-size:1.25rem; font-weight:700;">
                    🏪 {ship['store_name']}
                    <span style="opacity:0.5; font-weight:500; font-size:0.95rem;">#{ship['id']}</span>
                </div>
                <div style="margin-top:6px; font-size:0.85rem; opacity:0.85;">
                    📅 Shipped: <b>{ship['date']}</b> &nbsp;|&nbsp; 📆 Scheduled: <b>{scheduled_str}</b>
                </div>
            </div>
            <div style="background:{cfg['color']}; color:white; padding:8px 18px; border-radius:20px; font-weight:700; font-size:0.9rem;">
                {cfg['emoji']} {status}
            </div>
        </div>
        <div style="display:flex; gap:14px; flex-wrap:wrap; margin-bottom:10px;">
            <div style="background:rgba(52,152,219,0.15); padding:10px 16px; border-radius:10px; min-width:100px;">
                <span style="font-size:0.75rem; opacity:0.7;">🔵 30D</span>
                <div style="font-weight:700; font-size:1.2rem; color:#3498db;">{int(ship['qty_30d'])}</div>
            </div>
            <div style="background:rgba(230,126,34,0.15); padding:10px 16px; border-radius:10px; min-width:100px;">
                <span style="font-size:0.75rem; opacity:0.7;">🟠 40D</span>
                <div style="font-weight:700; font-size:1.2rem; color:#e67e22;">{int(ship['qty_40d'])}</div>
            </div>
            <div style="background:rgba(155,89,182,0.15); padding:10px 16px; border-radius:10px; min-width:100px;">
                <span style="font-size:0.75rem; opacity:0.7;">🟣 60D</span>
                <div style="font-weight:700; font-size:1.2rem; color:#9b59b6;">{int(ship['qty_60d'])}</div>
            </div>
            <div style="background:rgba(127,140,141,0.15); padding:10px 16px; border-radius:10px; min-width:100px;">
                <span style="font-size:0.75rem; opacity:0.7;">📦 Total</span>
                <div style="font-weight:700; font-size:1.2rem;">{total}</div>
            </div>
        </div>
        <div style="padding-top:10px; border-top:1px dashed rgba(127,140,141,0.3); font-size:0.85rem; opacity:0.9;">
            📝 <b>Notes:</b> {notes}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    c1, c2, c3 = st.columns([2, 1, 1])
    new_status = c1.selectbox(
        "Update Status",
        DELIVERY_STATUSES,
        index=DELIVERY_STATUSES.index(status) if status in DELIVERY_STATUSES else 0,
        key=f"status_sel_{ship['id']}_{idx}",
        label_visibility="collapsed"
    )
    if c2.button("💾 Update", key=f"upd_{ship['id']}_{idx}", use_container_width=True):
        update_shipment_status(ship['id'], new_status)
        st.success(f"✅ Updated to {new_status}")
        st.rerun()
    if c3.button("🗑️ Delete", key=f"del_{ship['id']}_{idx}", use_container_width=True):
        delete_shipment(ship['id'])
        st.warning(f"🗑️ Deleted #{ship['id']}")
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)


def render():
    """Render the Shipments page"""
    st.markdown("# 🚚 Shipments")

    stores_df = get_stores()
    shipments_df = get_shipments()

    if stores_df.empty:
        st.warning("⚠️ Add a store first.")
        return

    # ===== SCHEDULED SHIPMENTS SECTION =====
    scheduled_df = get_stores_with_pending_shipments(stores_df, shipments_df)
    
    if not scheduled_df.empty:
        render_section_title(f"📅 Scheduled Shipments — Based on Launch Dates ({len(scheduled_df)})")
        st.markdown("""
        <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                    border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
            💡 These are auto-suggested shipments for stores with upcoming launch dates and pending quantities.
            <b>Ship by = Launch Date - 1 day</b>
        </div>
        """, unsafe_allow_html=True)
        
        for idx, (_, row) in enumerate(scheduled_df.iterrows()):
            render_scheduled_card(row, idx)

    # ===== MANUAL ADD SHIPMENT =====
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

            c1, c2, c3 = st.columns(3)
            q30 = c1.number_input("🔵 Qty 30D", min_value=0, value=0)
            q40 = c2.number_input("🟠 Qty 40D", min_value=0, value=0)
            q60 = c3.number_input("🟣 Qty 60D", min_value=0, value=0)
            notes = st.text_area("📝 Notes")

            if st.form_submit_button("💾 Record Shipment", use_container_width=True):
                store_id = store_options[selected]
                add_shipment(
                    store_id, ship_date, q30, q40, q60,
                    notes, delivery_status, scheduled_date
                )
                st.success("✅ Shipment recorded!")
                st.rerun()

    # ===== ALL SHIPMENTS =====
    render_section_title("📋 All Shipments")

    if shipments_df.empty:
        st.info("📭 No shipments yet.")
        return

    # Filter & Stats
    c1, c2, c3, c4, c5 = st.columns(5)
    status_filter = c1.selectbox(
        "Filter by Status",
        ['All'] + DELIVERY_STATUSES,
        key='status_filter'
    )

    # Count by status
    pending = len(shipments_df[shipments_df['delivery_status'] == 'Pending']) if 'delivery_status' in shipments_df.columns else 0
    transit = len(shipments_df[shipments_df['delivery_status'] == 'In Transit']) if 'delivery_status' in shipments_df.columns else 0
    delivered = len(shipments_df[shipments_df['delivery_status'] == 'Delivered']) if 'delivery_status' in shipments_df.columns else 0
    delayed = len(shipments_df[shipments_df['delivery_status'] == 'Delayed']) if 'delivery_status' in shipments_df.columns else 0
    
    c2.metric("🟡 Pending", pending)
    c3.metric("🔵 In Transit", transit)
    c4.metric("🟢 Delivered", delivered)
    c5.metric("🔴 Delayed", delayed)

    st.markdown("<br>", unsafe_allow_html=True)

    filtered_df = shipments_df.copy()
    if status_filter != 'All':
        filtered_df = filtered_df[filtered_df['delivery_status'] == status_filter]

    if filtered_df.empty:
        st.info(f"📭 No shipments with status '{status_filter}'.")
        return

    for idx, (_, ship) in enumerate(filtered_df.iterrows()):
        render_shipment_card(ship, idx)
