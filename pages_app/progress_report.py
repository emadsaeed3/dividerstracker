"""
Progress Report page
Manages report settings and generates PDF reports
"""
import streamlit as st
from datetime import date, datetime, timedelta
from database import (
    get_report_settings, update_report_settings,
    get_stores, get_shipments, get_stocks_dict, get_threshold,
    get_magnet_stock, get_magnet_status_dict,
    get_action_items, get_upcoming_launches
)
from components import render_section_title, render_stat_card
from pdf_generator import generate_progress_report


def auto_suggest_highlights(stores_df, shipments_df):
    """Auto-generate highlight suggestions"""
    suggestions = []
    today = date.today()

    # Recently launched stores
    if not stores_df.empty and 'is_launched' in stores_df.columns:
        launched = stores_df[stores_df['is_launched'] == True]
        if not launched.empty:
            for _, store in launched.head(3).iterrows():
                name = store['name']
                loc = store.get('location') or 'N/A'
                suggestions.append(f"✓ {name} ({loc}) is launched and operational")

    # Recent deliveries
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        delivered = shipments_df[shipments_df['delivery_status'] == 'Delivered']
        if not delivered.empty:
            total_delivered = len(delivered)
            suggestions.append(f"✓ {total_delivered} shipments successfully delivered to stores")

    return '\n'.join(suggestions) if suggestions else ''


def auto_suggest_lowlights(stocks, threshold, stores_df, shipments_df, magnet_stock, magnet_status):
    """Auto-generate lowlight suggestions"""
    suggestions = []

    # Stock shortages
    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = stores_df[col].sum() if not stores_df.empty else 0
        shipped = shipments_df[ship_col].sum() if not shipments_df.empty else 0
        remaining = max(0, required - shipped)

        if stock < remaining:
            shortage = remaining - stock
            suggestions.append(f"⚠ {dtype} shortage: Need {shortage} more units to cover pending")
        elif stock < threshold and stock > 0:
            suggestions.append(f"⚠ {dtype} low stock: Only {stock} units left")
        elif stock == 0:
            suggestions.append(f"❌ {dtype} OUT OF STOCK")

    # Magnet shortage
    total_without_magnet = sum(
        magnet_status.get(t, {}).get('without_magnet', 0)
        for t in ['30D', '40D', '60D']
    )
    if total_without_magnet > 0 and magnet_stock < total_without_magnet:
        shortage = total_without_magnet - magnet_stock
        suggestions.append(f"⚠ Magnet strips shortage: Need {shortage} more to cover all dividers")

    # Overdue launches
    if not stores_df.empty and 'launch_date' in stores_df.columns:
        today = date.today()
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
                days_left = (ld_obj - today).days
                if days_left < 0:
                    suggestions.append(f"⚠ {store['name']} launch date passed ({abs(days_left)}d ago) - not yet launched")
                elif days_left <= 2 and not store.get('transportation_ready'):
                    suggestions.append(f"⚠ {store['name']} launches in {days_left}d - transportation NOT ready")
            except Exception:
                pass

    return '\n'.join(suggestions) if suggestions else ''


