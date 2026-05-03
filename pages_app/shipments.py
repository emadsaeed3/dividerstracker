"""
Shipments management page
"""
import streamlit as st
from datetime import date
from database import get_stores, get_shipments, add_shipment, delete_shipment
from components import render_section_title


def render():
    """Render the Shipments page"""
    st.markdown("# 🚚 Shipments")
    
    stores_df = get_stores()
    
    if stores_df.empty:
        st.warning("⚠️ Add a store first.")
    else:
        # Add new shipment form
        with st.expander("➕ **Record New Shipment**", expanded=False):
            with st.form("add_shipment", clear_on_submit=True):
                store_options = {
                    f"{row['name']} ({row['location'] or 'N/A'})": row['id']
                    for _, row in stores_df.iterrows()
                }
                
                c1, c2 = st.columns(2)
                selected = c1.selectbox("🏪 Store", list(store_options.keys()))
                ship_date = c2.date_input("📅 Date", value=date.today())
                
                c1, c2, c3 = st.columns(3)
                q30 = c1.number_input("🔵 Qty 30D", min_value=0, value=0)
                q40 = c2.number_input("🟠 Qty 40D", min_value=0, value=0)
                q60 = c3.number_input("🟣 Qty 60D", min_value=0, value=0)
                notes = st.text_area("📝 Notes")
                
                if st.form_submit_button("💾 Record"):
                    store_id = store_options[selected]
                    add_shipment(store_id, ship_date, q30, q40, q60, notes)
                    st.success("✅ Recorded!")
                    st.rerun()
    
    # All shipments
    render_section_title("📋 All Shipments")
    shipments_df = get_shipments()
    
    if shipments_df.empty:
        st.info("📭 No shipments yet.")
        return
    
    display_df = shipments_df[['id', 'store_name', 'date', 'qty_30d', 'qty_40d', 'qty_60d', 'notes']].copy()
    display_df.columns = ['ID', 'Store', 'Date', '30D', '40D', '60D', 'Notes']
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Delete shipment
    st.markdown("---")
    c1, c2 = st.columns([1, 3])
    del_id = c1.number_input("Shipment ID", min_value=0, value=0)
    if c2.button("🗑️ Delete"):
        if del_id > 0:
            delete_shipment(del_id)
            st.warning(f"🗑️ Deleted #{del_id}")
            st.rerun()
