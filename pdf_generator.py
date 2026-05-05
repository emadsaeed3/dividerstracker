"""
PDF Report Generator
Generates professional progress reports similar to the reference design
"""
import os
from io import BytesIO
from datetime import date, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas


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
TEXT_ON_DARK = colors.HexColor('#ECF0F1')
TEXT_DARK = colors.HexColor('#2C3E50')
TEXT_GRAY = colors.HexColor('#7F8C8D')
DIVIDER_GRAY = colors.HexColor('#BDC3C7')


# ==================== STYLES ====================

def get_styles():
    """Return custom paragraph styles"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        borderPadding=4,
    ))

    styles.add(ParagraphStyle(
        name='BodyTextCustom',
        fontName='Helvetica',
        fontSize=9,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY,
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name='BulletText',
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_LEFT,
        leading=13,
        leftIndent=10,
    ))

    styles.add(ParagraphStyle(
        name='KPINumber',
        fontName='Helvetica-Bold',
        fontSize=20,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='KPILabel',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT_GRAY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='TableCellCenter',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white,
        alignment=TA_LEFT,
    ))

    return styles


# ==================== HEADER ====================

def build_header(week_number, report_date, next_update, styles):
    """Build the dark report header"""
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
    subtitle = f'Week {week_number} | Report Date: {report_date_str} | Next Update: {next_update_str}'

    title_para = Paragraph(f'<b>{title_text}</b>', styles['ReportTitle'])
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
    """Build a section header with thin line"""
    elements = []
    para = Paragraph(
        f'<para fontSize="12" fontName="Helvetica-Bold" textColor="#2C3E50">'
        f'<b>{title}</b></para>',
        getSampleStyleSheet()['Normal']
    )
    elements.append(para)

    # Thin line underneath
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
    """Build executive summary section"""
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

def build_highlights_box(title, bullets_text, bg_color):
    """Build a dark box with bullets for highlights/lowlights"""
    if not bullets_text or not bullets_text.strip():
        bullets_text = '<i>None reported.</i>'

    # Split by lines and build bullet list
    lines = [line.strip() for line in bullets_text.split('\n') if line.strip()]
    
    bullet_html = ''
    for line in lines:
        # Remove existing bullets
        clean_line = line.lstrip('•-*').strip()
        if clean_line:
            bullet_html += f'<para fontName="Helvetica" fontSize="9" textColor="#FFFFFF" leading="13" leftIndent="10">• {clean_line}</para>'
    
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
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))

    return box


def build_highlights_section(highlights_text):
    """Build highlights section"""
    elements = []
    elements.extend(build_section_header('Highlights'))
    elements.append(build_highlights_box('Highlights', highlights_text, HIGHLIGHT_BG))
    elements.append(Spacer(1, 12))
    return elements


def build_lowlights_section(lowlights_text):
    """Build lowlights section"""
    elements = []
    elements.extend(build_section_header('Lowlights'))
    elements.append(build_highlights_box('Lowlights', lowlights_text, LOWLIGHT_BG))
    elements.append(Spacer(1, 12))
    return elements


# ==================== KPI CARDS ====================

def build_kpi_cards(kpis):
    """Build Portfolio KPI cards row
    kpis: list of tuples (value, label, color)
    """
    elements = []
    elements.extend(build_section_header('Portfolio Key Performance Indicators'))

    styles = getSampleStyleSheet()

    # Build each card
    cards_row = []
    for value, label, color in kpis:
        number_para = Paragraph(
            f'<para fontSize="22" fontName="Helvetica-Bold" textColor="{color.hexval()[2:]}" alignment="center">'
            f'<b>{value}</b></para>',
            styles['Normal']
        )
        label_para = Paragraph(
            f'<para fontSize="7" fontName="Helvetica" textColor="#7F8C8D" alignment="center">{label}</para>',
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

    # Put cards in a row with spacing
    num_cards = len(cards_row)
    col_widths = [3.2 * cm] * num_cards
    # Add spacers between
    row_content = cards_row

    cards_table = Table([row_content], colWidths=col_widths)
    cards_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(cards_table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== STORE STATUS TABLE ====================

def get_store_status(store, shipped_total, required_total):
    """Determine store status and color"""
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
    """Build store status summary table"""
    elements = []
    elements.extend(build_section_header('Store Status Summary'))

    if stores_df.empty:
        elements.append(Paragraph(
            '<i>No stores to display.</i>',
            getSampleStyleSheet()['Normal']
        ))
        elements.append(Spacer(1, 12))
        return elements

    header = [
        'Store',
        'Location',
        'Launch Date',
        'Progress',
        'Status',
        'Transport',
        'Pending'
    ]

    rows = [header]
    row_statuses = []  # track status colors per row

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

        transport = '✓ Ready' if store.get('transportation_ready') else '✗ Not Ready'

        rows.append([
            str(store['name'])[:20],
            str(store['location'] or '—')[:18],
            launch_str,
            f'{pct:.0f}%',
            status_label,
            transport,
            str(pending_total)
        ])
        row_statuses.append(status_color)

    col_widths = [2.8 * cm, 2.8 * cm, 2.3 * cm, 1.8 * cm, 2 * cm, 2.3 * cm, 1.8 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    # Base style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('ALIGN', (3, 0), (6, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, DIVIDER_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
    ])

    # Color status cells
    for i, color in enumerate(row_statuses, start=1):
        style.add('BACKGROUND', (4, i), (4, i), color)
        style.add('TEXTCOLOR', (4, i), (4, i), colors.white)
        style.add('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')

    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 14))
    return elements


# ==================== DIVIDERS SUMMARY TABLE ====================

def build_dividers_summary(stocks, stores_df, shipments_df):
    """Build dividers stock summary"""
    elements = []
    elements.extend(build_section_header('Dividers Summary'))

    header = ['Type', 'Vendor Stock', 'Required', 'Shipped', 'Pending', 'Progress']
    rows = [header]

    color_map = {'30D': ACCENT_BLUE, '40D': ACCENT_ORANGE, '60D': ACCENT_PURPLE}
    row_colors = []

    for dtype in ['30D', '40D', '60D']:
        stock = stocks.get(dtype, 0)
        col = f'required_{dtype.lower()}'
        ship_col = f'qty_{dtype.lower()}'
        required = int(stores_df[col].sum()) if not stores_df.empty else 0
        shipped = int(shipments_df[ship_col].sum()) if not shipments_df.empty else 0
        pending = max(0, required - shipped)
        pct = (shipped / required * 100) if required > 0 else 0

        rows.append([
            dtype,
            str(stock),
            str(required),
            str(shipped),
            str(pending),
            f'{pct:.0f}%'
        ])
        row_colors.append(color_map.get(dtype, ACCENT_BLUE))

    # Totals row
    total_stock = sum(stocks.get(t, 0) for t in ['30D', '40D', '60D'])
    total_req = sum(int(stores_df[f'required_{t.lower()}'].sum()) if not stores_df.empty else 0
                     for t in ['30D', '40D', '60D'])
    total_ship = sum(int(shipments_df[f'qty_{t.lower()}'].sum()) if not shipments_df.empty else 0
                      for t in ['30D', '40D', '60D'])
    total_pending = max(0, total_req - total_ship)
    total_pct = (total_ship / total_req * 100) if total_req > 0 else 0

    rows.append([
        'TOTAL',
        str(total_stock),
        str(total_req),
        str(total_ship),
        str(total_pending),
        f'{total_pct:.0f}%'
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
        # Totals row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F4F8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])

    # Color type cells
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
    """Build magnet summary table"""
    elements = []
    elements.extend(build_section_header('Magnet Status'))

    # Info line
    info_para = Paragraph(
        f'<para fontSize="9" fontName="Helvetica" textColor="#2C3E50">'
        f'<b>Strips at Vendor:</b> {magnet_stock} | '
        f'Each strip can magnetize ~1 divider (3 squares + 1 rectangle)</para>',
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

        rows.append([dtype, str(w), str(wo), str(total), f'{pct:.0f}%'])
        row_colors.append(color_map.get(dtype))

    grand_total = total_with + total_without
    grand_pct = (total_with / grand_total * 100) if grand_total > 0 else 0
    rows.append([
        'TOTAL',
        str(total_with),
        str(total_without),
        str(grand_total),
        f'{grand_pct:.0f}%'
    ])

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
    """Build action items table"""
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
                eta_str = eta.strftime('%d %b %Y')
        else:
            eta_str = '—'

        status = item.get('status') or 'Pending'
        action = str(item.get('action_text') or '')[:50]
        owner = str(item.get('owner') or '—')[:20]
        store_name = str(item.get('store_name') or '—')[:18]

        rows.append([
            str(idx),
            action,
            owner,
            eta_str,
            status,
            store_name
        ])
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
    """Add page number footer"""
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(TEXT_GRAY)
    page_num = canvas_obj.getPageNumber()
    text = f'Launch Team Tracker - Progress Report | Page {page_num}'
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
    """Generate the complete progress report PDF"""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title='Launch Team Tracker Report'
    )

    styles = get_styles()
    story = []

    # Data prep
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

    # === HEADER ===
    story.append(build_header(week_num, report_date, next_update, styles))
    story.append(Spacer(1, 16))

    # === EXECUTIVE SUMMARY ===
    story.extend(build_executive_summary(exec_summary, styles))

    # === HIGHLIGHTS ===
    story.extend(build_highlights_section(highlights))

    # === LOWLIGHTS ===
    story.extend(build_lowlights_section(lowlights))

    # === KPI CARDS ===
    total_stores = len(stores_df) if not stores_df.empty else 0
    launched_count = len(stores_df[stores_df['is_launched'] == True]) if not stores_df.empty and 'is_launched' in stores_df.columns else 0
    upcoming_count = total_stores - launched_count

    pending_ships = 0
    if not shipments_df.empty and 'delivery_status' in shipments_df.columns:
        pending_ships = len(shipments_df[
            shipments_df['delivery_status'].isin(['Pending', 'In Transit', 'Delayed'])
        ])

    action_items_count = len(action_items_df) if not action_items_df.empty else 0
    open_actions = 0
    if not action_items_df.empty and 'status' in action_items_df.columns:
        open_actions = len(action_items_df[action_items_df['status'] != 'Completed'])

    kpis = [
        (str(total_stores), 'Total Stores', DARK_HEADER),
        (str(launched_count), 'Launched', ACCENT_GREEN),
        (str(upcoming_count), 'Upcoming', ACCENT_BLUE),
        (str(pending_ships), 'Pending Ships', ACCENT_ORANGE),
        (str(open_actions), 'Open Actions', ACCENT_RED),
    ]
    story.extend(build_kpi_cards(kpis))

    # === STORE STATUS TABLE ===
    story.extend(build_stores_table(stores_df, shipments_df))

    # === DIVIDERS SUMMARY ===
    story.extend(build_dividers_summary(stocks, stores_df, shipments_df))

    # === MAGNET STATUS ===
    story.extend(build_magnet_summary(magnet_stock, magnet_status))

    # === ACTION ITEMS ===
    story.extend(build_action_items_table(action_items_df))

    # Build PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return buffer
