"""
Database module for 4M IT Equipment section
"""
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from database import get_client


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
    supabase = get_client()
    res = supabase.table('it_equipment_stock').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=['equipment_type', 'quantity'])


def get_it_stock_dict():
    df = get_it_stock()
    if df.empty:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    result = dict(zip(df['equipment_type'], df['quantity']))
    for t in IT_EQUIPMENT_TYPES:
        if t not in result:
            result[t] = 0
    return result


def update_it_stock(equipment_type, new_qty, note=''):
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
    supabase = get_client()
    res = supabase.table('it_stock_history').select('*').order('date', desc=True).limit(limit).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def clear_it_stock_history():
    """Clear all IT stock history entries"""
    supabase = get_client()
    supabase.table('it_stock_history').delete().neq('id', 0).execute()


# ==================== RDCs ====================

def get_rdcs():
    supabase = get_client()
    res = supabase.table('rdcs').select('*').order('name').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def add_rdc(name, location, launch_date=None):
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date

    res = supabase.table('rdcs').insert(data).execute()
    if res.data:
        return res.data[0]['id']
    return None


def update_rdc(rdc_id, name, location, launch_date=None):
    supabase = get_client()
    data = {
        'name': name,
        'location': location,
    }
    if launch_date:
        data['launch_date'] = launch_date.isoformat() if hasattr(launch_date, 'isoformat') else launch_date
    else:
        data['launch_date'] = None

    supabase.table('rdcs').update(data).eq('id', rdc_id).execute()


def delete_rdc(rdc_id):
    supabase = get_client()
    ships_res = supabase.table('it_shipments').select('*').eq('rdc_id', rdc_id).execute()

    if ships_res.data:
        for ship in ships_res.data:
            ship_id = ship['id']
            items_res = supabase.table('it_shipment_items').select('*').eq('shipment_id', ship_id).execute()

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

            supabase.table('it_shipments').delete().eq('id', ship_id).execute()

    try:
        hist_res = supabase.table('it_stock_history').select('*').execute()
        if hist_res.data:
            for entry in hist_res.data:
                note = entry.get('note') or ''
                if 'RDC #' + str(rdc_id) in note:
                    supabase.table('it_stock_history').delete().eq('id', entry['id']).execute()
    except Exception:
        pass

    supabase.table('rdc_requirements').delete().eq('rdc_id', rdc_id).execute()
    supabase.table('rdcs').delete().eq('id', rdc_id).execute()


def get_upcoming_rdc_launches(days_ahead=4):
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
    supabase = get_client()
    query = supabase.table('rdc_requirements').select('*')
    if rdc_id is not None:
        query = query.eq('rdc_id', rdc_id)
    res = query.execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_rdc_requirements_dict(rdc_id):
    df = get_rdc_requirements(rdc_id)
    if df.empty:
        return {t: 0 for t in IT_EQUIPMENT_TYPES}
    result = dict(zip(df['equipment_type'], df['required_qty']))
    for t in IT_EQUIPMENT_TYPES:
        if t not in result:
            result[t] = 0
    return result


def set_rdc_requirement(rdc_id, equipment_type, required_qty):
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
    for equipment_type, qty in requirements_dict.items():
        set_rdc_requirement(rdc_id, equipment_type, qty)


def get_total_requirements():
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
    supabase = get_client()
    res = supabase.table('it_shipments').select('*, rdcs(name, location)').order('date', desc=True).execute()
    if not res.data:
        return pd.DataFrame()

    df = pd.DataFrame(res.data)
    df['rdc_name'] = df['rdcs'].apply(lambda x: x['name'] if x else 'Unknown')
    df['rdc_location'] = df['rdcs'].apply(lambda x: x.get('location', '') if x else '')
    return df


