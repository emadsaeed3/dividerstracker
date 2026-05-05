"""
Email Draft Generator
Creates mailto links with pre-filled content for Daily Reports
"""
import urllib.parse
from datetime import date, datetime


def _build_mailto_link(subject, body, to=""):
    """Build a mailto: link with URL-encoded subject and body"""
    params = {
        'subject': subject,
        'body': body
    }
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"mailto:{to}?{query}"


def _line(text=''):
    """Return a line for plain text email"""
    return text + '\n'


def _separator():
    """Return a separator line"""
    return '=' * 50 + '\n'


def _sub_separator():
    """Return a sub-separator"""
    return '-' * 50 + '\n'


# ==================== DIVIDERS REPORT ====================

def generate_dividers_report_body(stocks, threshold, stores_df, shipments_df,
                                    magnet_stock, magnet_status, upcoming_launches,
                                    discrepancies_df):
    """Generate plain text body for Dividers daily report"""
    today = date.today().strftime('%A, %B %d, %Y')
    
    body = ''
    body += _line('📦 DIVIDERS DAILY REPORT')
    body += _line(today)
    body += _separator()
    body += _line()
    
    # === VENDOR STOCK ===
    body += _line('📦 VENDOR STOCK')
    body += _sub_separator()
    for dtype in ['30D', '40D', '60D']:
        qty = stocks.get(dtype, 0)
        if qty == 0:
            status = '❌ OUT OF STOCK'
        elif qty < threshold:
            status = '⚠️ LOW STOCK'
        else:
            status = '✅ OK'
        body += _line(f'  {dtype}: {qty} units  {status}')
    body += _line()
    
    # === REQUIRED VS SHIPPED ===
    body += _line('🎯 REQUIRED vs SHIPPED')
    body += _sub_separator()
    total_req = 0
    total_ship = 0
    for dtype in ['30D', '40D', '60D']:
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        pending = max(0, required - shipped)
        pct = (shipped / required * 100) if required > 0 else 0
        total_req += required
        total_ship += shipped
        body += _line(f'  {dtype}:  Required={required}  |  Shipped={shipped}  |  Pending={pending}  ({pct:.0f}%)')
    
    body += _line()
    body += _line(f'  TOTAL:  Required={total_req}  |  Shipped={total_ship}  |  Pending={max(0, total_req - total_ship)}')
    body += _line()
    
    # === MAGNETS ===
    body += _line('🧲 MAGNETS STATUS')
    body += _sub_separator()
    body += _line(f'  Strips at Vendor: {magnet_stock}')
    total_with = 0
    total_without = 0
    for dtype in ['30D', '40D', '60D']:
        status = magnet_status.get(dtype, {'with_magnet': 0, 'without_magnet': 0})
        with_m = status['with_magnet']
        without_m = status['without_magnet']
        total_with += with_m
        total_without += without_m
        body += _line(f'  {dtype}:  With={with_m}  |  Without={without_m}')
    body += _line(f'  TOTAL:  With Magnet={total_with}  |  Without Magnet={total_without}')
    if magnet_stock < total_without:
        shortage = total_without - magnet_stock
        body += _line(f'  ⚠️ Need {shortage} more strips to cover all dividers!')
    body += _line()
    
    # === STORES OVERVIEW ===
    total_stores = len(stores_df) if not stores_df.empty else 0
    launched = len(stores_df[stores_df['is_launched'] == True]) if not stores_df.empty and 'is_launched' in stores_df.columns else 0
    upcoming = total_stores - launched
    
    body += _line('🏪 STORES OVERVIEW')
    body += _sub_separator()
    body += _line(f'  Total Stores: {total_stores}')
    body += _line(f'  ✅ Launched: {launched}')
    body += _line(f'  🚀 Upcoming: {upcoming}')
    body += _line()
    
    # === UPCOMING LAUNCHES ===
    if not upcoming_launches.empty:
        body += _line(f'🚀 UPCOMING LAUNCHES ({len(upcoming_launches)} in next 4 days)')
        body += _sub_separator()
        for _, store in upcoming_launches.iterrows():
            days = store['days_left']
            name = store['name']
            loc = store.get('location') or 'N/A'
            transport = '✅' if store.get('transportation_ready') else '❌'
            
            if days == 0:
                urgency = '🚀 TODAY!'
            elif days == 1:
                urgency = '🚨 TOMORROW!'
            elif days <= 2:
                urgency = '⚠️ URGENT'
            else:
                urgency = '📅'
            
            body += _line(f'  {urgency} {name} ({loc})')
            body += _line(f'       Launch: {store["launch_date"]}  |  Days Left: {days}  |  Transport: {transport}')
        body += _line()
    
    # === PENDING SHIPMENTS ===
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        pending_ships = shipments_df[shipments_df['delivery_status'].isin(['Pending', 'In Transit', 'Delayed'])]
        
        if not pending_ships.empty:
            body += _line(f'🚚 PENDING SHIPMENTS ({len(pending_ships)})')
            body += _sub_separator()
            
            for status in ['Pending', 'In Transit', 'Delayed']:
                subset = pending_ships[pending_ships['delivery_status'] == status]
                if not subset.empty:
                    emoji = {'Pending': '🟡', 'In Transit': '🔵', 'Delayed': '🔴'}[status]
                    body += _line(f'  {emoji} {status}: {len(subset)}')
                    for _, ship in subset.iterrows():
                        total = int(ship['qty_30d']) + int(ship['qty_40d']) + int(ship['qty_60d'])
                        body += _line(f'       #{ship["id"]} - {ship["store_name"]} - {ship["date"]} - {total} units')
            body += _line()
    
    # === DISCREPANCIES ===
    if not discrepancies_df.empty:
        body += _line(f'⚖️ SHIPPED vs RECEIVED DISCREPANCIES ({len(discrepancies_df)})')
        body += _sub_separator()
        for _, disc in discrepancies_df.iterrows():
            body += _line(f'  🏪 {disc["name"]} ({disc["location"]})')
            for dtype, ship_col, rec_col, diff_col in [
                ('30D', 'shipped_30d', 'received_30d', 'diff_30d'),
                ('40D', 'shipped_40d', 'received_40d', 'diff_40d'),
                ('60D', 'shipped_60d', 'received_60d', 'diff_60d'),
            ]:
                diff = int(disc[diff_col])
                if diff != 0:
                    sign = '+' if diff > 0 else ''
                    kind = 'EXCESS' if diff > 0 else 'SHORTAGE'
                    body += _line(f'       {dtype}: Shipped={disc[ship_col]} | Received={disc[rec_col]} | Diff: {sign}{diff} ({kind})')
        body += _line()
    
    # === FOOTER ===
    body += _separator()
    body += _line('Generated from Launch Team Tracker')
    body += _line('Launch Team • Amazon Now')
    body += _line(f'Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    
    return body


def generate_dividers_mailto(stocks, threshold, stores_df, shipments_df,
                              magnet_stock, magnet_status, upcoming_launches,
                              discrepancies_df):
    """Generate mailto link for Dividers report"""
    today_str = date.today().strftime('%Y-%m-%d')
    subject = f'Dividers Daily Report - {today_str}'
    body = generate_dividers_report_body(
        stocks, threshold, stores_df, shipments_df,
        magnet_stock, magnet_status, upcoming_launches, discrepancies_df
    )
    return _build_mailto_link(subject, body)


# ==================== IT EQUIPMENT REPORT ====================

def generate_it_report_body(stocks, threshold, requirements, shipped_totals,
                             rdcs_df, shipments_df, upcoming_launches, rdc_progress):
    """Generate plain text body for IT Equipment daily report"""
    today = date.today().strftime('%A, %B %d, %Y')
    
    body = ''
    body += _line('💻 4M IT EQUIPMENT DAILY REPORT')
    body += _line(today)
    body += _separator()
    body += _line()
    
    # === EQUIPMENT STOCK ===
    body += _line('📦 EQUIPMENT STOCK')
    body += _sub_separator()
    for item, qty in stocks.items():
        req = requirements.get(item, 0)
        if qty == 0:
            status = '❌ OUT'
        elif req > 0 and qty < req:
            status = '⚠️ LOW'
        elif qty < threshold:
            status = '⚠️ LOW'
        else:
            status = '✅ OK'
        body += _line(f'  {item}: Stock={qty} | Req={req}  {status}')
    body += _line()
    
    # === SHIPPED SUMMARY ===
    body += _line('🚚 SHIPPED TOTALS')
    body += _sub_separator()
    total_req = sum(requirements.values())
    total_ship = sum(shipped_totals.values())
    for item in stocks.keys():
        req = requirements.get(item, 0)
        ship = shipped_totals.get(item, 0)
        pending = max(0, req - ship)
        pct = (ship / req * 100) if req > 0 else 0
        body += _line(f'  {item}')
        body += _line(f'       Required={req} | Shipped={ship} | Pending={pending} ({pct:.0f}%)')
    body += _line()
    body += _line(f'  TOTAL: Required={total_req} | Shipped={total_ship} | Pending={max(0, total_req - total_ship)}')
    body += _line()
    
    # === RDCs OVERVIEW ===
    total_rdcs = len(rdcs_df) if not rdcs_df.empty else 0
    body += _line(f'🏢 RDCs OVERVIEW ({total_rdcs} RDCs)')
    body += _sub_separator()
    
    if rdc_progress:
        for rdc in rdc_progress:
            status_icon = '✅' if rdc['pct'] >= 100 else ('🟡' if rdc['pct'] > 0 else '🔴')
            body += _line(f'  {status_icon} {rdc["name"]} ({rdc["location"]})')
            body += _line(f'       Req={rdc["total_req"]} | Ship={rdc["total_ship"]} | Pend={rdc["total_pending"]} ({rdc["pct"]:.0f}%)')
    body += _line()
    
    # === UPCOMING LAUNCHES ===
    if not upcoming_launches.empty:
        body += _line(f'🚀 UPCOMING LAUNCHES ({len(upcoming_launches)} in next 4 days)')
        body += _sub_separator()
        for _, rdc in upcoming_launches.iterrows():
            days = rdc['days_left']
            name = rdc['name']
            loc = rdc.get('location') or 'N/A'
            transport = '✅' if rdc.get('transportation_ready') else '❌'
            
            if days == 0:
                urgency = '🚀 TODAY!'
            elif days == 1:
                urgency = '🚨 TOMORROW!'
            elif days <= 2:
                urgency = '⚠️ URGENT'
            else:
                urgency = '📅'
            
            body += _line(f'  {urgency} {name} ({loc})')
            body += _line(f'       Launch: {rdc["launch_date"]}  |  Days Left: {days}  |  Transport: {transport}')
        body += _line()
    
    # === PENDING SHIPMENTS ===
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        pending_ships = shipments_df[shipments_df['delivery_status'].isin(['Pending', 'In Transit', 'Delayed'])]
        
        if not pending_ships.empty:
            body += _line(f'🚚 PENDING SHIPMENTS ({len(pending_ships)})')
            body += _sub_separator()
            
            for status in ['Pending', 'In Transit', 'Delayed']:
                subset = pending_ships[pending_ships['delivery_status'] == status]
                if not subset.empty:
                    emoji = {'Pending': '🟡', 'In Transit': '🔵', 'Delayed': '🔴'}[status]
                    body += _line(f'  {emoji} {status}: {len(subset)}')
                    for _, ship in subset.iterrows():
                        receiver = ship.get('receiver_name') or '—'
                        body += _line(f'       #{ship["id"]} - {ship["rdc_name"]} - {ship["date"]} - Receiver: {receiver}')
            body += _line()
    
    # === FOOTER ===
    body += _separator()
    body += _line('Generated from Launch Team Tracker')
    body += _line('Launch Team • Amazon Now')
    body += _line(f'Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    
    return body


def generate_it_mailto(stocks, threshold, requirements, shipped_totals,
                        rdcs_df, shipments_df, upcoming_launches, rdc_progress):
    """Generate mailto link for IT Equipment report"""
    today_str = date.today().strftime('%Y-%m-%d')
    subject = f'4M IT Equipment Daily Report - {today_str}'
    body = generate_it_report_body(
        stocks, threshold, requirements, shipped_totals,
        rdcs_df, shipments_df, upcoming_launches, rdc_progress
    )
    return _build_mailto_link(subject, body)
