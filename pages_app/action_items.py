"""
Action Items management page
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import (
    get_action_items, add_action_item, update_action_item,
    delete_action_item, update_action_status, get_stores
)
from components import render_section_title, render_stat_card


STATUS_OPTIONS = ['Pending', 'In Progress', 'Completed', 'Blocked']
PRIORITY_OPTIONS = ['High', 'Medium', 'Low']

STATUS_CONFIG = {
    'Pending':     {'emoji': '🟡', 'color': '#f39c12', 'bg': 'rgba(243, 156, 18, 0.08)'},
    'In Progress': {'emoji': '🔵', 'color': '#3498db', 'bg': 'rgba(52, 152, 219, 0.08)'},
    'Completed':   {'emoji': '🟢', 'color': '#27ae60', 'bg': 'rgba(39, 174, 96, 0.08)'},
    'Blocked':     {'emoji': '🔴', 'color': '#e74c3c', 'bg': 'rgba(231, 76, 60, 0.08)'},
}

PRIORITY_CONFIG = {
    'High':   {'emoji': '🔥', 'color': '#e74c3c'},
    'Medium': {'emoji': '⚡', 'color': '#f39c12'},
    'Low':    {'emoji': '🌱', 'color': '#27ae60'},
}


def get_eta_status(eta):
    """Return ETA status (overdue, due soon, upcoming)"""
    if not eta:
        return '', '', ''

    if isinstance(eta, str):
        eta = date.fromisoformat(eta)

    today = date.today()
    days_left = (eta - today).days

    if days_left < 0:
        return '🚨', 'OVERDUE', '#e74c3c'
    elif days_left == 0:
        return '⚠️', 'DUE TODAY', '#e67e22'
    elif days_left <= 3:
        return '🔔', 'DUE SOON', '#f39c12'
    else:
        return '📅', f'{days_left}d', '#3498db'


def render_action_card(item, stores_df, idx):
    """Render an action item card"""
    status = item.get('status') or 'Pending'
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG['Pending'])

    priority = item.get('priority') or 'Medium'
    pcfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG['Medium'])

    eta = item.get('eta')
    eta_emoji, eta_label, eta_color = get_eta_status(eta)
    eta_str = str(eta) if eta else '—'

    store_name = item.get('store_name') or '—'
    owner = item.get('owner') or '—'
    notes = item.get('notes') or ''
    action = item.get('action_text') or ''

    # Badges
    status_badge = (
        '<span style="background:' + cfg['color'] + '; color:white; padding:3px 10px; '
        'border-radius:10px; font-size:0.72rem; font-weight:700;">'
        + cfg['emoji'] + ' ' + status + '</span>'
    )

    priority_badge = (
        '<span style="background:' + pcfg['color'] + '20; color:' + pcfg['color'] + '; '
        'padding:3px 10px; border-radius:10px; font-size:0.72rem; font-weight:700; '
        'border:1px solid ' + pcfg['color'] + '60;">'
        + pcfg['emoji'] + ' ' + priority + '</span>'
    )

    eta_badge = ''
    if eta_label:
        eta_badge = (
            '<span style="background:' + eta_color + '; color:white; padding:3px 10px; '
            'border-radius:10px; font-size:0.72rem; font-weight:700;">'
            + eta_emoji + ' ' + eta_label + '</span>'
        )

    # Build card
    card_html = (
        '<div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, ' + cfg['bg'] + ' 100%);'
        'border-left: 5px solid ' + cfg['color'] + ';'
        'border-radius: 14px;'
        'padding: 16px 20px;'
        'margin-bottom: 12px;'
        'box-shadow: 0 4px 16px rgba(0,0,0,0.08);">'

        '<div style="display:flex; justify-content:space-between; align-items:flex-start; '
        'margin-bottom:10px; flex-wrap:wrap; gap:8px;">'
        '<div style="flex:1; min-width:200px;">'
        '<div style="font-size:1rem; font-weight:700; margin-bottom:6px;">'
        '#' + str(item['id']) + ' — ' + action + '</div>'
        '<div style="font-size:0.8rem; opacity:0.85;">'
        '👤 <b>' + owner + '</b>'
        + (' | 🏪 ' + store_name if store_name != '—' else '') +
        ' | 📅 ETA: <b>' + eta_str + '</b>'
        '</div>'
        '</div>'
        '<div style="display:flex; gap:6px; flex-wrap:wrap; align-items:flex-start;">'
        + status_badge + priority_badge + eta_badge +
        '</div>'
        '</div>'
    )

    if notes:
        card_html += (
            '<div style="padding-top:8px; border-top:1px dashed rgba(127,140,141,0.3); '
            'font-size:0.8rem; opacity:0.85;">'
            '📝 ' + notes + '</div>'
        )

    card_html += '</div>'

    st.markdown(card_html, unsafe_allow_html=True)

    # Quick actions
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    new_status = c1.selectbox(
        'Update Status',
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
        key='ai_status_' + str(item['id']) + '_' + str(idx),
        label_visibility='collapsed'
    )
    if c2.button('💾', key='ai_upd_' + str(item['id']) + '_' + str(idx),
                 use_container_width=True, help='Update Status'):
        update_action_status(item['id'], new_status)
        st.success('✅ Updated')
        st.rerun()

    if c3.button('✏️', key='ai_edit_' + str(item['id']) + '_' + str(idx),
                 use_container_width=True, help='Edit'):
        st.session_state['edit_action_id'] = item['id']
        st.rerun()

    if c4.button('🗑️', key='ai_del_' + str(item['id']) + '_' + str(idx),
                 use_container_width=True, help='Delete'):
        delete_action_item(item['id'])
        st.warning('🗑️ Deleted')
        st.rerun()


def render_edit_form(item, stores_df):
    """Render edit form for an action item"""
    store_options = {'(None)': None}
    if not stores_df.empty:
        for _, store in stores_df.iterrows():
            store_options[store['name']] = store['id']

    with st.form('edit_action_form'):
        st.markdown('### ✏️ Edit Action Item #' + str(item['id']))

        action_text = st.text_area('Action', value=item.get('action_text') or '')

        c1, c2 = st.columns(2)
        owner = c1.text_input('Owner', value=item.get('owner') or '')

        current_eta = None
        eta_val = item.get('eta')
        if eta_val:
            if isinstance(eta_val, str):
                current_eta = date.fromisoformat(eta_val)
            else:
                current_eta = eta_val

        eta = c2.date_input('ETA', value=current_eta)

        c1, c2, c3 = st.columns(3)
        status = c1.selectbox(
            'Status',
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(item.get('status') or 'Pending')
        )
        priority = c2.selectbox(
            'Priority',
            PRIORITY_OPTIONS,
            index=PRIORITY_OPTIONS.index(item.get('priority') or 'Medium')
        )

        current_store_name = '(None)'
        if item.get('store_id') and not stores_df.empty:
            matching = stores_df[stores_df['id'] == item['store_id']]
            if not matching.empty:
                current_store_name = matching.iloc[0]['name']

        store_key = c3.selectbox(
            'Store',
            list(store_options.keys()),
            index=list(store_options.keys()).index(current_store_name) if current_store_name in store_options else 0
        )
        store_id = store_options[store_key]

        notes = st.text_area('Notes', value=item.get('notes') or '')

        c1, c2 = st.columns(2)
        save_btn = c1.form_submit_button('💾 Save', use_container_width=True)
        cancel_btn = c2.form_submit_button('❌ Cancel', use_container_width=True)

        if save_btn:
            update_action_item(
                item['id'], action_text, owner, eta, status,
                store_id, priority, notes
            )
            del st.session_state['edit_action_id']
            st.success('✅ Updated!')
            st.rerun()

        if cancel_btn:
            del st.session_state['edit_action_id']
            st.rerun()


def render():
    """Render the Action Items page"""
    st.markdown('# 📝 Action Items')
    st.caption('Track tasks, owners, and deadlines')

    stores_df = get_stores()

    # Check if editing
    if 'edit_action_id' in st.session_state:
        items_df = get_action_items()
        if not items_df.empty:
            editing = items_df[items_df['id'] == st.session_state['edit_action_id']]
            if not editing.empty:
                render_edit_form(editing.iloc[0], stores_df)
                return

    # Add new action
    with st.expander('➕ **Add New Action Item**', expanded=False):
        store_options = {'(None)': None}
        if not stores_df.empty:
            for _, store in stores_df.iterrows():
                store_options[store['name']] = store['id']

        with st.form('add_action', clear_on_submit=True):
            action_text = st.text_area('Action *', placeholder='Describe the action...')

            c1, c2 = st.columns(2)
            owner = c1.text_input('Owner *', placeholder='e.g. John Doe')
            eta = c2.date_input('ETA', value=date.today() + timedelta(days=7))

            c1, c2, c3 = st.columns(3)
            status = c1.selectbox('Status', STATUS_OPTIONS)
            priority = c2.selectbox('Priority', PRIORITY_OPTIONS, index=1)
            store_key = c3.selectbox('Store (optional)', list(store_options.keys()))
            store_id = store_options[store_key]

            notes = st.text_area('Notes (optional)', placeholder='Additional details...')

            if st.form_submit_button('➕ Add Action Item', use_container_width=True):
                if action_text and owner:
                    add_action_item(
                        action_text, owner, eta, status,
                        store_id, priority, notes
                    )
                    st.success('✅ Action item added!')
                    st.rerun()
                else:
                    st.error('❌ Please fill in Action and Owner')

    # Load all items
    items_df = get_action_items()

    if items_df.empty:
        st.info('📭 No action items yet.')
        return

    # Stats
    render_section_title('📊 Overview')

    total = len(items_df)
    pending = len(items_df[items_df['status'] == 'Pending'])
    in_progress = len(items_df[items_df['status'] == 'In Progress'])
    completed = len(items_df[items_df['status'] == 'Completed'])
    blocked = len(items_df[items_df['status'] == 'Blocked'])

    # Count overdue
    today = date.today()
    overdue = 0
    if 'eta' in items_df.columns:
        items_df['eta_date'] = pd.to_datetime(items_df['eta'], errors='coerce').dt.date
        overdue = len(items_df[
            (items_df['eta_date'].notna()) &
            (items_df['eta_date'] < today) &
            (items_df['status'] != 'Completed')
        ])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_stat_card('Total', total, 'card-stores', 'bi-list-task')
    with c2:
        render_stat_card('Pending', pending, 'card-40d', 'bi-hourglass-split')
    with c3:
        render_stat_card('In Progress', in_progress, 'card-30d', 'bi-arrow-repeat')
    with c4:
        render_stat_card('Completed', completed, 'card-shipments', 'bi-check-circle-fill')
    with c5:
        st.markdown(
            '<div class="stat-card" style="border-left:5px solid #e74c3c;">'
            '<i class="bi bi-exclamation-triangle-fill icon-bg" style="color:#e74c3c;"></i>'
            '<div class="stat-label">Overdue</div>'
            '<div class="stat-value" style="color:#e74c3c;">' + str(overdue) + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    # Filters
    render_section_title('📋 All Action Items')

    c1, c2, c3 = st.columns([1, 1, 2])
    status_filter = c1.selectbox('Status', ['All'] + STATUS_OPTIONS, key='ai_filter_status')
    priority_filter = c2.selectbox('Priority', ['All'] + PRIORITY_OPTIONS, key='ai_filter_priority')
    search = c3.text_input('🔍 Search', placeholder='Search by action text or owner...', key='ai_search')

    filtered = items_df.copy()
    if status_filter != 'All':
        filtered = filtered[filtered['status'] == status_filter]
    if priority_filter != 'All':
        filtered = filtered[filtered['priority'] == priority_filter]
    if search:
        search_lower = search.lower()
        mask = (
            filtered['action_text'].fillna('').str.lower().str.contains(search_lower, na=False) |
            filtered['owner'].fillna('').str.lower().str.contains(search_lower, na=False)
        )
        filtered = filtered[mask]

    if filtered.empty:
        st.info('📭 No action items match the filters.')
        return

    # Sort: overdue first, then by eta
    filtered['_sort_eta'] = pd.to_datetime(filtered['eta'], errors='coerce')
    filtered = filtered.sort_values('_sort_eta', na_position='last')

    # Render cards
    items_list = list(filtered.iterrows())
    for i, (_, item) in enumerate(items_list):
        render_action_card(item, stores_df, i)
