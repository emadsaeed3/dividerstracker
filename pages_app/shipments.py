"""
Shipments management page
"""
import streamlit as st
from datetime import date, timedelta
from database import (
    get_stores, get_shipments, add_shipment,
    delete_shipment, update_shipment_status
)
from components import render_section_title


DELIVERY_STATUSES = ['Pending', 'In Transit', 'Delivered', 'Delayed']

STATUS_COLORS = {
    'Pending': '🟡',
    'In Transit': '🔵',
    'Delivered': '🟢',
    'Delayed': '🔴'
}


def render():
    """Render the Shipments page"""
    st.markdown("# 🚚 Shipments")

    stores_df = get_stores()

    if stores_df.empty:
        st.warning("⚠️ Add a store first.")
    else:
        # Add new shipment
        with st.expander("➕ **Record New Shipment**", expanded=False):
            with st.form("add_shipment", clear_on_submit=True):
                store_options = {
                    f"{row['name']} ({row['location'] or 'N/A'})": row['id']
                    for _, row in stores_df.iterrows()
                }

                c1, c2 = st.columns(2)
                selected = c1.selectbox("🏪 Store", list(store_options.keys()))
                ship_date = c2.date_input("📅 Shipment Date", value=date.today())

                c1, c2 = st.columns(2)
                scheduled_date = c1.date_input(
                    "📆 Scheduled Delivery Date (optional)",
                    value=date.today() + timedelta(days=1)
                )
                delivery_status = c2.selectbox("🚚 Delivery Status", DELIVERY_STATUSES)

                c1, c2, c3 = st.columns(3)
                q30 = c1.number_input("🔵 Qty 30D", min_value=0, value=0)
                q40 = c2.number_input("🟠 Qty 40D", min_value=0, value=0)
                q60 = c3.number_input("🟣 Qty 60D", min_value=0, value=0)
                notes = st.text_area("📝 Notes")

                if st.form_submit_button("💾 Record Shipment"):
                    store_id = store_options[selected]
                    add_shipment(
                        store_id, ship_date, q30, q40, q60,
                        notes, delivery_status, scheduled_date
                    )
                    st.success("✅ Shipment recorded!")
                    st.rerun()

    # All shipments
    render_section_title("📋 All Shipments")
    shipments_df = get_shipments()

    if shipments_df.empty:
        st.info("📭 No shipments yet.")
        return

    # Filter by status
    c1, c2 = st.columns([1, 3])
    status_filter = c1.selectbox(
        "Filter by Status",
        ['All'] + DELIVERY_STATUSES,
        key='status_filter'
    )

    filtered_df = shipments_df.copy()
    if status_filter != 'All':
        filtered_df = filtered_df[filtered_df['delivery_status'] == status_filter]

    if filtered_df.empty:
        st.info(f"📭 No shipments with status '{status_filter}'.")
        return

    # Display shipments as expandable cards (so we can update status)
    for _, ship in filtered_df.iterrows():
        status = ship.get('delivery_status', 'Pending') or 'Pending'
        emoji = STATUS_COLORS.get(status, '⚪')
        
        ship_date_str = str(ship['date'])
        total_qty = int(ship['qty_30d']) + int(ship['qty_40d']) + int(ship['qty_60d'])
        
        title = f"{emoji} **#{ship['id']}** — 🏪 {ship['store_name']} — 📅 {ship_date_str} — 📦 {total_qty} units — **{status}**"
        
        with st.expander(title):
            c1, c2, c3 = st.columns(3)
            c1.metric("🔵 30D", int(ship['qty_30d']))
            c2.metric("🟠 40D", int(ship['qty_40d']))
            c3.metric("🟣 60D", int(ship['qty_60d']))

            c1, c2 = st.columns(2)
            with c1:
                scheduled = ship.get('scheduled_date')
                if scheduled:
                    st.markdown(f"**📆 Scheduled:** {scheduled}")
                else:
                    st.markdown("**📆 Scheduled:** —")
            with c2:
                st.markdown(f"**📝 Notes:** {ship.get('notes') or '—'}")

            st.markdown("---")
            
            # Update delivery status
            c1, c2, c3 = st.columns([2, 1, 1])
            new_status = c1.selectbox(
                "Update Status",
                DELIVERY_STATUSES,
                index=DELIVERY_STATUSES.index(status) if status in DELIVERY_STATUSES else 0,
                key=f"status_{ship['id']}"
            )
            
            if c2.button("💾 Update", key=f"upd_{ship['id']}"):
                update_shipment_status(ship['id'], new_status)
                st.success(f"✅ Status updated to {new_status}")
                st.rerun()
            
            if c3.button("🗑️ Delete", key=f"del_{ship['id']}"):
                delete_shipment(ship['id'])
                st.warning(f"🗑️ Deleted #{ship['id']}")
                st.rerun()
