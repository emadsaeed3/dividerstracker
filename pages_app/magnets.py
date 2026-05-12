"""
Magnets tracking page (with optimal cutting calculation)
"""
import math
import streamlit as st
import pandas as pd
from database import (
    get_magnet_stock, update_magnet_stock,
    get_magnet_status, get_magnet_status_dict,
    apply_magnet_to_dividers, set_dividers_without_magnet,
    get_magnet_history, get_stocks_dict,
    get_pending_pos
)
from components import render_section_title, render_magnet_status_card


# ==================== CALCULATION HELPERS ====================

def calculate_strips_needed(total_dividers):
    """
    Optimal strips calculation with cutting strategy.
    1 strip = 3 squares + 1 rectangle
    1 square → 2 rectangles (when cut)
    1 divider = 2 squares + 1 rectangle
    Formula: strips = ceil(5 * dividers / 7)
    """
    if total_dividers <= 0:
        return 0
    return math.ceil(5 * total_dividers / 7)


def calculate_magnet_breakdown(total_dividers, strips_used):
    """Detailed breakdown of magnet usage"""
    squares_produced = strips_used * 3
    rectangles_from_strips = strips_used * 1

    squares_for_dividers = total_dividers * 2
    rectangles_for_dividers = total_dividers * 1

    squares_surplus = max(0, squares_produced - squares_for_dividers)
    rectangles_from_cutting = squares_surplus * 2

    total_rectangles_available = rectangles_from_strips + rectangles_from_cutting
    rectangles_surplus = total_rectangles_available - rectangles_for_dividers

    return {
        'strips_used': strips_used,
        'squares_produced': squares_produced,
        'rectangles_from_strips': rectangles_from_strips,
        'squares_used_directly': squares_for_dividers,
        'squares_cut_to_rectangles': squares_surplus,
        'rectangles_from_cutting': rectangles_from_cutting,
        'rectangles_total_available': total_rectangles_available,
        'rectangles_used': rectangles_for_dividers,
        'rectangles_surplus': rectangles_surplus,
    }


# ==================== UI COMPONENTS ====================

