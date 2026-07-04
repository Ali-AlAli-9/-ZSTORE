from django.core.mail import send_mail as django_send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_email(subject, message, from_email, recipient_list):
    try:
        django_send_mail(
            subject=subject,
            message="",
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        raise
