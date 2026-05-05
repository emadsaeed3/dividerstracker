"""
Notifications page - Shows all alerts from both sections
"""
import streamlit as st
from notifications import (
    get_all_notifications, get_notifications_count,
    SEVERITY_CONFIG, CRITICAL, WARNING, INFO
)
from components import render_section_title


def render_notification_card(notif, idx):
    """Render a single notification card"""
    severity = notif['severity']
    cfg = SEVERITY_CONFIG[severity]

    section = notif.get('section', '')
    section_label = '📦 Dividers' if section == 'dividers' else ('💻 IT' if section == 'it' else '')

    category = notif.get('category', '')
    goto_page = notif.get('goto_page', '')

    # Build card HTML
    card_html = (
        '<div style="background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, ' + cfg['bg'] + ' 100%);'
        'border-left: 5px solid ' + cfg['color'] + ';'
        'border-radius: 14px;'
        'padding: 16px 20px;'
        'margin-bottom: 12px;'
        'box-shadow: 0 4px 16px rgba(0,0,0,0.08);">'

        '<div style="display:flex; justify-content:space-between; align-items:flex-start; '
        'margin-bottom:8px; flex-wrap:wrap; gap:8px;">'

        '<div style="flex:1; min-width:200px;">'
        '<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px; flex-wrap:wrap;">'
        '<span style="background:' + cfg['color'] + '; color:white; padding:3px 10px; '
        'border-radius:10px; font-size:0.72rem; font-weight:700;">'
        + cfg['emoji'] + ' ' + cfg['label'] + '</span>'
    )

    if section_label:
        card_html += (
            '<span style="background:rgba(127,140,141,0.2); padding:3px 10px; '
            'border-radius:10px; font-size:0.72rem; font-weight:600;">'
            + section_label + '</span>'
        )

    if category:
        card_html += (
            '<span style="background:rgba(52, 152, 219, 0.15); color:#3498db; padding:3px 10px; '
            'border-radius:10px; font-size:0.72rem; font-weight:600;">'
            + category + '</span>'
        )

    card_html += (
        '</div>'
        '<div style="font-size:1rem; font-weight:700; margin-bottom:4px;">'
        + notif['title'] + '</div>'
        '<div style="font-size:0.85rem; opacity:0.85;">'
        + notif['message'] + '</div>'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

    # Go to button
    if goto_page:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c3:
            if st.button('🔗 Go to', key='goto_' + str(idx), use_container_width=True):
                # Switch to the correct section and page
                st.session_state.section = section
                # Note: Streamlit radio doesn't support direct page selection
                # but the user can navigate easily after the section switches
                st.success('Navigating to ' + goto_page + '...')
                st.rerun()


def render():
    """Render the notifications page"""
    st.markdown('# 🔔 Notifications')
    st.caption('All alerts and notifications from both sections')

    # Get all notifications
    notifs = get_all_notifications()

    if not notifs:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:4rem; margin-bottom:15px;">✨</div>
            <div style="font-size:1.5rem; font-weight:700; margin-bottom:8px;">All Clear!</div>
            <div style="font-size:1rem; opacity:0.7;">No notifications right now. Everything looks good.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Count by severity
    critical_count = sum(1 for n in notifs if n['severity'] == CRITICAL)
    warning_count = sum(1 for n in notifs if n['severity'] == WARNING)
    info_count = sum(1 for n in notifs if n['severity'] == INFO)

    # Overview
    render_section_title('📊 Overview')
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #95a5a6;">
            <i class="bi bi-bell-fill icon-bg"></i>
            <div class="stat-label">Total</div>
            <div class="stat-value">{len(notifs)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #e74c3c;">
            <i class="bi bi-exclamation-triangle-fill icon-bg" style="color:#e74c3c;"></i>
            <div class="stat-label">Critical</div>
            <div class="stat-value" style="color:#e74c3c;">{critical_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #f39c12;">
            <i class="bi bi-exclamation-circle-fill icon-bg" style="color:#f39c12;"></i>
            <div class="stat-label">Warning</div>
            <div class="stat-value" style="color:#f39c12;">{warning_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="stat-card" style="border-left:5px solid #3498db;">
            <i class="bi bi-info-circle-fill icon-bg" style="color:#3498db;"></i>
            <div class="stat-label">Info</div>
            <div class="stat-value" style="color:#3498db;">{info_count}</div>
        </div>
        """, unsafe_allow_html=True)

    # Filters
    render_section_title('📋 All Notifications')

    c1, c2, c3 = st.columns([1, 1, 1])

    severity_filter = c1.selectbox(
        'Severity',
        ['All', '🚨 Critical', '⚠️ Warning', 'ℹ️ Info'],
        key='notif_severity'
    )

    section_filter = c2.selectbox(
        'Section',
        ['All', '📦 Dividers', '💻 IT Equipment'],
        key='notif_section'
    )

    # Get unique categories
    categories = sorted(set(n.get('category', 'General') for n in notifs))
    category_filter = c3.selectbox(
        'Category',
        ['All'] + categories,
        key='notif_category'
    )

    # Apply filters
    filtered = notifs[:]

    if severity_filter == '🚨 Critical':
        filtered = [n for n in filtered if n['severity'] == CRITICAL]
    elif severity_filter == '⚠️ Warning':
        filtered = [n for n in filtered if n['severity'] == WARNING]
    elif severity_filter == 'ℹ️ Info':
        filtered = [n for n in filtered if n['severity'] == INFO]

    if section_filter == '📦 Dividers':
        filtered = [n for n in filtered if n.get('section') == 'dividers']
    elif section_filter == '💻 IT Equipment':
        filtered = [n for n in filtered if n.get('section') == 'it']

    if category_filter != 'All':
        filtered = [n for n in filtered if n.get('category') == category_filter]

    if not filtered:
        st.info('📭 No notifications match the filters.')
        return

    st.markdown(f'**Showing {len(filtered)} of {len(notifs)} notifications**')
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Render all notifications
    for idx, notif in enumerate(filtered):
        render_notification_card(notif, idx)
