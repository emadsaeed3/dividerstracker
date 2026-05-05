"""
Database module for 4M IT Equipment section
"""
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from database import get_client


# ==================== IT EQUIPMENT TYPES ====================

IT_EQUIPMENT_TYPES = [
    'Laptop',
    'Wired Scanner',
    'Wireless Scanner - PM560',
    'Charger Wireless Scanner - PM560',
    'Yubikey - Security Key',
    'Zukey',
    'Zebra ZD621'
]

IT_ICONS = {
    'Laptop': 'bi-laptop',
    'Wired Scanner': 'bi-upc-scan',
    'Wireless Scanner - PM560': 'bi-upc',
    'Charger Wireless Scanner - PM560': 'bi-battery-charging',
    'Yubikey - Security Key': 'bi-key-fill',
    'Zukey': 'bi-shield-lock-fill',
    'Zebra ZD621': 'bi-printer-fill'
}


# ==================== IT STOCK ====================

def get_it_stock():
    """Get all IT equipment stock as DataFrame"""
    supabase = get_client()
    res = supabase.table('it_equipment_stock').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=['equipment_type', 'quantity'])


def get_it_stock_dict():
    """Get IT stock as dict {equipment_type: quantity}"""
    df = get_it_stock()
    if df.empty:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    result = dict(zip(df['equipment_type'], df['quantity']))
    # Ensure all types exist
    for t in IT_EQUIPMENT_TYPES:
        if t not in result:
            result[t] = 0
    return result


def update_it_stock(equipment_type, new_qty, note=''):
    """Update IT stock quantity"""
    supabase = get_client()
    
    res = supabase.table('it_equipment_stock').select('*').eq('equipment_type', equipment_type).execute()
    
    if res.data:
        old_qty = res.data[0]['quantity']
        supabase.table('it_equipment_stock').update({
            'quantity': new_qty,
            'last_updated': datetime.utcnow().isoformat()
        }).eq('equipment_type', equipment_type).execute()
    else:
        old_qty = 0
        supabase.table('it_equipment_stock').insert({
            'equipment_type': equipment_type,
            'quantity': new_qty
        }).execute()
    
    supabase.table('it_stock_history').insert({
        'equipment_type': equipment_type,
        'old_qty': old_qty,
        'new_qty': new_qty,
        'change': new_qty - old_qty,
        'note': note
    }).execute()


def deduct_it_stock(equipment_type, qty, note=''):
    """Deduct quantity from IT stock"""
    supabase = get_client()
    res = supabase.table('it_equipment_stock').select('*').eq('equipment_type', equipment_type).execute()
    
    if res.data:
        old_qty = res.data[0]['quantity']
        new_qty = max(0, old_qty - qty)
        
        supabase.table('it_equipment_stock').update({
            'quantity': new_qty,
            'last_updated': datetime.utcnow().isoformat()
        }).eq('equipment_type', equipment_type).execute()
        
        supabase.table('it_stock_history').insert({
            'equipment_type': equipment_type,
            'old_qty': old_qty,
            'new_qty': new_qty,
            'change': -qty,
            'note': note
        }).execute()


def get_it_stock_history(limit=20):
    """Get recent IT stock history"""
    supabase = get_client()
    res = supabase.table('it_stock_history').select('*').order('date', desc=True).limit(limit).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


# ==================== RDCs ====================

def get_rdcs():
    """Get all RDCs"""
    supabase = get_client()
    res = supabase.table('rdcs').select('*').order('name').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def add_rdc(name, location, launch_date=None, transportation_ready=False):
    """Add a new RDC"""
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
        'transportation_ready': transportation_ready
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    
    res = supabase.table('rdcs').insert(data).execute()
    if res.data:
        return res.data[0]['id']
    return None


def update_rdc(rdc_id, name, location, launch_date=None, transportation_ready=False):
    """Update an existing RDC"""
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
        'transportation_ready': transportation_ready
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    else:
        data['launch_date'] = None
    
    supabase.table('rdcs').update(data).eq('id', rdc_id).execute()


def delete_rdc(rdc_id):
    """Delete an RDC"""
    supabase = get_client()
    supabase.table('rdcs').delete().eq('id', rdc_id).execute()


def get_upcoming_rdc_launches(days_ahead=4):
    """Get RDCs with launch date within the specified days"""
    supabase = get_client()
    today = date.today()
    future = today + timedelta(days=days_ahead)
    res = supabase.table('rdcs').select('*').not_.is_('launch_date', 'null').execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df['launch_date'] = pd.to_datetime(df['launch_date']).dt.date
    df = df[(df['launch_date'] >= today) & (df['launch_date'] <= future)]
    df['days_left'] = df['launch_date'].apply(lambda d: (d - today).days)
    return df.sort_values('days_left')


# ==================== RDC REQUIREMENTS ====================

def get_rdc_requirements(rdc_id=None):
    """Get requirements for a specific RDC or all RDCs"""
    supabase = get_client()
    query = supabase.table('rdc_requirements').select('*')
    if rdc_id is not None:
        query = query.eq('rdc_id', rdc_id)
    res = query.execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_rdc_requirements_dict(rdc_id):
    """Get requirements as dict for a specific RDC {equipment_type: required_qty}"""
    df = get_rdc_requirements(rdc_id)
    if df.empty:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    result = dict(zip(df['equipment_type'], df['required_qty']))
    for t in IT_EQUIPMENT_TYPES:
        if t not in result:
            result[t] = 0
    return result


