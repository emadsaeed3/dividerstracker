"""
Coverage Analysis Helper
Calculates if current stock + pending POs can cover upcoming + under-shipped stores.
"""
import math
import pandas as pd
from datetime import date, datetime
from database import (
    get_stores, get_shipments, get_stocks_dict,
    get_pending_pos, get_magnet_stock
)


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            try:
                return pd.to_datetime(value).date()
            except Exception:
                return None
    return None


def calculate_strips_needed(total_dividers):
    """Optimal strips with cutting (5/7 formula)"""
    if total_dividers <= 0:
        return 0
    return math.ceil(5 * total_dividers / 7)


def get_demand_stores(stores_df=None, shipments_df=None):
    """
    Get all stores that need dividers (Upcoming + Under-shipped Launched).
    Returns list of dicts with: id, name, location, is_launched, launch_date,
    days_left, need_30d, need_40d, need_60d, total_need
    """
    if stores_df is None:
        stores_df = get_stores()
    if shipments_df is None:
        shipments_df = get_shipments()

    if stores_df.empty:
        return []

    today = date.today()
    demand_list = []

    for _, store in stores_df.iterrows():
        store_id = store['id']
        is_launched = bool(store.get('is_launched', False))

        # Required
        r30 = int(store.get('required_30d', 0) or 0)
        r40 = int(store.get('required_40d', 0) or 0)
        r60 = int(store.get('required_60d', 0) or 0)

        # Shipped so far
        if not shipments_df.empty:
            store_ships = shipments_df[shipments_df['store_id'] == store_id]
            s30 = int(store_ships['qty_30d'].sum()) if not store_ships.empty else 0
            s40 = int(store_ships['qty_40d'].sum()) if not store_ships.empty else 0
            s60 = int(store_ships['qty_60d'].sum()) if not store_ships.empty else 0
        else:
            s30 = s40 = s60 = 0

        # Need = Required - Shipped (only positive)
        need_30 = max(0, r30 - s30)
        need_40 = max(0, r40 - s40)
        need_60 = max(0, r60 - s60)
        total_need = need_30 + need_40 + need_60

        # Skip stores with no need
        if total_need == 0:
            continue

        # Launch date info
        launch_date_obj = _to_date(store.get('launch_date'))
        days_left = None
        if launch_date_obj:
            days_left = (launch_date_obj - today).days

        demand_list.append({
            'id': store_id,
            'name': store.get('name', ''),
            'location': store.get('location', '') or '',
            'is_launched': is_launched,
            'launch_date': launch_date_obj,
            'days_left': days_left,
            'required_30d': r30,
            'required_40d': r40,
            'required_60d': r60,
            'shipped_30d': s30,
            'shipped_40d': s40,
            'shipped_60d': s60,
            'need_30d': need_30,
            'need_40d': need_40,
            'need_60d': need_60,
            'total_need': total_need,
        })

    return demand_list


def get_supply_breakdown(extra_po=None):
    """
    Calculate available supply.
    extra_po (optional): dict with {qty_30d, qty_40d, qty_60d} for hypothetical new PO.
    Returns dict with supply per type.
    """
    stocks = get_stocks_dict()
    pending_pos = get_pending_pos()

    pending_30 = int(pending_pos['qty_30d'].sum()) if not pending_pos.empty else 0
    pending_40 = int(pending_pos['qty_40d'].sum()) if not pending_pos.empty else 0
    pending_60 = int(pending_pos['qty_60d'].sum()) if not pending_pos.empty else 0

    extra_30 = extra_po.get('qty_30d', 0) if extra_po else 0
    extra_40 = extra_po.get('qty_40d', 0) if extra_po else 0
    extra_60 = extra_po.get('qty_60d', 0) if extra_po else 0

    return {
        'stock_30d': stocks.get('30D', 0),
        'stock_40d': stocks.get('40D', 0),
        'stock_60d': stocks.get('60D', 0),
        'pending_30d': pending_30,
        'pending_40d': pending_40,
        'pending_60d': pending_60,
        'extra_30d': extra_30,
        'extra_40d': extra_40,
        'extra_60d': extra_60,
        'total_30d': stocks.get('30D', 0) + pending_30 + extra_30,
        'total_40d': stocks.get('40D', 0) + pending_40 + extra_40,
        'total_60d': stocks.get('60D', 0) + pending_60 + extra_60,
    }


