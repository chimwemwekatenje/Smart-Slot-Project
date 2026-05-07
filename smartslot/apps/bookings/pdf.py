"""PDF receipt generation for SmartSlot bookings."""
import io
import qrcode
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import pt
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

TEAL   = colors.HexColor('#14B8A6')
DARK   = colors.HexColor('#0F172A')
SURFACE = colors.HexColor('#1E2937')
MUTED  = colors.HexColor('#94A3B8')
WHITE  = colors.white
WARNING = colors.HexColor('#F59E0B')


def _qr_image(data: str, size: int = 120) -> Image:
    """Generate a QR code image and return a ReportLab Image object."""
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return Image(buf, width=size * pt, height=size * pt)


def _fmt_dt(dt):
    """Format a datetime as 'Mon 05 May 2026, 09:00'."""
    if not dt:
        return '-'
    try:
        local = dt.astimezone()
    except Exception:
        local = dt
    return local.strftime('%a %d %b %Y, %H:%M')


def generate_booking_pdf(booking) -> io.BytesIO:
    """
    Generate a PDF receipt for the given booking.
    Returns a BytesIO buffer seeked to position 0.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40 * pt,
        rightMargin=40 * pt,
        topMargin=40 * pt,
        bottomMargin=40 * pt,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header band ──────────────────────────────────────────────────────────
    org = booking.organisation
    cd  = booking.custom_data

    # Build header table: [logo/name | SmartSlot label]
    header_left_content = []

    if org.logo:
        try:
            logo_img = Image(org.logo.path, width=120 * pt, height=40 * pt)
            logo_img.hAlign = 'LEFT'
            header_left_content.append(logo_img)
        except Exception:
            pass

    org_name_style = ParagraphStyle(
        'OrgName',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=WHITE,
        spaceAfter=2,
    )
    header_left_content.append(Paragraph(org.name, org_name_style))

    receipt_label_style = ParagraphStyle(
        'ReceiptLabel',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#E2E8F0'),
    )
    header_left_content.append(Paragraph('SmartSlot Booking Receipt', receipt_label_style))

    from reportlab.platypus import KeepInFrame
    header_cell = header_left_content

    header_table = Table(
        [[header_cell]],
        colWidths=[doc.width],
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), TEAL),
        ('TOPPADDING',    (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('LEFTPADDING',   (0, 0), (-1, -1), 20),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 20),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20 * pt))

    # ── Detail rows ───────────────────────────────────────────────────────────
    label_style = ParagraphStyle(
        'Label',
        fontName='Helvetica',
        fontSize=10,
        textColor=MUTED,
    )
    value_style = ParagraphStyle(
        'Value',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#E2E8F0'),
    )

    def row(label, value):
        return [Paragraph(label, label_style), Paragraph(str(value) if value else '-', value_style)]

    detail_rows = [
        row('Resource',    booking.resource.name),
        row('Category',    booking.resource.category),
        row('Organisation', org.name),
    ]
    if cd.get('full_name'):
        detail_rows.append(row('Booked by', cd['full_name']))
    if cd.get('email'):
        detail_rows.append(row('Email', cd['email']))
    if cd.get('phone'):
        detail_rows.append(row('Phone', cd['phone']))
    if cd.get('department'):
        detail_rows.append(row('Department', cd['department']))
    if cd.get('reason'):
        detail_rows.append(row('Reason', cd['reason']))

    detail_rows += [
        row('From',   _fmt_dt(booking.start_time)),
        row('To',     _fmt_dt(booking.end_time)),
        row('Status', booking.status),
    ]

    detail_table = Table(
        detail_rows,
        colWidths=[120 * pt, doc.width - 120 * pt],
    )
    detail_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), SURFACE),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.5, colors.HexColor('#334155')),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 24 * pt))

    # ── QR Code ───────────────────────────────────────────────────────────────
    base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    verify_url = f"{base_url}/verify/{booking.qr_token}/"

    qr_img = _qr_image(verify_url, size=120)
    qr_img.hAlign = 'CENTER'

    qr_label_style = ParagraphStyle(
        'QRLabel',
        fontName='Helvetica',
        fontSize=9,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    booking_id_style = ParagraphStyle(
        'BookingID',
        fontName='Helvetica',
        fontSize=8,
        textColor=MUTED,
        alignment=TA_CENTER,
    )

    qr_table = Table(
        [[qr_img], [Paragraph('Scan to verify at entrance', qr_label_style)],
         [Paragraph(f'Booking ID: #{booking.id}', booking_id_style)]],
        colWidths=[doc.width],
    )
    qr_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), SURFACE),
        ('TOPPADDING',    (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(qr_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
