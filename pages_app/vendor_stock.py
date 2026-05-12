"""
Vendor Stock Management with Tabs:
- Current Stock
- Purchase Orders
- History
"""
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


# ==================== MAGNET CALCULATION HELPERS ====================

def calculate_strips_needed(total_dividers):
    """
    Optimal strips calculation with cutting strategy.
    
    Logic:
    - 1 strip = 3 squares + 1 rectangle
    - 1 square can be cut into 2 rectangles
    - 1 divider = 2 squares + 1 rectangle
    
    Formula: strips = ceil(5 * dividers / 7)
    Saves ~28% vs naive 1:1 method.
    """
    if total_dividers <= 0:
        return 0
    return math.ceil(5 * total_dividers / 7)


def render_magnet_warning(q30, q40, q60, context_label="this PO"):
    """Show magnet availability warning for a PO quantity"""
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

    # Magnet info on card
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

            # 🧲 Magnet warning (live)
            if q30 + q40 + q60 > 0:
                render_magnet_warning(q30, q40, q60, "This new PO")

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


# ==================== TAB 3: HISTORY ====================

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
    st.caption("Manage stock levels, purchase orders, and movement history")

    tab1, tab2, tab3 = st.tabs(["📊 Current Stock", "📋 Purchase Orders", "📜 History"])

    with tab1:
        render_current_stock_tab()

    with tab2:
        render_purchase_orders_tab()

    with tab3:
        render_history_tab()
