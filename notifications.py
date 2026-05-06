"""
Notifications System
Generates live notifications from the current data
"""
from datetime import date, timedelta


CRITICAL = 'critical'
WARNING = 'warning'
INFO = 'info'


SEVERITY_CONFIG = {
    CRITICAL: {
        'emoji': '🚨',
        'label': 'CRITICAL',
        'color': '#e74c3c',
        'bg': 'rgba(231, 76, 60, 0.08)',
        'priority': 1,
    },
    WARNING: {
        'emoji': '⚠️',
        'label': 'WARNING',
        'color': '#f39c12',
        'bg': 'rgba(243, 156, 18, 0.08)',
        'priority': 2,
    },
    INFO: {
        'emoji': 'ℹ️',
        'label': 'INFO',
        'color': '#3498db',
        'bg': 'rgba(52, 152, 219, 0.08)',
        'priority': 3,
    },
}


# ==================== DIVIDERS NOTIFICATIONS ====================

def get_dividers_notifications(stocks, threshold, stores_df, shipments_df,
                                 magnet_stock, magnet_status, action_items_df):
    """Generate all notifications for Dividers section"""
    notifications = []
    today = date.today()

    # ----- STOCK SHORTAGES -----
    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = 'required_' + dtype.lower()
        ship_col = 'qty_' + dtype.lower()
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        remaining = max(0, required - shipped)

        if stock == 0:
            notifications.append({
                'severity': CRITICAL,
                'title': dtype + ' Out of Stock',
                'message': 'Vendor has 0 units of ' + dtype + '. Order immediately!',
                'section': 'dividers',
                'goto_page': 'Vendor Stock',
                'category': 'Stock',
            })
        elif stock < remaining:
            shortage = remaining - stock
            notifications.append({
                'severity': CRITICAL,
                'title': dtype + ' Critical Shortage',
                'message': 'Need ' + str(shortage) + ' more units to cover pending shipments. Available: ' + str(stock) + ' | Remaining needed: ' + str(remaining),
                'section': 'dividers',
                'goto_page': 'Vendor Stock',
                'category': 'Stock',
            })
        elif stock < threshold:
            notifications.append({
                'severity': WARNING,
                'title': dtype + ' Low Stock',
                'message': 'Only ' + str(stock) + ' units left (threshold: ' + str(threshold) + ')',
                'section': 'dividers',
                'goto_page': 'Vendor Stock',
                'category': 'Stock',
            })

    # ----- LAUNCHES -----
    if not stores_df.empty and 'launch_date' in stores_df.columns:
        for _, store in stores_df.iterrows():
            if store.get('is_launched'):
                continue

            ld = store.get('launch_date')
            if not ld:
                continue

            try:
                if isinstance(ld, str):
                    ld_obj = date.fromisoformat(ld)
                else:
                    ld_obj = ld
            except Exception:
                continue

            days_left = (ld_obj - today).days
            name = store['name']
            loc = store.get('location') or 'N/A'

            if days_left < 0:
                notifications.append({
                    'severity': CRITICAL,
                    'title': 'Overdue Launch: ' + name,
                    'message': name + ' (' + loc + ') launch date was ' + str(abs(days_left)) + ' days ago but still not marked as launched.',
                    'section': 'dividers',
                    'goto_page': 'Stores',
                    'category': 'Launch',
                })
            elif days_left == 0:
                notifications.append({
                    'severity': CRITICAL,
                    'title': '🚀 ' + name + ' Launches TODAY!',
                    'message': name + ' (' + loc + ') is launching today. Ensure everything is delivered.',
                    'section': 'dividers',
                    'goto_page': 'Stores',
                    'category': 'Launch',
                })
            elif days_left == 1:
                notifications.append({
                    'severity': CRITICAL,
                    'title': name + ' Launches TOMORROW',
                    'message': name + ' (' + loc + ') launches in 1 day. Shipment must be out!',
                    'section': 'dividers',
                    'goto_page': 'Shipments',
                    'category': 'Launch',
                })
            elif days_left == 2:
                notifications.append({
                    'severity': WARNING,
                    'title': name + ' Launches in 2 Days',
                    'message': name + ' (' + loc + ') launches in 2 days. Schedule shipment today.',
                    'section': 'dividers',
                    'goto_page': 'Shipments',
                    'category': 'Launch',
                })
            elif days_left <= 4:
                notifications.append({
                    'severity': INFO,
                    'title': 'Upcoming: ' + name,
                    'message': name + ' (' + loc + ') launches in ' + str(days_left) + ' days.',
                    'section': 'dividers',
                    'goto_page': 'Stores',
                    'category': 'Launch',
                })

    # ----- SHIPMENTS WITHOUT TRANSPORT -----
    if not shipments_df.empty:
        for _, ship in shipments_df.iterrows():
            status = ship.get('delivery_status') or 'Pending'
            if status not in ('Pending', 'In Transit'):
                continue

            transport_ready = bool(ship.get('transportation_ready', False))
            if transport_ready:
                continue

            scheduled = ship.get('scheduled_date')
            if not scheduled:
                continue

            try:
                if isinstance(scheduled, str):
                    sched_obj = date.fromisoformat(scheduled[:10])
                else:
                    sched_obj = scheduled
            except Exception:
                continue

            days_to_delivery = (sched_obj - today).days
            ship_id = ship.get('id')
            store_name = str(ship.get('store_name', 'Unknown'))

            if days_to_delivery < 0:
                notifications.append({
                    'severity': CRITICAL,
                    'title': 'Shipment #' + str(ship_id) + ' Transport NOT Arranged',
                    'message': 'Shipment to ' + store_name + ' was scheduled for ' + str(sched_obj) + ' but transport not arranged!',
                    'section': 'dividers',
                    'goto_page': 'Shipments',
                    'category': 'Transport',
                })
            elif days_to_delivery <= 1:
                notifications.append({
                    'severity': CRITICAL,
                    'title': 'Transport NOT Ready - Shipment #' + str(ship_id),
                    'message': 'Shipment to ' + store_name + ' delivers tomorrow but transport not arranged!',
                    'section': 'dividers',
                    'goto_page': 'Shipments',
                    'category': 'Transport',
                })
            elif days_to_delivery <= 2:
                notifications.append({
                    'severity': WARNING,
                    'title': 'Arrange Transport - Shipment #' + str(ship_id),
                    'message': 'Shipment to ' + store_name + ' delivers in ' + str(days_to_delivery) + ' days. Arrange transport!',
                    'section': 'dividers',
                    'goto_page': 'Shipments',
                    'category': 'Transport',
                })

    # ----- DELAYED SHIPMENTS -----
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        delayed = shipments_df[shipments_df['delivery_status'] == 'Delayed']
        if not delayed.empty:
            for _, ship in delayed.iterrows():
                notifications.append({
                    'severity': WARNING,
                    'title': 'Delayed Shipment #' + str(ship['id']),
                    'message': 'Shipment to ' + str(ship.get('store_name', 'Unknown')) + ' is marked as Delayed.',
                    'section': 'dividers',
                    'goto_page': 'Shipments',
                    'category': 'Shipment',
                })

    # ----- MAGNET SHORTAGE -----
    total_without_magnet = sum(
        magnet_status.get(t, {}).get('without_magnet', 0)
        for t in ['30D', '40D', '60D']
    )
    if total_without_magnet > 0 and magnet_stock < total_without_magnet:
        shortage = total_without_magnet - magnet_stock
        notifications.append({
            'severity': WARNING,
            'title': 'Magnet Strips Shortage',
            'message': 'Need ' + str(shortage) + ' more strips. ' + str(total_without_magnet) + ' dividers without magnet, only ' + str(magnet_stock) + ' strips available.',
            'section': 'dividers',
            'goto_page': 'Magnets',
            'category': 'Magnet',
        })

    # ----- DISCREPANCIES -----
    if not stores_df.empty:
        for _, store in stores_df.iterrows():
            store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else None

            if store_ships is None or store_ships.empty:
                s30 = s40 = s60 = 0
            else:
                s30 = int(store_ships['qty_30d'].sum())
                s40 = int(store_ships['qty_40d'].sum())
                s60 = int(store_ships['qty_60d'].sum())

            r30 = int(store.get('received_30d', 0) or 0)
            r40 = int(store.get('received_40d', 0) or 0)
            r60 = int(store.get('received_60d', 0) or 0)

            if r30 == 0 and r40 == 0 and r60 == 0:
                continue

            diff_30 = r30 - s30
            diff_40 = r40 - s40
            diff_60 = r60 - s60

            if diff_30 != 0 or diff_40 != 0 or diff_60 != 0:
                parts = []
                if diff_30 != 0:
                    parts.append('30D: ' + ('+' if diff_30 > 0 else '') + str(diff_30))
                if diff_40 != 0:
                    parts.append('40D: ' + ('+' if diff_40 > 0 else '') + str(diff_40))
                if diff_60 != 0:
                    parts.append('60D: ' + ('+' if diff_60 > 0 else '') + str(diff_60))

                notifications.append({
                    'severity': WARNING,
                    'title': 'Discrepancy: ' + store['name'],
                    'message': 'Shipped vs Received mismatch — ' + ' | '.join(parts),
                    'section': 'dividers',
                    'goto_page': 'Stores',
                    'category': 'Discrepancy',
                })

    # ----- ACTION ITEMS -----
    if action_items_df is not None and not action_items_df.empty:
        for _, item in action_items_df.iterrows():
            if item.get('status') == 'Completed':
                continue

            eta = item.get('eta')
            if not eta:
                continue

            try:
                if isinstance(eta, str):
                    eta_obj = date.fromisoformat(eta)
                else:
                    eta_obj = eta
            except Exception:
                continue

            days_left = (eta_obj - today).days
            action_text = str(item.get('action_text', ''))[:60]
            owner = item.get('owner') or 'Unassigned'

            if days_left < 0:
                notifications.append({
                    'severity': CRITICAL,
                    'title': 'Overdue Action',
                    'message': action_text + ' (Owner: ' + owner + ') was due ' + str(abs(days_left)) + ' days ago',
                    'section': 'dividers',
                    'goto_page': 'Action Items',
                    'category': 'Action',
                })
            elif days_left == 0:
                notifications.append({
                    'severity': WARNING,
                    'title': 'Action Due TODAY',
                    'message': action_text + ' (Owner: ' + owner + ')',
                    'section': 'dividers',
                    'goto_page': 'Action Items',
                    'category': 'Action',
                })
            elif days_left <= 2:
                notifications.append({
                    'severity': WARNING,
                    'title': 'Action Due Soon',
                    'message': action_text + ' (Owner: ' + owner + ') due in ' + str(days_left) + ' days',
                    'section': 'dividers',
                    'goto_page': 'Action Items',
                    'category': 'Action',
                })

    return notifications


