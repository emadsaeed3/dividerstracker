"""
Executive Progress Report PDF Generator
Designed for leadership review - clean, focused, actionable
"""
import os
from io import BytesIO
from datetime import date, datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, KeepTogether
)


# ==================== COLORS ====================

DARK_HEADER = colors.HexColor('#1A2332')
ACCENT_PRIMARY = colors.HexColor('#FF9900')  # Amazon Orange
ACCENT_BLUE = colors.HexColor('#3498DB')
ACCENT_ORANGE = colors.HexColor('#E67E22')
ACCENT_PURPLE = colors.HexColor('#9B59B6')
ACCENT_GREEN = colors.HexColor('#27AE60')
ACCENT_RED = colors.HexColor('#E74C3C')
ACCENT_YELLOW = colors.HexColor('#F39C12')

LIGHT_BG = colors.HexColor('#F4F6F8')
CARD_BG = colors.HexColor('#FFFFFF')
TEXT_DARK = colors.HexColor('#1A2332')
TEXT_MUTED = colors.HexColor('#6C7A89')
DIVIDER_LIGHT = colors.HexColor('#E1E8ED')

HIGHLIGHT_BG = colors.HexColor('#1A2332')
LOWLIGHT_BG = colors.HexColor('#34495E')


COLOR_HEX = {
    'DARK_HEADER': '#1A2332',
    'ACCENT_PRIMARY': '#FF9900',
    'ACCENT_BLUE': '#3498DB',
    'ACCENT_ORANGE': '#E67E22',
    'ACCENT_PURPLE': '#9B59B6',
    'ACCENT_GREEN': '#27AE60',
    'ACCENT_RED': '#E74C3C',
    'ACCENT_YELLOW': '#F39C12',
    'TEXT_DARK': '#1A2332',
    'TEXT_MUTED': '#6C7A89',
    'WHITE': '#FFFFFF',
}


# ==================== HELPERS ====================

def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle', fontName='Helvetica-Bold', fontSize=18,
        textColor=colors.white, alignment=TA_LEFT, spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle', fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor('#BDC3C7'), alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='BodyTextCustom', fontName='Helvetica', fontSize=10,
        textColor=TEXT_DARK, alignment=TA_JUSTIFY, leading=14,
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle', fontName='Helvetica-Bold', fontSize=13,
        textColor=TEXT_DARK, alignment=TA_LEFT, spaceAfter=4,
    ))

    return styles


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            return None
    return None


# ==================== HEADER ====================

def build_header(week_number, report_date, next_update, styles):
    logo_path = 'Now-PrimaryLogo-White.png'
    logo_element = ''

    if os.path.exists(logo_path):
        try:
            logo_element = Image(logo_path, width=3.5 * cm, height=1.2 * cm, kind='proportional')
        except Exception:
            logo_element = Paragraph('<b>amazon now</b>', styles['ReportTitle'])
    else:
        logo_element = Paragraph('<b>amazon now</b>', styles['ReportTitle'])

    title_text = 'LAUNCH TEAM PROGRESS REPORT'
    report_date_str = report_date.strftime('%d %B %Y') if report_date else '—'
    next_update_str = next_update.strftime('%d %B %Y') if next_update else '—'

    title_para = Paragraph('<b>' + title_text + '</b>', styles['ReportTitle'])
    
    subtitle = (
        '<para fontSize="9" fontName="Helvetica" textColor="#BDC3C7">'
        '<b>WEEK ' + str(week_number) + '</b>  •  '
        'Report Date: ' + report_date_str + '  •  '
        'Next Update: ' + next_update_str +
        '</para>'
    )
    subtitle_para = Paragraph(subtitle, styles['Normal'])

    header_content = [[
        [title_para, Spacer(1, 4), subtitle_para],
        logo_element
    ]]

    header_table = Table(header_content, colWidths=[13.5 * cm, 3.5 * cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_HEADER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 18),
        ('RIGHTPADDING', (0, 0), (-1, -1), 18),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
    ]))

    # Orange accent bar below header
    accent_bar = Table([['']], colWidths=[17 * cm], rowHeights=[0.15 * cm])
    accent_bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT_PRIMARY),
    ]))

    return [header_table, accent_bar]


