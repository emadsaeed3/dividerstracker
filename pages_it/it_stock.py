"""
IT Equipment Stock Management
"""
import streamlit as st
import pandas as pd
from database_it import (
    IT_EQUIPMENT_TYPES, IT_ICONS,
    get_it_stock_dict, update_it_stock, get_it_stock_history,
    get_total_requirements
)
from database import get_threshold
from components import render_it_stock_card, render_section_title


def render():
    """Render the IT Stock page"""
    st.markdown("# 💻 IT Equipment Stock")
    st.caption("Manage vendor stock of all IT equipment")

    threshold = get_threshold()
    stocks = get_it_stock_dict()
    requirements = get_total_requirements()

    # Summary stats
    total_stock = sum(stocks.values())
    total_required = sum(requirements.values())
    out_of_stock = sum(1 for qty in stocks.values() if qty == 0)
    low_stock = sum(1 for qty in stocks.values() if 0 < qty < threshold)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card card-stores">
            <i class="bi bi-box-seam-fill icon-bg"></i>
            <div class="stat-label">Total Stock</div>
            <div class="stat-value">{total_stock}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card card-30d">
            <i class="bi bi-clipboard-check icon-bg"></i>
            <div class="stat-label">Total Required</div>
            <div class="stat-value">{total_required}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card card-40d">
            <i class="bi bi-exclamation-triangle-fill icon-bg"></i>
            <div class="stat-label">Low Stock Items</div>
            <div class="stat-value">{low_stock}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card" style="border-left: 5px solid #e74c3c;">
            <i class="bi bi-x-circle-fill icon-bg" style="color:#e74c3c;"></i>
            <div class="stat-label">Out of Stock</div>
            <div class="stat-value" style="color:#e74c3c;">{out_of_stock}</div>
        </div>
        """, unsafe_allow_html=True)

    # Current stock cards
    render_section_title("📦 Current Equipment Stock")
    
    cols = st.columns(3)
    for idx, item in enumerate(IT_EQUIPMENT_TYPES):
        with cols[idx % 3]:
            render_it_stock_card(
                item,
                stocks.get(item, 0),
                threshold,
                icon=IT_ICONS.get(item, 'bi-cpu')
            )

    # Stock vs Required comparison table
    render_section_title("📊 Stock vs Required Overview")
    
    comparison_rows = []
    for item in IT_EQUIPMENT_TYPES:
        stock = stocks.get(item, 0)
        req = requirements.get(item, 0)
        gap = max(0, req - stock)
        status = "✅ Sufficient" if stock >= req else ("⚠️ Low" if stock > 0 else "❌ Out")
        comparison_rows.append({
            'Equipment': item,
            'In Stock': stock,
            'Total Required': req,
            'Shortage': gap,
            'Status': status
        })
    
    comp_df = pd.DataFrame(comparison_rows)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

 # Update stock form
    render_section_title("🔄 Update Stock")
    
    # Equipment selector OUTSIDE form (so current_val updates dynamically)
    item = st.selectbox("Equipment Type", IT_EQUIPMENT_TYPES, key="it_stock_item_select")
    current_val = int(stocks.get(item, 0)) if item else 0
    
    st.info(f"ℹ️ Current stock for **{item}**: **{current_val}**")
    
    with st.form("update_it_stock", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        c1.markdown(f"**Equipment:** {item}")
        c1.markdown(f"**Current Qty:** {current_val}")
        
        new_qty = c2.number_input(
            "New Quantity",
            min_value=0,
            value=current_val,
            step=1
            # ← شيلنا الـ key عشان clear_on_submit يشتغل صح
        )
        note = st.text_input("Note (optional)")

        submitted = st.form_submit_button("🔄 Update Stock", use_container_width=True)
        
        if submitted:
            new_qty_int = int(new_qty)
            
            # Debug info
            st.write(f"🔧 Debug: Updating **{item}** from **{current_val}** to **{new_qty_int}**")
            
            if new_qty_int == current_val:
                st.warning("⚠️ New quantity is the same as current. No change made.")
            else:
                try:
                    result = update_it_stock(item, new_qty_int, note or 'Manual update')
                    
                    # Verify the update
                    fresh_stocks = get_it_stock_dict()
                    actual = fresh_stocks.get(item, 0)
                    
                    if actual == new_qty_int:
                        st.success(f"✅ {item} stock updated: {current_val} → {new_qty_int}")
                        st.info(f"🔍 Verification: Database now shows **{actual}**")
                    else:
                        st.error(f"❌ Update FAILED! Expected {new_qty_int}, but database shows {actual}")
                        st.warning("⚠️ Check `update_it_stock` function in database_it.py")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # Stock history
    render_section_title("📜 Stock History")
    hist_df = get_it_stock_history(limit=20)

    if not hist_df.empty:
        display_cols = ['date', 'equipment_type', 'old_qty', 'new_qty', 'change', 'note']
        available = [c for c in display_cols if c in hist_df.columns]
        hist_df = hist_df[available].copy()
        
        rename_map = {
            'date': 'Date',
            'equipment_type': 'Equipment',
            'old_qty': 'Old Qty',
            'new_qty': 'New Qty',
            'change': 'Change',
            'note': 'Note'
        }
        hist_df = hist_df.rename(columns=rename_map)
        
        if 'Date' in hist_df.columns:
            hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No history yet.")
