"""
Management command to sync services from JustAnotherPanel (JAP) API
Run with: python manage.py sync_services --markup 100
"""
import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from social.models import Service, Platform, ServiceCategory


class Command(BaseCommand):
    help = 'Sync services from JustAnotherPanel API with real prices'

    PLATFORM_KEYWORDS = {
        'instagram': ['instagram', 'insta ', 'ig '],
        'tiktok': ['tiktok', 'tik tok', 'tik-tok'],
        'youtube': ['youtube', 'yt ', 'youtuber'],
        'twitter': ['twitter', 'tweet', ' x '],
        'facebook': ['facebook', 'fb '],
        'telegram': ['telegram', 'tg '],
        'spotify': ['spotify'],
        'threads': ['threads'],
    }

    CATEGORY_KEYWORDS = {
        'followers': ['follower', 'subscriber', 'fan', 'member'],
        'likes': ['like', 'heart', 'reaction', 'upvote'],
        'views': ['view', 'watch', 'play', 'impression'],
        'comments': ['comment', 'reply'],
        'shares': ['share', 'retweet', 'repost', 'forward'],
    }

    def add_arguments(self, parser):
        parser.add_argument('--markup', type=float, default=100, help='Markup percentage (100 = 100%% = 2x price)')
        parser.add_argument('--limit', type=int, default=200, help='Max services to import per platform')
        parser.add_argument('--min-price', type=float, default=0.001, help='Min provider price to import')
        parser.add_argument('--clear', action='store_true', help='Clear existing services before import')

    def detect_platform(self, name):
        name_lower = name.lower()
        for slug, keywords in self.PLATFORM_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower:
                    return slug
        return None

    def detect_category(self, name):
        name_lower = name.lower()
        for slug, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower:
                    return slug
        return None
    
    def detect_quality(self, name):
        name_lower = name.lower()
        if 'real' in name_lower or 'active' in name_lower:
            return 'real'
        if 'premium' in name_lower or 'hq' in name_lower or 'high quality' in name_lower:
            return 'premium'
        if 'high' in name_lower:
            return 'high'
        return 'standard'

    def handle(self, *args, **options):
        api_url = getattr(settings, 'SMM_PROVIDER_URL', None)
        api_key = getattr(settings, 'SMM_PROVIDER_KEY', None)

        if not api_url or not api_key:
            self.stderr.write(self.style.ERROR('Missing SMM_PROVIDER_URL or SMM_PROVIDER_KEY in settings'))
            return

        self.stdout.write(f'Fetching services from {api_url}...')

        try:
            response = requests.post(api_url, data={'key': api_key, 'action': 'services'}, timeout=60)
            services_data = response.json()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'API error: {e}'))
            return

        if isinstance(services_data, dict) and 'error' in services_data:
            self.stderr.write(self.style.ERROR(f"API error: {services_data['error']}"))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(services_data)} services from provider'))

        # Ensure platforms exist
        platforms_data = [
            {'name': 'Instagram', 'icon': '📸', 'slug': 'instagram', 'order': 1},
            {'name': 'TikTok', 'icon': '🎵', 'slug': 'tiktok', 'order': 2},
            {'name': 'YouTube', 'icon': '▶️', 'slug': 'youtube', 'order': 3},
            {'name': 'Twitter/X', 'icon': '🐦', 'slug': 'twitter', 'order': 4},
            {'name': 'Facebook', 'icon': '👤', 'slug': 'facebook', 'order': 5},
            {'name': 'Telegram', 'icon': '✈️', 'slug': 'telegram', 'order': 6},
            {'name': 'Spotify', 'icon': '🎧', 'slug': 'spotify', 'order': 7},
            {'name': 'Threads', 'icon': '🧵', 'slug': 'threads', 'order': 8},
        ]
        for p in platforms_data:
            Platform.objects.get_or_create(slug=p['slug'], defaults=p)

        # Ensure categories exist
        categories_data = [
            {'name': 'Followers', 'slug': 'followers', 'order': 1},
            {'name': 'Likes', 'slug': 'likes', 'order': 2},
            {'name': 'Views', 'slug': 'views', 'order': 3},
            {'name': 'Comments', 'slug': 'comments', 'order': 4},
            {'name': 'Shares', 'slug': 'shares', 'order': 5},
        ]
        for c in categories_data:
            ServiceCategory.objects.get_or_create(slug=c['slug'], defaults=c)

        if options['clear']:
            deleted = Service.objects.all().delete()[0]
            self.stdout.write(f'Cleared {deleted} existing services')

        markup_percentage = Decimal(str(options['markup']))
        min_price = Decimal(str(options['min_price']))
        limit_per_platform = options['limit']
        
        # Track imports per platform
        platform_counts = {slug: 0 for slug in self.PLATFORM_KEYWORDS.keys()}
        imported = 0
        skipped = 0

        # Sort by price to get cheapest services first
        sorted_services = sorted(services_data, key=lambda x: float(x.get('rate', 999999)))

        for svc in sorted_services:
            service_id = str(svc.get('service', ''))
            name = svc.get('name', '')
            rate = Decimal(str(svc.get('rate', 0)))
            min_qty = int(svc.get('min', 100))
            max_qty = int(svc.get('max', 10000))

            # Skip if price too low (likely broken service)
            if rate < min_price:
                skipped += 1
                continue

            platform_slug = self.detect_platform(name)
            category_slug = self.detect_category(name)

            if not platform_slug or not category_slug:
                skipped += 1
                continue
            
            # Check platform limit
            if platform_counts[platform_slug] >= limit_per_platform:
                continue

            try:
                platform = Platform.objects.get(slug=platform_slug)
                category = ServiceCategory.objects.get(slug=category_slug)
            except (Platform.DoesNotExist, ServiceCategory.DoesNotExist):
                skipped += 1
                continue

            quality = self.detect_quality(name)
            
            # Create or update service
            service, created = Service.objects.update_or_create(
                provider_service_id=service_id,
                defaults={
                    'platform': platform,
                    'category': category,
                    'name': name[:200],
                    'provider_price': rate,
                    'markup_percentage': markup_percentage,
                    'price_per_1000': rate * (1 + markup_percentage / 100),  # Will be recalculated on save
                    'min_quantity': min_qty,
                    'max_quantity': max_qty,
                    'average_time': '0-24 hours',
                    'quality': quality,
                    'is_active': True,
                }
            )
            
            platform_counts[platform_slug] += 1
            imported += 1
            
            user_price = service.price_per_1000
            status = '✓ New' if created else '↻ Updated'
            self.stdout.write(f'  {status}: {platform_slug[:4]} | ${rate:.4f} → ${user_price:.4f}/1K | {name[:45]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'═══ IMPORT COMPLETE ═══'))
        self.stdout.write(f'  Imported: {imported} services')
        self.stdout.write(f'  Skipped: {skipped} services')
        self.stdout.write(f'  Markup: {markup_percentage}%')
        self.stdout.write('')
        self.stdout.write('  Per platform:')
        for slug, count in platform_counts.items():
            if count > 0:
                self.stdout.write(f'    {slug}: {count}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Admin can now adjust markup % per service in admin panel!'))
