import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_order_confirmation_email(self, order_id):
    """
    Runs on the Celery worker (via Redis broker), so placing the order
    never has to wait on the SMTP connection.
    Sends the customer an email with the order amount + a PDF invoice,
    and mentions the delivery-within-N-days commitment.
    """
    from Orders.models import Order
    from Orders.invoice import generate_invoice_pdf

    try:
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)
    except Order.DoesNotExist:
        logger.error("send_order_confirmation_email: Order %s not found", order_id)
        return

    delivery_days = getattr(settings, 'DELIVERY_DAYS', 3)
    site_name = getattr(settings, 'SITE_NAME', 'ShopKart')

    subject = f"Order Confirmed - {order.order_number} | {site_name}"

    lines = [
        f"Hi {order.full_name},",
        "",
        f"Thank you for shopping with {site_name}! Your order has been placed successfully.",
        "",
        f"Order Number : {order.order_number}",
        f"Total Amount : Rs. {order.total_amount}",
        f"Payment Mode : Cash on Delivery (COD)",
        "",
        "Items:",
    ]
    for item in order.items.all():
        variant = f" ({item.variant_info})" if item.variant_info else ""
        lines.append(f"  - {item.product_name}{variant} x {item.quantity} = Rs. {item.sub_total}")

    lines += [
        "",
        f"Delivery Address: {order.address_line}, {order.city}, {order.state} - {order.pincode}",
        "",
        f"Your order will be delivered within {delivery_days} days.",
        f"Please keep Rs. {order.total_amount} ready for payment at the time of delivery.",
        "",
        "A detailed invoice is attached with this email.",
        "",
        f"Thanks,\n{site_name} Team",
    ]
    body = "\n".join(lines)

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=[order.user.email],
        )
        pdf_bytes = generate_invoice_pdf(order)
        email.attach(f"Invoice_{order.order_number}.pdf", pdf_bytes, "application/pdf")
        email.send(fail_silently=False)
        logger.info("Order confirmation email sent for %s", order.order_number)
    except Exception as exc:
        logger.exception("Failed to send order confirmation email for %s", order.order_number)
        raise self.retry(exc=exc)
