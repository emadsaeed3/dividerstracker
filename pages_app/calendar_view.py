"""
Calendar View - Shows launches, shipments, and action items on a calendar
"""
import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
from database import get_stores, get_shipments, get_action_items
from components import render_section_title


EVENT_COLORS = {
    'launch': '#e74c3c',       # Red - Launch dates
    'shipment': '#3498db',     # Blue - Shipments
    'scheduled': '#9b59b6',    # Purple - Scheduled shipments
    'action': '#f39c12',       # Orange - Action items
    'launched': '#27ae60',     # Green - Already launched
}

EVENT_ICONS = {
    'launch': '🚀',
    'shipment': '🚚',
    'scheduled': '📆',
    'action': '📝',
    'launched': '✅',
}


def collect_events(stores_df, shipments_df, action_items_df):
    """Collect all events grouped by date"""
    events = {}  # {date: [list of events]}

    def add_event(event_date, event_type, title, subtitle='', item_id=None):
        if not event_date:
            return
        if isinstance(event_date, str):
            try:
                event_date = date.fromisoformat(event_date)
            except Exception:
                return
        if event_date not in events:
            events[event_date] = []
        events[event_date].append({
            'type': event_type,
            'title': title,
            'subtitle': subtitle,
            'id': item_id,
        })

    # Launch dates from stores
    if not stores_df.empty and 'launch_date' in stores_df.columns:
        for _, store in stores_df.iterrows():
            ld = store.get('launch_date')
            if ld:
                is_launched = bool(store.get('is_launched', False))
                event_type = 'launched' if is_launched else 'launch'
                add_event(
                    ld,
                    event_type,
                    '🏪 ' + str(store['name']),
                    'Location: ' + str(store.get('location') or 'N/A'),
                    store['id']
                )

    # Shipment dates
    if not shipments_df.empty:
        for _, ship in shipments_df.iterrows():
            # Shipped date
            ship_date = ship.get('date')
            if ship_date:
                total = int(ship.get('qty_30d', 0)) + int(ship.get('qty_40d', 0)) + int(ship.get('qty_60d', 0))
                store_name = str(ship.get('store_name', 'Unknown'))
                add_event(
                    ship_date,
                    'shipment',
                    '🚚 ' + store_name,
                    str(total) + ' units | Status: ' + str(ship.get('delivery_status', 'Pending')),
                    ship['id']
                )

            # Scheduled date (if different from ship date)
            sched = ship.get('scheduled_date')
            if sched and sched != ship_date:
                store_name = str(ship.get('store_name', 'Unknown'))
                add_event(
                    sched,
                    'scheduled',
                    '📆 Scheduled: ' + store_name,
                    'Shipment #' + str(ship['id']),
                    ship['id']
                )

    # Action Items ETAs
    if not action_items_df.empty and 'eta' in action_items_df.columns:
        for _, item in action_items_df.iterrows():
            if item.get('status') == 'Completed':
                continue
            eta = item.get('eta')
            if eta:
                action_text = str(item.get('action_text', ''))[:40]
                owner = str(item.get('owner') or '—')
                add_event(
                    eta,
                    'action',
                    '📝 ' + action_text,
                    'Owner: ' + owner,
                    item['id']
                )

    return events


def render_month_calendar(year, month, events):
    """Render a monthly calendar as a table"""
    cal = calendar.Calendar(firstweekday=6)  # Sunday first
    weeks = cal.monthdatescalendar(year, month)
    today = date.today()

    # Build HTML table
    html = '<div style="overflow-x:auto;">'
    html += '<table style="width:100%; border-collapse:separate; border-spacing:4px; font-family:inherit;">'

    # Header row (days)
    html += '<tr>'
    for day_name in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']:
        html += (
            '<th style="background:#2c3e50; color:white; padding:10px; '
            'border-radius:8px; font-size:0.85rem; font-weight:700;">'
            + day_name + '</th>'
        )
    html += '</tr>'

    # Calendar rows
    for week in weeks:
        html += '<tr>'
        for day in week:
            is_current_month = day.month == month
            is_today = day == today
            day_events = events.get(day, [])

            # Cell styling
            if not is_current_month:
                cell_bg = 'rgba(127,140,141,0.05)'
                cell_opacity = '0.4'
            else:
                cell_bg = 'rgba(255,255,255,0.04)'
                cell_opacity = '1'

            border_style = ''
            if is_today:
                border_style = 'border:2px solid #3498db;'
                cell_bg = 'rgba(52, 152, 219, 0.1)'

            html += (
                '<td style="background:' + cell_bg + '; '
                'border-radius:8px; padding:8px; vertical-align:top; '
                'min-width:110px; height:110px; opacity:' + cell_opacity + '; '
                + border_style + '">'
            )

            # Day number
            day_color = '#3498db' if is_today else 'inherit'
            html += (
                '<div style="font-weight:700; font-size:0.95rem; '
                'margin-bottom:4px; color:' + day_color + ';">'
                + str(day.day) + '</div>'
            )

            # Events (max 3 visible, rest as "+N more")
            max_visible = 3
            visible = day_events[:max_visible]
            remaining = len(day_events) - max_visible

            for ev in visible:
                color = EVENT_COLORS.get(ev['type'], '#7f8c8d')
                # Shorten title
                title = ev['title']
                if len(title) > 18:
                    title = title[:17] + '…'
                html += (
                    '<div style="background:' + color + '; color:white; '
                    'padding:2px 6px; border-radius:4px; font-size:0.7rem; '
                    'margin-bottom:2px; white-space:nowrap; overflow:hidden; '
                    'text-overflow:ellipsis; font-weight:600;" '
                    'title="' + ev['title'] + ' — ' + ev.get('subtitle', '') + '">'
                    + title + '</div>'
                )

            if remaining > 0:
                html += (
                    '<div style="font-size:0.7rem; opacity:0.7; '
                    'font-weight:600; padding:2px 6px;">+' + str(remaining) + ' more</div>'
                )

            html += '</td>'
        html += '</tr>'

    html += '</table></div>'
    st.markdown(html, unsafe_allow_html=True)


def render_day_details(events, selected_date):
    """Render details of events for a selected date"""
    day_events = events.get(selected_date, [])

    if not day_events:
        st.info('📭 No events on this date.')
        return

    st.markdown('### 📅 Events on ' + selected_date.strftime('%A, %B %d, %Y'))

    for ev in day_events:
        color = EVENT_COLORS.get(ev['type'], '#7f8c8d')
        icon = EVENT_ICONS.get(ev['type'], '📌')

        st.markdown(
            '<div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, ' + color + '15 100%);'
            'border-left: 5px solid ' + color + ';'
            'border-radius: 10px;'
            'padding: 12px 16px;'
            'margin-bottom: 10px;">'
            '<div style="font-weight:700; font-size:1rem;">'
            + icon + ' ' + ev['title'] + '</div>'
            + ('<div style="font-size:0.85rem; opacity:0.8; margin-top:4px;">'
               + ev.get('subtitle', '') + '</div>' if ev.get('subtitle') else '')
            + '</div>',
            unsafe_allow_html=True
        )


