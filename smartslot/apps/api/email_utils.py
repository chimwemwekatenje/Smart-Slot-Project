import io
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


TEAL = colors.HexColor('#14B8A6')
DARK = colors.HexColor('#0F172A')
SURFACE = colors.HexColor('#1E2937')
MUTED = colors.HexColor('#94A3B8')
WHITE = colors.white


def _fmt_dt(dt_str):
    if not dt_str:
        return '-'
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%a %d %b %Y, %H:%M')
    except Exception:
        return dt_str


def generate_booking_pdf(booking, resource, guest_name, guest_phone, guest_email, reason):
    """Generate a PDF receipt and return it as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', fontSize=26, textColor=WHITE,
                                  fontName='Helvetica-Bold', spaceAfter=4)
    sub_style = ParagraphStyle('sub', fontSize=12, textColor=WHITE,
                                fontName='Helvetica')
    section_style = ParagraphStyle('section', fontSize=9, textColor=MUTED,
                                    fontName='Helvetica-Bold', spaceBefore=16,
                                    spaceAfter=4, letterSpacing=1.5)
    body_style = ParagraphStyle('body', fontSize=10, textColor=DARK,
                                 fontName='Helvetica')

    price = float(resource.get('price') or 0)
    price_str = 'Free' if price == 0 else f"MWK {price:,.2f}"
    booking_id = booking.get('id', 'N/A')
    qr_token = booking.get('qr_token', '')
    status = booking.get('status', 'Issued')
    start = _fmt_dt(booking.get('start_time'))
    end_raw = booking.get('end_time', '')
    end_time = '-'
    if end_raw:
        try:
            dt = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))
            end_time = dt.strftime('%H:%M')
        except Exception:
            end_time = end_raw

    elements = []

    # ── Header banner ──────────────────────────────────────────────────────────
    header_data = [[
        Paragraph('SmartSlot', title_style),
        Paragraph('Booking Receipt', sub_style),
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), TEAL),
        ('ROUNDEDCORNERS', [8]),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))

    def section(title):
        elements.append(Paragraph(title, section_style))
        elements.append(HRFlowable(width='100%', thickness=0.5,
                                    color=colors.HexColor('#334155')))
        elements.append(Spacer(1, 3*mm))

    def row_table(rows):
        data = [[Paragraph(f'<font color="#94A3B8">{k}</font>', body_style),
                 Paragraph(f'<b>{v}</b>', body_style)] for k, v in rows]
        t = Table(data, colWidths=[45*mm, 120*mm])
        t.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 2*mm))

    # ── Booking details ────────────────────────────────────────────────────────
    section('BOOKING DETAILS')
    row_table([
        ('Booking ID', f'#{booking_id}'),
        ('Resource', resource.get('name', '-')),
        ('Category', resource.get('category', '-')),
        ('Organisation', resource.get('organisation_name', '-')),
        ('From', start),
        ('To', end_time),
        ('Amount Paid', price_str),
        ('Status', status),
    ])

    # ── Guest details ──────────────────────────────────────────────────────────
    section('GUEST DETAILS')
    row_table([
        ('Full Name', guest_name),
        ('Phone', guest_phone),
        ('Email', guest_email),
        ('Reason', reason),
    ])

    # ── QR token ───────────────────────────────────────────────────────────────
    section('QR TOKEN (for check-in)')
    elements.append(Paragraph(qr_token, ParagraphStyle(
        'qr', fontSize=8, textColor=MUTED, fontName='Helvetica')))
    elements.append(Spacer(1, 10*mm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width='100%', thickness=0.5,
                                color=colors.HexColor('#334155')))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(
        'Thank you for booking with SmartSlot',
        ParagraphStyle('footer', fontSize=11, textColor=TEAL,
                        fontName='Helvetica-Bold', alignment=TA_CENTER)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def send_booking_receipt_email(booking, resource, guest_name, guest_phone,
                                guest_email, reason):
    """Generate PDF and send it to the guest's email. Runs silently on failure."""
    if not guest_email or not settings.EMAIL_HOST_USER:
        return

    try:
        pdf_bytes = generate_booking_pdf(
            booking, resource, guest_name, guest_phone, guest_email, reason)

        booking_id = booking.get('id', '')
        resource_name = resource.get('name', 'Resource')

        msg = EmailMessage(
            subject=f'SmartSlot — Booking Confirmation #{booking_id}',
            body=(
                f'Dear {guest_name},\n\n'
                f'Your booking for {resource_name} has been confirmed.\n'
                f'Please find your receipt attached as a PDF.\n\n'
                f'Show the QR code in the receipt at the entrance for check-in.\n\n'
                f'Thank you for using SmartSlot.\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[guest_email],
        )
        msg.attach(
            f'SmartSlot_Receipt_{booking_id}.pdf',
            pdf_bytes,
            'application/pdf',
        )
        msg.send(fail_silently=True)
    except Exception:
        pass  # Never crash the booking flow due to email failure