# ==================== SECTION HEADER ====================

def build_section_header(title, icon=''):
    elements = []
    
    title_text = (icon + ' ' if icon else '') + title
    para = Paragraph(
        '<para fontSize="13" fontName="Helvetica-Bold" textColor="' + COLOR_HEX['TEXT_DARK'] + '">'
        '<b>' + title_text + '</b></para>',
        getSampleStyleSheet()['Normal']
    )
    elements.append(para)

    line_table = Table([['']], colWidths=[17 * cm], rowHeights=[1.5])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT_PRIMARY),
    ]))
    elements.append(Spacer(1, 3))
    elements.append(line_table)
    elements.append(Spacer(1, 10))

    return elements


# ==================== EXECUTIVE SUMMARY ====================

def build_executive_summary(text, styles):
    elements = []
    elements.extend(build_section_header('Executive Summary', '📋'))

    if text and text.strip():
        para = Paragraph(text, styles['BodyTextCustom'])
        # Wrap in box
        box = Table([[para]], colWidths=[17 * cm])
        box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
            ('LINEABOVE', (0, 0), (-1, 0), 3, ACCENT_PRIMARY),
        ]))
        elements.append(box)
    else:
        elements.append(Paragraph(
            '<i>No summary provided.</i>',
            styles['BodyTextCustom']
        ))

    elements.append(Spacer(1, 16))
    return elements


# ==================== HIGHLIGHTS / LOWLIGHTS ====================

def build_highlights_box(bullets_text, bg_color, accent_color):
    if not bullets_text or not bullets_text.strip():
        bullets_text = 'None reported.'

    lines = [line.strip() for line in bullets_text.split('\n') if line.strip()]

    bullet_html = ''
    for line in lines:
        clean_line = line.lstrip('•-*✓✗⚠✅❌').strip()
        if clean_line:
            clean_line = clean_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            bullet_html += (
                '<para fontName="Helvetica" fontSize="10" textColor="#FFFFFF" leading="16" leftIndent="8" spaceAfter="4">'
                '▸ ' + clean_line + '</para>'
            )

    if not bullet_html:
        bullet_html = '<para fontName="Helvetica" fontSize="10" textColor="#FFFFFF" leading="16" leftIndent="8"><i>None reported.</i></para>'

    content_para = Paragraph(bullet_html, getSampleStyleSheet()['Normal'])

    box = Table([[content_para]], colWidths=[17 * cm])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 18),
        ('RIGHTPADDING', (0, 0), (-1, -1), 18),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LINEBEFORE', (0, 0), (0, -1), 4, accent_color),
    ]))

    return box


def build_highlights_section(highlights_text):
    elements = []
    elements.extend(build_section_header('Highlights', '✅'))
    elements.append(build_highlights_box(highlights_text, HIGHLIGHT_BG, ACCENT_GREEN))
    elements.append(Spacer(1, 14))
    return elements


def build_lowlights_section(lowlights_text):
    elements = []
    elements.extend(build_section_header('Lowlights & Risks', '⚠️'))
    elements.append(build_highlights_box(lowlights_text, LOWLIGHT_BG, ACCENT_RED))
    elements.append(Spacer(1, 16))
    return elements


# ==================== KPI CARDS ====================

