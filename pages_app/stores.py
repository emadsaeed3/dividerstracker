"""
Stores management page
"""
import streamlit as st
from database import get_stores, add_store, update_store, delete_store
from components import render_section_title


def render():
    """Render the Stores page"""
    st.markdown("# 🏪 Stores Management")
    
    # Add new store form
    with st.expander("➕ **Add New Store**", expanded=False):
        with st.form("add_store", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Store Name *")
            location = c2.text_input("Location")
            
            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("🔵 Required 30D", min_value=0, value=0)
            r40 = c2.number_input("🟠 Required 40D", min_value=0, value=0)
            r60 = c3.number_input("🟣 Required 60D", min_value=0, value=0)
            
            submitted = st.form_submit_button("➕ Add Store")
            if submitted and name:
                add_store(name, location, r30, r40, r60)
                st.success(f"✅ Store '{name}' added!")
                st.rerun()
    
    # List all stores
    render_section_title("📋 All Stores")
    stores_df = get_stores()
    
    if stores_df.empty:
        st.info("📭 No stores added yet.")
        return
    
    for _, store in stores_df.iterrows():
        with st.expander(f"🏪 **{store['name']}** — 📍 {store['location'] or 'N/A'}"):
            with st.form(f"edit_{store['id']}"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Name", value=store['name'], key=f"n_{store['id']}")
                location = c2.text_input("Location", value=store['location'] or '', key=f"l_{store['id']}")
                
                c1, c2, c3 = st.columns(3)
                r30 = c1.number_input("🔵 Required 30D", min_value=0, value=int(store['required_30d']), key=f"r30_{store['id']}")
                r40 = c2.number_input("🟠 Required 40D", min_value=0, value=int(store['required_40d']), key=f"r40_{store['id']}")
                r60 = c3.number_input("🟣 Required 60D", min_value=0, value=int(store['required_60d']), key=f"r60_{store['id']}")
                
                c1, c2 = st.columns(2)
                update_btn = c1.form_submit_button("💾 Update")
                delete_btn = c2.form_submit_button("🗑️ Delete")
                
                if update_btn:
                    update_store(store['id'], name, location, r30, r40, r60)
                    st.success("✅ Updated!")
                    st.rerun()
                
                if delete_btn:
                    delete_store(store['id'])
                    st.warning("🗑️ Deleted!")
                    st.rerun()