def get_it_shipment_items(shipment_id):
    supabase = get_client()
    res = supabase.table('it_shipment_items').select('*').eq('shipment_id', shipment_id).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_all_shipment_items():
    supabase = get_client()
    res = supabase.table('it_shipment_items').select('*').execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def get_shipped_totals_per_rdc(rdc_id):
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
                    scheduled_date=None, receiver_name='', receiver_contact='',
                    transportation_ready=False):
    supabase = get_client()

    data = {
        'rdc_id': rdc_id,
        'date': ship_date.isoformat() if hasattr(ship_date, 'isoformat') else ship_date,
        'notes': notes,
        'delivery_status': delivery_status,
        'receiver_name': receiver_name,
        'receiver_contact': receiver_contact,
        'transportation_ready': transportation_ready,
    }
    if scheduled_date:
        data['scheduled_date'] = scheduled_date.isoformat() if hasattr(scheduled_date, 'isoformat') else scheduled_date

    res = supabase.table('it_shipments').insert(data).execute()
    if not res.data:
        return None

    shipment_id = res.data[0]['id']

    for equipment_type, qty in items_dict.items():
        if qty > 0:
            supabase.table('it_shipment_items').insert({
                'shipment_id': shipment_id,
                'equipment_type': equipment_type,
                'quantity': qty
            }).execute()

            deduct_it_stock(equipment_type, qty, 'Shipped to RDC #' + str(rdc_id))

    return shipment_id


def update_it_shipment_status(shipment_id, delivery_status):
    supabase = get_client()
    supabase.table('it_shipments').update({
        'delivery_status': delivery_status
    }).eq('id', shipment_id).execute()


def update_it_shipment_transport(shipment_id, transportation_ready):
    """Update transportation ready status for an IT shipment"""
    supabase = get_client()
    supabase.table('it_shipments').update({
        'transportation_ready': transportation_ready
    }).eq('id', shipment_id).execute()


def delete_it_shipment(shipment_id):
    supabase = get_client()

    items_res = supabase.table('it_shipment_items').select('*').eq('shipment_id', shipment_id).execute()

    ship_res = supabase.table('it_shipments').select('rdc_id').eq('id', shipment_id).execute()
    rdc_id = ship_res.data[0]['rdc_id'] if ship_res.data else None

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

    try:
        hist_res = supabase.table('it_stock_history').select('*').execute()
        if hist_res.data:
            for entry in hist_res.data:
                note = entry.get('note') or ''
                if (rdc_id and 'RDC #' + str(rdc_id) in note):
                    supabase.table('it_stock_history').delete().eq('id', entry['id']).execute()
    except Exception:
        pass

    supabase.table('it_shipments').delete().eq('id', shipment_id).execute()


# ============================================================
# IT Purchase Orders
# ============================================================

IT_PO_STATUSES = [
    'Draft',
    'Sent to Vendor',
    'Confirmed',
    'In Production',
    'Shipped',
    'Received',
    'Cancelled'
]


