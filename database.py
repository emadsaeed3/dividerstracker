```python
"""
Database module - All Supabase interactions
"""
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd


# ==================== CONNECTION ====================

@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_client():
    """Get Supabase client instance"""
    return init_supabase()


# ==================== SETTINGS ====================

DEFAULT_THRESHOLD = 50


def get_threshold():
    """Get low stock threshold from settings"""
    try:
        supabase = get_client()
        res = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
        if res.data:
            return int(res.data[0]['value'])
    except Exception:
        pass
    return DEFAULT_THRESHOLD


def set_threshold(val):
    """Update low stock threshold"""
    supabase = get_client()
    existing = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
    if existing.data:
        supabase.table('settings').update({'value': str(val)}).eq('key', 'low_stock_threshold').execute()
    else:
        supabase.table('settings').insert({'key': 'low_stock_threshold', 'value': str(val)}).execute()


# ==================== VENDOR STOCK ====================

def get_stocks():
    """Get all vendor stock as DataFrame"""
    supabase = get_client()
    res = supabase.table('vendor_stock').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=['divider_type', 'quantity'])


def get_stocks_dict():
    """Get vendor stock as dictionary {type: quantity}"""
    df = get_stocks()
    if df.empty:
        return {}
    return dict(zip(df['divider_type'], df['quantity']))


def update_stock(divider_type, new_qty, note=''):
    """Update vendor stock quantity and log history"""
    supabase = get_client()
    
    # Get old quantity
    res = supabase.table('vendor_stock').select('*').eq('divider_type', divider_type).execute()
    old_qty = res.data[0]['quantity'] if res.data else 0
    
    # Update stock
    supabase.table('vendor_stock').update({
        'quantity': new_qty,
        'last_updated': datetime.utcnow().isoformat()
    }).eq('divider_type', divider_type).execute()
    
    # Log history
    supabase.table('stock_history').insert({
        'divider_type': divider_type,
        'old_qty': old_qty,
        'new_qty': new_qty,
        'change': new_qty - old_qty,
        'note': note
    }).execute()


def deduct_stock(divider_type, qty, note=''):
    """Deduct quantity from stock (used in shipments)"""
    supabase = get_client()
    res = supabase.table('vendor_stock').select('*').eq('divider_type', divider_type).execute()
    
    if res.data:
        old_qty = res.data[0]['quantity']
        new_qty = max(0, old_qty - qty)
        
        supabase.table('vendor_stock').update({
            'quantity': new_qty,
            'last_updated': datetime.utcnow().isoformat()
        }).eq('divider_type', divider_type).execute()
        
        supabase.table('stock_history').insert({
            'divider_type': divider_type,
            'old_qty': old_qty,
            'new_qty': new_qty,
            'change': -qty,
            'note': note
        }).execute()


def get_stock_history(limit=20):
    """Get recent stock history"""
    supabase = get_client()
    res = supabase.table('stock_history').select('*').order('date', desc=True).limit(limit).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


# ==================== STORES ====================

def get_stores():
    """Get all stores"""
    supabase = get_client()
    res = supabase.table('stores').select('*').order('name').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def add_store(name, location, r30, r40, r60):
    """Add a new store"""
    supabase = get_client()
    supabase.table('stores').insert({
        'name': name,
        'location': location,
        'required_30d': r30,
        'required_40d': r40,
        'required_60d': r60
    }).execute()


def update_store(store_id, name, location, r30, r40, r60):
    """Update an existing store"""
    supabase = get_client()
    supabase.table('stores').update({
        'name': name,
        'location': location,
        'required_30d': r30,
        'required_40d': r40,
        'required_60d': r60
    }).eq('id', store_id).execute()


def delete_store(store_id):
    """Delete a store"""
    supabase = get_client()
    supabase.table('stores').delete().eq('id', store_id).execute()


# ==================== SHIPMENTS ====================

def get_shipments():
    """Get all shipments with store names"""
    supabase = get_client()
    res = supabase.table('shipments').select('*, stores(name)').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    df['store_name'] = df['stores'].apply(lambda x: x['name'] if x else 'Unknown')
    return df


def add_shipment(store_id, ship_date, q30, q40, q60, notes=''):
    """Add a new shipment and deduct from stock"""
    supabase = get_client()
    
    # Insert shipment
    supabase.table('shipments').insert({
        'store_id': store_id,
        'date': ship_date.isoformat(),
        'qty_30d': q30,
        'qty_40d': q40,
        'qty_60d': q60,
        'notes': notes
    }).execute()
    
    # Deduct from stock
    for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
        if qty > 0:
            deduct_stock(dtype, qty, f'Shipped to store #{store_id}')


def delete_shipment(shipment_id):
    """Delete a shipment"""
    supabase = get_client()
    supabase.table('shipments').delete().eq('id', shipment_id).execute()
```
