import streamlit as st
from supabase import create_client
from datetime import datetime, date
import pandas as pd
from io import BytesIO
import openpyxl

# Page config
st.set_page_config(page_title="Dividers Tracker", page_icon="📦", layout="wide")

# Supabase connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

LOW_STOCK_THRESHOLD = 50


def get_threshold():
    res = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
    if res.data:
        return int(res.data[0]['value'])
    return LOW_STOCK_THRESHOLD


def set_threshold(val):
    existing = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
    if existing.data:
        supabase.table('settings').update({'value': str(val)}).eq('key', 'low_stock_threshold').execute()
    else:
        supabase.table('settings').insert({'key': 'low_stock_threshold', 'value': str(val)}).execute()


def get_stocks():
    res = supabase.table('vendor_stock').select('*').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['divider_type', 'quantity'])


def get_stores():
    res = supabase.table('stores').select('*').order('name').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


def get_shipments():
    res = supabase.table('shipments').select('*, stores(name)').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df['store_name'] = df['stores'].apply(lambda x: x['name'] if x else 'Unknown')
    return df


def calculate_alerts():
    alerts = []
    threshold = get_threshold()
    stocks_df = get_stocks()
    stores_df = get_stores()
    shipments_df = get_shipments()

    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}

    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = stores_df[col].sum() if not stores_df.empty else 0
        shipped = shipments_df[ship_col].sum() if not shipments_df.empty else 0
        remaining_need = max(0, required - shipped)

        if stock < remaining_need:
            shortage = remaining_need - stock
            alerts.append(('danger', f'🚨 Critical! {dtype} shortage: Need to order {shortage} more units from vendor'))
        elif stock < threshold:
            alerts.append(('warning', f'⚠️ Low stock alert: {dtype} has only {stock} units left. Consider contacting vendor'))

    return alerts


# Sidebar navigation
st.sidebar.title("📦 Dividers Tracker")
page = st.sidebar.radio("Navigate", ["Dashboard", "Stores", "Vendor Stock", "Shipments", "Reports"])

# ============ DASHBOARD ============
if page == "Dashboard":
    st.title("📊 Dashboard")

    alerts = calculate_alerts()
    if alerts:
        for level, msg in alerts:
            if level == 'danger':
                st.error(msg)
            else:
                st.warning(msg)

    stocks_df = get_stocks()
    stores_df = get_stores()
    shipments_df = get_shipments()

    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}

    st.subheader("📦 Vendor Stock")
    c1, c2, c3 = st.columns(3)
    c1.metric("30D Stock", stocks.get('30D', 0))
    c2.metric("40D Stock", stocks.get('40D', 0))
    c3.metric("60D Stock", stocks.get('60D', 0))

    st.subheader("🎯 Required vs Shipped")
    for dtype in ['30D', '40D', '60D']:
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = stores_df[col].sum() if not stores_df.empty else 0
        shipped = shipments_df[ship_col].sum() if not shipments_df.empty else 0
        gap = required - shipped

        c1, c2, c3 = st.columns(3)
        c1.metric(f"{dtype} Required", int(required))
        c2.metric(f"{dtype} Shipped", int(shipped))
        c3.metric(f"{dtype} Gap", int(gap), delta=f"{-gap}" if gap > 0 else "✓ Complete")

    st.subheader("📈 Summary")
    c1, c2 = st.columns(2)
    c1.metric("Total Stores", len(stores_df))
    c2.metric("Total Shipments", len(shipments_df))