# ==================== IT NOTIFICATIONS ====================

def get_it_notifications(it_stocks, threshold, rdcs_df, it_shipments_df,
                           it_requirements, it_shipped_totals):
    """Generate all notifications for IT section"""
    notifications = []
    today = date.today()

    # ----- IT STOCK SHORTAGES -----
    for item, stock in it_stocks.items():
        req = it_requirements.get(item, 0)
        shipped = it_shipped_totals.get(item, 0)
        pending = max(0, req - shipped)

        if stock == 0 and req > 0:
            notifications.append({
                'severity': CRITICAL,
                'title': item + ' Out of Stock',
                'message': 'No ' + item + ' available. Required: ' + str(req) + ' | Pending: ' + str(pending),
                'section': 'it',
                'goto_page': 'IT Stock',
                'category': 'Stock',
            })
        elif stock < pending:
            shortage = pending - stock
            notifications.append({
                'severity': CRITICAL,
                'title': item + ' Shortage',
                'message': 'Need ' + str(shortage) + ' more. Stock: ' + str(stock) + ' | Pending: ' + str(pending),
                'section': 'it',
                'goto_page': 'IT Stock',
                'category': 'Stock',
            })
        elif 0 < stock < threshold:
            notifications.append({
                'severity': WARNING,
                'title': item + ' Low Stock',
                'message': 'Only ' + str(stock) + ' units left',
                'section': 'it',
                'goto_page': 'IT Stock',
                'category': 'Stock',
            })

    # ----- RDC LAUNCHES -----
    if not rdcs_df.empty and 'launch_date' in rdcs_df.columns:
        for _, rdc in rdcs_df.iterrows():
            ld = rdc.get('launch_date')
            if not ld:
                continue

            try:
                if isinstance(ld, str):
                    ld_obj = date.fromisoformat(ld)
                else:
                    ld_obj = ld
            except Exception:
                continue

            days_left = (ld_obj - today).days
            name = rdc['name']
            loc = rdc.get('location') or 'N/A'

            if days_left == 0:
                notifications.append({
                    'severity': CRITICAL,
                    'title': '🚀 ' + name + ' Launches TODAY!',
                    'message': 'RDC ' + name + ' (' + loc + ') is launching today.',
                    'section': 'it',
                    'goto_page': 'RDCs',
                    'category': 'Launch',
                })
            elif days_left == 1:
                notifications.append({
                    'severity': CRITICAL,
                    'title': name + ' Launches TOMORROW',
                    'message': 'RDC ' + name + ' launches in 1 day. Ship IT equipment NOW!',
                    'section': 'it',
                    'goto_page': 'Shipments',
                    'category': 'Launch',
                })
            elif 1 < days_left <= 4:
                notifications.append({
                    'severity': INFO,
                    'title': 'Upcoming: ' + name,
                    'message': 'RDC ' + name + ' (' + loc + ') launches in ' + str(days_left) + ' days.',
                    'section': 'it',
                    'goto_page': 'RDCs',
                    'category': 'Launch',
                })

    # ----- IT SHIPMENTS WITHOUT TRANSPORT -----
    if not it_shipments_df.empty:
        for _, ship in it_shipments_df.iterrows():
            status = ship.get('delivery_status') or 'Pending'
            if status not in ('Pending', 'In Transit'):
                continue

            transport_ready = bool(ship.get('transportation_ready', False))
            if transport_ready:
                continue

            scheduled = ship.get('scheduled_date')
            if not scheduled:
                continue

            try:
                if isinstance(scheduled, str):
                    sched_obj = date.fromisoformat(scheduled[:10])
                else:
                    sched_obj = scheduled
            except Exception:
                continue

            days_to_delivery = (sched_obj - today).days
            ship_id = ship.get('id')
            rdc_name = str(ship.get('rdc_name', 'Unknown'))

            if days_to_delivery < 0:
                notifications.append({
                    'severity': CRITICAL,
                    'title': 'IT Shipment #' + str(ship_id) + ' Transport NOT Arranged',
                    'message': 'Shipment to ' + rdc_name + ' was scheduled for ' + str(sched_obj) + ' but transport not arranged!',
                    'section': 'it',
                    'goto_page': 'Shipments',
                    'category': 'Transport',
                })
            elif days_to_delivery <= 1:
                notifications.append({
                    'severity': CRITICAL,
                    'title': 'Transport NOT Ready - IT Shipment #' + str(ship_id),
                    'message': 'Shipment to ' + rdc_name + ' delivers tomorrow but transport not arranged!',
                    'section': 'it',
                    'goto_page': 'Shipments',
                    'category': 'Transport',
                })
            elif days_to_delivery <= 2:
                notifications.append({
                    'severity': WARNING,
                    'title': 'Arrange Transport - IT Shipment #' + str(ship_id),
                    'message': 'Shipment to ' + rdc_name + ' delivers in ' + str(days_to_delivery) + ' days. Arrange transport!',
                    'section': 'it',
                    'goto_page': 'Shipments',
                    'category': 'Transport',
                })

    # ----- DELAYED IT SHIPMENTS -----
    if not it_shipments_df.empty and 'delivery_status' in it_shipments_df.columns:
        delayed = it_shipments_df[it_shipments_df['delivery_status'] == 'Delayed']
        if not delayed.empty:
            for _, ship in delayed.iterrows():
                notifications.append({
                    'severity': WARNING,
                    'title': 'Delayed IT Shipment #' + str(ship['id']),
                    'message': 'Shipment to ' + str(ship.get('rdc_name', 'Unknown')) + ' is marked as Delayed.',
                    'section': 'it',
                    'goto_page': 'Shipments',
                    'category': 'Shipment',
                })

    return notifications


