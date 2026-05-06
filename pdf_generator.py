"""
PDF Report Generator
Generates professional progress reports
"""
import os
from io import BytesIO
from datetime import date, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)


# ==================== COLORS ====================

DARK_HEADER = colors.HexColor('#2C3E50')
LIGHT_BG = colors.HexColor('#ECF0F1')
ACCENT_BLUE = colors.HexColor('#3498DB')
ACCENT_ORANGE = colors.HexColor('#E67E22')
ACCENT_PURPLE = colors.HexColor('#9B59B6')
ACCENT_GREEN = colors.HexColor('#27AE60')
ACCENT_RED = colors.HexColor('#E74C3C')
ACCENT_YELLOW = colors.HexColor('#F39C12')

HIGHLIGHT_BG = colors.HexColor('#2C3E50')
LOWLIGHT_BG = colors.HexColor('#34495E')
TEXT_DARK = colors.HexColor('#2C3E50')
TEXT_GRAY = colors.HexColor('#7F8C8D')
DIVIDER_GRAY = colors.HexColor('#BDC3C7')


COLOR_HEX = {
    'DARK_HEADER': '#2C3E50',
    'ACCENT_BLUE': '#3498DB',
    'ACCENT_ORANGE': '#E67E22',
    'ACCENT_PURPLE': '#9B59B6',
    'ACCENT_GREEN': '#27AE60',
    'ACCENT_RED': '#E74C3C',
    'ACCENT_YELLOW': '#F39C12',
    'TEXT_DARK': '#2C3E50',
    'TEXT_GRAY': '#7F8C8D',
}


def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle', fontName='Helvetica-Bold', fontSize=16,
        textColor=colors.white, alignment=TA_LEFT, spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle', fontName='Helvetica', fontSize=9,
        textColor=colors.white, alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='BodyTextCustom', fontName='Helvetica', fontSize=9,
        textColor=TEXT_DARK, alignment=TA_JUSTIFY, leading=12,
    ))

    return styles


# ==================== HEADER ====================

def build_header(week_number, report_date, next_update, styles):
    logo_path = 'Now-PrimaryLogo-White.png'
    logo_element = ''

    if os.path.exists(logo_path):
        try:
            logo_element = Image(logo_path, width=3 * cm, height=1 * cm, kind='proportional')
        except Exception:
            logo_element = Paragraph('<b>amazon now</b>', styles['ReportTitle'])
    else:
        logo_element = Paragraph('<b>amazon now</b>', styles['ReportTitle'])

    title_text = 'LAUNCH TEAM TRACKER - PROGRESS REPORT'
    report_date_str = report_date.strftime('%d %b %Y') if report_date else '—'
    next_update_str = next_update.strftime('%d %b %Y') if next_update else '—'
    subtitle = 'Week ' + str(week_number) + ' | Report Date: ' + report_date_str + ' | Next Update: ' + next_update_str

    title_para = Paragraph('<b>' + title_text + '</b>', styles['ReportTitle'])
    subtitle_para = Paragraph(subtitle, styles['ReportSubtitle'])

    header_content = [[
        [title_para, Spacer(1, 3), subtitle_para],
        logo_element
    ]]

    header_table = Table(header_content, colWidths=[13 * cm, 4 * cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_HEADER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ]))

    return header_table


# ==================== SECTION HEADER ====================

def build_section_header(title):
    elements = []
    para = Paragraph(
        '<para fontSize="12" fontName="Helvetica-Bold" textColor="' + COLOR_HEX['TEXT_DARK'] + '">'
        '<b>' + title + '</b></para>',
        getSampleStyleSheet()['Normal']
    )
    elements.append(para)

    line_table = Table([['']], colWidths=[17 * cm], rowHeights=[1])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DIVIDER_GRAY),
    ]))
    elements.append(Spacer(1, 2))
    elements.append(line_table)
    elements.append(Spacer(1, 8))

    return elements


# ==================== EXECUTIVE SUMMARY ====================

def build_executive_summary(text, styles):
    elements = []
    elements.extend(build_section_header('Executive Summary'))

    if text and text.strip():
        para = Paragraph(text, styles['BodyTextCustom'])
        elements.append(para)
    else:
        elements.append(Paragraph(
            '<i>No summary provided.</i>',
            styles['BodyTextCustom']
        ))

    elements.append(Spacer(1, 12))
    return elements


