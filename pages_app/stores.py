"""
Stores management page
"""
import streamlit as st
from datetime import date, timedelta
from database import get_stores, add_store, update_store, delete_store
from components import render_section_title


def get_launch_status(launch_date):
    """Return status emoji and message based on launch date proximity"""
    if not launch_date:
        return "", ""
    
    if isinstance(launch_date, str):
        launch_date = date.fromisoformat(launch_date)
    
    today = date.today()
    days_left = (launch_date - today).days
    
    if days_left < 0:
        return "✅", f"Launched {abs(days_left)} days ago"
    elif days_left == 0:
        return "🚀", "Launching TODAY!"
    elif days_left <= 2:
        return "🚨", f"{days_left} day(s) left - URGENT!"
    elif days_left <= 4:
        return "⚠️", f"{days_left} days left - Prepare shipment!"
    else:
        return "📅", f"{days_left} days left"


def render():
    """Render the Stores page"""
    st.markdown("# 🏪 Stores Management")

    # Add new store
    with st.expander("➕ **Add New Store**", expanded=False):
        with st.form("add_store", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Store Name *")
            location = c2.text_input("Location")

            c1, c2 = st.columns(2)
            launch_date_input = c1.date_input(
                "🚀 Launch Date (optional)",
                value=None,
                min_value=date.today()
            )
            transportation_ready = c2.checkbox("🚚 Transportation Ready", value=False)

            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("🔵 Required 30D", min_value=0, value=0)
            r40 = c2.number_input("🟠 Required 40D", min_value=0, value=0)
            r60 = c3.number_input("🟣 Required 60D", min_value=0, value=0)

            submitted = st.form_submit_button("➕ Add Store")
            if submitted and name:
                add_store(name, location, r30, r40, r60, launch_date_input, transportation_ready)
                st.success(f"✅ Store '{name}' added!")
                st.rerun()

    # List all stores
    render_section_title("📋 All Stores")
    stores_df = get_stores()

    if stores_df.empty:
        st.info("📭 No stores added yet.")
        return

    for _, store in stores_df.iterrows():
        # Build expander title with launch status
        launch_date_val = store.get('launch_date')
        emoji, status_msg = get_launch_status(launch_date_val)
        
        title_parts = [f"🏪 **{store['name']}**", f"📍 {store['location'] or 'N/A'}"]
        if launch_date_val:
            title_parts.append(f"{emoji} {status_msg}")
        
        with st.expander(" — ".join(title_parts)):
            with st.form(f"edit_{store['id']}"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Name", value=store['name'], key=f"n_{store['id']}")
                location = c2.text_input("Location", value=store['location'] or '', key=f"l_{store['id']}")

                c1, c2 = st.columns(2)
                current_launch = None
                if launch_date_val:
                    if isinstance(launch_date_val, str):
                        current_launch = date.fromisoformat(launch_date_val)
                    else:
                        current_launch = launch_date_val
                
                launch_date_edit = c1.date_input(
                    "🚀 Launch Date",
                    value=current_launch,
                    key=f"ld_{store['id']}"
                )
                transportation_ready_edit = c2.checkbox(
                    "🚚 Transportation Ready",
                    value=bool(store.get('transportation_ready', False)),
                    key=f"tr_{store['id']}"
                )

                c1, c2, c3 = st.columns(3)
                r30 = c1.number_input("🔵 Required 30D", min_value=0, value=int(store['required_30d']), key=f"r30_{store['id']}")
                r40 = c2.number_input("🟠 Required 40D", min_value=0, value=int(store['required_40d']), key=f"r40_{store['id']}")
                r60 = c3.number_input("🟣 Required 60D", min_value=0, value=int(store['required_60d']), key=f"r60_{store['id']}")

                c1, c2 = st.columns(2)
                update_btn = c1.form_submit_button("💾 Update")
                delete_btn = c2.form_submit_button("🗑️ Delete")

                if update_btn:
                    update_store(
                        store['id'], name, location, r30, r40, r60,
                        launch_date_edit, transportation_ready_edit
                    )
                    st.success("✅ Updated!")
                    st.rerun()

                if delete_btn:
                    delete_store(store['id'])
                    st.warning("🗑️ Deleted!")
                    st.rerun()
