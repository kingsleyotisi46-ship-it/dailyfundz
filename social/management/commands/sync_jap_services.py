"""
Fetch services from JustAnotherPanel and sync to local database.

Usage:
    python manage.py sync_jap_services
    python manage.py sync_jap_services --import  # Auto-import new services
"""

from django.core.management.base import BaseCommand
from social.smm_provider import smm_provider
from social.models import Platform, ServiceCategory, Service


class Command(BaseCommand):
    help = 'Fetch and sync services from JustAnotherPanel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--import',
            action='store_true',
            dest='auto_import',
            help='Auto-import new services from provider',
        )

    def handle(self, *args, **options):
        if not smm_provider.is_configured():
            self.stderr.write(self.style.ERROR(
                'SMM Provider not configured. Add SMM_PROVIDER_KEY to settings.py'
            ))
            return

        # Check balance first
        balance_result = smm_provider.get_balance()
        if 'error' in balance_result:
            self.stderr.write(self.style.ERROR(f"API Error: {balance_result['error']}"))
            return
        
        self.stdout.write(f"Provider Balance: ${balance_result.get('balance', '0')} {balance_result.get('currency', 'USD')}")

        # Fetch services
        self.stdout.write("Fetching services from provider...")
        result = smm_provider.get_services()
        
        if 'error' in result:
            self.stderr.write(self.style.ERROR(f"Error: {result['error']}"))
            return

        if not isinstance(result, list):
            self.stderr.write(self.style.ERROR("Unexpected response format"))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(result)} services from provider"))

        # Group by category
        categories = {}
        for svc in result:
            cat = svc.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(svc)

        self.stdout.write(f"\nCategories: {list(categories.keys())}")

        # Show sample services
        self.stdout.write("\n--- Sample Services ---")
        for i, svc in enumerate(result[:10]):
            self.stdout.write(
                f"  ID: {svc['service']} | {svc['name']} | "
                f"Rate: ${svc['rate']}/1K | Min: {svc['min']} | Max: {svc['max']} | "
                f"Category: {svc.get('category', 'N/A')}"
            )
        
        if len(result) > 10:
            self.stdout.write(f"  ... and {len(result) - 10} more")

        if options['auto_import']:
            self.import_services(result)
        else:
            self.stdout.write(self.style.WARNING(
                "\nRun with --import flag to auto-import services, or manually set "
                "provider_service_id in Django Admin for existing services."
            ))

    def import_services(self, provider_services):
        """Auto-import services from provider"""
        self.stdout.write("\n--- Importing Services ---")

        # Platform detection keywords
        platform_keywords = {
            'instagram': ['instagram', 'ig ', 'insta'],
            'tiktok': ['tiktok', 'tik tok', 'tt '],
            'youtube': ['youtube', 'yt ', 'subscribers'],
            'twitter': ['twitter', 'x ', 'tweet'],
            'facebook': ['facebook', 'fb '],
        }

        # Category detection keywords
        category_keywords = {
            'followers': ['follower', 'subscriber', 'fan'],
            'likes': ['like', 'heart'],
            'views': ['view', 'watch', 'impression'],
            'comments': ['comment', 'reply'],
            'shares': ['share', 'retweet', 'repost'],
        }

        imported = 0
        skipped = 0

        for svc in provider_services:
            name = svc['name'].lower()
            
            # Detect platform
            detected_platform = None
            for slug, keywords in platform_keywords.items():
                if any(kw in name for kw in keywords):
                    detected_platform = slug
                    break
            
            if not detected_platform:
                skipped += 1
                continue

            # Detect category
            detected_category = 'followers'  # default
            for slug, keywords in category_keywords.items():
                if any(kw in name for kw in keywords):
                    detected_category = slug
                    break

            # Get or create platform and category
            platform, _ = Platform.objects.get_or_create(
                slug=detected_platform,
                defaults={
                    'name': detected_platform.title(),
                    'icon': {'instagram': '📸', 'tiktok': '🎵', 'youtube': '▶️', 
                            'twitter': '🐦', 'facebook': '👤'}.get(detected_platform, '📱')
                }
            )
            category, _ = ServiceCategory.objects.get_or_create(
                slug=detected_category,
                defaults={'name': detected_category.title()}
            )

            # Check if service already exists
            existing = Service.objects.filter(provider_service_id=str(svc['service'])).first()
            if existing:
                skipped += 1
                continue

            # Create service - store provider_price and let markup calculate user price
            from decimal import Decimal
            provider_rate = Decimal(str(svc['rate']))
            markup = Decimal('50')  # 50% default markup
            user_price = provider_rate * (Decimal('1') + markup / Decimal('100'))
            
            Service.objects.create(
                platform=platform,
                category=category,
                name=svc['name'],
                provider_price=provider_rate,
                markup_percentage=markup,
                price_per_1000=user_price,
                min_quantity=int(svc['min']),
                max_quantity=int(svc['max']),
                average_time='0-24 hours',
                provider_service_id=str(svc['service']),
                is_active=True,
            )
            imported += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported {imported} services, skipped {skipped}"
        ))
