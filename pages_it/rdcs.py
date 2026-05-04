"""
RDCs management page (4M IT Equipment)
"""
import streamlit as st
import pandas as pd
from datetime import date
from database_it import (
    IT_EQUIPMENT_TYPES, IT_ICONS,
    get_rdcs, add_rdc, update_rdc, delete_rdc,
    get_rdc_requirements_dict, set_rdc_requirements_bulk,
    get_shipped_totals_per_rdc
)
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


def render_rdc_summary(rdc_id, requirements):
    """Render a visual summary of required vs shipped for an RDC"""
    shipped = get_shipped_totals_per_rdc(rdc_id)

    total_req = sum(requirements.values())
    total_ship = sum(shipped.get(t, 0) for t in IT_EQUIPMENT_TYPES)
    total_pending = max(0, total_req - total_ship)

    pct = (total_ship / total_req * 100) if total_req > 0 else 0
    status_color = '#27ae60' if pct >= 100 else ('#f39c12' if pct > 0 else '#e74c3c')

    st.markdown(f"""
    <div style="background: rgba(52,152,219,0.05); padding: 12px 14px; border-radius: 10px; 
                border-left: 4px solid {status_color}; margin-bottom: 12px;">
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; font-size:0.85rem;">
            <span><b>📦 Req:</b> {total_req}</span>
            <span style="color:#27ae60;"><b>🚚 Ship:</b> {total_ship}</span>
            <span style="color:#e74c3c;"><b>⏳ Pend:</b> {total_pending}</span>
            <span style="color:{status_color}; font-weight:700;">{pct:.0f}%</span>
        </div>
        <div class="progress-container" style="margin-top:8px;">
            <div class="progress-fill" style="width:{min(pct,100)}%; background:{status_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_rdc_card(rdc):
    """Render an editable RDC card"""
    launch_date_val = rdc.get('launch_date')
    emoji, status_msg = get_launch_status(launch_date_val)

    transport_ready = bool(rdc.get('transportation_ready', False))
    transport_label = "✅ Transport Ready" if transport_ready else "❌ Transport Not Ready"

    title_parts = [f"🏢 **{rdc['name']}**", f"📍 {rdc['location'] or 'N/A'}"]
    if launch_date_val:
        title_parts.append(f"{emoji} {status_msg}")
    title_parts.append(transport_label)

    with st.expander(" — ".join(title_parts)):
        requirements = get_rdc_requirements_dict(rdc['id'])
        render_rdc_summary(rdc['id'], requirements)

        with st.form(f"edit_rdc_{rdc['id']}"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name", value=rdc['name'], key=f"n_{rdc['id']}")
            location = c2.text_input("Location", value=rdc['location'] or '', key=f"l_{rdc['id']}")

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
                key=f"ld_{rdc['id']}"
            )
            transportation_ready_edit = c2.checkbox(
                "🚚 Transport Ready",
                value=transport_ready,
                key=f"tr_{rdc['id']}"
            )

            st.markdown("**📋 Required Equipment:**")

            req_edit = {}
            for item in IT_EQUIPMENT_TYPES:
                req_edit[item] = st.number_input(
                    f"{item}",
                    min_value=0,
                    value=int(requirements.get(item, 0)),
                    key=f"req_{rdc['id']}_{item}"
                )

            c1, c2 = st.columns(2)
            update_btn = c1.form_submit_button("💾 Update", use_container_width=True)
            delete_btn = c2.form_submit_button("🗑️ Delete", use_container_width=True)

            if update_btn:
                update_rdc(
                    rdc['id'], name, location,
                    launch_date_edit, transportation_ready_edit
                )
                set_rdc_requirements_bulk(rdc['id'], req_edit)
                st.success("✅ Updated!")
                st.rerun()

            if delete_btn:
                delete_rdc(rdc['id'])
                st.warning("🗑️ Deleted!")
                st.rerun()


def render():
    """Render the RDCs page"""
    st.markdown("# 🏢 RDCs Management")
    st.caption("Regional Distribution Centers for 4M IT Equipment")

    # Add new RDC
    with st.expander("➕ **Add New RDC**", expanded=False):
        with st.form("add_rdc", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("RDC Name *")
            location = c2.text_input("Location")

            c1, c2 = st.columns(2)
            launch_date_input = c1.date_input(
                "🚀 Launch Date (optional)",
                value=None,
                min_value=date.today()
            )
            transportation_ready = c2.checkbox("🚚 Transportation Ready", value=False)

            st.markdown("**📋 Required Equipment:**")

            req_values = {}
            cols = st.columns(2)
            for idx, item in enumerate(IT_EQUIPMENT_TYPES):
                with cols[idx % 2]:
                    req_values[item] = st.number_input(
                        f"{item}",
                        min_value=0,
                        value=0,
                        key=f"add_req_{item}"
                    )

            submitted = st.form_submit_button("➕ Add RDC", use_container_width=True)
            if submitted and name:
                rdc_id = add_rdc(name, location, launch_date_input, transportation_ready)
                if rdc_id:
                    set_rdc_requirements_bulk(rdc_id, req_values)
                    st.success(f"✅ RDC '{name}' added!")
                    st.rerun()

    # List all RDCs (2 per row)
    render_section_title("📋 All RDCs")
    rdcs_df = get_rdcs()

    if rdcs_df.empty:
        st.info("📭 No RDCs added yet.")
        return

    rdcs_list = list(rdcs_df.iterrows())

    for i in range(0, len(rdcs_list), 2):
        c1, c2 = st.columns(2)

        with c1:
            render_rdc_card(rdcs_list[i][1])

        if i + 1 < len(rdcs_list):
            with c2:
                render_rdc_card(rdcs_list[i + 1][1])