def build_kpi_cards(kpis):
    elements = []
    elements.extend(build_section_header('Portfolio Overview', '📊'))

    styles = getSampleStyleSheet()
    cards_row = []
    
    for value, label, color_hex in kpis:
        number_para = Paragraph(
            '<para fontSize="26" fontName="Helvetica-Bold" textColor="' + color_hex + '" alignment="center">'
            '<b>' + str(value) + '</b></para>',
            styles['Normal']
        )
        label_para = Paragraph(
            '<para fontSize="8" fontName="Helvetica-Bold" textColor="' + COLOR_HEX['TEXT_MUTED'] + '" alignment="center">'
            + label.upper() + '</para>',
            styles['Normal']
        )

        card_content = [[number_para], [label_para]]
        card = Table(card_content, colWidths=[3.2 * cm], rowHeights=[1.3 * cm, 0.7 * cm])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor(color_hex)),
            ('BOX', (0, 0), (-1, -1), 0.5, DIVIDER_LIGHT),
        ]))
        cards_row.append(card)

    num_cards = len(cards_row)
    col_widths = [3.2 * cm] * num_cards

    cards_table = Table([cards_row], colWidths=col_widths)
    cards_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(cards_table)
    elements.append(Spacer(1, 16))
    return elements


# ==================== STATUS DISTRIBUTION ====================

def calculate_store_statuses(stores_df, shipments_df):
    """Calculate distribution of stores by status"""
    counts = {
        'Launched': 0,
        'Ready': 0,
        'On Track': 0,
        'At Risk': 0,
        'Delayed': 0,
        'No Date': 0,
    }
    
    if stores_df.empty:
        return counts
    
    today = date.today()
    
    for _, store in stores_df.iterrows():
        is_launched = bool(store.get('is_launched', False))
        
        if is_launched:
            counts['Launched'] += 1
            continue
        
        ld = _to_date(store.get('launch_date'))
        if not ld:
            counts['No Date'] += 1
            continue
        
        # Calc shipping progress
        store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else None
        if store_ships is not None and not store_ships.empty:
            shipped = int(store_ships['qty_30d'].sum()) + int(store_ships['qty_40d'].sum()) + int(store_ships['qty_60d'].sum())
        else:
            shipped = 0
        
        required = int(store['required_30d']) + int(store['required_40d']) + int(store['required_60d'])
        pct = (shipped / required * 100) if required > 0 else 0
        days_left = (ld - today).days
        
        if days_left < 0:
            counts['Delayed'] += 1
        elif days_left <= 2 and pct < 100:
            counts['At Risk'] += 1
        elif pct >= 100:
            counts['Ready'] += 1
        else:
            counts['On Track'] += 1
    
    return counts


def build_status_distribution(stores_df, shipments_df):
    elements = []
    elements.extend(build_section_header('Store Status Distribution', '🎯'))
    
    counts = calculate_store_statuses(stores_df, shipments_df)
    
    status_config = [
        ('Launched', ACCENT_GREEN, '✓'),
        ('Ready', colors.HexColor('#16A085'), '●'),
        ('On Track', ACCENT_BLUE, '●'),
        ('At Risk', ACCENT_ORANGE, '!'),
        ('Delayed', ACCENT_RED, '✗'),
        ('No Date', TEXT_MUTED, '?'),
    ]
    
    cards = []
    for status, color, icon in status_config:
        count = counts[status]
        
        number_para = Paragraph(
            '<para fontSize="22" fontName="Helvetica-Bold" textColor="#FFFFFF" alignment="center">'
            '<b>' + str(count) + '</b></para>',
            getSampleStyleSheet()['Normal']
        )
        label_para = Paragraph(
            '<para fontSize="8" fontName="Helvetica-Bold" textColor="#FFFFFF" alignment="center">'
            + status.upper() + '</para>',
            getSampleStyleSheet()['Normal']
        )
        
        card = Table([[number_para], [label_para]], colWidths=[2.6 * cm], rowHeights=[1 * cm, 0.7 * cm])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        cards.append(card)
    
    cards_table = Table([cards], colWidths=[2.6 * cm] * 6)
    cards_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(cards_table)
    elements.append(Spacer(1, 16))
    return elements


