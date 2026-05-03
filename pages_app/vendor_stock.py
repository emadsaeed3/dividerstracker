"""
Vendor Stock management page
"""
import streamlit as st
import pandas as pd
from database import (
    get_threshold, set_threshold, get_stocks_dict,
    update_stock, get_stock_history
)
from components import render_stock_card, render_section_title


def render():
    """Render the Vendor Stock page"""
    st.markdown("# 📦 Vendor Stock Management")
    
    threshold = get_threshold()
    
    # Threshold settings
    with st.expander("⚙️ **Low Stock Threshold Settings**"):
        st.info(f"💡 Current threshold: **{threshold}** units")
        c1, c2 = st.columns([3, 1])
        new_threshold = c1.number_input(
            "Threshold", min_value=0, value=threshold,
            label_visibility="collapsed"
        )
        if c2.button("💾 Save"):
            set_threshold(new_threshold)
            st.success(f"✅ Updated to {new_threshold}")
            st.rerun()
    
    # Current stock
    render_section_title("📊 Current Stock")
    stocks = get_stocks_dict()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        render_stock_card('30D', stocks.get('30D', 0), threshold)
    with c2:
        render_stock_card('40D', stocks.get('40D', 0), threshold)
    with c3:
        render_stock_card('60D', stocks.get('60D', 0), threshold)
    
    # Update stock form
    render_section_title("🔄 Update Stock")
    with st.form("update_stock", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        dtype = c1.selectbox("Type", ['30D', '40D', '60D'])
        qty = c2.number_input("New Quantity", min_value=0, value=0)
        note = st.text_input("Note (optional)")
        
        if st.form_submit_button("🔄 Update"):
            update_stock(dtype, qty, note)
            st.success(f"✅ {dtype} updated!")
            st.rerun()
    
    # Stock history
    render_section_title("📜 Stock History")
    hist_df = get_stock_history(limit=20)
    
    if not hist_df.empty:
        hist_df = hist_df[['date', 'divider_type', 'old_qty', 'new_qty', 'change', 'note']]
        hist_df.columns = ['Date', 'Type', 'Old Qty', 'New Qty', 'Change', 'Note']
        hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No history yet.")
