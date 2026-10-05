"""
Django signals for DAILYFUNDZBOOST
Handles automatic notifications and actions when models are created/updated
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Deposit
from .emails import (
    send_admin_new_deposit_notification,
    send_admin_new_user_notification,
    send_welcome_email,
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Deposit)
def notify_admin_on_new_deposit(sender, instance, created, **kwargs):
    """
    Automatically send email notification to admin when a new deposit is created.
    Only triggers for new pending deposits (not updates).
    """
    if created and instance.status == 'pending':
        try:
            send_admin_new_deposit_notification(instance)
            logger.info(f"[SIGNAL] Admin notified about deposit #{instance.id}")
        except Exception as e:
            logger.error(f"[SIGNAL] Failed to notify admin about deposit #{instance.id}: {e}")


@receiver(post_save, sender=User)
def notify_admin_on_new_user(sender, instance, created, **kwargs):
    """
    Send notifications when a new user registers.
    Sends welcome email to user and notification to admin.
    """
    if created:
        try:
            # Send welcome email to user
            send_welcome_email(instance)
            logger.info(f"[SIGNAL] Welcome email sent to {instance.username}")
            
            # Notify admin about new user
            send_admin_new_user_notification(instance)
            logger.info(f"[SIGNAL] Admin notified about new user {instance.username}")
        except Exception as e:
            logger.error(f"[SIGNAL] Failed to send new user notifications: {e}")