def render():
    """Render the Progress Report page"""
    st.markdown('# 📄 Progress Report')
    st.caption('Configure report settings and generate professional PDF reports')

    # Load data
    settings = get_report_settings()
    stocks = get_stocks_dict()
    threshold = get_threshold()
    stores_df = get_stores()
    shipments_df = get_shipments()
    magnet_stock = get_magnet_stock()
    magnet_status = get_magnet_status_dict()
    action_items_df = get_action_items()

    # === QUICK STATS ===
    render_section_title('📊 Report Preview Stats')

    total_stores = len(stores_df) if not stores_df.empty else 0
    launched_count = len(stores_df[stores_df['is_launched'] == True]) if not stores_df.empty and 'is_launched' in stores_df.columns else 0
    upcoming_count = total_stores - launched_count

    pending_ships = 0
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        pending_ships = len(shipments_df[
            shipments_df['delivery_status'].isin(['Pending', 'In Transit', 'Delayed'])
        ])

    open_actions = 0
    if not action_items_df.empty and 'status' in action_items_df.columns:
        open_actions = len(action_items_df[action_items_df['status'] != 'Completed'])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_stat_card('Total Stores', total_stores, 'card-stores', 'bi-shop')
    with c2:
        render_stat_card('Launched', launched_count, 'card-shipments', 'bi-check-circle-fill')
    with c3:
        render_stat_card('Upcoming', upcoming_count, 'card-30d', 'bi-rocket-takeoff')
    with c4:
        render_stat_card('Pending Ships', pending_ships, 'card-40d', 'bi-truck')
    with c5:
        render_stat_card('Open Actions', open_actions, 'card-60d', 'bi-list-task')

    # === AUTO-SUGGEST BUTTONS (outside forms) ===
    render_section_title('⚙️ Report Settings')

    st.markdown('''
    <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
        💡 Configure the content of your report below. Use auto-suggest to add insights automatically from your data.
    </div>
    ''', unsafe_allow_html=True)

    # Auto-suggest buttons (outside form)
    c1, c2 = st.columns(2)
    with c1:
        if st.button('💡 Auto-Suggest Highlights', use_container_width=True, key='btn_suggest_h'):
            suggestions = auto_suggest_highlights(stores_df, shipments_df)
            if suggestions:
                current_highlights = settings.get('highlights') or ''
                new_highlights = current_highlights + ('\n' if current_highlights else '') + suggestions
                update_report_settings(
                    settings.get('report_title') or 'LAUNCH TEAM TRACKER - PROGRESS REPORT',
                    settings.get('executive_summary') or '',
                    new_highlights,
                    settings.get('lowlights') or '',
                    int(settings.get('week_number') or 1),
                    settings.get('next_update_date')
                )
                st.success('✅ Highlights suggested and saved!')
                st.rerun()
            else:
                st.info('💡 No highlights to suggest right now.')

    with c2:
        if st.button('💡 Auto-Suggest Lowlights', use_container_width=True, key='btn_suggest_l'):
            suggestions = auto_suggest_lowlights(
                stocks, threshold, stores_df, shipments_df,
                magnet_stock, magnet_status
            )
            if suggestions:
                current_lowlights = settings.get('lowlights') or ''
                new_lowlights = current_lowlights + ('\n' if current_lowlights else '') + suggestions
                update_report_settings(
                    settings.get('report_title') or 'LAUNCH TEAM TRACKER - PROGRESS REPORT',
                    settings.get('executive_summary') or '',
                    settings.get('highlights') or '',
                    new_lowlights,
                    int(settings.get('week_number') or 1),
                    settings.get('next_update_date')
                )
                st.success('✅ Lowlights suggested and saved!')
                st.rerun()
            else:
                st.info('💡 No issues detected right now.')

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # === MAIN SETTINGS FORM ===
    with st.form('report_settings_form'):
        c1, c2 = st.columns(2)

        week_number = c1.number_input(
            'Week Number',
            min_value=1,
            max_value=53,
            value=int(settings.get('week_number') or 1)
        )

        current_next_update = settings.get('next_update_date')
        if current_next_update and isinstance(current_next_update, str):
            try:
                current_next_update = date.fromisoformat(current_next_update)
            except Exception:
                current_next_update = None

        next_update_date = c2.date_input(
            'Next Update Date',
            value=current_next_update or (date.today() + timedelta(days=3))
        )

        report_title = st.text_input(
            'Report Title',
            value=settings.get('report_title') or 'LAUNCH TEAM TRACKER - PROGRESS REPORT'
        )

        executive_summary = st.text_area(
            'Executive Summary',
            value=settings.get('executive_summary') or '',
            height=100,
            placeholder='Describe the overall progress...'
        )

        st.markdown('**✅ Highlights** (one point per line)')
        highlights = st.text_area(
            'Highlights',
            value=settings.get('highlights') or '',
            height=120,
            placeholder='• Store A launched successfully\n• All shipments on track',
            label_visibility='collapsed'
        )

        st.markdown('**⚠️ Lowlights** (one point per line)')
        lowlights = st.text_area(
            'Lowlights',
            value=settings.get('lowlights') or '',
            height=120,
            placeholder='• 30D stock shortage\n• Store X transport not ready',
            label_visibility='collapsed'
        )

        save_btn = st.form_submit_button('💾 Save Settings', use_container_width=True, type='primary')

        if save_btn:
            update_report_settings(
                report_title, executive_summary, highlights, lowlights,
                week_number, next_update_date
            )
            st.success('✅ Settings saved!')
            st.rerun()

    # === GENERATE PDF ===
    render_section_title('📥 Generate Report')

    st.markdown('''
    <div style="background: rgba(39, 174, 96, 0.1); padding: 14px 18px; border-radius: 10px; 
                border-left: 4px solid #27ae60; margin-bottom: 16px;">
        🎯 <b>Ready to generate?</b> Click the button below to download a professional PDF report 
        with all the current data and settings above.
    </div>
    ''', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try:
            # Reload settings to make sure we use the latest
            current_settings = get_report_settings()

            pdf_buffer = generate_progress_report(
                current_settings,
                stocks, threshold,
                stores_df, shipments_df,
                magnet_stock, magnet_status,
                action_items_df,
                report_date=date.today()
            )

            week_str = str(current_settings.get('week_number') or 1)
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f'progress_report_W{week_str}_{date_str}.pdf'

            st.download_button(
                label='📥 Download Progress Report PDF',
                data=pdf_buffer,
                file_name=filename,
                mime='application/pdf',
                use_container_width=True,
                type='primary'
            )
        except Exception as e:
            st.error(f'❌ Error generating PDF: {str(e)}')
            st.info('💡 Make sure `reportlab` is in your requirements.txt')

    # === PREVIEW WHATS INCLUDED ===
    with st.expander('👀 **What\'s included in the report?**', expanded=False):
        st.markdown('''
        The generated PDF includes:
        
        ### 📋 Content Sections:
        
        1. **Dark Header** — Title, week number, report dates, and Amazon Now logo
        
        2. **Executive Summary** — Your custom written summary
        
        3. **Highlights** — Dark box with bullet points of key achievements
        
        4. **Lowlights** — Dark box with bullet points of issues/challenges
        
        5. **Portfolio KPIs** — 5 key metric cards
        
        6. **Store Status Summary** — Full table with color-coded statuses
        
        7. **Dividers Summary** — Stock vs Requirements per type
        
        8. **Magnet Status** — With/Without magnet counts
        
        9. **Action Items** — All tasks with statuses
        ''')