def get_it_purchase_orders(status_filter=None):
    """Get all IT purchase orders, optionally filtered by status."""
    supabase = get_client()
    try:
        query = supabase.table('it_purchase_orders').select('*')
        
        if status_filter:
            if isinstance(status_filter, list):
                query = query.in_('status', status_filter)
            else:
                query = query.eq('status', status_filter)
        
        response = query.order('po_date', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching IT POs: {e}")
        return []


def get_it_po_by_id(po_id):
    """Get a single IT PO by ID."""
    supabase = get_client()
    try:
        response = supabase.table('it_purchase_orders').select('*').eq('id', po_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching IT PO {po_id}: {e}")
        return None


def add_it_purchase_order(po_number, vendor_name, po_date, expected_date,
                          equipment_type, quantity, status='Draft', notes=None):
    """Add a new IT purchase order."""
    supabase = get_client()
    try:
        data = {
            'po_number': po_number,
            'vendor_name': vendor_name,
            'po_date': str(po_date) if po_date else None,
            'expected_date': str(expected_date) if expected_date else None,
            'equipment_type': equipment_type,
            'quantity': int(quantity) if quantity else 0,
            'status': status,
            'notes': notes
        }
        response = supabase.table('it_purchase_orders').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error adding IT PO: {e}")
        return None


def update_it_purchase_order(po_id, po_number=None, vendor_name=None, po_date=None,
                             expected_date=None, equipment_type=None, quantity=None,
                             status=None, notes=None):
    """Update an existing IT purchase order. Cannot update if status is 'Received'."""
    supabase = get_client()
    try:
        # Check if PO is already received
        existing = get_it_po_by_id(po_id)
        if not existing:
            return None
        if existing.get('status') == 'Received':
            print(f"Cannot update IT PO {po_id}: already Received")
            return None
        
        update_data = {'updated_at': datetime.now().isoformat()}
        
        if po_number is not None:
            update_data['po_number'] = po_number
        if vendor_name is not None:
            update_data['vendor_name'] = vendor_name
        if po_date is not None:
            update_data['po_date'] = str(po_date)
        if expected_date is not None:
            update_data['expected_date'] = str(expected_date) if expected_date else None
        if equipment_type is not None:
            update_data['equipment_type'] = equipment_type
        if quantity is not None:
            update_data['quantity'] = int(quantity)
        if status is not None:
            update_data['status'] = status
        if notes is not None:
            update_data['notes'] = notes
        
        response = supabase.table('it_purchase_orders').update(update_data).eq('id', po_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating IT PO {po_id}: {e}")
        return None


def receive_it_purchase_order(po_id):
    """
    Mark IT PO as Received:
    1. Add quantity to it_equipment_stock
    2. Log entry in it_stock_history
    3. Update PO status to 'Received' + set received_date
    """
    supabase = get_client()
    try:
        po = get_it_po_by_id(po_id)
        if not po:
            return False, "PO not found"
        
        if po.get('status') == 'Received':
            return False, "PO is already received"
        
        equipment_type = po['equipment_type']
        quantity = int(po.get('quantity', 0))
        
        if quantity <= 0:
            return False, "PO quantity must be greater than 0"
        
        # 1. Get current stock
        stock_resp = supabase.table('it_equipment_stock').select('*').eq('equipment_type', equipment_type).execute()
        
        if stock_resp.data:
            current_qty = int(stock_resp.data[0].get('quantity', 0))
            new_qty = current_qty + quantity
            # Update stock
            try:
                supabase.table('it_equipment_stock').update({
                    'quantity': new_qty,
                    'last_updated': datetime.now().isoformat()
                }).eq('equipment_type', equipment_type).execute()
            except Exception:
                # Fallback if last_updated column missing
                supabase.table('it_equipment_stock').update({
                    'quantity': new_qty
                }).eq('equipment_type', equipment_type).execute()
        else:
            # Insert new stock row
            current_qty = 0
            new_qty = quantity
            try:
                supabase.table('it_equipment_stock').insert({
                    'equipment_type': equipment_type,
                    'quantity': new_qty,
                    'last_updated': datetime.now().isoformat()
                }).execute()
            except Exception:
                supabase.table('it_equipment_stock').insert({
                    'equipment_type': equipment_type,
                    'quantity': new_qty
                }).execute()
        
        # 2. Log in history
        try:
            supabase.table('it_stock_history').insert({
                'equipment_type': equipment_type,
                'old_qty': current_qty,
                'new_qty': new_qty,
                'change': quantity,
                'note': f"Received PO #{po.get('po_number', po_id)} from {po.get('vendor_name', 'N/A')}",
                'date': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"Warning: failed to log stock history: {e}")
        
        # 3. Update PO
        supabase.table('it_purchase_orders').update({
            'status': 'Received',
            'received_date': datetime.now().date().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('id', po_id).execute()
        
        return True, f"PO received: +{quantity} {equipment_type}"
    except Exception as e:
        print(f"Error receiving IT PO {po_id}: {e}")
        return False, str(e)


def delete_it_purchase_order(po_id):
    """Delete an IT purchase order. Cannot delete if status is 'Received'."""
    supabase = get_client()
    try:
        existing = get_it_po_by_id(po_id)
        if not existing:
            return False, "PO not found"
        if existing.get('status') == 'Received':
            return False, "Cannot delete a Received PO"
        
        supabase.table('it_purchase_orders').delete().eq('id', po_id).execute()
        return True, "PO deleted successfully"
    except Exception as e:
        print(f"Error deleting IT PO {po_id}: {e}")
        return False, str(e)


def get_it_pending_pos():
    """Get all IT POs that are not Received or Cancelled (for alerts/dashboard)."""
    supabase = get_client()
    try:
        response = supabase.table('it_purchase_orders').select('*').not_.in_(
            'status', ['Received', 'Cancelled']
        ).order('expected_date', desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching pending IT POs: {e}")
        return []

