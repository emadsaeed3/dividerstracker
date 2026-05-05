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
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_client():
    return init_supabase()


# ==================== SETTINGS ====================

DEFAULT_THRESHOLD = 50


def get_threshold():
    try:
        supabase = get_client()
        res = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
        if res.data:
            return int(res.data[0]['value'])
    except Exception:
        pass
    return DEFAULT_THRESHOLD


def set_threshold(val):
    supabase = get_client()
    existing = supabase.table('settings').select('*').eq('key', 'low_stock_threshold').execute()
    if existing.data:
        supabase.table('settings').update({'value': str(val)}).eq('key', 'low_stock_threshold').execute()
    else:
        supabase.table('settings').insert({'key': 'low_stock_threshold', 'value': str(val)}).execute()


# ==================== VENDOR STOCK ====================

def get_stocks():
    supabase = get_client()
    res = supabase.table('vendor_stock').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=['divider_type', 'quantity'])


def get_stocks_dict():
    df = get_stocks()
    if df.empty:
        return {}
    return dict(zip(df['divider_type'], df['quantity']))


def update_stock(divider_type, new_qty, note=''):
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
    supabase = get_client()
    res = supabase.table('stock_history').select('*').order('date', desc=True).limit(limit).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def clear_stock_history():
    """Clear all stock history entries"""
    supabase = get_client()
    # Supabase requires a filter; use a condition that matches all
    supabase.table('stock_history').delete().neq('id', 0).execute()


# ==================== STORES ====================

def get_stores():
    supabase = get_client()
    res = supabase.table('stores').select('*').order('name').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def add_store(name, location, r30, r40, r60, launch_date=None,
              is_launched=False, received_30d=0, received_40d=0, received_60d=0):
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
        'required_30d': r30,
        'required_40d': r40,
        'required_60d': r60,
        'is_launched': is_launched,
        'received_30d': received_30d,
        'received_40d': received_40d,
        'received_60d': received_60d,
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    supabase.table('stores').insert(data).execute()


def update_store(store_id, name, location, r30, r40, r60, launch_date=None,
                 is_launched=False, received_30d=0, received_40d=0, received_60d=0):
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
        'required_30d': r30,
        'required_40d': r40,
        'required_60d': r60,
        'is_launched': is_launched,
        'received_30d': received_30d,
        'received_40d': received_40d,
        'received_60d': received_60d,
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    else:
        data['launch_date'] = None
    supabase.table('stores').update(data).eq('id', store_id).execute()


def delete_store(store_id):
    supabase = get_client()
    ships_res = supabase.table('shipments').select('*').eq('store_id', store_id).execute()

    if ships_res.data:
        for ship in ships_res.data:
            ship_id = ship['id']
            q30 = int(ship.get('qty_30d', 0) or 0)
            q40 = int(ship.get('qty_40d', 0) or 0)
            q60 = int(ship.get('qty_60d', 0) or 0)

            for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
                if qty > 0:
                    stock_res = supabase.table('vendor_stock').select('*').eq('divider_type', dtype).execute()
                    if stock_res.data:
                        old_qty = stock_res.data[0]['quantity']
                        new_qty = old_qty + qty
                        supabase.table('vendor_stock').update({
                            'quantity': new_qty,
                            'last_updated': datetime.utcnow().isoformat()
                        }).eq('divider_type', dtype).execute()

            supabase.table('shipments').delete().eq('id', ship_id).execute()

    try:
        hist_res = supabase.table('stock_history').select('*').execute()
        if hist_res.data:
            for entry in hist_res.data:
                note = entry.get('note') or ''
                if 'store #' + str(store_id) in note.lower():
                    supabase.table('stock_history').delete().eq('id', entry['id']).execute()
    except Exception:
        pass

    supabase.table('stores').delete().eq('id', store_id).execute()


def get_upcoming_launches(days_ahead=4):
    supabase = get_client()
    today = date.today()
    future = today + timedelta(days=days_ahead)
    res = supabase.table('stores').select('*').not_.is_('launch_date', 'null').execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)

    if 'is_launched' in df.columns:
        df = df[df['is_launched'] != True]

    if df.empty:
        return pd.DataFrame()

    df['launch_date'] = pd.to_datetime(df['launch_date']).dt.date
    df = df[(df['launch_date'] >= today) & (df['launch_date'] <= future)]
    df['days_left'] = df['launch_date'].apply(lambda d: (d - today).days)
    return df.sort_values('days_left')