def set_rdc_requirement(rdc_id, equipment_type, required_qty):
    """Set requirement for a specific RDC and equipment type"""
    supabase = get_client()
    res = supabase.table('rdc_requirements').select('*').eq('rdc_id', rdc_id).eq('equipment_type', equipment_type).execute()
    
    if res.data:
        supabase.table('rdc_requirements').update({
            'required_qty': required_qty
        }).eq('id', res.data[0]['id']).execute()
    else:
        supabase.table('rdc_requirements').insert({
            'rdc_id': rdc_id,
            'equipment_type': equipment_type,
            'required_qty': required_qty
        }).execute()


def set_rdc_requirements_bulk(rdc_id, requirements_dict):
    """Set multiple requirements for an RDC at once"""
    for equipment_type, qty in requirements_dict.items():
        set_rdc_requirement(rdc_id, equipment_type, qty)


def get_total_requirements():
    """Get total required quantity for each equipment type across all RDCs"""
    df = get_rdc_requirements()
    if df.empty:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    totals = df.groupby('equipment_type')['required_qty'].sum().to_dict()
    for t in IT_EQUIPMENT_TYPES:
        if t not in totals:
            totals[t] = 0
    return totals


# ==================== IT SHIPMENTS ====================

def get_it_shipments():
    """Get all IT shipments with RDC names and items"""
    supabase = get_client()
    res = supabase.table('it_shipments').select('*, rdcs(name, location)').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    df['rdc_name'] = df['rdcs'].apply(lambda x: x['name'] if x else 'Unknown')
    df['rdc_location'] = df['rdcs'].apply(lambda x: x.get('location', '') if x else '')
    return df


def get_it_shipment_items(shipment_id):
    """Get items for a specific shipment"""
    supabase = get_client()
    res = supabase.table('it_shipment_items').select('*').eq('shipment_id', shipment_id).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_all_shipment_items():
    """Get all shipment items across all shipments"""
    supabase = get_client()
    res = supabase.table('it_shipment_items').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_shipped_totals_per_rdc(rdc_id):
    """Calculate total shipped per equipment type for a specific RDC"""
    supabase = get_client()
    res = supabase.table('it_shipments').select('id').eq('rdc_id', rdc_id).execute()
    if not res.data:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    
    shipment_ids = [s['id'] for s in res.data]
    if not shipment_ids:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    
    items_res = supabase.table('it_shipment_items').select('*').in_('shipment_id', shipment_ids).execute()
    
    totals = {t: 0 for t in IT_EQUIPMENT_TYPES}
    if items_res.data:
        for item in items_res.data:
            etype = item['equipment_type']
            if etype in totals:
                totals[etype] += item['quantity']
    return totals


def add_it_shipment(rdc_id, ship_date, items_dict, notes='', delivery_status='Pending', 
                    scheduled_date=None, receiver_name='', receiver_contact=''):
    """Add IT shipment with multiple items
    items_dict: {equipment_type: quantity}
    """
    supabase = get_client()
    
    # Create shipment
    data = {
        'rdc_id': rdc_id,
        'date': ship_date.isoformat() if hasattr(ship_date, 'isoformat') else ship_date,
        'notes': notes,
        'delivery_status': delivery_status,
        'receiver_name': receiver_name,
        'receiver_contact': receiver_contact
    }
    if scheduled_date:
        data['scheduled_date'] = scheduled_date.isoformat() if hasattr(scheduled_date, 'isoformat') else scheduled_date
    
    res = supabase.table('it_shipments').insert(data).execute()
    if not res.data:
        return None
    
    shipment_id = res.data[0]['id']
    
    # Add items
    for equipment_type, qty in items_dict.items():
        if qty > 0:
            supabase.table('it_shipment_items').insert({
                'shipment_id': shipment_id,
                'equipment_type': equipment_type,
                'quantity': qty
            }).execute()
            
            # Deduct from stock
            deduct_it_stock(equipment_type, qty, f'Shipped to RDC #{rdc_id}')
    
    return shipment_id


def update_it_shipment_status(shipment_id, delivery_status):
    """Update IT shipment delivery status"""
    supabase = get_client()
    supabase.table('it_shipments').update({
        'delivery_status': delivery_status
    }).eq('id', shipment_id).execute()

def delete_it_shipment(shipment_id):
    """Delete an IT shipment, return quantities to stock, and clean history"""
    supabase = get_client()

    items_res = supabase.table('it_shipment_items').select('*').eq('shipment_id', shipment_id).execute()

    ship_res = supabase.table('it_shipments').select('rdc_id').eq('id', shipment_id).execute()
    rdc_id = ship_res.data[0]['rdc_id'] if ship_res.data else None

    # Return items to stock
    if items_res.data:
        for item in items_res.data:
            equipment_type = item['equipment_type']
            qty = int(item.get('quantity', 0) or 0)

            if qty > 0:
                stock_res = supabase.table('it_equipment_stock').select('*').eq('equipment_type', equipment_type).execute()
                if stock_res.data:
                    old_qty = stock_res.data[0]['quantity']
                    new_qty = old_qty + qty

                    supabase.table('it_equipment_stock').update({
                        'quantity': new_qty,
                        'last_updated': datetime.utcnow().isoformat()
                    }).eq('equipment_type', equipment_type).execute()

    # Clean up IT stock history related to this shipment
    try:
        hist_res = supabase.table('it_stock_history').select('*').execute()
        if hist_res.data:
            for entry in hist_res.data:
                note = entry.get('note') or ''
                if (f'shipment #{shipment_id}' in note.lower() or
                    (rdc_id and f'RDC #{rdc_id}' == note.split('(')[-1].rstrip(')').strip())):
                    supabase.table('it_stock_history').delete().eq('id', entry['id']).execute()
    except Exception:
        pass

    # Delete the shipment (items will cascade)
    supabase.table('it_shipments').delete().eq('id', shipment_id).execute()