# ==================== MAIN FUNCTIONS ====================

def get_all_notifications():
    """Get all notifications from both sections"""
    from database import (
        get_stocks_dict, get_threshold, get_stores, get_shipments,
        get_magnet_stock, get_magnet_status_dict, get_action_items
    )
    from database_it import (
        get_it_stock_dict, get_rdcs, get_it_shipments,
        get_total_requirements, get_all_shipment_items, IT_EQUIPMENT_TYPES
    )

    all_notifs = []

    try:
        stocks = get_stocks_dict()
        threshold = get_threshold()
        stores_df = get_stores()
        shipments_df = get_shipments()
        magnet_stock = get_magnet_stock()
        magnet_status = get_magnet_status_dict()
        action_items_df = get_action_items()

        all_notifs.extend(get_dividers_notifications(
            stocks, threshold, stores_df, shipments_df,
            magnet_stock, magnet_status, action_items_df
        ))
    except Exception:
        pass

    try:
        it_stocks = get_it_stock_dict()
        threshold = get_threshold()
        rdcs_df = get_rdcs()
        it_shipments_df = get_it_shipments()
        it_requirements = get_total_requirements()

        all_items = get_all_shipment_items()
        it_shipped_totals = {t: 0 for t in IT_EQUIPMENT_TYPES}
        if not all_items.empty:
            for t in IT_EQUIPMENT_TYPES:
                it_shipped_totals[t] = int(all_items[all_items['equipment_type'] == t]['quantity'].sum())

        all_notifs.extend(get_it_notifications(
            it_stocks, threshold, rdcs_df, it_shipments_df,
            it_requirements, it_shipped_totals
        ))
    except Exception:
        pass

    all_notifs.sort(key=lambda n: SEVERITY_CONFIG[n['severity']]['priority'])

    return all_notifs


def get_notifications_count():
    """Get counts by severity for the badge"""
    notifs = get_all_notifications()
    counts = {
        CRITICAL: 0,
        WARNING: 0,
        INFO: 0,
        'total': 0,
    }
    for n in notifs:
        counts[n['severity']] += 1
        counts['total'] += 1
    return counts