def get_discrepancies(stores_df, shipments_df):
    discrepancies = []

    if stores_df.empty:
        return pd.DataFrame()

    for _, store in stores_df.iterrows():
        store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else pd.DataFrame()

        s30 = int(store_ships['qty_30d'].sum()) if not store_ships.empty else 0
        s40 = int(store_ships['qty_40d'].sum()) if not store_ships.empty else 0
        s60 = int(store_ships['qty_60d'].sum()) if not store_ships.empty else 0

        r30 = int(store.get('received_30d', 0) or 0)
        r40 = int(store.get('received_40d', 0) or 0)
        r60 = int(store.get('received_60d', 0) or 0)

        if r30 == 0 and r40 == 0 and r60 == 0:
            continue

        diff_30 = r30 - s30
        diff_40 = r40 - s40
        diff_60 = r60 - s60

        if diff_30 != 0 or diff_40 != 0 or diff_60 != 0:
            discrepancies.append({
                'store_id': store['id'],
                'name': store['name'],
                'location': store['location'] or 'N/A',
                'shipped_30d': s30,
                'received_30d': r30,
                'diff_30d': diff_30,
                'shipped_40d': s40,
                'received_40d': r40,
                'diff_40d': diff_40,
                'shipped_60d': s60,
                'received_60d': r60,
                'diff_60d': diff_60,
            })

    return pd.DataFrame(discrepancies)


# ==================== SHIPMENTS ====================

def get_shipments():
    supabase = get_client()
    res = supabase.table('shipments').select('*, stores(name)').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()

    df = pd.DataFrame(res.data)
    df['store_name'] = df['stores'].apply(lambda x: x['name'] if x else 'Unknown')
    return df


def add_shipment(store_id, ship_date, q30, q40, q60, notes='',
                  delivery_status='Pending', scheduled_date=None, transportation_ready=False):
    supabase = get_client()

    data = {
        'store_id': store_id,
        'date': ship_date.isoformat(),
        'qty_30d': q30,
        'qty_40d': q40,
        'qty_60d': q60,
        'notes': notes,
        'delivery_status': delivery_status,
        'transportation_ready': transportation_ready,
    }
    if scheduled_date:
        data['scheduled_date'] = scheduled_date.isoformat() if hasattr(scheduled_date, 'isoformat') else scheduled_date

    supabase.table('shipments').insert(data).execute()

    for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
        if qty > 0:
            deduct_stock(dtype, qty, 'Shipped to store #' + str(store_id))


def update_shipment_status(shipment_id, delivery_status):
    supabase = get_client()
    supabase.table('shipments').update({
        'delivery_status': delivery_status
    }).eq('id', shipment_id).execute()


def update_shipment_transport(shipment_id, transportation_ready):
    """Update transportation ready status for a shipment"""
    supabase = get_client()
    supabase.table('shipments').update({
        'transportation_ready': transportation_ready
    }).eq('id', shipment_id).execute()


def delete_shipment(shipment_id):
    supabase = get_client()

    res = supabase.table('shipments').select('*').eq('id', shipment_id).execute()
    if not res.data:
        return

    shipment = res.data[0]
    q30 = int(shipment.get('qty_30d', 0) or 0)
    q40 = int(shipment.get('qty_40d', 0) or 0)
    q60 = int(shipment.get('qty_60d', 0) or 0)
    store_id = shipment.get('store_id')

    for dtype, qty in [('30D', q30), ('40D', q40), ('60D', q60)]:
        if qty > 0:
            stock_res = supabase.table('vendor_stock').select('*').eq('divider_type', dtype).execute()
            if stock_res.data:
                old_qty = stock_res.data[0]['quantity']
                new_qty = old_qty + qty
                supabase.table('vendor_stock').update({
                    'quantity': new_qty,
                    'last_updated': datetime.utcnow().isoformat()
                }).eq('divider_type', dtype).execute()

    try:
        hist_res = supabase.table('stock_history').select('*').execute()
        if hist_res.data:
            for entry in hist_res.data:
                note = entry.get('note') or ''
                if ('shipment #' + str(shipment_id) in note.lower() or
                    'Shipped to store #' + str(store_id) == note):
                    supabase.table('stock_history').delete().eq('id', entry['id']).execute()
    except Exception:
        pass

    supabase.table('shipments').delete().eq('id', shipment_id).execute()


# ==================== MAGNETS ====================

def get_magnet_stock():
    supabase = get_client()
    res = supabase.table('magnet_stock').select('*').limit(1).execute()
    if res.data:
        return res.data[0]['strips_qty']
    return 0


