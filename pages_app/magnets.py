"""
Magnets tracking page
"""
import streamlit as st
import pandas as pd
from database import (
    get_magnet_stock, update_magnet_stock,
    get_magnet_status, get_magnet_status_dict,
    apply_magnet_to_dividers, set_dividers_without_magnet,
    get_magnet_history, get_stocks_dict
)
from components import render_section_title, render_magnet_status_card


def render_strips_card(strips_qty):
    """Render the magnet strips stock card"""
    possible_dividers = strips_qty  # 1 strip = 1 divider (limited by rectangles)

    st.markdown(f"""
    <div class="stat-card" style="border-left: 5px solid #16a085;">
        <i class="bi bi-layout-three-columns icon-bg" style="color:#16a085;"></i>
        <div class="stat-label" style="color:#16a085;">🎗️ Magnet Strips at Vendor</div>
        <div class="stat-value" style="color:#16a085;">{strips_qty}</div>
        <div style="margin-top:10px; font-size:0.85rem; opacity:0.8;">
            📐 Can produce <b>~{possible_dividers}</b> magnetized dividers
        </div>
        <div style="margin-top:6px; font-size:0.75rem; opacity:0.7;">
            💡 1 strip = 3 squares + 1 rectangle | 1 divider = 2 squares + 1 rectangle
        </div>
    </div>
    """, unsafe_allow_html=True)


def render():
    """Render the Magnets page"""
    st.markdown("# 🧲 Magnets Tracker")

    st.markdown("""
    <div style="background: rgba(52, 152, 219, 0.1); padding: 14px 18px; border-radius: 10px; border-left: 4px solid #3498db; margin-bottom: 20px;">
        <b>📌 How it works:</b><br>
        • Each <b>magnet strip</b> is cut into <b>4 pieces</b>: 3 squares + 1 rectangle<br>
        • Each <b>divider</b> needs: <b>2 squares + 1 rectangle</b><br>
        • Limiting factor = rectangles → <b>1 strip ≈ 1 divider</b>
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
