#!/usr/bin/env python
"""
Import services from SMM provider API
Run: python import_services.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from social.smm_provider import SMMProvider
from social.models import Service, Platform, ServiceCategory
from decimal import Decimal

def import_services():
    """Import services from SMM provider"""
    
    print("🔄 Fetching services from SMM provider...")
    provider = SMMProvider()
    services_data = provider.get_services()
    
    if not isinstance(services_data, list):
        print(f"❌ Error: {services_data}")
        return
    
    print(f"✅ Found {len(services_data)} services from API")
    
    # Get or create default category
    default_category, _ = ServiceCategory.objects.get_or_create(
        slug='default',
        defaults={'name': 'Social Media Services', 'description': 'General SMM services'}
    )
    
    # Platform mapping (from API category to our platforms)
    platform_mapping = {
        'Instagram': 'instagram',
        'TikTok': 'tiktok',
        'YouTube': 'youtube',
        'Twitter': 'twitter',
        'Facebook': 'facebook',
        'Telegram': 'telegram',
        'Spotify': 'spotify',
        'Threads': 'threads',
    }
    
    imported = 0
    skipped = 0
    
    for service_data in services_data:
        try:
            service_id = service_data.get('service')
            service_name = service_data.get('name', '')
            category_name = service_data.get('category', '')
            provider_rate = Decimal(str(service_data.get('rate', 0)))
            min_qty = service_data.get('min', 100)
            max_qty = service_data.get('max', 10000)
            
            # Find matching platform
            platform = None
            for api_platform, our_slug in platform_mapping.items():
                if api_platform.lower() in category_name.lower() or api_platform.lower() in service_name.lower():
                    try:
                        platform = Platform.objects.get(slug=our_slug)
                        break
                    except Platform.DoesNotExist:
                        pass
            
            # Skip if no matching platform
            if not platform:
                skipped += 1
                continue
            
            # Get or create category
            category_slug = category_name.lower().replace(' ', '-').replace('&', 'and')[:50]
            category, _ = ServiceCategory.objects.get_or_create(
                slug=category_slug,
                defaults={'name': category_name}
            )
            
            # Check if service already exists
            if Service.objects.filter(provider_service_id=service_id).exists():
                skipped += 1
                continue
            
            # Create service
            Service.objects.create(
                platform=platform,
                category=category,
                name=service_name[:200],  # Limit to 200 chars
                description=f"High-quality {platform.name} service",
                provider_price=provider_rate,  # Price from API is per 1000
                markup_percentage=Decimal('50'),  # 50% markup
                price_per_1000=provider_rate * Decimal('1.5'),  # Will be auto-calculated in save()
                min_quantity=min_qty,
                max_quantity=max_qty,
                average_time="1-24 hours",
                is_active=True,
                is_featured=False,
                quality='standard',
                provider_service_id=service_id,
            )
            
            imported += 1
            
            if imported % 100 == 0:
                print(f"   Imported {imported} services...")
        
        except Exception as e:
            print(f"   Error importing service {service_data.get('service')}: {e}")
            continue
    
    print(f"\n✅ Import complete!")
    print(f"   Imported: {imported}")
    print(f"   Skipped: {skipped}")
    print(f"   Total active services: {Service.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    import_services()
