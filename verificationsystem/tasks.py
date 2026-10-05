import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_account_activation_email_task(self, email, email_token):
    site_domain = getattr(settings, 'SITE_DOMAIN', 'http://127.0.0.1:8000')
    site_name = getattr(settings, 'SITE_NAME', 'ShopKart')

    subject = f"Verify Your {site_name} Account"
    message = (
        f"Welcome to {site_name}!\n\n"
        f"Click the link below to verify your account:\n\n"
        f"{site_domain}/account/activate/{email_token}/\n\n"
        f"If you did not create this account, please ignore this email."
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info("Verification email sent to %s", email)
    except Exception as exc:
        logger.exception("Failed to send verification email to %s", email)
        raise self.retry(exc=exc)