"""
RDCs management page (4M IT Equipment) - Executive View
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from database_it import (
    IT_EQUIPMENT_TYPES, IT_ICONS,
    get_rdcs, add_rdc, update_rdc, delete_rdc,
    get_rdc_requirements_dict, set_rdc_requirements_bulk,
    get_shipped_totals_per_rdc, get_total_requirements,
    get_it_stock_dict
)
from components import render_section_title


# ============================================================
# Helpers
# ============================================================

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


def get_launch_status(launch_date):
    launch_date = _to_date(launch_date)
    if not launch_date:
        return "📅", "No launch date", "#95a5a6"

    today = date.today()
    days_left = (launch_date - today).days

    if days_left < 0:
        return "✅", f"Launched {abs(days_left)}d ago", "#27ae60"
    elif days_left == 0:
        return "🚀", "Launching TODAY!", "#e74c3c"
    elif days_left <= 2:
        return "🚨", f"{days_left}d left - URGENT!", "#e74c3c"
    elif days_left <= 7:
        return "⚠️", f"{days_left}d left", "#f39c12"
    else:
        return "📅", f"{days_left}d left", "#3498db"


def get_readiness_status(pct):
    """Returns (label, color, emoji) based on completion percentage"""
    if pct >= 100:
        return "Ready", "#27ae60", "🟢"
    elif pct >= 75:
        return "Almost Ready", "#2ecc71", "🟢"
    elif pct >= 50:
        return "In Progress", "#f39c12", "🟡"
    elif pct > 0:
        return "Started", "#e67e22", "🟠"
    else:
        return "Not Started", "#e74c3c", "🔴"


def calc_rdc_metrics(rdc_id, requirements):
    """Calculate metrics for a single RDC"""
    shipped = get_shipped_totals_per_rdc(rdc_id)
    total_req = sum(requirements.values())
    total_ship = sum(shipped.get(t, 0) for t in IT_EQUIPMENT_TYPES)
    total_pending = max(0, total_req - total_ship)
    pct = (total_ship / total_req * 100) if total_req > 0 else 0
    return {
        'shipped': shipped,
        'total_req': total_req,
        'total_ship': total_ship,
        'total_pending': total_pending,
        'pct': pct
    }


# ============================================================
# Executive KPI Header
# ============================================================

def render_executive_kpis(rdcs_df):
    """Top-level KPIs for all RDCs network"""
    total_rdcs = len(rdcs_df)
    total_req_all = 0
    total_ship_all = 0
    ready_count = 0
    critical_count = 0
    upcoming_launches = 0
    today = date.today()

    for _, rdc in rdcs_df.iterrows():
        reqs = get_rdc_requirements_dict(rdc['id'])
        m = calc_rdc_metrics(rdc['id'], reqs)
        total_req_all += m['total_req']
        total_ship_all += m['total_ship']
        if m['pct'] >= 100 and m['total_req'] > 0:
            ready_count += 1
        elif m['pct'] < 50 and m['total_req'] > 0:
            critical_count += 1

        ld = _to_date(rdc.get('launch_date'))
        if ld and 0 <= (ld - today).days <= 7:
            upcoming_launches += 1

    overall_pct = (total_ship_all / total_req_all * 100) if total_req_all > 0 else 0

    # Use Streamlit columns instead of HTML grid (more reliable)
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(52,152,219,0.1),rgba(52,152,219,0.02));border-left:4px solid #3498db;padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">🏢 Total RDCs</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#2c3e50;">{total_rdcs}</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">In network</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with cols[1]:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(155,89,182,0.1),rgba(155,89,182,0.02));border-left:4px solid #9b59b6;padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">📋 Total Required</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#2c3e50;">{total_req_all:,}</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">Equipment units</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with cols[2]:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(39,174,96,0.1),rgba(39,174,96,0.02));border-left:4px solid #27ae60;padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">🚚 Total Shipped</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#2c3e50;">{total_ship_all:,}</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">Delivered</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with cols[3]:
        overall_color = "#27ae60" if overall_pct >= 75 else ("#f39c12" if overall_pct >= 50 else "#e74c3c")
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{overall_color}1a,{overall_color}05);border-left:4px solid {overall_color};padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">📊 Overall Coverage</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:{overall_color};">{overall_pct:.0f}%</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">Network readiness</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    
    cols2 = st.columns(3)
    
    with cols2[0]:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(39,174,96,0.1),rgba(39,174,96,0.02));border-left:4px solid #27ae60;padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">✅ Ready RDCs</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#27ae60;">{ready_count}</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">100% covered</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with cols2[1]:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(231,76,60,0.1),rgba(231,76,60,0.02));border-left:4px solid #e74c3c;padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">🔴 Critical RDCs</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#e74c3c;">{critical_count}</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">Below 50%</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with cols2[2]:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(243,156,18,0.1),rgba(243,156,18,0.02));border-left:4px solid #f39c12;padding:16px;border-radius:10px;">'
            f'<div style="font-size:0.75rem;color:#7f8c8d;text-transform:uppercase;font-weight:600;">🚀 Upcoming Launches</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#f39c12;">{upcoming_launches}</div>'
            f'<div style="font-size:0.75rem;color:#95a5a6;">Next 7 days</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)


# ============================================================
# Executive Summary Table
# ============================================================

def render_summary_table(rdcs_df):
    """Comprehensive summary table for all RDCs"""
    rows = []
    today = date.today()

    for _, rdc in rdcs_df.iterrows():
        reqs = get_rdc_requirements_dict(rdc['id'])
        m = calc_rdc_metrics(rdc['id'], reqs)
        status_label, _, status_emoji = get_readiness_status(m['pct'])

        ld = _to_date(rdc.get('launch_date'))
        if ld:
            days_left = (ld - today).days
            launch_str = f"{ld.strftime('%Y-%m-%d')} ({days_left:+d}d)"
        else:
            launch_str = "—"

        rows.append({
            'Status': f"{status_emoji} {status_label}",
            'RDC': rdc['name'],
            'Location': rdc.get('location') or '—',
            'Launch Date': launch_str,
            'Required': m['total_req'],
            'Shipped': m['total_ship'],
            'Pending': m['total_pending'],
            'Coverage %': f"{m['pct']:.0f}%"
        })

    df = pd.DataFrame(rows)
    df = df.sort_values('Coverage %', ascending=True, key=lambda x: x.str.rstrip('%').astype(float))
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# Equipment Breakdown Matrix
# ============================================================

def render_equipment_matrix(rdcs_df):
    """Matrix view: RDCs × Equipment Types"""
    rows = []
    for _, rdc in rdcs_df.iterrows():
        reqs = get_rdc_requirements_dict(rdc['id'])
        shipped = get_shipped_totals_per_rdc(rdc['id'])
        row = {'RDC': rdc['name']}
        for item in IT_EQUIPMENT_TYPES:
            r = reqs.get(item, 0)
            s = shipped.get(item, 0)
            if r == 0:
                row[item] = "—"
            else:
                if s >= r:
                    row[item] = f"✅ {s}/{r}"
                elif s == 0:
                    row[item] = f"❌ 0/{r}"
                else:
                    row[item] = f"⚠️ {s}/{r}"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# Executive RDC Card (visual)
# ============================================================

def render_executive_rdc_card(rdc):
    """Beautiful executive-style card for each RDC"""
    rdc_id = rdc['id']
    requirements = get_rdc_requirements_dict(rdc_id)
    m = calc_rdc_metrics(rdc_id, requirements)

    emoji, status_msg, launch_color = get_launch_status(rdc.get('launch_date'))
    status_label, status_color, status_emoji = get_readiness_status(m['pct'])

    # Build equipment rows
    equip_rows = ""
    for item in IT_EQUIPMENT_TYPES:
        req = requirements.get(item, 0)
        ship = m['shipped'].get(item, 0)
        if req == 0:
            continue
        if ship >= req:
            icon = "✅"
            row_color = "#27ae60"
        elif ship == 0:
            icon = "❌"
            row_color = "#e74c3c"
        else:
            icon = "⚠️"
            row_color = "#f39c12"

        equip_rows += f'<div style="display:flex; justify-content:space-between; align-items:center; padding:6px 8px; margin:3px 0; background:rgba(0,0,0,0.02); border-radius:6px; border-left: 3px solid {row_color};"><span style="font-size:0.85rem; color:#2c3e50; font-weight:500;">{icon} {item}</span><span style="font-size:0.85rem; font-weight:700; color:{row_color};">{ship}/{req}</span></div>'

    if not equip_rows:
        equip_rows = '<div style="color:#95a5a6; font-style:italic; padding:10px;">No equipment requirements set</div>'

    rdc_name = rdc['name']
    rdc_location = rdc.get('location') or 'No location'
    pct_width = min(m['pct'], 100)

    # Build full HTML as one line (no leading whitespace)
    html = (
        f'<div style="background:white; border-radius:14px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.08); margin-bottom:14px; border-top: 4px solid {status_color};">'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">'
        f'<div>'
        f'<div style="font-size:1.15rem; font-weight:700; color:#2c3e50;">🏢 {rdc_name}</div>'
        f'<div style="font-size:0.82rem; color:#7f8c8d; margin-top:3px;">📍 {rdc_location}</div>'
        f'</div>'
        f'<div style="background:{status_color}; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600;">{status_emoji} {status_label}</div>'
        f'</div>'
        f'<div style="background:rgba(0,0,0,0.03); padding:8px 12px; border-radius:8px; margin-bottom:12px; border-left:3px solid {launch_color};">'
        f'<span style="font-size:0.85rem; color:#2c3e50;"><b>{emoji} Launch:</b> {status_msg}</span>'
        f'</div>'
        f'<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin-bottom:12px;">'
        f'<div style="text-align:center; padding:8px; background:rgba(155,89,182,0.08); border-radius:8px;">'
        f'<div style="font-size:0.7rem; color:#7f8c8d; text-transform:uppercase;">Required</div>'
        f'<div style="font-size:1.3rem; font-weight:700; color:#9b59b6;">{m["total_req"]}</div>'
        f'</div>'
        f'<div style="text-align:center; padding:8px; background:rgba(39,174,96,0.08); border-radius:8px;">'
        f'<div style="font-size:0.7rem; color:#7f8c8d; text-transform:uppercase;">Shipped</div>'
        f'<div style="font-size:1.3rem; font-weight:700; color:#27ae60;">{m["total_ship"]}</div>'
        f'</div>'
        f'<div style="text-align:center; padding:8px; background:rgba(231,76,60,0.08); border-radius:8px;">'
        f'<div style="font-size:0.7rem; color:#7f8c8d; text-transform:uppercase;">Pending</div>'
        f'<div style="font-size:1.3rem; font-weight:700; color:#e74c3c;">{m["total_pending"]}</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-bottom:12px;">'
        f'<div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:4px;">'
        f'<span style="color:#7f8c8d; font-weight:600;">Coverage</span>'
        f'<span style="color:{status_color}; font-weight:700;">{m["pct"]:.0f}%</span>'
        f'</div>'
        f'<div style="background:#ecf0f1; border-radius:8px; height:10px; overflow:hidden;">'
        f'<div style="width:{pct_width}%; height:100%; background:{status_color}; border-radius:8px;"></div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:10px;">'
        f'<div style="font-size:0.8rem; font-weight:600; color:#2c3e50; margin-bottom:6px;">📦 Equipment Breakdown</div>'
        f'{equip_rows}'
        f'</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)



# ============================================================
# Edit form (collapsible, separate from card)
# ============================================================

def render_rdc_edit_form(rdc):
    """Edit form in expander - separate from visual card"""
    requirements = get_rdc_requirements_dict(rdc['id'])
    
    with st.expander(f"⚙️ Manage **{rdc['name']}** (Edit / Delete)"):
        with st.form(f"edit_rdc_{rdc['id']}"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name", value=rdc['name'], key=f"n_{rdc['id']}")
            location = c2.text_input("Location", value=rdc.get('location') or '', key=f"l_{rdc['id']}")

            current_launch = _to_date(rdc.get('launch_date'))
            launch_date_edit = st.date_input(
                "🚀 Launch Date",
                value=current_launch,
                key=f"ld_{rdc['id']}"
            )

            st.markdown("**📋 Required Equipment:**")
            req_edit = {}
            cols = st.columns(2)
            for idx, item in enumerate(IT_EQUIPMENT_TYPES):
                with cols[idx % 2]:
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
                update_rdc(rdc['id'], name, location, launch_date_edit)
                set_rdc_requirements_bulk(rdc['id'], req_edit)
                st.success("✅ Updated!")
                st.rerun()

            if delete_btn:
                delete_rdc(rdc['id'])
                st.warning("🗑️ Deleted!")
                st.rerun()


# ============================================================
# Main render
# ============================================================

def render():
    st.markdown("# 🏢 RDCs Management")
    st.caption("Regional Distribution Centers — Executive Overview")

    # Add new RDC
    with st.expander("➕ **Add New RDC**", expanded=False):
        with st.form("add_rdc", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("RDC Name *")
            location = c2.text_input("Location")
            launch_date_input = st.date_input("🚀 Launch Date (optional)", value=None)

            st.markdown("**📋 Required Equipment:**")
            req_values = {}
            cols = st.columns(2)
            for idx, item in enumerate(IT_EQUIPMENT_TYPES):
                with cols[idx % 2]:
                    req_values[item] = st.number_input(
                        f"{item}", min_value=0, value=0,
                        key=f"add_req_{item}"
                    )

            submitted = st.form_submit_button("➕ Add RDC", use_container_width=True)
            if submitted and name:
                rdc_id = add_rdc(name, location, launch_date_input)
                if rdc_id:
                    set_rdc_requirements_bulk(rdc_id, req_values)
                    st.success(f"✅ RDC '{name}' added!")
                    st.rerun()

    rdcs_df = get_rdcs()

    if rdcs_df.empty:
        st.info("📭 No RDCs added yet. Click **➕ Add New RDC** above to get started.")
        return

    # Executive KPIs
    render_executive_kpis(rdcs_df)

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Executive Cards",
        "📊 Summary Table",
        "📋 Equipment Matrix",
        "⚙️ Manage RDCs"
    ])

    # ===== TAB 1: Executive Cards =====
    with tab1:
        # Filter & Sort
        c1, c2, c3 = st.columns([2, 2, 2])
        status_filter = c1.selectbox(
            "Filter by Status",
            ["All", "🟢 Ready", "🟡 In Progress", "🔴 Not Started/Critical"],
            key="rdc_filter"
        )
        sort_by = c2.selectbox(
            "Sort by",
            ["Coverage % (Lowest first)", "Coverage % (Highest first)", "Launch Date", "Name"],
            key="rdc_sort"
        )
        c3.markdown(f"<div style='padding-top:28px; color:#7f8c8d;'>Showing <b>{len(rdcs_df)}</b> RDCs</div>", unsafe_allow_html=True)

        # Build list with metrics
        rdc_list = []
        for _, rdc in rdcs_df.iterrows():
            reqs = get_rdc_requirements_dict(rdc['id'])
            m = calc_rdc_metrics(rdc['id'], reqs)
            rdc_list.append((rdc, m))

        # Apply filter
        if status_filter == "🟢 Ready":
            rdc_list = [(r, m) for r, m in rdc_list if m['pct'] >= 100 and m['total_req'] > 0]
        elif status_filter == "🟡 In Progress":
            rdc_list = [(r, m) for r, m in rdc_list if 0 < m['pct'] < 100]
        elif status_filter == "🔴 Not Started/Critical":
            rdc_list = [(r, m) for r, m in rdc_list if m['pct'] < 50]

        # Apply sort
        if sort_by == "Coverage % (Lowest first)":
            rdc_list.sort(key=lambda x: x[1]['pct'])
        elif sort_by == "Coverage % (Highest first)":
            rdc_list.sort(key=lambda x: -x[1]['pct'])
        elif sort_by == "Launch Date":
            rdc_list.sort(key=lambda x: _to_date(x[0].get('launch_date')) or date.max)
        elif sort_by == "Name":
            rdc_list.sort(key=lambda x: x[0]['name'])

        if not rdc_list:
            st.info("📭 No RDCs match the selected filter.")
        else:
            # Render in 2-column grid
            for i in range(0, len(rdc_list), 2):
                c1, c2 = st.columns(2)
                with c1:
                    render_executive_rdc_card(rdc_list[i][0])
                if i + 1 < len(rdc_list):
                    with c2:
                        render_executive_rdc_card(rdc_list[i + 1][0])

    # ===== TAB 2: Summary Table =====
    with tab2:
        render_section_title("📊 RDCs Summary Overview")
        st.caption("Sorted by lowest coverage first (most attention needed)")
        render_summary_table(rdcs_df)

    # ===== TAB 3: Equipment Matrix =====
    with tab3:
        render_section_title("📋 Equipment Allocation Matrix")
        st.caption("Shipped / Required per equipment type for each RDC")
        render_equipment_matrix(rdcs_df)

        # Legend
        st.markdown("""
        <div style="background:rgba(52,152,219,0.05); padding:10px; border-radius:8px; margin-top:10px;">
            <b>Legend:</b> ✅ Fully shipped &nbsp;|&nbsp; ⚠️ Partially shipped &nbsp;|&nbsp; ❌ Not shipped &nbsp;|&nbsp; — Not required
        </div>
        """, unsafe_allow_html=True)

    # ===== TAB 4: Manage =====
    with tab4:
        render_section_title("⚙️ Manage RDCs")
        st.caption("Edit details, requirements, or delete RDCs")
        for _, rdc in rdcs_df.iterrows():
            render_rdc_edit_form(rdc)