def calculate_coverage(extra_po=None, stores_df=None, shipments_df=None):
    """
    Main coverage calculation.
    extra_po: optional dict for what-if scenario.
    Returns full coverage report.
    """
    demand_stores = get_demand_stores(stores_df, shipments_df)
    supply = get_supply_breakdown(extra_po)

    # Total demand
    total_need_30 = sum(s['need_30d'] for s in demand_stores)
    total_need_40 = sum(s['need_40d'] for s in demand_stores)
    total_need_60 = sum(s['need_60d'] for s in demand_stores)
    total_need = total_need_30 + total_need_40 + total_need_60

    # Coverage per type
    def coverage_pct(supply_qty, demand_qty):
        if demand_qty == 0:
            return 100.0 if supply_qty >= 0 else 0.0
        return min(100.0, (supply_qty / demand_qty) * 100)

    cov_30 = coverage_pct(supply['total_30d'], total_need_30)
    cov_40 = coverage_pct(supply['total_40d'], total_need_40)
    cov_60 = coverage_pct(supply['total_60d'], total_need_60)

    # Shortages
    short_30 = max(0, total_need_30 - supply['total_30d'])
    short_40 = max(0, total_need_40 - supply['total_40d'])
    short_60 = max(0, total_need_60 - supply['total_60d'])

    # Magnet calculation
    total_supply_dividers = supply['total_30d'] + supply['total_40d'] + supply['total_60d']
    strips_available = get_magnet_stock()
    strips_needed_for_supply = calculate_strips_needed(total_supply_dividers)
    strips_needed_for_demand = calculate_strips_needed(total_need)
    magnet_shortage = max(0, strips_needed_for_demand - strips_available)

    # Overall status
    if short_30 == 0 and short_40 == 0 and short_60 == 0:
        overall_status = 'covered'
    elif cov_30 >= 50 and cov_40 >= 50 and cov_60 >= 50:
        overall_status = 'partial'
    else:
        overall_status = 'shortage'

    return {
        'demand_stores': demand_stores,
        'supply': supply,
        'demand': {
            'total_30d': total_need_30,
            'total_40d': total_need_40,
            'total_60d': total_need_60,
            'total': total_need,
            'stores_count': len(demand_stores),
        },
        'coverage': {
            'pct_30d': cov_30,
            'pct_40d': cov_40,
            'pct_60d': cov_60,
            'overall_status': overall_status,
        },
        'shortages': {
            'short_30d': short_30,
            'short_40d': short_40,
            'short_60d': short_60,
            'total_shortage': short_30 + short_40 + short_60,
        },
        'magnets': {
            'strips_available': strips_available,
            'strips_needed_for_demand': strips_needed_for_demand,
            'strips_needed_for_supply': strips_needed_for_supply,
            'magnet_shortage': magnet_shortage,
        }
    }


def classify_store_coverage(store, supply_remaining):
    """
    Classify if a store can be covered with remaining supply.
    Mutates supply_remaining (decreases it).
    Returns: ('covered'|'partial'|'shortage', details_dict)
    """
    need_30 = store['need_30d']
    need_40 = store['need_40d']
    need_60 = store['need_60d']

    # Try to allocate
    alloc_30 = min(need_30, max(0, supply_remaining['total_30d']))
    alloc_40 = min(need_40, max(0, supply_remaining['total_40d']))
    alloc_60 = min(need_60, max(0, supply_remaining['total_60d']))

    short_30 = need_30 - alloc_30
    short_40 = need_40 - alloc_40
    short_60 = need_60 - alloc_60

    # Decrement supply
    supply_remaining['total_30d'] -= alloc_30
    supply_remaining['total_40d'] -= alloc_40
    supply_remaining['total_60d'] -= alloc_60

    total_short = short_30 + short_40 + short_60
    total_need = need_30 + need_40 + need_60

    if total_short == 0:
        status = 'covered'
    elif total_short < total_need:
        status = 'partial'
    else:
        status = 'shortage'

    return status, {
        'alloc_30d': alloc_30,
        'alloc_40d': alloc_40,
        'alloc_60d': alloc_60,
        'short_30d': short_30,
        'short_40d': short_40,
        'short_60d': short_60,
        'total_short': total_short,
    }


def allocate_supply_to_stores(coverage_report, sort_by='launch_date'):
    """
    Greedy allocation: assign supply to stores by priority (launch date or need).
    Returns list of stores with allocation status.
    """
    stores = coverage_report['demand_stores'].copy()
    supply_remaining = {
        'total_30d': coverage_report['supply']['total_30d'],
        'total_40d': coverage_report['supply']['total_40d'],
        'total_60d': coverage_report['supply']['total_60d'],
    }

    # Sort by priority
    if sort_by == 'launch_date':
        # Stores with closer launch first; None goes last
        stores.sort(key=lambda s: (
            s['days_left'] is None,
            s['days_left'] if s['days_left'] is not None else 99999
        ))
    elif sort_by == 'need_high':
        stores.sort(key=lambda s: -s['total_need'])
    elif sort_by == 'need_low':
        stores.sort(key=lambda s: s['total_need'])

    results = []
    for store in stores:
        status, details = classify_store_coverage(store, supply_remaining)
        results.append({
            **store,
            'status': status,
            **details,
        })

    return results
