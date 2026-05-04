"""
Database module - All Supabase interactions
"""
import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta
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

    res = supabase.table('vendor_stock').select('*').eq('divider_type', divider_type).execute()
    old_qty = res.data[0]['quantity'] if res.data else 0

    supabase.table('vendor_stock').update({
        'quantity': new_qty,
        'last_updated': datetime.utcnow().isoformat()
    }).eq('divider_type', divider_type).execute()

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


def add_store(name, location, r30, r40, r60, launch_date=None, transportation_ready=False):
    """Add a new store"""
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
        'required_30d': r30,
        'required_40d': r40,
        'required_60d': r60,
        'transportation_ready': transportation_ready
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    supabase.table('stores').insert(data).execute()


def update_store(store_id, name, location, r30, r40, r60, launch_date=None, transportation_ready=False):
    """Update an existing store"""
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
        'required_30d': r30,
        'required_40d': r40,
        'required_60d': r60,
        'transportation_ready': transportation_ready
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    else:
        data['launch_date'] = None
    supabase.table('stores').update(data).eq('id', store_id).execute()


def delete_store(store_id):
    """Delete a store"""
    supabase = get_client()
    supabase.table('stores').delete().eq('id', store_id).execute()


def get_upcoming_launches(days_ahead=4):
    """Get stores with launch date within the specified days"""
    supabase = get_client()
    today = date.today()
    future = today + timedelta(days=days_ahead)
    res = supabase.table('stores').select('*').not_.is_('launch_date', 'null').execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df['launch_date'] = pd.to_datetime(df['launch_date']).dt.date
    df = df[(df['launch_date'] >= today) & (df['launch_date'] <= future)]
    df['days_left'] = df['launch_date'].apply(lambda d: (d - today).days)
    return df.sort_values('days_left')


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


def add_shipment(store_id, ship_date, q30, q40, q60, notes='', delivery_status='Pending', scheduled_date=None):
    """Add a new shipment and deduct from stock"""
    supabase = get_client()

    data = {
        'store_id': store_id,
        'date': ship_date.isoformat(),
        'qty_30d': q30,
        'qty_40d': q40,
        'qty_60d': q60,
        'notes': notes,
        'delivery_status': delivery_status
    }
    if scheduled_date:
        data['scheduled_date'] = scheduled_date.isoformat() if hasattr(scheduled_date, 'isoformat') else scheduled_date

    supabase.table('shipments').insert(data).execute()

    for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
        if qty > 0:
            deduct_stock(dtype, qty, f'Shipped to store #{store_id}')


def update_shipment_status(shipment_id, delivery_status):
    """Update shipment delivery status"""
    supabase = get_client()
    supabase.table('shipments').update({
        'delivery_status': delivery_status
    }).eq('id', shipment_id).execute()


def delete_shipment(shipment_id):
    """Delete a shipment"""
    supabase = get_client()
    supabase.table('shipments').delete().eq('id', shipment_id).execute()


# ==================== MAGNETS ====================

def get_magnet_stock():
    """Get magnet strips quantity at vendor"""
    supabase = get_client()
    res = supabase.table('magnet_stock').select('*').limit(1).execute()
    if res.data:
        return res.data[0]['strips_qty']
    return 0


def update_magnet_stock(new_qty, note=''):
    """Update magnet strips quantity"""
    supabase = get_client()
    res = supabase.table('magnet_stock').select('*').limit(1).execute()

    if res.data:
        old_qty = res.data[0]['strips_qty']
        record_id = res.data[0]['id']
        supabase.table('magnet_stock').update({
            'strips_qty': new_qty,
            'last_updated': datetime.utcnow().isoformat()
        }).eq('id', record_id).execute()
    else:
        old_qty = 0
        supabase.table('magnet_stock').insert({'strips_qty': new_qty}).execute()

    supabase.table('magnet_history').insert({
        'action': 'Stock Update',
        'strips_used': new_qty - old_qty,
        'note': note
    }).execute()


def get_magnet_status():
    """Get magnet status for all dividers as DataFrame"""
    supabase = get_client()
    res = supabase.table('dividers_magnet_status').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_magnet_status_dict():
    """Get magnet status as dict"""
    df = get_magnet_status()
    if df.empty:
        return {}
    return {
        row['divider_type']: {
            'with_magnet': row['with_magnet'],
            'without_magnet': row['without_magnet']
        }
        for _, row in df.iterrows()
    }


def apply_magnet_to_dividers(divider_type, qty, note=''):
    """Apply magnet to dividers (تلزيق المغناطيس)
    Each divider needs 2 squares + 1 rectangle = uses parts from strips
    1 strip = 3 squares + 1 rectangle
    So for 1 divider we need parts from strips
    
    Let's calculate: 1 strip serves ~1 divider (uses 2/3 of squares + full rectangle)
    For simplicity: 1 divider = 1 strip equivalent worth of pieces
    Actually: 3 strips = 9 squares + 3 rectangles = can make 4.5 dividers (9/2=4, limited by rect)
    So 3 strips = 3 dividers (limited by rectangles)
    Therefore: 1 strip = 1 divider
    """
    supabase = get_client()
    strips_needed = qty  # 1 strip per divider (limited by rectangles)

    # Check current strips
    current_strips = get_magnet_stock()
    if current_strips < strips_needed:
        return False, f"Not enough strips! Need {strips_needed}, have {current_strips}"

    # Get current magnet status
    res = supabase.table('dividers_magnet_status').select('*').eq('divider_type', divider_type).execute()
    if not res.data:
        return False, "Divider type not found"

    current = res.data[0]
    new_with = current['with_magnet'] + qty
    new_without = max(0, current['without_magnet'] - qty)

    # Update magnet status
    supabase.table('dividers_magnet_status').update({
        'with_magnet': new_with,
        'without_magnet': new_without,
        'last_updated': datetime.utcnow().isoformat()
    }).eq('divider_type', divider_type).execute()

    # Deduct strips
    new_strips = current_strips - strips_needed
    strip_res = supabase.table('magnet_stock').select('*').limit(1).execute()
    if strip_res.data:
        supabase.table('magnet_stock').update({
            'strips_qty': new_strips,
            'last_updated': datetime.utcnow().isoformat()
        }).eq('id', strip_res.data[0]['id']).execute()

    # Log history
    supabase.table('magnet_history').insert({
        'action': 'Apply Magnet',
        'divider_type': divider_type,
        'qty': qty,
        'strips_used': strips_needed,
        'note': note
    }).execute()

    return True, f"✅ Applied magnet to {qty} {divider_type} dividers"


def set_dividers_without_magnet(divider_type, qty):
    """Set the quantity of dividers without magnet (initial setup)"""
    supabase = get_client()
    supabase.table('dividers_magnet_status').update({
        'without_magnet': qty,
        'last_updated': datetime.utcnow().isoformat()
    }).eq('divider_type', divider_type).execute()

    supabase.table('magnet_history').insert({
        'action': 'Set Without Magnet',
        'divider_type': divider_type,
        'qty': qty,
        'note': 'Manual update'
    }).execute()


def get_magnet_history(limit=20):
    """Get recent magnet history"""
    supabase = get_client()
    res = supabase.table('magnet_history').select('*').order('date', desc=True).limit(limit).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()