# ==================== DIVIDERS SUMMARY ====================

def build_dividers_summary(stocks, stores_df, shipments_df):
    elements = []
    elements.extend(build_section_header('Dividers Inventory & Fulfillment', '📦'))

    header = ['Type', 'Vendor Stock', 'Required', 'Shipped', 'Pending', 'Progress']
    rows = [header]

    color_map = {'30D': ACCENT_BLUE, '40D': ACCENT_ORANGE, '60D': ACCENT_PURPLE}
    row_colors = []

    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = 'required_' + dtype.lower()
        ship_col = 'qty_' + dtype.lower()
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        pending = max(0, required - shipped)
        pct = (shipped / required * 100) if required > 0 else 0

        rows.append([
            dtype, str(stock), str(required), str(shipped),
            str(pending), str(int(pct)) + '%'
        ])
        row_colors.append(color_map.get(dtype, ACCENT_BLUE))

    total_stock = sum(stocks.get(t, 0) for t in ['30D', '40D', '60D'])
    total_req = sum(int(stores_df['required_' + t.lower()].sum()) if not stores_df.empty else 0
                     for t in ['30D', '40D', '60D'])
    total_ship = sum(int(shipments_df['qty_' + t.lower()].sum()) if not shipments_df.empty else 0
                      for t in ['30D', '40D', '60D'])
    total_pending = max(0, total_req - total_ship)
    total_pct = (total_ship / total_req * 100) if total_req > 0 else 0

    rows.append([
        'TOTAL', str(total_stock), str(total_req), str(total_ship),
        str(total_pending), str(int(total_pct)) + '%'
    ])

    col_widths = [2.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 4 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_LIGHT),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF3E0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, ACCENT_PRIMARY),
    ])

    for i, color in enumerate(row_colors, start=1):
        style.add('BACKGROUND', (0, i), (0, i), color)
        style.add('TEXTCOLOR', (0, i), (0, i), colors.white)
        style.add('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 16))
    return elements


# ==================== MAGNET SUMMARY ====================

def build_magnet_summary(magnet_stock, magnet_status):
    elements = []
    elements.extend(build_section_header('Magnet Coverage', '🧲'))

    info_text = '<b>Strips Available at Vendor:</b> ' + str(magnet_stock) + ' units'
    info_para = Paragraph(
        '<para fontSize="9" fontName="Helvetica" textColor="' + COLOR_HEX['TEXT_DARK'] + '">' + info_text + '</para>',
        getSampleStyleSheet()['Normal']
    )
    
    info_box = Table([[info_para]], colWidths=[17 * cm])
    info_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_box)
    elements.append(Spacer(1, 8))

    header = ['Type', 'With Magnet', 'Without Magnet', 'Total', 'Coverage']
    rows = [header]
    color_map = {'30D': ACCENT_BLUE, '40D': ACCENT_ORANGE, '60D': ACCENT_PURPLE}
    row_colors = []

    total_with = 0
    total_without = 0

    for dtype in ['30D', '40D', '60D']:
        status = magnet_status.get(dtype, {'with_magnet': 0, 'without_magnet': 0})
        w = status['with_magnet']
        wo = status['without_magnet']
        total = w + wo
        pct = (w / total * 100) if total > 0 else 0

        total_with += w
        total_without += wo

        rows.append([dtype, str(w), str(wo), str(total), str(int(pct)) + '%'])
        row_colors.append(color_map.get(dtype))

    grand_total = total_with + total_without
    grand_pct = (total_with / grand_total * 100) if grand_total > 0 else 0
    rows.append(['TOTAL', str(total_with), str(total_without), str(grand_total), str(int(grand_pct)) + '%'])

    col_widths = [2.5 * cm, 3.5 * cm, 3.5 * cm, 3 * cm, 4.5 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_LIGHT),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF3E0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, ACCENT_PRIMARY),
    ])

    for i, color in enumerate(row_colors, start=1):
        style.add('BACKGROUND', (0, i), (0, i), color)
        style.add('TEXTCOLOR', (0, i), (0, i), colors.white)
        style.add('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 16))
    return elements


# ==================== CRITICAL ALERTS ====================

def collect_critical_alerts(stocks, threshold, stores_df, shipments_df,
                             magnet_stock, magnet_status, action_items_df):
    """Collect top critical issues for leadership attention"""
    alerts = []
    today = date.today()
    
    # Stock outages
    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = 'required_' + dtype.lower()
        ship_col = 'qty_' + dtype.lower()
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        remaining = max(0, required - shipped)
        
        if stock == 0 and remaining > 0:
            alerts.append({
                'severity': 'CRITICAL',
                'category': 'Stock',
                'message': dtype + ' OUT OF STOCK - ' + str(remaining) + ' units needed for pending shipments',
                'color': ACCENT_RED,
            })
        elif stock < remaining:
            shortage = remaining - stock
            alerts.append({
                'severity': 'CRITICAL',
                'category': 'Stock',
                'message': dtype + ' shortage: Need ' + str(shortage) + ' more units (Stock: ' + str(stock) + ')',
                'color': ACCENT_RED,
            })
    
    # Overdue/imminent launches
    if not stores_df.empty:
        for _, store in stores_df.iterrows():
            if store.get('is_launched'):
                continue
            ld = _to_date(store.get('launch_date'))
            if not ld:
                continue
            days = (ld - today).days
            name = str(store['name'])
            
            if days < 0:
                alerts.append({
                    'severity': 'CRITICAL',
                    'category': 'Launch',
                    'message': name + ' is ' + str(abs(days)) + ' days OVERDUE - not yet launched',
                    'color': ACCENT_RED,
                })
            elif days == 0:
                alerts.append({
                    'severity': 'CRITICAL',
                    'category': 'Launch',
                    'message': name + ' is launching TODAY',
                    'color': ACCENT_ORANGE,
                })
            elif days == 1:
                alerts.append({
                    'severity': 'HIGH',
                    'category': 'Launch',
                    'message': name + ' launches TOMORROW',
                    'color': ACCENT_ORANGE,
                })
    
    # Transport not ready
    if not shipments_df.empty:
        no_transport_count = 0
        urgent_no_transport = []
        for _, ship in shipments_df.iterrows():
            status = ship.get('delivery_status') or 'Pending'
            if status not in ('Pending', 'In Transit'):
                continue
            if bool(ship.get('transportation_ready', False)):
                continue
            
            scheduled = _to_date(ship.get('scheduled_date'))
            if scheduled:
                days = (scheduled - today).days
                if days <= 2:
                    urgent_no_transport.append((ship.get('store_name', 'Unknown'), days))
            no_transport_count += 1
        
        if urgent_no_transport:
            for store_name, days in urgent_no_transport[:2]:
                msg = 'Transport not arranged for ' + str(store_name)
                if days < 0:
                    msg += ' (' + str(abs(days)) + 'd overdue)'
                elif days == 0:
                    msg += ' (delivers today)'
                else:
                    msg += ' (delivers in ' + str(days) + 'd)'
                alerts.append({
                    'severity': 'CRITICAL',
                    'category': 'Transport',
                    'message': msg,
                    'color': ACCENT_RED,
                })
    
    # Magnet shortage
    total_without_magnet = sum(
        magnet_status.get(t, {}).get('without_magnet', 0)
        for t in ['30D', '40D', '60D']
    )
    if total_without_magnet > 0 and magnet_stock < total_without_magnet:
        shortage = total_without_magnet - magnet_stock
        alerts.append({
            'severity': 'HIGH',
            'category': 'Magnet',
            'message': 'Magnet strips shortage: Need ' + str(shortage) + ' more strips',
            'color': ACCENT_ORANGE,
        })
    
    # Overdue actions
    if action_items_df is not None and not action_items_df.empty:
        overdue_actions = 0
        for _, item in action_items_df.iterrows():
            if item.get('status') == 'Completed':
                continue
            eta = _to_date(item.get('eta'))
            if eta and (eta - today).days < 0:
                overdue_actions += 1
        if overdue_actions > 0:
            alerts.append({
                'severity': 'HIGH',
                'category': 'Actions',
                'message': str(overdue_actions) + ' action items are overdue',
                'color': ACCENT_ORANGE,
            })
    
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
    alerts.sort(key=lambda a: severity_order.get(a['severity'], 99))
    
    return alerts[:8]  # Top 8 only


def build_critical_alerts(stocks, threshold, stores_df, shipments_df,
                           magnet_stock, magnet_status, action_items_df):
    elements = []
    
    alerts = collect_critical_alerts(
        stocks, threshold, stores_df, shipments_df,
        magnet_stock, magnet_status, action_items_df
    )
    
    if not alerts:
        elements.extend(build_section_header('Critical Items', '🚨'))
        success_box = Table([[Paragraph(
            '<para fontSize="11" fontName="Helvetica-Bold" textColor="#FFFFFF" alignment="center">'
            '✓ No critical items at this time. All systems operational.</para>',
            getSampleStyleSheet()['Normal']
        )]], colWidths=[17 * cm])
        success_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ACCENT_GREEN),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ]))
        elements.append(success_box)
        elements.append(Spacer(1, 16))
        return elements
    
    elements.extend(build_section_header('Critical Items Requiring Attention', '🚨'))
    
    header = ['Severity', 'Category', 'Issue']
    rows = [header]
    row_colors = []
    
    for alert in alerts:
        rows.append([alert['severity'], alert['category'], alert['message']])
        row_colors.append(alert['color'])
    
    col_widths = [2.5 * cm, 2.5 * cm, 12 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFBFC')]),
    ])
    
    # Color severity column
    for i, color in enumerate(row_colors, start=1):
        style.add('BACKGROUND', (0, i), (0, i), color)
        style.add('TEXTCOLOR', (0, i), (0, i), colors.white)
        style.add('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 16))
    return elements


# ==================== ACTION ITEMS ====================

def build_action_items_table(items_df):
    elements = []
    elements.extend(build_section_header('Open Action Items', '📌'))

    if items_df.empty:
        elements.append(Paragraph(
            '<para fontSize="10" fontName="Helvetica" textColor="' + COLOR_HEX['TEXT_MUTED'] + '"><i>No open action items.</i></para>',
            getSampleStyleSheet()['Normal']
        ))
        elements.append(Spacer(1, 12))
        return elements

    # Filter only open ones
    open_items = items_df[items_df['status'] != 'Completed'] if 'status' in items_df.columns else items_df
    
    if open_items.empty:
        success_box = Table([[Paragraph(
            '<para fontSize="11" fontName="Helvetica-Bold" textColor="#FFFFFF" alignment="center">'
            '✓ All action items completed.</para>',
            getSampleStyleSheet()['Normal']
        )]], colWidths=[17 * cm])
        success_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ACCENT_GREEN),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ]))
        elements.append(success_box)
        elements.append(Spacer(1, 12))
        return elements

    header = ['#', 'Action', 'Owner', 'ETA', 'Status']
    rows = [header]
    row_statuses = []

    status_colors = {
        'Pending': ACCENT_YELLOW,
        'In Progress': ACCENT_BLUE,
        'Blocked': ACCENT_RED,
    }

    for idx, (_, item) in enumerate(open_items.iterrows(), start=1):
        eta = item.get('eta')
        if eta:
            if isinstance(eta, str):
                try:
                    eta_str = date.fromisoformat(eta).strftime('%d %b %Y')
                except Exception:
                    eta_str = str(eta)
            else:
                eta_str = eta.strftime('%d %b %Y') if hasattr(eta, 'strftime') else str(eta)
        else:
            eta_str = '—'

        status = item.get('status') or 'Pending'
        action = str(item.get('action_text') or '')[:65]
        owner = str(item.get('owner') or '—')[:18]

        rows.append([str(idx), action, owner, eta_str, status])
        row_statuses.append(status_colors.get(status, TEXT_MUTED))

    col_widths = [0.8 * cm, 8 * cm, 3 * cm, 2.5 * cm, 2.7 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (4, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFBFC')]),
    ])

    for i, color in enumerate(row_statuses, start=1):
        style.add('BACKGROUND', (4, i), (4, i), color)
        style.add('TEXTCOLOR', (4, i), (4, i), colors.white)
        style.add('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 12))
    return elements


# ==================== FOOTER ====================

def add_page_decorations(canvas_obj, doc):
    canvas_obj.saveState()
    
    # Footer line
    canvas_obj.setStrokeColor(DIVIDER_LIGHT)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2 * cm, 1.3 * cm, A4[0] - 2 * cm, 1.3 * cm)
    
    # Footer text
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(TEXT_MUTED)
    
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawString(2 * cm, 0.8 * cm, 'Launch Team Tracker  •  Confidential')
    canvas_obj.drawRightString(A4[0] - 2 * cm, 0.8 * cm, 'Page ' + str(page_num))
    
    canvas_obj.restoreState()