# ============ STORES ============
elif page == "Stores":
    st.title("🏪 Stores Management")

    with st.expander("➕ Add New Store", expanded=False):
        with st.form("add_store"):
            name = st.text_input("Store Name *")
            location = st.text_input("Location")
            c1, c2, c3 = st.columns(3)
            r30 = c1.number_input("Required 30D", min_value=0, value=0)
            r40 = c2.number_input("Required 40D", min_value=0, value=0)
            r60 = c3.number_input("Required 60D", min_value=0, value=0)
            submitted = st.form_submit_button("Add Store")
            if submitted and name:
                supabase.table('stores').insert({
                    'name': name, 'location': location,
                    'required_30d': r30, 'required_40d': r40, 'required_60d': r60
                }).execute()
                st.success(f"✅ Store '{name}' added!")
                st.rerun()

    st.subheader("All Stores")
    stores_df = get_stores()
    if stores_df.empty:
        st.info("No stores added yet.")
    else:
        for _, store in stores_df.iterrows():
            with st.expander(f"🏪 {store['name']} - {store['location'] or 'N/A'}"):
                with st.form(f"edit_{store['id']}"):
                    name = st.text_input("Name", value=store['name'], key=f"n_{store['id']}")
                    location = st.text_input("Location", value=store['location'] or '', key=f"l_{store['id']}")
                    c1, c2, c3 = st.columns(3)
                    r30 = c1.number_input("Required 30D", min_value=0, value=int(store['required_30d']), key=f"r30_{store['id']}")
                    r40 = c2.number_input("Required 40D", min_value=0, value=int(store['required_40d']), key=f"r40_{store['id']}")
                    r60 = c3.number_input("Required 60D", min_value=0, value=int(store['required_60d']), key=f"r60_{store['id']}")
                    c1, c2 = st.columns(2)
                    update = c1.form_submit_button("💾 Update")
                    delete = c2.form_submit_button("🗑️ Delete")
                    if update:
                        supabase.table('stores').update({
                            'name': name, 'location': location,
                            'required_30d': r30, 'required_40d': r40, 'required_60d': r60
                        }).eq('id', store['id']).execute()
                        st.success("Updated!")
                        st.rerun()
                    if delete:
                        supabase.table('stores').delete().eq('id', store['id']).execute()
                        st.warning("Deleted!")
                        st.rerun()


# ============ VENDOR STOCK ============
elif page == "Vendor Stock":
    st.title("📦 Vendor Stock Management")

    threshold = get_threshold()
    with st.expander("⚙️ Settings"):
        new_threshold = st.number_input("Low Stock Threshold", min_value=0, value=threshold)
        if st.button("Update Threshold"):
            set_threshold(new_threshold)
            st.success(f"Threshold updated to {new_threshold}")
            st.rerun()

    st.subheader("Current Stock")
    stocks_df = get_stocks()
    stocks = dict(zip(stocks_df['divider_type'], stocks_df['quantity'])) if not stocks_df.empty else {}
    c1, c2, c3 = st.columns(3)
    c1.metric("30D", stocks.get('30D', 0))
    c2.metric("40D", stocks.get('40D', 0))
    c3.metric("60D", stocks.get('60D', 0))

    st.subheader("🔄 Update Stock")
    with st.form("update_stock"):
        dtype = st.selectbox("Divider Type", ['30D', '40D', '60D'])
        qty = st.number_input("New Quantity", min_value=0, value=0)
        note = st.text_input("Note (optional)")
        if st.form_submit_button("Update Stock"):
            res = supabase.table('vendor_stock').select('*').eq('divider_type', dtype).execute()
            old_qty = res.data[0]['quantity'] if res.data else 0
            supabase.table('vendor_stock').update({
                'quantity': qty,
                'last_updated': datetime.utcnow().isoformat()
            }).eq('divider_type', dtype).execute()
            supabase.table('stock_history').insert({
                'divider_type': dtype, 'old_qty': old_qty, 'new_qty': qty,
                'change': qty - old_qty, 'note': note
            }).execute()
            st.success(f"{dtype} stock updated!")
            st.rerun()

    st.subheader("📜 Stock History (Last 20)")
    res = supabase.table('stock_history').select('*').order('date', desc=True).limit(20).execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
    else:
        st.info("No history yet.")


