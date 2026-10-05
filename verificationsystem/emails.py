import logging
from .tasks import send_account_activation_email_task

logger = logging.getLogger(__name__)


def send_account_activation_email(email, email_token):
    """
    Queues the verification email on Celery (via Redis) instead of sending
    it synchronously, so user registration never fails/hangs just because
    the SMTP call is slow or temporarily down.
    """
    try:
        send_account_activation_email_task.delay(email, email_token)
    except Exception:
        logger.exception(
            "Could not queue verification email for %s. "
            "Is the Redis server and Celery worker running?", email
        )
        