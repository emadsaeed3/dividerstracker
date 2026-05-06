"""
Progress Report page - Unified PDF + Email Generation
"""
import streamlit as st
from datetime import date, datetime, timedelta
from database import (
    get_report_settings, update_report_settings,
    get_stores, get_shipments, get_stocks_dict, get_threshold,
    get_magnet_stock, get_magnet_status_dict,
    get_action_items, get_upcoming_launches, get_discrepancies
)
from components import render_section_title, render_stat_card
from pdf_generator import generate_progress_report
from email_drafts import generate_dividers_mailto


# ==================== AUTO-SUGGEST ====================

def auto_suggest_highlights(stores_df, shipments_df, action_items_df):
    """Generate highlights from current data (REPLACES existing)"""
    suggestions = []

    # Launched stores
    if not stores_df.empty and 'is_launched' in stores_df.columns:
        launched = stores_df[stores_df['is_launched'] == True]
        if len(launched) > 0:
            suggestions.append(f"{len(launched)} store(s) successfully launched and operational")
            for _, store in launched.head(3).iterrows():
                name = store['name']
                loc = store.get('location') or 'N/A'
                suggestions.append(f"{name} ({loc}) is live")

    # Delivered shipments
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        delivered = shipments_df[shipments_df['delivery_status'] == 'Delivered']
        if not delivered.empty:
            total_delivered = len(delivered)
            total_units = int(delivered['qty_30d'].sum()) + int(delivered['qty_40d'].sum()) + int(delivered['qty_60d'].sum())
            suggestions.append(f"{total_delivered} shipment(s) delivered successfully ({total_units} total units)")

    # Completed actions
    if action_items_df is not None and not action_items_df.empty and 'status' in action_items_df.columns:
        completed = action_items_df[action_items_df['status'] == 'Completed']
        if not completed.empty:
            suggestions.append(f"{len(completed)} action item(s) completed this period")

    # Stock health
    stocks = get_stocks_dict()
    threshold = get_threshold()
    healthy_types = []
    for dtype in ['30D', '40D', '60D']:
        if stocks.get(dtype, 0) >= threshold:
            healthy_types.append(dtype)
    if len(healthy_types) == 3:
        suggestions.append("All divider types have healthy stock levels at vendor")

    return '\n'.join(suggestions) if suggestions else 'No highlights to report at this time.'


def auto_suggest_lowlights(stocks, threshold, stores_df, shipments_df,
                            magnet_stock, magnet_status, action_items_df):
    """Generate lowlights from current data (REPLACES existing)"""
    suggestions = []
    today = date.today()

    # Stock shortages
    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = stores_df[col].sum() if not stores_df.empty else 0
        shipped = shipments_df[ship_col].sum() if not shipments_df.empty else 0
        remaining = max(0, required - shipped)

        if stock == 0 and remaining > 0:
            suggestions.append(f"{dtype} OUT OF STOCK - immediate procurement required ({remaining} units pending)")
        elif stock < remaining:
            shortage = remaining - stock
            suggestions.append(f"{dtype} stock shortage: Need {shortage} more units to fulfill pending shipments")
        elif 0 < stock < threshold:
            suggestions.append(f"{dtype} stock running low ({stock} units left, threshold: {threshold})")

    # Magnet shortage
    total_without_magnet = sum(
        magnet_status.get(t, {}).get('without_magnet', 0)
        for t in ['30D', '40D', '60D']
    )
    if total_without_magnet > 0 and magnet_stock < total_without_magnet:
        shortage = total_without_magnet - magnet_stock
        suggestions.append(f"Magnet strips shortage: Need {shortage} more strips to cover all pending dividers")

    # Overdue launches
    overdue_count = 0
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
                days_left = (ld_obj - today).days
                if days_left < 0:
                    overdue_count += 1
                    if overdue_count <= 3:
                        suggestions.append(f"{store['name']} launch overdue by {abs(days_left)} days")
            except Exception:
                pass

    if overdue_count > 3:
        suggestions.append(f"+ {overdue_count - 3} additional overdue launches")

    # Transport issues
    if not shipments_df.empty:
        no_transport_urgent = 0
        for _, ship in shipments_df.iterrows():
            status = ship.get('delivery_status') or 'Pending'
            if status not in ('Pending', 'In Transit'):
                continue
            if bool(ship.get('transportation_ready', False)):
                continue
            scheduled = ship.get('scheduled_date')
            if scheduled:
                try:
                    if isinstance(scheduled, str):
                        sched_obj = date.fromisoformat(scheduled[:10])
                    else:
                        sched_obj = scheduled
                    if (sched_obj - today).days <= 2:
                        no_transport_urgent += 1
                except Exception:
                    pass
        if no_transport_urgent > 0:
            suggestions.append(f"{no_transport_urgent} urgent shipment(s) still need transportation arranged")

    # Overdue actions
    if action_items_df is not None and not action_items_df.empty:
        overdue_actions = 0
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
                if (eta_obj - today).days < 0:
                    overdue_actions += 1
            except Exception:
                pass
        if overdue_actions > 0:
            suggestions.append(f"{overdue_actions} action item(s) past their ETA")

    # Delayed shipments
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        delayed = shipments_df[shipments_df['delivery_status'] == 'Delayed']
        if not delayed.empty:
            suggestions.append(f"{len(delayed)} shipment(s) currently marked as Delayed")

    return '\n'.join(suggestions) if suggestions else 'No critical issues detected.'


