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
    week_ago = today - timedelta(days=7)

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

    # === REPORT SETTINGS FORM ===
    render_section_title('⚙️ Report Settings')

    st.markdown('''
    <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
        💡 Configure the content of your report below. Changes are saved before generating the PDF.
    </div>
    ''', unsafe_allow_html=True)

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

        # Highlights
        st.markdown('**✅ Highlights** (one point per line)')
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            highlights = st.text_area(
                'Highlights',
                value=settings.get('highlights') or '',
                height=120,
                placeholder='• Store A launched successfully\n• All 3P shipments on track',
                label_visibility='collapsed'
            )
        with col_h2:
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            suggest_h = st.form_submit_button('💡 Auto-Suggest', use_container_width=True)

        # Lowlights
        st.markdown('**⚠️ Lowlights** (one point per line)')
        col_l1, col_l2 = st.columns([3, 1])
        with col_l1:
            lowlights = st.text_area(
                'Lowlights',
                value=settings.get('lowlights') or '',
                height=120,
                placeholder='• 30D stock shortage\n• Store X transport not ready',
                label_visibility='collapsed'
            )
        with col_l2:
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            suggest_l = st.form_submit_button('💡 Auto-Suggest', use_container_width=True)

        c1, c2 = st.columns([1, 1])
        save_btn = c1.form_submit_button('💾 Save Settings', use_container_width=True)

        if save_btn:
            update_report_settings(
                report_title, executive_summary, highlights, lowlights,
                week_number, next_update_date
            )
            st.success('✅ Settings saved!')
            st.rerun()

        if suggest_h:
            suggestions = auto_suggest_highlights(stores_df, shipments_df)
            if suggestions:
                new_highlights = highlights + ('\n' if highlights else '') + suggestions
                update_report_settings(
                    report_title, executive_summary, new_highlights, lowlights,
                    week_number, next_update_date
                )
                st.success('✅ Highlights suggested and saved!')
                st.rerun()
            else:
                st.info('💡 No highlights to suggest right now.')

        if suggest_l:
            suggestions = auto_suggest_lowlights(
                stocks, threshold, stores_df, shipments_df,
                magnet_stock, magnet_status
            )
            if suggestions:
                new_lowlights = lowlights + ('\n' if lowlights else '') + suggestions
                update_report_settings(
                    report_title, executive_summary, highlights, new_lowlights,
                    week_number, next_update_date
                )
                st.success('✅ Lowlights suggested and saved!')
                st.rerun()
            else:
                st.info('💡 No issues detected right now.')

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
        
        5. **Portfolio KPIs** — 5 key metric cards:
           - Total Stores, Launched, Upcoming, Pending Shipments, Open Actions
        
        6. **Store Status Summary** — Full table with:
           - Store name, Location, Launch Date, Progress %, Status (color-coded), 
             Transport readiness, Pending quantity
        
        7. **Dividers Summary** — Table showing stock vs requirements per divider type (30D/40D/60D)
        
        8. **Magnet Status** — Table with with/without magnet counts per type
        
        9. **Action Items** — Table with all tasks, owners, ETAs, and statuses
        
        ### 🎨 Styling:
        - Professional dark header
        - Color-coded status badges
        - Alternating row colors
        - Clean typography
        - Page numbering
        ''')
