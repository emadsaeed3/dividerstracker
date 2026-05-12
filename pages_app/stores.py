"""
Stores management page (no transportation field - moved to shipments)
Discrepancy = Required vs Shipped (planning view, not logistics)
Features: Collapsible section, filters, sorting, CSV export
"""
import io
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import (
    get_stores, add_store, update_store, delete_store,
    get_shipments
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


def get_required_vs_shipped(stores_df, shipments_df):
    """
    Calculate discrepancies between Required and Shipped quantities.

    diff = shipped - required
    - positive => over-shipped (shipped more than needed)
    - negative => under-shipped (still pending shipment)
    - zero    => exact match
    """
    if stores_df.empty:
        return pd.DataFrame()

    rows = []
    for _, store in stores_df.iterrows():
        store_id = store['id']

        if not shipments_df.empty:
            store_ships = shipments_df[shipments_df['store_id'] == store_id]
            s30 = int(store_ships['qty_30d'].sum()) if not store_ships.empty else 0
            s40 = int(store_ships['qty_40d'].sum()) if not store_ships.empty else 0
            s60 = int(store_ships['qty_60d'].sum()) if not store_ships.empty else 0
        else:
            s30 = s40 = s60 = 0

        r30 = int(store.get('required_30d', 0) or 0)
        r40 = int(store.get('required_40d', 0) or 0)
        r60 = int(store.get('required_60d', 0) or 0)

        diff_30 = s30 - r30
        diff_40 = s40 - r40
        diff_60 = s60 - r60

        if diff_30 != 0 or diff_40 != 0 or diff_60 != 0:
            rows.append({
                'id': store_id,
                'name': store['name'],
                'location': store.get('location', '') or '',
                'is_launched': bool(store.get('is_launched', False)),
                'required_30d': r30,
                'required_40d': r40,
                'required_60d': r60,
                'shipped_30d': s30,
                'shipped_40d': s40,
                'shipped_60d': s60,
                'diff_30d': diff_30,
                'diff_40d': diff_40,
                'diff_60d': diff_60,
            })

    return pd.DataFrame(rows)


def render_discrepancy_card(row, kind):
    """Render a single Required vs Shipped discrepancy card"""
    if kind == 'over':
        color = '#e67e22'
        icon = '📈'
        kind_label = 'OVER-SHIPPED'
        kind_bg = '#e67e22'
    elif kind == 'under':
        color = '#e74c3c'
        icon = '📉'
        kind_label = 'UNDER-SHIPPED'
        kind_bg = '#e74c3c'
    else:  # mixed
        color = '#9b59b6'
        icon = '🔄'
        kind_label = 'MIXED'
        kind_bg = '#9b59b6'

    if row.get('is_launched', False):
        status_badge = ' <span style="background:#27ae60; color:white; padding:2px 8px; border-radius:8px; font-size:0.7rem; font-weight:600; margin-left:6px;">✅ LAUNCHED</span>'
    else:
        status_badge = ' <span style="background:#3498db; color:white; padding:2px 8px; border-radius:8px; font-size:0.7rem; font-weight:600; margin-left:6px;">📅 UPCOMING</span>'

    type_badge = '<span style="background:' + kind_bg + '; color:white; padding:3px 10px; border-radius:10px; font-size:0.72rem; font-weight:700; letter-spacing:0.5px;">' + icon + ' ' + kind_label + '</span>'

    total_diff = row['diff_30d'] + row['diff_40d'] + row['diff_60d']
    if total_diff > 0:
        total_summary = '<span style="color:#e67e22; font-weight:700;">+' + str(total_diff) + ' over-shipped</span>'
    elif total_diff < 0:
        total_summary = '<span style="color:#e74c3c; font-weight:700;">' + str(total_diff) + ' under-shipped</span>'
    else:
        total_summary = '<span style="color:#9b59b6; font-weight:700;">Net: 0 (mixed)</span>'

    def diff_html(label, required, shipped, diff):
        if diff == 0:
            return (
                '<div style="background:rgba(127,140,141,0.1); padding:8px 12px; border-radius:8px; flex:1; min-width:130px;">'
                '<div style="font-size:0.7rem; opacity:0.6;">' + label + '</div>'
                '<div style="font-size:0.75rem; opacity:0.7;">Req: ' + str(required) + ' | Ship: ' + str(shipped) + '</div>'
                '<div style="font-weight:700; opacity:0.6;">— Match ✓</div>'
                '</div>'
            )

        if diff > 0:
            sign = '+'
            diff_color = '#e67e22'
            diff_label = 'OVER'
        else:
            sign = ''
            diff_color = '#e74c3c'
            diff_label = 'UNDER'

        return (
            '<div style="background:' + diff_color + '20; padding:8px 12px; border-radius:8px; flex:1; min-width:130px; border:1.5px solid ' + diff_color + '60;">'
            '<div style="font-size:0.7rem; opacity:0.85; color:' + diff_color + ';"><b>' + label + ' — ' + diff_label + '</b></div>'
            '<div style="font-size:0.72rem; opacity:0.8;">Req: ' + str(required) + ' | Ship: ' + str(shipped) + '</div>'
            '<div style="font-weight:800; color:' + diff_color + '; font-size:1.1rem;">' + sign + str(diff) + '</div>'
            '</div>'
        )

    html_30 = diff_html('🔵 30D', row['required_30d'], row['shipped_30d'], row['diff_30d'])
    html_40 = diff_html('🟠 40D', row['required_40d'], row['shipped_40d'], row['diff_40d'])
    html_60 = diff_html('🟣 60D', row['required_60d'], row['shipped_60d'], row['diff_60d'])

    card = (
        '<div style="background: rgba(255,255,255,0.02);'
        'border-left: 5px solid ' + color + ';'
        'border-radius: 12px;'
        'padding: 14px 18px;'
        'margin-bottom: 10px;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">'
        '<div>'
        '<span style="font-weight:700; font-size:1.05rem;">🏪 ' + str(row['name']) + '</span>'
        + status_badge +
        '<div style="opacity:0.7; font-size:0.82rem; margin-top:3px;">📍 ' + str(row['location']) + ' &nbsp;•&nbsp; ' + total_summary + '</div>'
        '</div>'
        '<div>' + type_badge + '</div>'
        '</div>'
        '<div style="display:flex; gap:8px; flex-wrap:wrap;">'
        + html_30 + html_40 + html_60 +
        '</div>'
        '</div>'
    )

    st.markdown(card, unsafe_allow_html=True)


def build_export_dataframe(filtered_rows):
    """Build a clean DataFrame for CSV export"""
    export_rows = []
    for row, kind, severity in filtered_rows:
        kind_label_map = {
            'over': 'Over-shipped',
            'under': 'Under-shipped',
            'mixed': 'Mixed'
        }
        export_rows.append({
            'Store Name': row.get('name', ''),
            'Location': row.get('location', ''),
            'Status': 'Launched' if row.get('is_launched') else 'Upcoming',
            'Discrepancy Type': kind_label_map.get(kind, kind),
            'Required 30D': row['required_30d'],
            'Shipped 30D': row['shipped_30d'],
            'Diff 30D': row['diff_30d'],
            'Required 40D': row['required_40d'],
            'Shipped 40D': row['shipped_40d'],
            'Diff 40D': row['diff_40d'],
            'Required 60D': row['required_60d'],
            'Shipped 60D': row['shipped_60d'],
            'Diff 60D': row['diff_60d'],
            'Total Diff': row['diff_30d'] + row['diff_40d'] + row['diff_60d'],
            'Severity (abs)': severity,
        })
    return pd.DataFrame(export_rows)


def render_discrepancy_section(stores_df, shipments_df):
    """Render Required vs Shipped section - collapsible with filters, sort, export"""
    disc_df = get_required_vs_shipped(stores_df, shipments_df)

    # Empty state - collapsed by default
    if disc_df.empty:
        with st.expander("⚖️ **Required vs Shipped** — ✅ All matched", expanded=False):
            st.markdown(
                '<div style="background: rgba(39, 174, 96, 0.1); padding: 16px 20px; border-radius: 10px; '
                'border-left: 4px solid #27ae60; margin-bottom: 8px;">'
                '✅ <b>All shipments match requirements!</b> Every store has been shipped exactly what they need.'
                '</div>',
                unsafe_allow_html=True
            )
        return

    # Drop duplicates safety
    if 'id' in disc_df.columns:
        disc_df = disc_df.drop_duplicates(subset=['id'], keep='first')

    # Classify all rows
    over_count = 0
    under_count = 0
    mixed_count = 0
    classified = []

    for _, row in disc_df.iterrows():
        has_over = row['diff_30d'] > 0 or row['diff_40d'] > 0 or row['diff_60d'] > 0
        has_under = row['diff_30d'] < 0 or row['diff_40d'] < 0 or row['diff_60d'] < 0

        if has_over and has_under:
            kind = 'mixed'
            mixed_count += 1
        elif has_over:
            kind = 'over'
            over_count += 1
        else:
            kind = 'under'
            under_count += 1

        total_diff = abs(row['diff_30d']) + abs(row['diff_40d']) + abs(row['diff_60d'])
        classified.append((row, kind, total_diff))

    # Build expander label
    summary_badges = []
    if under_count > 0:
        summary_badges.append("📉 " + str(under_count) + " Under")
    if over_count > 0:
        summary_badges.append("📈 " + str(over_count) + " Over")
    if mixed_count > 0:
        summary_badges.append("🔄 " + str(mixed_count) + " Mixed")
    summary_label = " | ".join(summary_badges)

    expander_label = "⚖️ **Required vs Shipped** — " + str(len(disc_df)) + " stores (" + summary_label + ")"

    # Remember user's expand/collapse choice
    if 'disc_expanded' not in st.session_state:
        st.session_state['disc_expanded'] = True

    with st.expander(expander_label, expanded=st.session_state['disc_expanded']):
        # Top toolbar
        col_hint, col_reset = st.columns([3, 1])
        with col_hint:
            st.caption("💡 Click the section header to collapse this view")
        with col_reset:
            if st.button("🔄 Reset Filters", key='reset_disc_filters', use_container_width=True):
                for k in ['disc_search', 'disc_type_filter', 'disc_status_filter', 'disc_sort']:
                    st.session_state.pop(k, None)
                st.rerun()

        # Info banner
        summary_parts = []
        if under_count > 0:
            summary_parts.append('<span style="color:#e74c3c;"><b>📉 ' + str(under_count) + ' Under-shipped</b></span>')
        if over_count > 0:
            summary_parts.append('<span style="color:#e67e22;"><b>📈 ' + str(over_count) + ' Over-shipped</b></span>')
        if mixed_count > 0:
            summary_parts.append('<span style="color:#9b59b6;"><b>🔄 ' + str(mixed_count) + ' Mixed</b></span>')

        summary_text = ' &nbsp;|&nbsp; '.join(summary_parts)

        st.markdown(
            '<div style="background: rgba(243, 156, 18, 0.1); padding: 12px 18px; border-radius: 10px; '
            'border-left: 4px solid #f39c12; margin-bottom: 14px; font-size:0.9rem;">'
            '💡 Stores where shipped quantities don\'t match required quantities.<br>'
            '<div style="margin-top:6px;">' + summary_text + '</div>'
            '<span style="font-size:0.78rem; opacity:0.85; margin-top:4px; display:block;">'
            '📉 <b>Under-shipped</b> = Shipped &lt; Required &nbsp;|&nbsp; '
            '📈 <b>Over-shipped</b> = Shipped &gt; Required &nbsp;|&nbsp; '
            '🔄 <b>Mixed</b> = Both in different sizes'
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )

        # Filters row
        col_search, col_type, col_status, col_sort = st.columns([2, 1.2, 1.2, 1.2])

        with col_search:
            disc_search = st.text_input(
                "🔍 Search store",
                placeholder="Type store name or location...",
                key='disc_search',
                label_visibility="collapsed"
            )

        with col_type:
            type_options = ['All Types']
            if under_count > 0:
                type_options.append('📉 Under-shipped only')
            if over_count > 0:
                type_options.append('📈 Over-shipped only')
            if mixed_count > 0:
                type_options.append('🔄 Mixed only')

            type_filter = st.selectbox(
                "Type",
                type_options,
                key='disc_type_filter',
                label_visibility="collapsed"
            )

        with col_status:
            status_filter = st.selectbox(
                "Status",
                ['All Stores', '✅ Launched only', '📅 Upcoming only'],
                key='disc_status_filter',
                label_visibility="collapsed"
            )

        with col_sort:
            sort_option = st.selectbox(
                "Sort by",
                ['Severity (high→low)', 'Severity (low→high)', 'Name (A→Z)', 'Name (Z→A)'],
                key='disc_sort',
                label_visibility="collapsed"
            )

        # Apply filters
        filtered = list(classified)

        if 'Under-shipped' in type_filter:
            filtered = [item for item in filtered if item[1] == 'under']
        elif 'Over-shipped' in type_filter:
            filtered = [item for item in filtered if item[1] == 'over']
        elif 'Mixed' in type_filter:
            filtered = [item for item in filtered if item[1] == 'mixed']

        if 'Launched' in status_filter:
            filtered = [item for item in filtered if bool(item[0].get('is_launched', False))]
        elif 'Upcoming' in status_filter:
            filtered = [item for item in filtered if not bool(item[0].get('is_launched', False))]

        if disc_search and disc_search.strip():
            s = disc_search.strip().lower()
            filtered = [
                item for item in filtered
                if s in str(item[0].get('name', '')).lower()
                or s in str(item[0].get('location', '')).lower()
            ]

        # Sort
        if sort_option == 'Severity (high→low)':
            filtered.sort(key=lambda x: -x[2])
        elif sort_option == 'Severity (low→high)':
            filtered.sort(key=lambda x: x[2])
        elif sort_option == 'Name (A→Z)':
            filtered.sort(key=lambda x: str(x[0].get('name', '')).lower())
        elif sort_option == 'Name (Z→A)':
            filtered.sort(key=lambda x: str(x[0].get('name', '')).lower(), reverse=True)

        # Counter
        if len(filtered) != len(classified):
            st.caption("🔎 Showing **" + str(len(filtered)) + "** of **" + str(len(classified)) + "** stores")
        else:
            st.caption("📊 Showing all **" + str(len(classified)) + "** stores")

        # No results
        if not filtered:
            st.markdown(
                '<div style="background: rgba(127, 140, 141, 0.1); padding: 14px 18px; border-radius: 10px; '
                'border-left: 4px solid #7f8c8d; margin-top: 8px; font-size:0.9rem;">'
                '🔍 <b>No stores match your filters.</b> Click "Reset Filters" or adjust your search.'
                '</div>',
                unsafe_allow_html=True
            )
            return

        # Render filtered cards
        for row, kind, _ in filtered:
            render_discrepancy_card(row, kind)

        # 📥 Export to CSV button (at the bottom)
        st.markdown("---")
        col_info, col_export = st.columns([2, 1])

        with col_info:
            st.caption(
                "📥 Export the **filtered** list above to CSV for sharing or further analysis."
            )

        with col_export:
            export_df = build_export_dataframe(filtered)
            csv_buffer = io.StringIO()
            export_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_data = csv_buffer.getvalue()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = "required_vs_shipped_" + timestamp + ".csv"

            st.download_button(
                label="📥 Export CSV (" + str(len(filtered)) + " rows)",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                use_container_width=True,
                key='export_disc_csv'
            )


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

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Search stores",
            placeholder="Type store name or location...",
            key='store_search',
            label_visibility="collapsed"
        )
    with col_filter:
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

    if search_query and search_query.strip():
        s = search_query.strip().lower()
        mask = (
            filtered_df['name'].astype(str).str.lower().str.contains(s, na=False) |
            filtered_df['location'].fillna('').astype(str).str.lower().str.contains(s, na=False)
        )
        filtered_df = filtered_df[mask]

    if filtered_df.empty:
        if search_query:
            st.info("🔍 No stores match your search '" + search_query + "'")
        else:
            st.info("📭 No stores match the filter.")
        return

    st.caption("Showing **" + str(len(filtered_df)) + "** of **" + str(len(stores_df)) + "** stores")

    stores_list = list(filtered_df.iterrows())

    for i in range(0, len(stores_list), 2):
        c1, c2 = st.columns(2)
        with c1:
            render_store_card(stores_list[i][1], shipments_df)
        if i + 1 < len(stores_list):
            with c2:
                render_store_card(stores_list[i + 1][1], shipments_df)