# ============ SHIPMENTS ============
elif page == "Shipments":
    st.title("🚚 Shipments")

    stores_df = get_stores()
    if stores_df.empty:
        st.warning("⚠️ Add a store first before recording shipments.")
    else:
        with st.expander("➕ Record New Shipment", expanded=False):
            with st.form("add_shipment"):
                store_options = {f"{row['name']} ({row['location'] or 'N/A'})": row['id'] for _, row in stores_df.iterrows()}
                selected = st.selectbox("Store", list(store_options.keys()))
                ship_date = st.date_input("Date", value=date.today())
                c1, c2, c3 = st.columns(3)
                q30 = c1.number_input("Qty 30D", min_value=0, value=0)
                q40 = c2.number_input("Qty 40D", min_value=0, value=0)
                q60 = c3.number_input("Qty 60D", min_value=0, value=0)
                notes = st.text_area("Notes")
                if st.form_submit_button("Record Shipment"):
                    store_id = store_options[selected]
                    supabase.table('shipments').insert({
                        'store_id': store_id, 'date': ship_date.isoformat(),
                        'qty_30d': q30, 'qty_40d': q40, 'qty_60d': q60, 'notes': notes
                    }).execute()
                    # Update stock
                    for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
                        if qty > 0:
                            res = supabase.table('vendor_stock').select('*').eq('divider_type', dtype).execute()
                            if res.data:
                                old_qty = res.data[0]['quantity']
                                new_qty = max(0, old_qty - qty)
                                supabase.table('vendor_stock').update({
                                    'quantity': new_qty,
                                    'last_updated': datetime.utcnow().isoformat()
                                }).eq('divider_type', dtype).execute()
                                supabase.table('stock_history').insert({
                                    'divider_type': dtype, 'old_qty': old_qty, 'new_qty': new_qty,
                                    'change': -qty, 'note': f'Shipped to store #{store_id}'
                                }).execute()
                    st.success("✅ Shipment recorded!")
                    st.rerun()

    st.subheader("All Shipments")
    shipments_df = get_shipments()
    if shipments_df.empty:
        st.info("No shipments yet.")
    else:
        display_df = shipments_df[['id', 'store_name', 'date', 'qty_30d', 'qty_40d', 'qty_60d', 'notes']].copy()
        display_df.columns = ['ID', 'Store', 'Date', '30D', '40D', '60D', 'Notes']
        st.dataframe(display_df, use_container_width=True)

        del_id = st.number_input("Shipment ID to Delete", min_value=0, value=0)
        if st.button("🗑️ Delete Shipment"):
            if del_id > 0:
                supabase.table('shipments').delete().eq('id', del_id).execute()
                st.warning(f"Shipment #{del_id} deleted.")
                st.rerun()


# ============ REPORTS ============
elif page == "Reports":
    st.title("📊 Reports")

    stores_df = get_stores()
    shipments_df = get_shipments()

    if stores_df.empty:
        st.info("No data to display.")
    else:
        report_rows = []
        for _, store in stores_df.iterrows():
            store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()
            s30 = store_ships['qty_30d'].sum() if not store_ships.empty else 0
            s40 = store_ships['qty_40d'].sum() if not store_ships.empty else 0
            s60 = store_ships['qty_60d'].sum() if not store_ships.empty else 0
            report_rows.append({
                'Store': store['name'],
                'Location': store['location'] or '',
                'Required 30D': store['required_30d'],
                'Shipped 30D': int(s30),
                'Gap 30D': store['required_30d'] - int(s30),
                'Required 40D': store['required_40d'],
                'Shipped 40D': int(s40),
                'Gap 40D': store['required_40d'] - int(s40),
                'Required 60D': store['required_60d'],
                'Shipped 60D': int(s60),
                'Gap 60D': store['required_60d'] - int(s60),
            })
        report_df = pd.DataFrame(report_rows)
        st.dataframe(report_df, use_container_width=True)

        output = BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Stores Report"
        ws.append(list(report_df.columns))
        for _, row in report_df.iterrows():
            ws.append(list(row))
        wb.save(output)
        output.seek(0)
        st.download_button(
            label="📥 Download Excel Report",
            data=output,
            file_name=f"dividers_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