def render():
    """Render the Calendar View page"""
    st.markdown('# 📅 Calendar View')
    st.caption('See all launches, shipments, and action items on a calendar')

    # Load data
    stores_df = get_stores()
    shipments_df = get_shipments()
    action_items_df = get_action_items()

    # Collect events
    events = collect_events(stores_df, shipments_df, action_items_df)

    # Legend
    st.markdown("""
    <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
        <b>Legend:</b>
        <span style="background:#e74c3c; color:white; padding:3px 10px; border-radius:10px; margin:0 4px; font-size:0.75rem;">🚀 Launch</span>
        <span style="background:#27ae60; color:white; padding:3px 10px; border-radius:10px; margin:0 4px; font-size:0.75rem;">✅ Launched</span>
        <span style="background:#3498db; color:white; padding:3px 10px; border-radius:10px; margin:0 4px; font-size:0.75rem;">🚚 Shipment</span>
        <span style="background:#9b59b6; color:white; padding:3px 10px; border-radius:10px; margin:0 4px; font-size:0.75rem;">📆 Scheduled</span>
        <span style="background:#f39c12; color:white; padding:3px 10px; border-radius:10px; margin:0 4px; font-size:0.75rem;">📝 Action</span>
    </div>
    """, unsafe_allow_html=True)

    # Month navigation
    if 'calendar_year' not in st.session_state:
        st.session_state.calendar_year = date.today().year
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = date.today().month

    c1, c2, c3, c4, c5 = st.columns([1, 1, 3, 1, 1])

    with c1:
        if st.button('◀️ Prev', use_container_width=True, key='cal_prev'):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
            st.rerun()

    with c2:
        if st.button('📅 Today', use_container_width=True, key='cal_today'):
            st.session_state.calendar_year = date.today().year
            st.session_state.calendar_month = date.today().month
            st.rerun()

    with c3:
        month_name = calendar.month_name[st.session_state.calendar_month]
        st.markdown(
            '<div style="text-align:center; font-size:1.4rem; font-weight:700; padding-top:6px;">'
            + month_name + ' ' + str(st.session_state.calendar_year) + '</div>',
            unsafe_allow_html=True
        )

    with c5:
        if st.button('Next ▶️', use_container_width=True, key='cal_next'):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1
            st.rerun()

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # Render calendar
    render_month_calendar(
        st.session_state.calendar_year,
        st.session_state.calendar_month,
        events
    )

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Day details picker
    render_section_title('🔍 View Day Details')

    selected_date = st.date_input(
        'Select a date to see events',
        value=date.today(),
        key='cal_date_picker'
    )

    render_day_details(events, selected_date)

    # Events this month summary
    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
    render_section_title('📊 This Month Summary')

    month_events = [
        ev for d, evs in events.items()
        if d.year == st.session_state.calendar_year and d.month == st.session_state.calendar_month
        for ev in evs
    ]

    launches = sum(1 for ev in month_events if ev['type'] == 'launch')
    launched = sum(1 for ev in month_events if ev['type'] == 'launched')
    ships = sum(1 for ev in month_events if ev['type'] == 'shipment')
    scheds = sum(1 for ev in month_events if ev['type'] == 'scheduled')
    acts = sum(1 for ev in month_events if ev['type'] == 'action')

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #e74c3c;">
            <i class="bi bi-rocket-takeoff icon-bg" style="color:#e74c3c;"></i>
            <div class="stat-label">Launches</div>
            <div class="stat-value" style="color:#e74c3c;">{launches}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #27ae60;">
            <i class="bi bi-check-circle-fill icon-bg" style="color:#27ae60;"></i>
            <div class="stat-label">Launched</div>
            <div class="stat-value" style="color:#27ae60;">{launched}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #3498db;">
            <i class="bi bi-truck icon-bg" style="color:#3498db;"></i>
            <div class="stat-label">Shipments</div>
            <div class="stat-value" style="color:#3498db;">{ships}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #9b59b6;">
            <i class="bi bi-calendar-event icon-bg" style="color:#9b59b6;"></i>
            <div class="stat-label">Scheduled</div>
            <div class="stat-value" style="color:#9b59b6;">{scheds}</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #f39c12;">
            <i class="bi bi-list-task icon-bg" style="color:#f39c12;"></i>
            <div class="stat-label">Actions</div>
            <div class="stat-value" style="color:#f39c12;">{acts}</div>
        </div>
        """, unsafe_allow_html=True)