# ==================== MAIN GENERATOR ====================

def generate_progress_report(
    report_settings,
    stocks, threshold,
    stores_df, shipments_df,
    magnet_stock, magnet_status,
    action_items_df,
    report_date=None
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.2 * cm, bottomMargin=1.8 * cm,
        title='Launch Team Progress Report'
    )

    styles = get_styles()
    story = []

    week_num = report_settings.get('week_number') or 1
    exec_summary = report_settings.get('executive_summary') or ''
    highlights = report_settings.get('highlights') or ''
    lowlights = report_settings.get('lowlights') or ''

    next_update = report_settings.get('next_update_date')
    if next_update and isinstance(next_update, str):
        try:
            next_update = date.fromisoformat(next_update)
        except Exception:
            next_update = None

    if not report_date:
        report_date = date.today()

    # Header
    story.extend(build_header(week_num, report_date, next_update, styles))
    story.append(Spacer(1, 18))

    # Executive Summary
    story.extend(build_executive_summary(exec_summary, styles))
    
    # Highlights & Lowlights
    story.extend(build_highlights_section(highlights))
    story.extend(build_lowlights_section(lowlights))

    # Portfolio KPIs
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

    kpis = [
        (str(total_stores), 'Total Stores', COLOR_HEX['DARK_HEADER']),
        (str(launched_count), 'Launched', COLOR_HEX['ACCENT_GREEN']),
        (str(upcoming_count), 'Upcoming', COLOR_HEX['ACCENT_BLUE']),
        (str(pending_ships), 'Pending Ships', COLOR_HEX['ACCENT_ORANGE']),
        (str(open_actions), 'Open Actions', COLOR_HEX['ACCENT_RED']),
    ]
    story.extend(build_kpi_cards(kpis))
    
    # Status Distribution
    story.extend(build_status_distribution(stores_df, shipments_df))
    
    # Critical Alerts (most important for leadership)
    story.extend(build_critical_alerts(
        stocks, threshold, stores_df, shipments_df,
        magnet_stock, magnet_status, action_items_df
    ))
    
    # Dividers Summary
    story.extend(build_dividers_summary(stocks, stores_df, shipments_df))
    
    # Magnet Coverage
    story.extend(build_magnet_summary(magnet_stock, magnet_status))
    
    # Open Action Items
    story.extend(build_action_items_table(action_items_df))

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    buffer.seek(0)
    return buffer