def render_strips_card(strips_qty):
    """Render the magnet strips stock card"""
    possible_dividers = math.floor(strips_qty * 7 / 5) if strips_qty > 0 else 0

    st.markdown(f"""
    <div class="stat-card" style="border-left: 5px solid #16a085;">
        <i class="bi bi-layout-three-columns icon-bg" style="color:#16a085;"></i>
        <div class="stat-label" style="color:#16a085;">🎗️ Magnet Strips at Vendor</div>
        <div class="stat-value" style="color:#16a085;">{strips_qty}</div>
        <div style="margin-top:10px; font-size:0.85rem; opacity:0.8;">
            ✂️ Can produce up to <b>~{possible_dividers}</b> dividers (with optimal cutting)
        </div>
        <div style="margin-top:6px; font-size:0.75rem; opacity:0.7;">
            💡 1 strip = 3 squares + 1 rect | 1 square → 2 rects | 1 divider = 2 squares + 1 rect
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_po_magnet_calculator():
    """Calculate magnet needs based on pending POs (with optimal cutting)"""
    render_section_title("🧮 PO Magnet Calculator")

    st.markdown(
        '<div style="background: rgba(155, 89, 182, 0.08); padding: 10px 14px; border-radius: 8px; '
        'border-left: 3px solid #9b59b6; margin-bottom: 14px; font-size:0.85rem;">'
        '✂️ <b>Smart Calculation:</b> Excess squares are cut into rectangles '
        '(1 square → 2 rectangles) to minimize waste.<br>'
        '<span style="opacity:0.8; font-size:0.78rem;">'
        'Formula: <code>strips = ⌈5 × dividers / 7⌉</code> '
        '(saves ~28% vs naive 1:1)'
        '</span>'
        '</div>',
        unsafe_allow_html=True
    )

    pending_pos = get_pending_pos()
    strips_available = get_magnet_stock()

    if pending_pos.empty:
        st.markdown(
            '<div style="background: rgba(52,152,219,0.1); padding: 14px 18px; border-radius: 10px; '
            'border-left: 4px solid #3498db; margin-bottom: 16px;">'
            '📭 <b>No pending POs.</b> All purchase orders are either received or cancelled.'
            '</div>',
            unsafe_allow_html=True
        )
        return

    total_30d = int(pending_pos['qty_30d'].sum())
    total_40d = int(pending_pos['qty_40d'].sum())
    total_60d = int(pending_pos['qty_60d'].sum())
    total_dividers = total_30d + total_40d + total_60d
    strips_needed = calculate_strips_needed(total_dividers)
    strips_naive = total_dividers
    savings = strips_naive - strips_needed

    if strips_needed == 0:
        st.info("📭 Pending POs have no quantities yet.")
        return

    if strips_needed <= strips_available:
        status_color = '#27ae60'
        status_bg = 'rgba(39,174,96,0.1)'
        status_icon = '✅'
        status_text = 'Sufficient stock'
        action_text = f'You have enough strips. Surplus: <b>{strips_available - strips_needed}</b>'
    else:
        shortage = strips_needed - strips_available
        status_color = '#e74c3c'
        status_bg = 'rgba(231,76,60,0.1)'
        status_icon = '🚨'
        status_text = 'Shortage detected'
        action_text = f'⚠️ <b>You need to order {shortage} more strips</b> to cover all pending POs!'

    st.markdown(
        f'<div style="background: {status_bg}; padding: 18px 22px; border-radius: 12px; '
        f'border-left: 5px solid {status_color}; margin-bottom: 16px;">'
        f'<div style="font-size:1.1rem; font-weight:700; margin-bottom:10px;">'
        f'{status_icon} {status_text}'
        f'</div>'
        f'<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:12px;">'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">Pending POs</div>'
        f'<div style="font-size:1.4rem; font-weight:700;">{len(pending_pos)}</div></div>'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">Total Dividers</div>'
        f'<div style="font-size:1.4rem; font-weight:700;">{total_dividers}</div></div>'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">Strips Needed ✂️</div>'
        f'<div style="font-size:1.4rem; font-weight:700; color:#e67e22;">{strips_needed}</div></div>'
        f'<div><div style="opacity:0.7; font-size:0.78rem;">Strips Available</div>'
        f'<div style="font-size:1.4rem; font-weight:700; color:#16a085;">{strips_available}</div></div>'
        f'</div>'
        f'<div style="padding-top:10px; border-top:1px solid rgba(255,255,255,0.1); font-size:0.92rem;">'
        f'{action_text}'
        f'</div>'
        f'<div style="margin-top:8px; padding-top:8px; font-size:0.82rem; opacity:0.85;">'
        f'💰 <b>Savings from optimization:</b> {savings} strips saved '
        f'(vs naive 1:1 = {strips_naive} strips)'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    breakdown = calculate_magnet_breakdown(total_dividers, strips_needed)

    with st.expander("🔬 View Detailed Magnet Breakdown", expanded=False):
        st.markdown(f"""
        **📦 From {breakdown['strips_used']} strips you'll get:**
        - 🟦 Squares produced: **{breakdown['squares_produced']}**
        - 🟫 Rectangles produced: **{breakdown['rectangles_from_strips']}**
        
        **🎯 For {total_dividers} dividers you need:**
        - 🟦 Squares (used directly): **{breakdown['squares_used_directly']}**
        - 🟫 Rectangles needed: **{total_dividers}**
        
        **✂️ Cutting strategy:**
        - 🟦 Surplus squares to cut: **{breakdown['squares_cut_to_rectangles']}**
        - 🟫 Extra rectangles from cutting: **{breakdown['rectangles_from_cutting']}**
        - 🟫 Total rectangles available: **{breakdown['rectangles_total_available']}**
        - 🟫 Rectangles surplus after use: **{breakdown['rectangles_surplus']}**
        """)

    st.markdown("**📊 Breakdown by Divider Type:**")
    c1, c2, c3 = st.columns(3)

    def type_card(col, label, qty, color, emoji):
        strips_for_type = calculate_strips_needed(qty)
        with col:
            st.markdown(
                f'<div style="background:{color}15; padding:12px 14px; border-radius:10px; '
                f'border-left:4px solid {color};">'
                f'<div style="font-size:0.8rem; opacity:0.8;">{emoji} {label}</div>'
                f'<div style="font-size:1.5rem; font-weight:700; color:{color};">{qty}</div>'
                f'<div style="font-size:0.75rem; opacity:0.7;">≈ {strips_for_type} strips</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    type_card(c1, '30D Dividers', total_30d, '#3498db', '🔵')
    type_card(c2, '40D Dividers', total_40d, '#e67e22', '🟠')
    type_card(c3, '60D Dividers', total_60d, '#9b59b6', '🟣')

    with st.expander(f"📋 View {len(pending_pos)} Pending PO(s) Breakdown", expanded=False):
        breakdown_df = pending_pos[['po_number', 'vendor_name', 'status',
                                     'qty_30d', 'qty_40d', 'qty_60d']].copy()
        breakdown_df['Total Dividers'] = breakdown_df['qty_30d'] + breakdown_df['qty_40d'] + breakdown_df['qty_60d']
        breakdown_df['Strips Needed ✂️'] = breakdown_df['Total Dividers'].apply(calculate_strips_needed)
        breakdown_df = breakdown_df.rename(columns={
            'po_number': 'PO #',
            'vendor_name': 'Vendor',
            'status': 'Status',
            'qty_30d': '30D',
            'qty_40d': '40D',
            'qty_60d': '60D'
        })
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)


def render_quick_calculator():
    """Quick what-if calculator for any quantity"""
    render_section_title("⚡ Quick Calculator")

    with st.expander("🧮 **Calculate strips for custom quantity**", expanded=False):
        c1, c2, c3 = st.columns(3)
        q30 = c1.number_input("🔵 30D Dividers", min_value=0, value=0, step=10, key="qc_30")
        q40 = c2.number_input("🟠 40D Dividers", min_value=0, value=0, step=10, key="qc_40")
        q60 = c3.number_input("🟣 60D Dividers", min_value=0, value=0, step=10, key="qc_60")

        total = q30 + q40 + q60
        if total > 0:
            strips = calculate_strips_needed(total)
            naive = total
            saved = naive - strips
            available = get_magnet_stock()

            if strips <= available:
                bg_color = 'rgba(39,174,96,0.1)'
                border_color = '#27ae60'
                status = f'✅ <b>Sufficient!</b> Surplus: {available - strips} strips'
            else:
                bg_color = 'rgba(231,76,60,0.1)'
                border_color = '#e74c3c'
                status = f'🚨 <b>Need to order {strips - available} more strips</b>'

            st.markdown(
                f'<div style="background:{bg_color}; padding:14px 18px; border-radius:10px; '
                f'border-left:4px solid {border_color}; margin-top:10px;">'
                f'<div style="font-size:1rem; margin-bottom:8px;">'
                f'📦 <b>{total}</b> dividers → 🧲 <b>{strips}</b> strips needed '
                f'<span style="opacity:0.7; font-size:0.85rem;">(saved {saved} strips vs 1:1)</span>'
                f'</div>'
                f'<div style="font-size:0.92rem;">{status}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


def render():
    """Render the Magnets page"""
    st.markdown("# 🧲 Magnets Tracker")

    st.markdown("""
    <div style="background: rgba(52, 152, 219, 0.1); padding: 14px 18px; border-radius: 10px; border-left: 4px solid #3498db; margin-bottom: 20px;">
        <b>📌 How it works:</b><br>
        • Each <b>magnet strip</b> is cut into <b>4 pieces</b>: 3 squares + 1 rectangle<br>
        • Each <b>divider</b> needs: <b>2 squares + 1 rectangle</b><br>
        • <b>✂️ Smart cut:</b> 1 square can be cut into 2 rectangles<br>
        • Optimal formula: <b>strips = ⌈5 × dividers / 7⌉</b> (saves ~28%)
    </div>
    """, unsafe_allow_html=True)

    # Strips stock
    render_section_title("🎗️ Magnet Strips Stock")
    strips_qty = get_magnet_stock()

    c1, c2 = st.columns([2, 1])
    with c1:
        render_strips_card(strips_qty)

    with c2:
        with st.form("update_strips"):
            st.markdown("**🔄 Update Strips Count**")
            new_strips = st.number_input(
                "New Quantity",
                min_value=0,
                value=int(strips_qty)
            )
            note = st.text_input("Note (optional)", key='strips_note')
            if st.form_submit_button("💾 Save"):
                update_magnet_stock(new_strips, note)
                st.success("✅ Updated!")
                st.rerun()

    # 🆕 PO Magnet Calculator
    render_po_magnet_calculator()

    # 🆕 Quick Calculator
    render_quick_calculator()

    # Dividers magnet status
    render_section_title("📊 Dividers Magnet Status")

    stocks = get_stocks_dict()
    magnet_status = get_magnet_status_dict()

    c1, c2, c3 = st.columns(3)
    for idx, dtype in enumerate(['30D', '40D', '60D']):
        status = magnet_status.get(dtype, {'with_magnet': 0, 'without_magnet': 0})
        with [c1, c2, c3][idx]:
            render_magnet_status_card(dtype, status['with_magnet'], status['without_magnet'])

    # Sync warning
    total_magnet_tracked = sum(
        magnet_status.get(t, {}).get('with_magnet', 0) + magnet_status.get(t, {}).get('without_magnet', 0)
        for t in ['30D', '40D', '60D']
    )
    total_vendor_stock = sum(stocks.get(t, 0) for t in ['30D', '40D', '60D'])

    if total_magnet_tracked != total_vendor_stock:
        st.warning(
            f"⚠️ **Mismatch detected:** Tracked dividers = **{total_magnet_tracked}** | "
            f"Vendor stock = **{total_vendor_stock}**. "
            f"Use 'Set Without Magnet' below to sync."
        )

    # Actions
    render_section_title("⚙️ Actions")

    tab1, tab2 = st.tabs(["🧲 Apply Magnet", "⭕ Set Without Magnet"])

    with tab1:
        st.markdown("**Apply magnet to dividers** (uses strips from stock)")
        with st.form("apply_magnet", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dtype = c1.selectbox("Divider Type", ['30D', '40D', '60D'])
            qty = c2.number_input("Quantity to Magnetize", min_value=1, value=1)
            note = st.text_input("Note (optional)", key='apply_note')

            current_without = magnet_status.get(dtype, {}).get('without_magnet', 0)
            st.info(f"💡 Available without magnet for {dtype}: **{current_without}** | Strips in stock: **{strips_qty}**")

            if st.form_submit_button("🧲 Apply Magnet"):
                if qty > current_without:
                    st.error(f"❌ Only {current_without} {dtype} dividers available without magnet!")
                else:
                    success, msg = apply_magnet_to_dividers(dtype, qty, note)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with tab2:
        st.markdown("**Set the total quantity of dividers without magnet** (e.g., when new stock arrives)")
        with st.form("set_without", clear_on_submit=True):
            c1, c2 = st.columns(2)
            dtype = c1.selectbox("Divider Type", ['30D', '40D', '60D'], key='set_dtype')
            current = magnet_status.get(dtype, {}).get('without_magnet', 0) if dtype else 0
            qty = c2.number_input("Total Without Magnet", min_value=0, value=int(current))

            if st.form_submit_button("💾 Set Quantity"):
                set_dividers_without_magnet(dtype, qty)
                st.success(f"✅ {dtype} without-magnet set to {qty}")
                st.rerun()

    # History
    render_section_title("📜 Magnet History")
    hist_df = get_magnet_history(limit=20)

    if not hist_df.empty:
        display_cols = ['date', 'action', 'divider_type', 'qty', 'strips_used', 'note']
        available_cols = [c for c in display_cols if c in hist_df.columns]
        hist_df = hist_df[available_cols].copy()

        rename_map = {
            'date': 'Date',
            'action': 'Action',
            'divider_type': 'Type',
            'qty': 'Qty',
            'strips_used': 'Strips Used',
            'note': 'Note'
        }
        hist_df = hist_df.rename(columns=rename_map)

        if 'Date' in hist_df.columns:
            hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.strftime('%Y-%m-%d %H:%M')

        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No magnet history yet.")
