"""
Vendor Stock Management with Tabs:
- Current Stock
- Purchase Orders
- Coverage Analysis (NEW)
- History
"""
import io
import math
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import (
    get_stocks_dict, get_stocks, update_stock, get_threshold,
    get_stock_history, clear_stock_history,
    get_purchase_orders, get_po_by_id, add_purchase_order,
    update_purchase_order, receive_purchase_order, delete_purchase_order,
    get_pending_pos, PO_STATUSES,
    get_magnet_stock
)
from components import render_section_title, render_stat_card
from coverage_helper import (
    calculate_strips_needed, calculate_coverage,
    allocate_supply_to_stores
)


# ==================== MAGNET WARNING ====================

def render_magnet_warning(q30, q40, q60, context_label="this PO"):
    total_dividers = q30 + q40 + q60
    if total_dividers == 0:
        return

    strips_available = get_magnet_stock()
    strips_needed = calculate_strips_needed(total_dividers)

    if strips_needed <= strips_available:
        remaining = strips_available - strips_needed
        st.markdown(
            f'<div style="background:rgba(39,174,96,0.1); padding:10px 14px; border-radius:8px; '
            f'border-left:4px solid #27ae60; margin:8px 0; font-size:0.88rem;">'
            f'🧲 <b>Magnet Check:</b> {context_label} needs <b>{strips_needed}</b> strips '
            f'for <b>{total_dividers}</b> dividers. '
            f'Available: <b>{strips_available}</b> ✅ '
            f'<span style="opacity:0.8;">(Surplus: {remaining})</span><br>'
            f'<span style="font-size:0.78rem; opacity:0.75;">'
            f'✂️ Optimized: cutting excess squares into rectangles (saves ~28%)'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        shortage = strips_needed - strips_available
        st.markdown(
            f'<div style="background:rgba(231,76,60,0.1); padding:10px 14px; border-radius:8px; '
            f'border-left:4px solid #e74c3c; margin:8px 0; font-size:0.88rem;">'
            f'🚨 <b>Magnet Shortage Alert!</b><br>'
            f'• {context_label}: <b>{total_dividers}</b> dividers<br>'
            f'• Strips needed (optimized): <b>{strips_needed}</b><br>'
            f'• Available at vendor: <b>{strips_available}</b><br>'
            f'• <span style="color:#e74c3c;"><b>⚠️ Need to order: {shortage} more strips</b></span>'
            f'</div>',
            unsafe_allow_html=True
        )


# ==================== PO COVERAGE WIDGET ====================

def render_po_coverage_widget(q30, q40, q60, context="this new PO"):
    """Mini coverage widget for use in PO forms"""
    if q30 + q40 + q60 == 0:
        return

    extra_po = {'qty_30d': q30, 'qty_40d': q40, 'qty_60d': q60}

    # Calculate WITHOUT this PO
    cov_without = calculate_coverage(extra_po=None)
    # Calculate WITH this PO
    cov_with = calculate_coverage(extra_po=extra_po)

    demand = cov_with['demand']

    if demand['total'] == 0:
        st.markdown(
            '<div style="background:rgba(52,152,219,0.1); padding:10px 14px; border-radius:8px; '
            'border-left:4px solid #3498db; margin:8px 0; font-size:0.88rem;">'
            '📊 <b>Coverage:</b> No upcoming or under-shipped stores currently. '
            'This PO will go into stock.'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # Compare before/after
    before_short = cov_without['shortages']['total_shortage']
    after_short = cov_with['shortages']['total_shortage']
    improvement = before_short - after_short

    if after_short == 0:
        bg = 'rgba(39,174,96,0.1)'
        border = '#27ae60'
        icon = '✅'
        verdict = f'<b>This PO will FULLY cover all {demand["stores_count"]} stores!</b>'
    elif improvement > 0:
        bg = 'rgba(243,156,18,0.1)'
        border = '#f39c12'
        icon = '⚠️'
        verdict = (
            f'<b>This PO will partially help:</b> '
            f'reduces shortage by <b>{improvement}</b> dividers '
            f'(still short: <b>{after_short}</b>)'
        )
    else:
        bg = 'rgba(231,76,60,0.1)'
        border = '#e74c3c'
        icon = '🚨'
        verdict = f'<b>Even with this PO, still short {after_short} dividers!</b>'

    cov30 = cov_with['coverage']['pct_30d']
    cov40 = cov_with['coverage']['pct_40d']
    cov60 = cov_with['coverage']['pct_60d']

    st.markdown(
        f'<div style="background:{bg}; padding:12px 16px; border-radius:10px; '
        f'border-left:4px solid {border}; margin:8px 0; font-size:0.88rem;">'
        f'<div style="font-weight:700; margin-bottom:8px;">'
        f'{icon} Coverage Analysis (after adding {context})'
        f'</div>'
        f'<div style="margin-bottom:8px;">{verdict}</div>'
        f'<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:8px; '
        f'font-size:0.82rem; margin-top:8px;">'
        f'<div>🔵 <b>30D:</b> {cov30:.0f}% covered</div>'
        f'<div>🟠 <b>40D:</b> {cov40:.0f}% covered</div>'
        f'<div>🟣 <b>60D:</b> {cov60:.0f}% covered</div>'
        f'</div>'
        f'<div style="margin-top:8px; font-size:0.78rem; opacity:0.85;">'
        f'📊 Demand: <b>{demand["total"]}</b> dividers across <b>{demand["stores_count"]}</b> stores '
        f'(upcoming + under-shipped)'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# ==================== TAB 1: CURRENT STOCK ====================

def render_current_stock_tab():
    threshold = get_threshold()
    stocks = get_stocks_dict()

    render_section_title("📦 Current Vendor Stock")

    c1, c2, c3, c4 = st.columns(4)
    total_stock = sum(stocks.values())
    with c1:
        render_stat_card("30D Stock", stocks.get('30D', 0), "card-30d", "bi-box-seam")
    with c2:
        render_stat_card("40D Stock", stocks.get('40D', 0), "card-40d", "bi-box-seam")
    with c3:
        render_stat_card("60D Stock", stocks.get('60D', 0), "card-60d", "bi-box-seam")
    with c4:
        render_stat_card("Total Stock", total_stock, "card-stores", "bi-boxes")

    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        if stock == 0:
            st.error(f"❌ **{dtype} is OUT OF STOCK!**")
        elif stock < threshold:
            st.warning(f"⚠️ **{dtype} low stock:** Only {stock} units left (threshold: {threshold})")

    st.markdown("---")

    render_section_title("➕ Add / Remove Stock Manually")
    st.caption("Use this for manual adjustments. For PO receipts, use the Purchase Orders tab.")

    with st.form("manual_stock_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dtype = c1.selectbox("Divider Type", ['30D', '40D', '60D'])
        movement = c2.selectbox("Movement", ['IN (Add)', 'OUT (Remove)'])
        qty = c3.number_input("Quantity", min_value=1, value=1, step=1)

        notes = st.text_input("Notes (optional)", placeholder="e.g., Manual adjustment, damaged, etc.")

        submit = st.form_submit_button("💾 Apply", use_container_width=True, type="primary")

        if submit:
            current = stocks.get(dtype, 0)
            if movement.startswith('IN'):
                new_qty = current + qty
                note_text = notes or 'Manual addition'
            else:
                if qty > current:
                    st.error(f"❌ Cannot remove {qty} - only {current} in stock!")
                    return
                new_qty = current - qty
                note_text = notes or 'Manual removal'

            try:
                update_stock(dtype, new_qty, note_text)
                st.success(f"✅ Stock updated! New {dtype} stock: {new_qty}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to update stock: {e}")


# ==================== TAB 2: PURCHASE ORDERS ====================

def render_po_status_badge(status):
    color_map = {
        'Draft': '#95a5a6',
        'Sent to Vendor': '#3498db',
        'Confirmed': '#9b59b6',
        'In Production': '#e67e22',
        'Shipped': '#f39c12',
        'Received': '#27ae60',
        'Cancelled': '#e74c3c'
    }
    color = color_map.get(status, '#95a5a6')
    return f'<span style="background:{color};color:white;padding:4px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;">{status}</span>'


def fmt_date(d):
    if not d:
        return '—'
    try:
        if isinstance(d, str):
            return date.fromisoformat(d[:10]).strftime('%d %b %Y')
        return d.strftime('%d %b %Y') if hasattr(d, 'strftime') else str(d)
    except Exception:
        return str(d)


def render_po_card(po):
    po_id = po['id']
    po_num = po.get('po_number', 'N/A')
    vendor = po.get('vendor_name', '—') or '—'
    status = po.get('status', 'Draft')
    notes = po.get('notes', '') or ''

    po_date_val = po.get('po_date')
    expected = po.get('expected_date')
    received = po.get('received_date')

    q30 = int(po.get('qty_30d', 0) or 0)
    q40 = int(po.get('qty_40d', 0) or 0)
    q60 = int(po.get('qty_60d', 0) or 0)
    total = q30 + q40 + q60

    strips_for_this_po = calculate_strips_needed(total)

    days_info = ''
    if expected and status not in ('Received', 'Cancelled'):
        try:
            if isinstance(expected, str):
                exp = date.fromisoformat(expected[:10])
            else:
                exp = expected
            days_left = (exp - date.today()).days
            if days_left < 0:
                days_info = f'<span style="color:#e74c3c;font-weight:600;">⚠ {abs(days_left)}d overdue</span>'
            elif days_left == 0:
                days_info = f'<span style="color:#e67e22;font-weight:600;">📅 Due today</span>'
            elif days_left <= 3:
                days_info = f'<span style="color:#f39c12;font-weight:600;">📅 {days_left}d left</span>'
            else:
                days_info = f'<span style="color:#7f8c8d;">📅 {days_left}d left</span>'
        except Exception:
            pass

    is_locked = status == 'Received'

    with st.container():
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                    border-radius:12px;padding:16px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div>
                    <span style="font-size:1.1rem;font-weight:700;">📋 PO #{po_num}</span>
                    <span style="margin-left:12px;">{render_po_status_badge(status)}</span>
                </div>
                <div>{days_info}</div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;font-size:0.88rem;margin-bottom:10px;">
                <div><b>Vendor:</b> {vendor}</div>
                <div><b>PO Date:</b> {fmt_date(po_date_val)}</div>
                <div><b>Expected:</b> {fmt_date(expected)}</div>
                <div><b>Received:</b> {fmt_date(received)}</div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;font-size:0.88rem;">
                <div>📘 <b>30D:</b> {q30}</div>
                <div>📙 <b>40D:</b> {q40}</div>
                <div>📕 <b>60D:</b> {q60}</div>
                <div>📦 <b>Total:</b> {total}</div>
                <div>🧲 <b>Strips:</b> {strips_for_this_po}</div>
            </div>
            {f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.08);font-size:0.85rem;color:#bdc3c7;"><b>Notes:</b> {notes}</div>' if notes else ''}
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([1, 1, 1, 3])

        with c1:
            if not is_locked and status != 'Cancelled':
                if st.button("✏️ Edit", key=f"edit_po_{po_id}", use_container_width=True):
                    st.session_state[f'editing_po_{po_id}'] = True
                    st.rerun()

        with c2:
            if status not in ('Received', 'Cancelled'):
                if st.button("✅ Receive", key=f"recv_po_{po_id}", use_container_width=True, type="primary"):
                    success, msg = receive_purchase_order(po_id)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        with c3:
            if not is_locked:
                if st.button("🗑️ Delete", key=f"del_po_{po_id}", use_container_width=True):
                    st.session_state[f'confirm_del_po_{po_id}'] = True
                    st.rerun()

        if st.session_state.get(f'confirm_del_po_{po_id}'):
            st.warning(f"⚠️ Delete PO #{po_num}?")
            cc1, cc2 = st.columns(2)
            if cc1.button("✅ Yes, delete", key=f"yes_del_{po_id}", use_container_width=True):
                if delete_purchase_order(po_id):
                    st.success("✅ PO deleted")
                    st.session_state.pop(f'confirm_del_po_{po_id}', None)
                    st.rerun()
                else:
                    st.error("❌ Cannot delete")
            if cc2.button("❌ Cancel", key=f"no_del_{po_id}", use_container_width=True):
                st.session_state.pop(f'confirm_del_po_{po_id}', None)
                st.rerun()

        if st.session_state.get(f'editing_po_{po_id}'):
            render_edit_po_form(po)


def render_edit_po_form(po):
    po_id = po['id']

    with st.form(f"edit_po_form_{po_id}"):
        st.markdown(f"### ✏️ Edit PO #{po.get('po_number')}")

        c1, c2 = st.columns(2)
        po_number = c1.text_input("PO Number*", value=po.get('po_number', ''))
        vendor = c2.text_input("Vendor Name", value=po.get('vendor_name', '') or '')

        c1, c2 = st.columns(2)
        po_date_val = po.get('po_date')
        if po_date_val and isinstance(po_date_val, str):
            try:
                po_date_val = date.fromisoformat(po_date_val[:10])
            except Exception:
                po_date_val = date.today()
        po_date_input = c1.date_input("PO Date*", value=po_date_val or date.today())

        expected = po.get('expected_date')
        if expected and isinstance(expected, str):
            try:
                expected = date.fromisoformat(expected[:10])
            except Exception:
                expected = None
        expected_input = c2.date_input("Expected Delivery", value=expected or (date.today() + timedelta(days=7)))

        c1, c2, c3 = st.columns(3)
        q30 = c1.number_input("30D Qty", min_value=0, value=int(po.get('qty_30d', 0) or 0), step=1)
        q40 = c2.number_input("40D Qty", min_value=0, value=int(po.get('qty_40d', 0) or 0), step=1)
        q60 = c3.number_input("60D Qty", min_value=0, value=int(po.get('qty_60d', 0) or 0), step=1)

        # 🧲 Magnet warning
        if q30 + q40 + q60 > 0:
            render_magnet_warning(q30, q40, q60, f"PO #{po.get('po_number')}")
            # 📊 Coverage widget
            render_po_coverage_widget(q30, q40, q60, f"PO #{po.get('po_number')}")

        editable_statuses = [s for s in PO_STATUSES if s != 'Received']
        current_status = po.get('status', 'Draft')
        if current_status not in editable_statuses:
            current_status = 'Draft'
        status = st.selectbox("Status", editable_statuses, index=editable_statuses.index(current_status))

        notes = st.text_area("Notes", value=po.get('notes', '') or '', height=80)

        c1, c2 = st.columns(2)
        save = c1.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
        cancel = c2.form_submit_button("❌ Cancel", use_container_width=True)

        if save:
            if not po_number.strip():
                st.error("❌ PO Number is required")
                return
            if q30 + q40 + q60 == 0:
                st.error("❌ Enter at least one quantity")
                return

            if update_purchase_order(po_id, po_number, vendor, po_date_input, expected_input,
                                     q30, q40, q60, status, notes):
                st.success("✅ PO updated!")
                st.session_state.pop(f'editing_po_{po_id}', None)
                st.rerun()
            else:
                st.error("❌ Failed to update PO")

        if cancel:
            st.session_state.pop(f'editing_po_{po_id}', None)
            st.rerun()


def render_add_po_form():
    with st.expander("➕ **Create New Purchase Order**", expanded=False):
        with st.form("add_po_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            po_number = c1.text_input("PO Number*", placeholder="e.g., PO-2025-001")
            vendor = c2.text_input("Vendor Name", placeholder="e.g., ABC Supplies")

            c1, c2 = st.columns(2)
            po_date_input = c1.date_input("PO Date*", value=date.today())
            expected_input = c2.date_input("Expected Delivery", value=date.today() + timedelta(days=7))

            c1, c2, c3 = st.columns(3)
            q30 = c1.number_input("30D Qty", min_value=0, value=0, step=1)
            q40 = c2.number_input("40D Qty", min_value=0, value=0, step=1)
            q60 = c3.number_input("60D Qty", min_value=0, value=0, step=1)

            # 🧲 Magnet warning
            if q30 + q40 + q60 > 0:
                render_magnet_warning(q30, q40, q60, "This new PO")
                # 📊 Coverage widget
                render_po_coverage_widget(q30, q40, q60, "this new PO")

            status = st.selectbox("Initial Status", ['Draft', 'Sent to Vendor', 'Confirmed'], index=0)

            notes = st.text_area("Notes", placeholder="Any additional info...", height=80)

            submit = st.form_submit_button("💾 Create PO", use_container_width=True, type="primary")

            if submit:
                if not po_number.strip():
                    st.error("❌ PO Number is required")
                    return
                if q30 + q40 + q60 == 0:
                    st.error("❌ Enter at least one quantity")
                    return

                result = add_purchase_order(po_number, vendor, po_date_input, expected_input,
                                            q30, q40, q60, status, notes)
                if result:
                    st.success(f"✅ PO #{po_number} created!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create PO")


def render_purchase_orders_tab():
    render_section_title("📋 Purchase Orders")

    all_pos = get_purchase_orders()
    pending = get_pending_pos()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card("Total POs", len(all_pos), "card-stores", "bi-file-earmark-text")
    with c2:
        render_stat_card("Pending", len(pending), "card-40d", "bi-hourglass-split")

    received_count = 0
    cancelled_count = 0
    if not all_pos.empty and 'status' in all_pos.columns:
        received_count = len(all_pos[all_pos['status'] == 'Received'])
        cancelled_count = len(all_pos[all_pos['status'] == 'Cancelled'])

    with c3:
        render_stat_card("Received", received_count, "card-shipments", "bi-check-circle")
    with c4:
        render_stat_card("Cancelled", cancelled_count, "card-60d", "bi-x-circle")

    st.markdown("---")

    render_add_po_form()

    st.markdown("---")

    c1, c2 = st.columns([2, 1])
    with c1:
        search = st.text_input("🔍 Search PO Number or Vendor", placeholder="Type to filter...")
    with c2:
        status_filter = st.selectbox("Filter by Status", ['All'] + PO_STATUSES)

    df = all_pos.copy() if not all_pos.empty else pd.DataFrame()

    if df.empty:
        st.info("📭 No purchase orders yet. Create your first PO above!")
        return

    if status_filter != 'All':
        df = df[df['status'] == status_filter]

    if search:
        s = search.lower()
        mask = (
            df['po_number'].astype(str).str.lower().str.contains(s, na=False) |
            df['vendor_name'].fillna('').astype(str).str.lower().str.contains(s, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("🔍 No POs match your filter")
        return

    st.markdown(f"**Showing {len(df)} PO(s)**")

    for _, po in df.iterrows():
        render_po_card(po)


# ==================== TAB 3: COVERAGE ANALYSIS (NEW) ====================

def render_store_coverage_card(store_result):
    """Render a single store's coverage card"""
    status = store_result['status']

    if status == 'covered':
        color = '#27ae60'
        bg = 'rgba(39,174,96,0.08)'
        icon = '✅'
        label = 'FULLY COVERED'
    elif status == 'partial':
        color = '#f39c12'
        bg = 'rgba(243,156,18,0.08)'
        icon = '⚠️'
        label = 'PARTIAL'
    else:
        color = '#e74c3c'
        bg = 'rgba(231,76,60,0.08)'
        icon = '❌'
        label = 'SHORTAGE'

    # Status badge
    if store_result.get('is_launched'):
        store_status = '<span style="background:#27ae60; color:white; padding:2px 8px; border-radius:8px; font-size:0.7rem; font-weight:600;">✅ LAUNCHED (under-shipped)</span>'
    else:
        store_status = '<span style="background:#3498db; color:white; padding:2px 8px; border-radius:8px; font-size:0.7rem; font-weight:600;">📅 UPCOMING</span>'

    # Days info
    days_left = store_result.get('days_left')
    if days_left is None:
        days_text = '<span style="opacity:0.6;">No launch date</span>'
    elif days_left < 0:
        days_text = f'<span style="color:#e74c3c;font-weight:600;">⏰ {abs(days_left)}d overdue</span>'
    elif days_left == 0:
        days_text = '<span style="color:#e74c3c;font-weight:700;">🚨 LAUNCHING TODAY</span>'
    elif days_left <= 7:
        days_text = f'<span style="color:#e67e22;font-weight:600;">⚠️ {days_left}d left</span>'
    else:
        days_text = f'<span style="opacity:0.8;">📅 {days_left}d left</span>'

    # Per-type breakdown
    def type_box(label, need, alloc, short, color_t):
        if need == 0:
            return ''
        if short == 0:
            box_color = '#27ae60'
            sign = '✓'
        else:
            box_color = '#e74c3c'
            sign = f'-{short}'
        return (
            f'<div style="background:{color_t}15; padding:6px 10px; border-radius:6px; '
            f'flex:1; min-width:100px; border-left:3px solid {color_t};">'
            f'<div style="font-size:0.7rem; opacity:0.8;">{label}</div>'
            f'<div style="font-size:0.8rem;">Need: <b>{need}</b> | Got: <b>{alloc}</b></div>'
            f'<div style="font-weight:700; color:{box_color}; font-size:0.85rem;">{sign}</div>'
            f'</div>'
        )

    box_30 = type_box('🔵 30D', store_result['need_30d'], store_result['alloc_30d'],
                      store_result['short_30d'], '#3498db')
    box_40 = type_box('🟠 40D', store_result['need_40d'], store_result['alloc_40d'],
                      store_result['short_40d'], '#e67e22')
    box_60 = type_box('🟣 60D', store_result['need_60d'], store_result['alloc_60d'],
                      store_result['short_60d'], '#9b59b6')

    st.markdown(
        f'<div style="background:{bg}; border-left:4px solid {color}; '
        f'border-radius:10px; padding:12px 16px; margin-bottom:8px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; '
        f'margin-bottom:8px; flex-wrap:wrap; gap:6px;">'
        f'<div>'
        f'<span style="font-weight:700; font-size:1rem;">🏪 {store_result["name"]}</span> '
        f'{store_status}'
        f'<div style="font-size:0.78rem; opacity:0.75; margin-top:2px;">'
        f'📍 {store_result["location"]} &nbsp;•&nbsp; {days_text}'
        f'</div>'
        f'</div>'
        f'<span style="background:{color}; color:white; padding:3px 10px; '
        f'border-radius:10px; font-size:0.72rem; font-weight:700;">'
        f'{icon} {label}'
        f'</span>'
        f'</div>'
        f'<div style="display:flex; gap:6px; flex-wrap:wrap;">'
        f'{box_30}{box_40}{box_60}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_coverage_analysis_tab():
    render_section_title("📊 Coverage Analysis")

    st.markdown(
        '<div style="background: rgba(52, 152, 219, 0.08); padding: 12px 16px; '
        'border-radius: 10px; border-left: 4px solid #3498db; margin-bottom: 16px; '
        'font-size:0.9rem;">'
        '💡 <b>What this shows:</b> Will your <b>current stock + pending POs</b> '
        'cover all upcoming stores and under-shipped existing stores?<br>'
        '<span style="font-size:0.82rem; opacity:0.85;">'
        'Allocation is greedy: stores with closest launch date get supplied first.'
        '</span>'
        '</div>',
        unsafe_allow_html=True
    )

    # Calculate coverage
    coverage = calculate_coverage()
    demand = coverage['demand']

    if demand['stores_count'] == 0:
        st.markdown(
            '<div style="background: rgba(39, 174, 96, 0.1); padding: 18px 22px; '
            'border-radius: 10px; border-left: 4px solid #27ae60;">'
            '✅ <b>No demand!</b> All stores are fully shipped, and no upcoming stores need supply.'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # Top: Supply vs Demand summary
    supply = coverage['supply']
    cov = coverage['coverage']
    short = coverage['shortages']

    # Overall status banner
    if cov['overall_status'] == 'covered':
        status_color = '#27ae60'
        status_bg = 'rgba(39,174,96,0.1)'
        status_icon = '✅'
        status_msg = 'All demand can be fully covered!'
    elif cov['overall_status'] == 'partial':
        status_color = '#f39c12'
        status_bg = 'rgba(243,156,18,0.1)'
        status_icon = '⚠️'
        status_msg = 'Partial coverage — some stores will fall short'
    else:
        status_color = '#e74c3c'
        status_bg = 'rgba(231,76,60,0.1)'
        status_icon = '🚨'
        status_msg = 'Critical shortage — order more stock NOW!'

    st.markdown(
        f'<div style="background:{status_bg}; padding:16px 20px; border-radius:12px; '
        f'border-left:5px solid {status_color}; margin-bottom:16px;">'
        f'<div style="font-size:1.1rem; font-weight:700; margin-bottom:8px;">'
        f'{status_icon} {status_msg}'
        f'</div>'
        f'<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px; '
        f'margin-top:10px;">'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">🔵 30D Coverage</div>'
        f'<div style="font-size:1.3rem; font-weight:700;">{cov["pct_30d"]:.0f}%</div></div>'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">🟠 40D Coverage</div>'
        f'<div style="font-size:1.3rem; font-weight:700;">{cov["pct_40d"]:.0f}%</div></div>'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">🟣 60D Coverage</div>'
        f'<div style="font-size:1.3rem; font-weight:700;">{cov["pct_60d"]:.0f}%</div></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Supply vs Demand breakdown
    render_section_title("⚖️ Supply vs Demand")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f'<div style="background:rgba(22,160,133,0.08); padding:14px 18px; '
            f'border-radius:10px; border-left:4px solid #16a085;">'
            f'<div style="font-weight:700; margin-bottom:8px;">💪 Available Supply</div>'
            f'<div style="font-size:0.82rem;">'
            f'📦 <b>Stock now:</b> 30D={supply["stock_30d"]} | 40D={supply["stock_40d"]} | 60D={supply["stock_60d"]}<br>'
            f'🚚 <b>Pending POs:</b> 30D={supply["pending_30d"]} | 40D={supply["pending_40d"]} | 60D={supply["pending_60d"]}<br>'
            f'<hr style="margin:6px 0; opacity:0.3;">'
            f'<b>Total: 30D={supply["total_30d"]} | 40D={supply["total_40d"]} | 60D={supply["total_60d"]}</b>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f'<div style="background:rgba(231,76,60,0.08); padding:14px 18px; '
            f'border-radius:10px; border-left:4px solid #e74c3c;">'
            f'<div style="font-weight:700; margin-bottom:8px;">📊 Total Demand</div>'
            f'<div style="font-size:0.82rem;">'
            f'🏪 <b>Stores needing supply:</b> {demand["stores_count"]}<br>'
            f'📦 <b>Total dividers needed:</b> {demand["total"]}<br>'
            f'<hr style="margin:6px 0; opacity:0.3;">'
            f'<b>30D={demand["total_30d"]} | 40D={demand["total_40d"]} | 60D={demand["total_60d"]}</b>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Shortage recommendations
    if short['total_shortage'] > 0:
        st.markdown(
            f'<div style="background:rgba(231,76,60,0.1); padding:14px 18px; '
            f'border-radius:10px; border-left:4px solid #e74c3c; margin-top:12px;">'
            f'<div style="font-weight:700; margin-bottom:8px;">🛒 Recommended Order</div>'
            f'<div style="font-size:0.88rem;">'
            f'To cover all demand, order <b>at least</b>:<br>'
            f'• 🔵 <b>{short["short_30d"]}</b> × 30D dividers<br>'
            f'• 🟠 <b>{short["short_40d"]}</b> × 40D dividers<br>'
            f'• 🟣 <b>{short["short_60d"]}</b> × 60D dividers<br>'
            f'<b>📦 Total: {short["total_shortage"]} additional dividers</b>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Magnet check
    magnets = coverage['magnets']
    render_section_title("🧲 Magnet Coverage")

    if magnets['magnet_shortage'] == 0:
        magnet_bg = 'rgba(39,174,96,0.1)'
        magnet_border = '#27ae60'
        magnet_icon = '✅'
        magnet_msg = 'Sufficient magnet strips available!'
    else:
        magnet_bg = 'rgba(231,76,60,0.1)'
        magnet_border = '#e74c3c'
        magnet_icon = '🚨'
        magnet_msg = f'<b>Need {magnets["magnet_shortage"]} more strips</b> to magnetize all demand'

    st.markdown(
        f'<div style="background:{magnet_bg}; padding:14px 18px; border-radius:10px; '
        f'border-left:4px solid {magnet_border}; font-size:0.88rem;">'
        f'<div style="font-weight:700; margin-bottom:6px;">{magnet_icon} {magnet_msg}</div>'
        f'<div>'
        f'🎗️ Strips available: <b>{magnets["strips_available"]}</b> | '
        f'🎯 Strips needed for demand: <b>{magnets["strips_needed_for_demand"]}</b>'
        f'</div>'
        f'<div style="font-size:0.78rem; opacity:0.8; margin-top:4px;">'
        f'✂️ Calculated with optimal cutting (5/7 formula)'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Store-by-store breakdown
    st.markdown("---")
    render_section_title("🏪 Store-by-Store Coverage")

    # Sort options
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption(
            "💡 Stores are allocated supply in priority order. "
            "Stores with closer launch dates get supplied first."
        )
    with col2:
        sort_by = st.selectbox(
            "Priority order",
            ['launch_date', 'need_high', 'need_low'],
            format_func=lambda x: {
                'launch_date': '📅 By Launch Date (closest first)',
                'need_high': '📦 By Need (largest first)',
                'need_low': '📦 By Need (smallest first)',
            }[x],
            key='coverage_sort',
            label_visibility="collapsed"
        )

    # Allocate
    allocated = allocate_supply_to_stores(coverage, sort_by=sort_by)

    # Filter
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input(
            "🔍 Search store",
            placeholder="Filter by name or location...",
            key='coverage_search',
            label_visibility="collapsed"
        )
    with col_filter:
        status_f = st.selectbox(
            "Status filter",
            ['All', '✅ Covered only', '⚠️ Partial only', '❌ Shortage only'],
            key='coverage_status_filter',
            label_visibility="collapsed"
        )

    # Apply filters
    filtered = list(allocated)
    if 'Covered' in status_f:
        filtered = [s for s in filtered if s['status'] == 'covered']
    elif 'Partial' in status_f:
        filtered = [s for s in filtered if s['status'] == 'partial']
    elif 'Shortage' in status_f:
        filtered = [s for s in filtered if s['status'] == 'shortage']

    if search and search.strip():
        s = search.strip().lower()
        filtered = [
            st_r for st_r in filtered
            if s in str(st_r.get('name', '')).lower()
            or s in str(st_r.get('location', '')).lower()
        ]

    # Counts
    covered_n = sum(1 for s in allocated if s['status'] == 'covered')
    partial_n = sum(1 for s in allocated if s['status'] == 'partial')
    shortage_n = sum(1 for s in allocated if s['status'] == 'shortage')

    st.caption(
        f"📊 Total: ✅ **{covered_n}** covered | ⚠️ **{partial_n}** partial | "
        f"❌ **{shortage_n}** shortage &nbsp;|&nbsp; "
        f"Showing **{len(filtered)}** of **{len(allocated)}**"
    )

    if not filtered:
        st.info("🔍 No stores match your filter.")
        return

    # Render cards
    for store_result in filtered:
        render_store_coverage_card(store_result)

    # Export button
    st.markdown("---")
    col_info, col_export = st.columns([2, 1])
    with col_info:
        st.caption("📥 Export the coverage analysis to CSV")
    with col_export:
        export_rows = []
        for s in filtered:
            export_rows.append({
                'Store Name': s['name'],
                'Location': s['location'],
                'Status': s['status'].title(),
                'Launched': 'Yes' if s['is_launched'] else 'No',
                'Days Left': s['days_left'] if s['days_left'] is not None else '',
                'Need 30D': s['need_30d'],
                'Allocated 30D': s['alloc_30d'],
                'Short 30D': s['short_30d'],
                'Need 40D': s['need_40d'],
                'Allocated 40D': s['alloc_40d'],
                'Short 40D': s['short_40d'],
                'Need 60D': s['need_60d'],
                'Allocated 60D': s['alloc_60d'],
                'Short 60D': s['short_60d'],
                'Total Short': s['total_short'],
            })
        export_df = pd.DataFrame(export_rows)
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        st.download_button(
            label=f"📥 Export CSV ({len(filtered)} rows)",
            data=csv_buffer.getvalue(),
            file_name=f"coverage_analysis_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
            key='export_coverage_csv'
        )


# ==================== TAB 4: HISTORY ====================

def render_history_tab():
    render_section_title("📜 Stock Movement History")

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state['confirm_clear_history'] = True
            st.rerun()

    if st.session_state.get('confirm_clear_history'):
        st.warning("⚠️ This will delete ALL stock history. This cannot be undone!")
        cc1, cc2 = st.columns(2)
        if cc1.button("✅ Yes, clear all", use_container_width=True, type="primary"):
            if clear_stock_history():
                st.success("✅ History cleared")
                st.session_state.pop('confirm_clear_history', None)
                st.rerun()
            else:
                st.error("❌ Failed to clear history")
        if cc2.button("❌ Cancel", use_container_width=True):
            st.session_state.pop('confirm_clear_history', None)
            st.rerun()

    history = get_stock_history(limit=100)

    if history.empty:
        st.info("📭 No stock history yet")
        return

    display = history.copy()
    if 'date' in display.columns:
        display['date'] = pd.to_datetime(display['date']).dt.strftime('%d %b %Y %H:%M')

    rename_map = {
        'date': 'Date',
        'divider_type': 'Type',
        'old_qty': 'Before',
        'new_qty': 'After',
        'change': 'Change',
        'note': 'Notes'
    }
    display = display.rename(columns={k: v for k, v in rename_map.items() if k in display.columns})

    cols_order = ['Date', 'Type', 'Before', 'After', 'Change', 'Notes']
    available_cols = [c for c in cols_order if c in display.columns]
    display = display[available_cols]

    st.dataframe(display, use_container_width=True, hide_index=True)


# ==================== MAIN RENDER ====================

def render():
    st.markdown("# 📦 Vendor Stock Management")
    st.caption("Manage stock levels, purchase orders, coverage analysis, and history")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Current Stock",
        "📋 Purchase Orders",
        "🎯 Coverage Analysis",
        "📜 History"
    ])

    with tab1:
        render_current_stock_tab()

    with tab2:
        render_purchase_orders_tab()

    with tab3:
        render_coverage_analysis_tab()

    with tab4:
        render_history_tab()