# ==================== HIGHLIGHTS / LOWLIGHTS ====================

def build_highlights_box(bullets_text, bg_color):
    if not bullets_text or not bullets_text.strip():
        bullets_text = 'None reported.'

    lines = [line.strip() for line in bullets_text.split('\n') if line.strip()]

    bullet_html = ''
    for line in lines:
        clean_line = line.lstrip('•-*').strip()
        if clean_line:
            clean_line = clean_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            bullet_html += '<para fontName="Helvetica" fontSize="9" textColor="#FFFFFF" leading="13" leftIndent="10">• ' + clean_line + '</para>'

    if not bullet_html:
        bullet_html = '<para fontName="Helvetica" fontSize="9" textColor="#FFFFFF" leading="13" leftIndent="10"><i>None reported.</i></para>'

    content_para = Paragraph(bullet_html, getSampleStyleSheet()['Normal'])

    box = Table([[content_para]], colWidths=[17 * cm])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))

    return box


def build_highlights_section(highlights_text):
    elements = []
    elements.extend(build_section_header('Highlights'))
    elements.append(build_highlights_box(highlights_text, HIGHLIGHT_BG))
    elements.append(Spacer(1, 12))
    return elements


def build_lowlights_section(lowlights_text):
    elements = []
    elements.extend(build_section_header('Lowlights'))
    elements.append(build_highlights_box(lowlights_text, LOWLIGHT_BG))
    elements.append(Spacer(1, 12))
    return elements


# ==================== KPI CARDS ====================