# ==================== MAIN RENDER ====================

def render():
    st.markdown('# 📈 Reports')
    st.caption('Configure, preview, and generate executive progress reports')

    # Load all data
    settings = get_report_settings()
    stocks = get_stocks_dict()
    threshold = get_threshold()
    stores_df = get_stores()
    shipments_df = get_shipments()
    magnet_stock = get_magnet_stock()
    magnet_status = get_magnet_status_dict()
    action_items_df = get_action_items()
    upcoming_launches = get_upcoming_launches(days_ahead=4)
    discrepancies_df = get_discrepancies(stores_df, shipments_df)

    # ==================== STATS PREVIEW ====================
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

    # ==================== CONFIGURE ====================
    render_section_title('⚙️ Report Configuration')

    st.markdown('''
    <div style="background: rgba(52, 152, 219, 0.1); padding: 12px 18px; border-radius: 10px; 
                border-left: 4px solid #3498db; margin-bottom: 16px; font-size:0.9rem;">
        💡 Configure the executive content below. Use <b>Auto-Suggest</b> to <b>regenerate</b> highlights/lowlights from current data 
        (this <b>replaces</b> existing content).
    </div>
    ''', unsafe_allow_html=True)

    # Auto-suggest buttons (REPLACE behavior now)
    c1, c2 = st.columns(2)
    with c1:
        if st.button('💡 Auto-Generate Highlights', use_container_width=True, key='btn_suggest_h',
                      help='Replaces existing highlights with auto-generated content from current data'):
            new_highlights = auto_suggest_highlights(stores_df, shipments_df, action_items_df)
            update_report_settings(
                settings.get('report_title') or 'LAUNCH TEAM TRACKER - PROGRESS REPORT',
                settings.get('executive_summary') or '',
                new_highlights,
                settings.get('lowlights') or '',
                int(settings.get('week_number') or 1),
                settings.get('next_update_date')
            )
            st.success('✅ Highlights regenerated and saved!')
            st.rerun()

    with c2:
        if st.button('💡 Auto-Generate Lowlights', use_container_width=True, key='btn_suggest_l',
                      help='Replaces existing lowlights with auto-generated content from current data'):
            new_lowlights = auto_suggest_lowlights(
                stocks, threshold, stores_df, shipments_df,
                magnet_stock, magnet_status, action_items_df
            )
            update_report_settings(
                settings.get('report_title') or 'LAUNCH TEAM TRACKER - PROGRESS REPORT',
                settings.get('executive_summary') or '',
                settings.get('highlights') or '',
                new_lowlights,
                int(settings.get('week_number') or 1),
                settings.get('next_update_date')
            )
            st.success('✅ Lowlights regenerated and saved!')
            st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Settings form
    with st.form('report_settings_form'):
        c1, c2 = st.columns(2)

        week_number = c1.number_input(
            'Week Number',
            min_value=1, max_value=53,
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
            height=120,
            placeholder='Provide a high-level overview of the current status, key achievements, and outlook...'
        )

        st.markdown('**✅ Highlights** (one point per line — these appear in the report)')
        highlights = st.text_area(
            'Highlights',
            value=settings.get('highlights') or '',
            height=140,
            placeholder='Major achievements, completed milestones, positive outcomes...',
            label_visibility='collapsed'
        )

        st.markdown('**⚠️ Lowlights & Risks** (one point per line)')
        lowlights = st.text_area(
            'Lowlights',
            value=settings.get('lowlights') or '',
            height=140,
            placeholder='Issues, blockers, risks requiring escalation...',
            label_visibility='collapsed'
        )

        save_btn = st.form_submit_button('💾 Save Configuration', use_container_width=True, type='primary')

        if save_btn:
            update_report_settings(
                report_title, executive_summary, highlights, lowlights,
                week_number, next_update_date
            )
            st.success('✅ Configuration saved!')
            st.rerun()

    # ==================== GENERATE & EMAIL ====================
    render_section_title('📥 Generate Report')

    st.markdown('''
    <div style="background: linear-gradient(135deg, rgba(255, 153, 0, 0.1) 0%, rgba(39, 174, 96, 0.1) 100%); 
                padding: 16px 20px; border-radius: 12px; 
                border-left: 4px solid #FF9900; margin-bottom: 20px;">
        🎯 <b>Ready to share?</b> Click below to <b>download the PDF</b> and 
        <b>open your email client</b> with a pre-filled summary. Just attach the downloaded PDF and send!
    </div>
    ''', unsafe_allow_html=True)

    # Get fresh settings
    current_settings = get_report_settings()

    # Generate PDF buffer once
    try:
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
        filename = f'launch_team_progress_W{week_str}_{date_str}.pdf'

        # Generate email mailto link
        try:
            mailto_link = generate_dividers_mailto(
                stocks, threshold, stores_df, shipments_df,
                magnet_stock, magnet_status, upcoming_launches,
                discrepancies_df
            )
        except Exception as e:
            mailto_link = None
            st.warning(f'⚠️ Email link generation failed: {e}')

        # Two-button row
        c1, c2 = st.columns(2)

        with c1:
            st.download_button(
                label='📥 Download PDF Report',
                data=pdf_buffer,
                file_name=filename,
                mime='application/pdf',
                use_container_width=True,
                type='primary',
                help='Download the professional PDF report'
            )

        with c2:
            if mailto_link:
                st.markdown(f'''
                <a href="{mailto_link}" target="_blank" style="text-decoration:none;">
                    <div style="background:#3498db; color:white; padding:0.6rem 1rem; 
                                border-radius:0.5rem; text-align:center; font-weight:600; 
                                cursor:pointer; transition:all 0.2s; border:1px solid #3498db;
                                font-size:1rem;">
                        📧 Open Email Draft
                    </div>
                </a>
                ''', unsafe_allow_html=True)
            else:
                st.button('📧 Open Email Draft', disabled=True, use_container_width=True)

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        # Workflow help
        with st.expander('📋 **How to send the report (Workflow)**', expanded=False):
            st.markdown('''
            **Step-by-step workflow:**
            
            1. 📥 Click **"Download PDF Report"** — saves the PDF to your computer
            2. 📧 Click **"Open Email Draft"** — opens your email client with subject + body pre-filled
            3. 📎 In the email window, **attach the downloaded PDF** to the email
            4. ✏️ Add recipient(s) and any custom message if needed
            5. 🚀 Send!
            
            ---
            
            **💡 Pro tip:** The email body contains a quick summary of all data, so even without 
            opening the PDF, recipients can see the current status at a glance.
            ''')

    except Exception as e:
        st.error(f'❌ Error generating report: {str(e)}')
        st.info('💡 Make sure `reportlab` is in your requirements.txt')

    # ==================== WHAT'S INCLUDED ====================
    with st.expander('👀 **What\'s included in the executive PDF report?**', expanded=False):
        st.markdown('''
        The executive PDF is designed for **leadership review** and includes:
        
        **📋 Strategic Content** *(your custom input)*
        - Executive Summary
        - Highlights (achievements)
        - Lowlights & Risks (issues/blockers)
        
        **📊 Data Insights** *(auto-generated)*
        - Portfolio KPIs (5 key metrics)
        - Store Status Distribution (visual breakdown)
        - **Critical Items Requiring Attention** (top 8 issues)
        - Dividers Inventory & Fulfillment summary
        - Magnet Coverage status
        - Open Action Items
        
        ---
        
        ❌ **Not included** (intentionally — too detailed for leadership):
        - Individual store rows
        - Shipment-by-shipment details
        - Transport ready/not ready per shipment
        - Stock movement history
        
        💡 *For detailed views, use the dashboard pages directly.*
        ''')
