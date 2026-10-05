"""
Management command to sync order statuses from SMM provider.
Run periodically via cron or scheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from social.models import Order
from social.smm_provider import smm_provider
from social.emails import send_order_completed_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync order statuses from SMM provider (JustAnotherPanel)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of orders to sync (default: 100)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all pending orders, not just recent ones'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        sync_all = options['all']
        
        if not smm_provider.is_configured():
            self.stdout.write(self.style.ERROR('SMM Provider not configured. Set SMM_PROVIDER_KEY.'))
            return
        
        # Get orders to sync
        orders_qs = Order.objects.filter(
            status__in=['pending', 'processing', 'in_progress'],
            provider_order_id__isnull=False
        ).exclude(provider_order_id='')
        
        if not sync_all:
            # Only sync orders from last 7 days by default
            week_ago = timezone.now() - timezone.timedelta(days=7)
            orders_qs = orders_qs.filter(created_at__gte=week_ago)
        
        orders = orders_qs[:limit]
        
        self.stdout.write(f'Syncing {orders.count()} orders...')
        
        synced = 0
        completed = 0
        errors = 0
        
        for order in orders:
            try:
                result = smm_provider.get_order_status(order.provider_order_id)
                
                if 'error' in result:
                    logger.warning(f"Order #{order.id}: API error - {result['error']}")
                    errors += 1
                    continue
                
                new_status = result.get('status', '').lower()
                start_count = result.get('start_count', order.start_count)
                remains = result.get('remains', order.remains)
                
                # Map provider status to our status
                status_map = {
                    'pending': 'pending',
                    'in progress': 'in_progress',
                    'inprogress': 'in_progress',
                    'processing': 'processing',
                    'completed': 'completed',
                    'partial': 'partial',
                    'cancelled': 'cancelled',
                    'canceled': 'cancelled',
                    'refunded': 'refunded',
                }
                
                mapped_status = status_map.get(new_status, order.status)
                
                # Update order if status changed
                if mapped_status != order.status or start_count != order.start_count:
                    old_status = order.status
                    order.status = mapped_status
                    order.start_count = start_count
                    order.remains = remains
                    
                    if mapped_status == 'completed' and old_status != 'completed':
                        order.completed_at = timezone.now()
                        completed += 1
                        # Send completion email
                        send_order_completed_email(order)
                    
                    order.save()
                    synced += 1
                    self.stdout.write(f'  Order #{order.id}: {old_status} -> {mapped_status}')
                    
            except Exception as e:
                logger.error(f"Error syncing order #{order.id}: {e}")
                errors += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Sync complete: {synced} updated, {completed} completed, {errors} errors'
        ))
