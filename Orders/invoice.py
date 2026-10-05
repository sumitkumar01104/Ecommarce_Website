import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.conf import settings
from django.utils import timezone
from xml.sax.saxutils import escape

def generate_invoice_pdf(order):
    """Builds a PDF invoice for the given Order and returns it as raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=25 * mm, bottomMargin=25 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', parent=styles['Heading1'], fontSize=20, spaceAfter=4)
    normal = styles['Normal']

    elements = []

    elements.append(Paragraph(getattr(settings, 'SITE_NAME', 'ShopKart'), title_style))
    elements.append(Paragraph("Order Invoice", styles['Heading3']))
    elements.append(Spacer(1, 10))

    meta = [
        ["Order Number:", order.order_number],
        ["Order Date:", timezone.localtime(order.created_at).strftime('%d %b %Y, %I:%M %p')],
        ["Payment Method:", order.get_payment_method_display()],
        ["Status:", order.get_status_display()],
    ]
    meta_table = Table(meta, colWidths=[120, 300])
    meta_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Ship To:", styles['Heading4']))
    address_text = (
        f"{escape(order.full_name)}<br/>"
        f"{escape(order.address_line)}<br/>"
        f"{escape(order.city)}, {escape(order.state)} - {escape(order.pincode)}<br/>"
        f"Phone: {escape(order.phone_number)}"
    )
    elements.append(Paragraph(address_text, normal))
    elements.append(Spacer(1, 16))

    # Items table
    data = [["#", "Item", "Variant", "Qty", "Unit Price", "Subtotal"]]
    for idx, item in enumerate(order.items.all(), start=1):
        data.append([
            str(idx),
            item.product_name,
            item.variant_info or "-",
            str(item.quantity),
            f"Rs. {item.unit_price}",
            f"Rs. {item.sub_total}",
        ])

    data.append(["", "", "", "", "Total", f"Rs. {order.total_amount}"])

    items_table = Table(data, colWidths=[25, 160, 90, 35, 75, 75])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#dddddd')),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 24))

    delivery_days = getattr(settings, 'DELIVERY_DAYS', 3)
    note_style = ParagraphStyle('note', parent=normal, textColor=colors.HexColor('#1a7a3c'), fontSize=11)
    elements.append(Paragraph(
        f"Your order will be delivered within {delivery_days} days. "
        f"Payment mode: Cash on Delivery — please keep Rs. {order.total_amount} ready at the time of delivery.",
        note_style
    ))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Thank you for shopping with us!", normal))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes