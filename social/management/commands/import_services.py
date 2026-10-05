"""
Django management command to import services from SMM provider API
Usage: python manage.py import_services
"""
from django.core.management.base import BaseCommand
from social.smm_provider import SMMProvider
from social.models import Service, Platform, ServiceCategory
from decimal import Decimal


class Command(BaseCommand):
    help = 'Import services from SMM provider API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of services to import (for testing)',
        )
        parser.add_argument(
            '--platform',
            type=str,
            default=None,
            help='Only import services for specific platform (e.g., instagram)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🔄 Starting service import...'))
        
        # Fetch services from provider
        provider = SMMProvider()
        services_data = provider.get_services()
        
        if not isinstance(services_data, list):
            self.stdout.write(self.style.ERROR(f'❌ Error fetching services: {services_data}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Found {len(services_data)} services from API\n'))
        
        # Get or create default category
        default_category, _ = ServiceCategory.objects.get_or_create(
            slug='default',
            defaults={'name': 'Social Media Services', 'description': 'General SMM services'}
        )
        
        # Platform mapping
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
        limit = options.get('limit')
        filter_platform = options.get('platform')
        
        for service_data in services_data:
            # Check limit
            if limit and imported >= limit:
                self.stdout.write(self.style.WARNING(f'⏸️  Reached limit of {limit} services'))
                break
            
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
                        # Check if filtering by platform
                        if filter_platform and our_slug != filter_platform:
                            continue
                        
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
                
                # Show progress every 100 services
                if imported % 100 == 0:
                    self.stdout.write(self.style.HTTP_INFO(f'   ⏳ Imported {imported} services...'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Error importing service {service_data.get("service")}: {e}'))
                skipped += 1
                continue
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ Import complete!'))
        self.stdout.write(self.style.SUCCESS(f'   Imported: {imported}'))
        self.stdout.write(self.style.WARNING(f'   Skipped: {skipped}'))
        self.stdout.write(self.style.SUCCESS(f'   Total active services: {Service.objects.filter(is_active=True).count()}'))
        self.stdout.write('='*50)