def update_magnet_stock(new_qty, note=''):
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
    supabase = get_client()
    res = supabase.table('dividers_magnet_status').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_magnet_status_dict():
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
    supabase = get_client()
    strips_needed = qty

    current_strips = get_magnet_stock()
    if current_strips < strips_needed:
        return False, 'Not enough strips! Need ' + str(strips_needed) + ', have ' + str(current_strips)

    res = supabase.table('dividers_magnet_status').select('*').eq('divider_type', divider_type).execute()
    if not res.data:
        return False, 'Divider type not found'

    current = res.data[0]
    new_with = current['with_magnet'] + qty
    new_without = max(0, current['without_magnet'] - qty)

    supabase.table('dividers_magnet_status').update({
        'with_magnet': new_with,
        'without_magnet': new_without,
        'last_updated': datetime.utcnow().isoformat()
    }).eq('divider_type', divider_type).execute()

    new_strips = current_strips - strips_needed
    strip_res = supabase.table('magnet_stock').select('*').limit(1).execute()
    if strip_res.data:
        supabase.table('magnet_stock').update({
            'strips_qty': new_strips,
            'last_updated': datetime.utcnow().isoformat()
        }).eq('id', strip_res.data[0]['id']).execute()

    supabase.table('magnet_history').insert({
        'action': 'Apply Magnet',
        'divider_type': divider_type,
        'qty': qty,
        'strips_used': strips_needed,
        'note': note
    }).execute()

    return True, '✅ Applied magnet to ' + str(qty) + ' ' + divider_type + ' dividers'


def set_dividers_without_magnet(divider_type, qty):
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
    supabase = get_client()
    res = supabase.table('magnet_history').select('*').order('date', desc=True).limit(limit).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


# ==================== ACTION ITEMS ====================

def get_action_items():
    supabase = get_client()
    res = supabase.table('action_items').select('*, stores(name)').order('eta').execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df['store_name'] = df['stores'].apply(lambda x: x['name'] if x else None)
    return df


def add_action_item(action_text, owner, eta, status, store_id, priority, notes):
    supabase = get_client()
    data = {
        'action_text': action_text,
        'owner': owner,
        'status': status,
        'priority': priority,
        'notes': notes,
    }
    if eta:
        data['eta'] = eta.isoformat() if hasattr(eta, 'isoformat') else eta
    if store_id:
        data['store_id'] = store_id
    supabase.table('action_items').insert(data).execute()


def update_action_item(item_id, action_text, owner, eta, status, store_id, priority, notes):
    supabase = get_client()
    data = {
        'action_text': action_text,
        'owner': owner,
        'status': status,
        'priority': priority,
        'notes': notes,
        'updated_at': datetime.utcnow().isoformat()
    }
    if eta:
        data['eta'] = eta.isoformat() if hasattr(eta, 'isoformat') else eta
    else:
        data['eta'] = None
    data['store_id'] = store_id if store_id else None
    supabase.table('action_items').update(data).eq('id', item_id).execute()


def delete_action_item(item_id):
    supabase = get_client()
    supabase.table('action_items').delete().eq('id', item_id).execute()


def update_action_status(item_id, status):
    supabase = get_client()
    supabase.table('action_items').update({
        'status': status,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('id', item_id).execute()


# ==================== REPORT SETTINGS ====================

def get_report_settings():
    supabase = get_client()
    res = supabase.table('report_settings').select('*').limit(1).execute()
    if res.data:
        return res.data[0]
    return {
        'report_title': 'LAUNCH TEAM TRACKER - PROGRESS REPORT',
        'executive_summary': '',
        'highlights': '',
        'lowlights': '',
        'week_number': 1,
        'next_update_date': None
    }


def update_report_settings(report_title, executive_summary, highlights, lowlights,
                            week_number, next_update_date):
    supabase = get_client()
    data = {
        'report_title': report_title,
        'executive_summary': executive_summary,
        'highlights': highlights,
        'lowlights': lowlights,
        'week_number': week_number,
        'updated_at': datetime.utcnow().isoformat()
    }
    if next_update_date:
        data['next_update_date'] = next_update_date.isoformat() if hasattr(next_update_date, 'isoformat') else next_update_date
    else:
        data['next_update_date'] = None

    res = supabase.table('report_settings').select('*').limit(1).execute()
    if res.data:
        supabase.table('report_settings').update(data).eq('id', res.data[0]['id']).execute()
    else:
        supabase.table('report_settings').insert(data).execute()