def build_kpi_cards(kpis):
    elements = []
    elements.extend(build_section_header('Portfolio Key Performance Indicators'))

    styles = getSampleStyleSheet()
    cards_row = []
    for value, label, color_hex in kpis:
        number_para = Paragraph(
            '<para fontSize="22" fontName="Helvetica-Bold" textColor="' + color_hex + '" alignment="center">'
            '<b>' + str(value) + '</b></para>',
            styles['Normal']
        )
        label_para = Paragraph(
            '<para fontSize="7" fontName="Helvetica" textColor="' + COLOR_HEX['TEXT_GRAY'] + '" alignment="center">'
            + label + '</para>',
            styles['Normal']
        )

        card_content = [[number_para], [label_para]]
        card = Table(card_content, colWidths=[3.2 * cm], rowHeights=[1.1 * cm, 0.6 * cm])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        cards_row.append(card)

    num_cards = len(cards_row)
    col_widths = [3.2 * cm] * num_cards

    cards_table = Table([cards_row], colWidths=col_widths)
    cards_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))

    elements.append(cards_table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== STORE STATUS TABLE ====================

def get_store_status(store, shipped_total, required_total):
    is_launched = bool(store.get('is_launched', False))
    launch_date_val = store.get('launch_date')

    if is_launched:
        return ('Launched', ACCENT_GREEN)

    if not launch_date_val:
        return ('No Date', TEXT_GRAY)

    try:
        if isinstance(launch_date_val, str):
            ld = date.fromisoformat(launch_date_val)
        else:
            ld = launch_date_val
    except Exception:
        return ('—', TEXT_GRAY)

    days_left = (ld - date.today()).days
    pct = (shipped_total / required_total * 100) if required_total > 0 else 0

    if days_left < 0:
        return ('Delayed', ACCENT_RED)
    elif days_left <= 2 and pct < 100:
        return ('At Risk', ACCENT_ORANGE)
    elif pct >= 100:
        return ('Ready', ACCENT_GREEN)
    else:
        return ('On Track', ACCENT_BLUE)


def build_stores_table(stores_df, shipments_df):
    elements = []
    elements.extend(build_section_header('Store Status Summary'))

    if stores_df.empty:
        elements.append(Paragraph(
            '<i>No stores to display.</i>',
            getSampleStyleSheet()['Normal']
        ))
        elements.append(Spacer(1, 12))
        return elements

    header = ['Store', 'Location', 'Launch Date', 'Progress', 'Status', 'Pending']
    rows = [header]
    row_statuses = []

    for _, store in stores_df.iterrows():
        store_ships = shipments_df[shipments_df['store_id'] == store['id']] if not shipments_df.empty else None

        if store_ships is not None and not store_ships.empty:
            s30 = int(store_ships['qty_30d'].sum())
            s40 = int(store_ships['qty_40d'].sum())
            s60 = int(store_ships['qty_60d'].sum())
        else:
            s30 = s40 = s60 = 0

        shipped_total = s30 + s40 + s60
        required_total = int(store['required_30d']) + int(store['required_40d']) + int(store['required_60d'])
        pct = (shipped_total / required_total * 100) if required_total > 0 else 0
        pending_total = max(0, required_total - shipped_total)

        status_label, status_color = get_store_status(store, shipped_total, required_total)

        launch_date_val = store.get('launch_date')
        if launch_date_val:
            if isinstance(launch_date_val, str):
                try:
                    launch_str = date.fromisoformat(launch_date_val).strftime('%d %b %Y')
                except Exception:
                    launch_str = str(launch_date_val)
            else:
                launch_str = launch_date_val.strftime('%d %b %Y')
        else:
            launch_str = '—'

        rows.append([
            str(store['name'])[:22],
            str(store['location'] or '—')[:20],
            launch_str,
            str(int(pct)) + '%',
            status_label,
            str(pending_total)
        ])
        row_statuses.append(status_color)

    col_widths = [3.2 * cm, 3 * cm, 2.5 * cm, 2 * cm, 2.3 * cm, 1.8 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (3, 0), (5, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
    ])

    for i, color in enumerate(row_statuses, start=1):
        style.add('BACKGROUND', (4, i), (4, i), color)
        style.add('TEXTCOLOR', (4, i), (4, i), colors.white)
        style.add('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== SHIPMENTS TABLE ====================

def build_shipments_table(shipments_df):
    """Build shipments table with transport status per shipment"""
    elements = []
    
    if shipments_df.empty:
        return elements
    
    # Filter pending/in transit only
    if 'delivery_status' in shipments_df.columns:
        active = shipments_df[shipments_df['delivery_status'].isin(['Pending', 'In Transit', 'Delayed'])]
    else:
        active = shipments_df

    if active.empty:
        return elements

    elements.extend(build_section_header('Active Shipments & Transport Status'))

    header = ['ID', 'Store', 'Ship Date', 'Scheduled', 'Status', 'Transport', 'Items']
    rows = [header]
    row_status_colors = []
    row_transport_colors = []

    status_colors = {
        'Pending': ACCENT_YELLOW,
        'In Transit': ACCENT_BLUE,
        'Delivered': ACCENT_GREEN,
        'Delayed': ACCENT_RED,
    }

    for _, ship in active.head(15).iterrows():
        ship_id = '#' + str(ship.get('id', ''))
        store_name = str(ship.get('store_name', 'Unknown'))[:20]
        
        ship_date = ship.get('date')
        if ship_date:
            if isinstance(ship_date, str):
                try:
                    ship_date_str = date.fromisoformat(ship_date[:10]).strftime('%d %b')
                except Exception:
                    ship_date_str = str(ship_date)[:10]
            else:
                ship_date_str = ship_date.strftime('%d %b') if hasattr(ship_date, 'strftime') else str(ship_date)
        else:
            ship_date_str = '—'
        
        scheduled = ship.get('scheduled_date')
        if scheduled:
            if isinstance(scheduled, str):
                try:
                    sched_str = date.fromisoformat(scheduled[:10]).strftime('%d %b')
                except Exception:
                    sched_str = str(scheduled)[:10]
            else:
                sched_str = scheduled.strftime('%d %b') if hasattr(scheduled, 'strftime') else str(scheduled)
        else:
            sched_str = '—'
        
        status = ship.get('delivery_status') or 'Pending'
        transport_ready = bool(ship.get('transportation_ready', False))
        transport_text = '✓ Ready' if transport_ready else '✗ Not Ready'
        
        total_items = int(ship.get('qty_30d', 0) or 0) + int(ship.get('qty_40d', 0) or 0) + int(ship.get('qty_60d', 0) or 0)
        
        rows.append([
            ship_id,
            store_name,
            ship_date_str,
            sched_str,
            status,
            transport_text,
            str(total_items)
        ])
        row_status_colors.append(status_colors.get(status, TEXT_GRAY))
        row_transport_colors.append(ACCENT_GREEN if transport_ready else ACCENT_RED)

    col_widths = [1.2 * cm, 3.5 * cm, 2 * cm, 2 * cm, 2.5 * cm, 2.8 * cm, 1.5 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
    ])

    # Color status column
    for i, color in enumerate(row_status_colors, start=1):
        style.add('BACKGROUND', (4, i), (4, i), color)
        style.add('TEXTCOLOR', (4, i), (4, i), colors.white)
        style.add('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')

    # Color transport column
    for i, color in enumerate(row_transport_colors, start=1):
        style.add('BACKGROUND', (5, i), (5, i), color)
        style.add('TEXTCOLOR', (5, i), (5, i), colors.white)
        style.add('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== DIVIDERS SUMMARY ====================

def build_dividers_summary(stocks, stores_df, shipments_df):
    elements = []
    elements.extend(build_section_header('Dividers Summary'))

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

    col_widths = [2.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_GRAY),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F4F8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])

    for i, color in enumerate(row_colors, start=1):
        style.add('BACKGROUND', (0, i), (0, i), color)
        style.add('TEXTCOLOR', (0, i), (0, i), colors.white)
        style.add('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== MAGNET STATUS ====================

def build_magnet_summary(magnet_stock, magnet_status):
    elements = []
    elements.extend(build_section_header('Magnet Status'))

    info_para = Paragraph(
        '<para fontSize="9" fontName="Helvetica" textColor="' + COLOR_HEX['TEXT_DARK'] + '">'
        '<b>Strips at Vendor:</b> ' + str(magnet_stock) + ' | '
        'Each strip can magnetize ~1 divider</para>',
        getSampleStyleSheet()['Normal']
    )
    elements.append(info_para)
    elements.append(Spacer(1, 6))

    header = ['Divider Type', 'With Magnet', 'Without Magnet', 'Total', 'Coverage %']
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

    col_widths = [3 * cm, 3 * cm, 3.5 * cm, 2.5 * cm, 3 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_GRAY),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F4F8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])

    for i, color in enumerate(row_colors, start=1):
        style.add('BACKGROUND', (0, i), (0, i), color)
        style.add('TEXTCOLOR', (0, i), (0, i), colors.white)
        style.add('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== ACTION ITEMS TABLE ====================

def build_action_items_table(items_df):
    elements = []
    elements.extend(build_section_header('Action Items'))

    if items_df.empty:
        elements.append(Paragraph(
            '<i>No action items.</i>',
            getSampleStyleSheet()['Normal']
        ))
        elements.append(Spacer(1, 12))
        return elements

    header = ['#', 'Action', 'Owner', 'ETA', 'Status', 'Store']
    rows = [header]
    row_statuses = []

    status_colors = {
        'Pending': ACCENT_YELLOW,
        'In Progress': ACCENT_BLUE,
        'Completed': ACCENT_GREEN,
        'Blocked': ACCENT_RED,
    }

    for idx, (_, item) in enumerate(items_df.iterrows(), start=1):
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
        action = str(item.get('action_text') or '')[:50]
        owner = str(item.get('owner') or '—')[:20]
        store_name = str(item.get('store_name') or '—')[:18]

        rows.append([str(idx), action, owner, eta_str, status, store_name])
        row_statuses.append(status_colors.get(status, TEXT_GRAY))

    col_widths = [0.8 * cm, 5.5 * cm, 2.8 * cm, 2.3 * cm, 2.5 * cm, 3.1 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (4, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
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

def add_page_number(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(TEXT_GRAY)
    page_num = canvas_obj.getPageNumber()
    text = 'Launch Team Tracker - Progress Report | Page ' + str(page_num)
    canvas_obj.drawCentredString(A4[0] / 2.0, 1 * cm, text)
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
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title='Launch Team Tracker Report'
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

    story.append(build_header(week_num, report_date, next_update, styles))
    story.append(Spacer(1, 16))

    story.extend(build_executive_summary(exec_summary, styles))
    story.extend(build_highlights_section(highlights))
    story.extend(build_lowlights_section(lowlights))

    # KPI cards
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

    story.extend(build_stores_table(stores_df, shipments_df))
    story.extend(build_shipments_table(shipments_df))
    story.extend(build_dividers_summary(stocks, stores_df, shipments_df))
    story.extend(build_magnet_summary(magnet_stock, magnet_status))
    story.extend(build_action_items_table(action_items_df))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return buffer
