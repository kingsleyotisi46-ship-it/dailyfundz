"""
SMM Provider API Integration

Supports providers with standard SMM panel API format:
- Add order: action=add, service, link, quantity
- Order status: action=status, order
- Balance: action=balance

Configure your provider in Django settings:
SMM_PROVIDER_URL = 'https://provider.com/api/v2'
SMM_PROVIDER_KEY = 'your-api-key'
"""

import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SMMProvider:
    """Interface for SMM panel provider APIs"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'SMM_PROVIDER_URL', None)
        self.api_key = getattr(settings, 'SMM_PROVIDER_KEY', None)
    
    def is_configured(self):
        return bool(self.api_url and self.api_key)
    
    def _request(self, data):
        """Make request to provider API"""
        if not self.is_configured():
            logger.warning("SMM Provider not configured")
            return {'error': 'Provider not configured'}
        
        data['key'] = self.api_key
        
        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SMM Provider request failed: {e}")
            return {'error': str(e)}
    
    def get_balance(self):
        """Get provider account balance"""
        return self._request({'action': 'balance'})
    
    def get_services(self):
        """Get list of services from provider"""
        return self._request({'action': 'services'})
    
    def add_order(self, service_id, link, quantity):
        """
        Place order with provider
        
        Args:
            service_id: Provider's service ID
            link: Target URL (profile/post)
            quantity: Number of followers/likes/etc
            
        Returns:
            {'order': provider_order_id} on success
            {'error': message} on failure
        """
        return self._request({
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': quantity,
        })
    
    def get_order_status(self, order_id):
        """
        Check order status from provider
        
        Returns:
            {
                'status': 'Pending'|'In progress'|'Processing'|'Completed'|'Partial'|'Canceled',
                'charge': cost,
                'start_count': initial count,
                'remains': remaining to deliver
            }
        """
        return self._request({
            'action': 'status',
            'order': order_id,
        })
    
    def get_multiple_status(self, order_ids):
        """Check multiple orders status"""
        return self._request({
            'action': 'status',
            'orders': ','.join(str(id) for id in order_ids),
        })


# Singleton instance
smm_provider = SMMProvider()


def place_provider_order(order):
    """
    Place order with SMM provider and update local order
    
    Args:
        order: Order model instance
        
    Returns:
        bool: Success status
    """
    from .models import Order
    
    if not smm_provider.is_configured():
        logger.info(f"Order #{order.id}: Provider not configured, staying pending")
        return False
    
    # Get provider service ID from our service
    provider_service_id = getattr(order.service, 'provider_service_id', None)
    if not provider_service_id:
        logger.warning(f"Order #{order.id}: No provider service ID mapped")
        return False
    
    result = smm_provider.add_order(
        service_id=provider_service_id,
        link=order.link,
        quantity=order.quantity
    )
    
    if 'order' in result:
        order.provider_order_id = str(result['order'])
        order.status = 'processing'
        order.save()
        logger.info(f"Order #{order.id}: Submitted to provider as #{result['order']}")
        return True
    else:
        logger.error(f"Order #{order.id}: Provider error - {result.get('error')}")
        return False


def sync_order_status(order):
    """
    Sync order status from provider
    
    Args:
        order: Order model instance with provider_order_id
    """
    from django.utils import timezone
    
    if not order.provider_order_id:
        return
    
    result = smm_provider.get_order_status(order.provider_order_id)
    
    if 'error' in result:
        logger.error(f"Order #{order.id}: Status check failed - {result['error']}")
        return
    
    # Map provider status to our status
    status_map = {
        'Pending': 'pending',
        'In progress': 'in_progress',
        'Processing': 'processing',
        'Completed': 'completed',
        'Partial': 'partial',
        'Canceled': 'cancelled',
        'Cancelled': 'cancelled',
    }
    
    new_status = status_map.get(result.get('status'), order.status)
    
    if order.status != new_status:
        order.status = new_status
        if new_status == 'completed':
            order.completed_at = timezone.now()
            order.remains = 0
        elif 'start_count' in result:
            order.start_count = int(result.get('start_count', 0))
        if 'remains' in result:
            order.remains = int(result.get('remains', 0))
        order.save()
        logger.info(f"Order #{order.id}: Status updated to {new_status}")
