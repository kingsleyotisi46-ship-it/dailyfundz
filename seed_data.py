import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from social.models import Platform, ServiceCategory, Service

# Create Platforms
platforms_data = [
    {'name': 'Instagram', 'icon': '📸', 'slug': 'instagram', 'order': 1},
    {'name': 'TikTok', 'icon': '🎵', 'slug': 'tiktok', 'order': 2},
    {'name': 'YouTube', 'icon': '▶️', 'slug': 'youtube', 'order': 3},
    {'name': 'Twitter/X', 'icon': '🐦', 'slug': 'twitter', 'order': 4},
    {'name': 'Facebook', 'icon': '👤', 'slug': 'facebook', 'order': 5},
]

# Create Categories
categories_data = [
    {'name': 'Followers', 'slug': 'followers', 'description': 'Increase your follower count', 'order': 1},
    {'name': 'Likes', 'slug': 'likes', 'description': 'Get more likes on your content', 'order': 2},
    {'name': 'Views', 'slug': 'views', 'description': 'Boost your video/story views', 'order': 3},
    {'name': 'Comments', 'slug': 'comments', 'description': 'Get real comments on your posts', 'order': 4},
    {'name': 'Shares', 'slug': 'shares', 'description': 'Increase shares and reposts', 'order': 5},
]

print("Creating platforms...")
platforms = {}
for p in platforms_data:
    platform, created = Platform.objects.get_or_create(slug=p['slug'], defaults=p)
    platforms[p['slug']] = platform
    print(f"  {'Created' if created else 'Exists'}: {platform.name}")

print("\nCreating categories...")
categories = {}
for c in categories_data:
    category, created = ServiceCategory.objects.get_or_create(slug=c['slug'], defaults=c)
    categories[c['slug']] = category
    print(f"  {'Created' if created else 'Exists'}: {category.name}")

# Create Services
services_data = [
    # Instagram Services
    {'platform': 'instagram', 'category': 'followers', 'name': 'Instagram Followers [Standard]', 'price_per_1000': 2.50, 'min_quantity': 100, 'max_quantity': 50000, 'average_time': '0-6 hours', 'quality': 'standard'},
    {'platform': 'instagram', 'category': 'followers', 'name': 'Instagram Followers [High Quality]', 'price_per_1000': 4.00, 'min_quantity': 100, 'max_quantity': 25000, 'average_time': '0-12 hours', 'quality': 'high', 'is_featured': True},
    {'platform': 'instagram', 'category': 'followers', 'name': 'Instagram Followers [Real & Active]', 'price_per_1000': 8.00, 'min_quantity': 50, 'max_quantity': 10000, 'average_time': '1-3 days', 'quality': 'real', 'is_featured': True},
    {'platform': 'instagram', 'category': 'likes', 'name': 'Instagram Likes [Fast]', 'price_per_1000': 1.50, 'min_quantity': 50, 'max_quantity': 50000, 'average_time': '0-1 hour', 'quality': 'standard'},
    {'platform': 'instagram', 'category': 'likes', 'name': 'Instagram Likes [Premium]', 'price_per_1000': 3.00, 'min_quantity': 50, 'max_quantity': 20000, 'average_time': '0-6 hours', 'quality': 'premium'},
    {'platform': 'instagram', 'category': 'views', 'name': 'Instagram Reels Views', 'price_per_1000': 0.80, 'min_quantity': 500, 'max_quantity': 1000000, 'average_time': '0-1 hour', 'quality': 'standard'},
    {'platform': 'instagram', 'category': 'views', 'name': 'Instagram Story Views', 'price_per_1000': 1.00, 'min_quantity': 100, 'max_quantity': 50000, 'average_time': '0-30 min', 'quality': 'standard'},
    {'platform': 'instagram', 'category': 'comments', 'name': 'Instagram Custom Comments', 'price_per_1000': 25.00, 'min_quantity': 5, 'max_quantity': 1000, 'average_time': '1-24 hours', 'quality': 'real'},

    # TikTok Services
    {'platform': 'tiktok', 'category': 'followers', 'name': 'TikTok Followers [Standard]', 'price_per_1000': 3.00, 'min_quantity': 100, 'max_quantity': 100000, 'average_time': '0-12 hours', 'quality': 'standard'},
    {'platform': 'tiktok', 'category': 'followers', 'name': 'TikTok Followers [High Quality]', 'price_per_1000': 5.50, 'min_quantity': 100, 'max_quantity': 50000, 'average_time': '0-24 hours', 'quality': 'high', 'is_featured': True},
    {'platform': 'tiktok', 'category': 'likes', 'name': 'TikTok Likes [Fast]', 'price_per_1000': 1.80, 'min_quantity': 50, 'max_quantity': 100000, 'average_time': '0-1 hour', 'quality': 'standard'},
    {'platform': 'tiktok', 'category': 'views', 'name': 'TikTok Video Views', 'price_per_1000': 0.50, 'min_quantity': 1000, 'max_quantity': 10000000, 'average_time': '0-1 hour', 'quality': 'standard', 'is_featured': True},
    {'platform': 'tiktok', 'category': 'shares', 'name': 'TikTok Shares', 'price_per_1000': 5.00, 'min_quantity': 100, 'max_quantity': 50000, 'average_time': '0-6 hours', 'quality': 'standard'},

    # YouTube Services
    {'platform': 'youtube', 'category': 'followers', 'name': 'YouTube Subscribers [Standard]', 'price_per_1000': 15.00, 'min_quantity': 50, 'max_quantity': 10000, 'average_time': '1-7 days', 'quality': 'standard'},
    {'platform': 'youtube', 'category': 'followers', 'name': 'YouTube Subscribers [Real]', 'price_per_1000': 35.00, 'min_quantity': 50, 'max_quantity': 5000, 'average_time': '3-15 days', 'quality': 'real', 'is_featured': True},
    {'platform': 'youtube', 'category': 'views', 'name': 'YouTube Views [Fast]', 'price_per_1000': 2.00, 'min_quantity': 500, 'max_quantity': 1000000, 'average_time': '0-24 hours', 'quality': 'standard'},
    {'platform': 'youtube', 'category': 'views', 'name': 'YouTube Views [High Retention]', 'price_per_1000': 8.00, 'min_quantity': 500, 'max_quantity': 100000, 'average_time': '1-3 days', 'quality': 'premium'},
    {'platform': 'youtube', 'category': 'likes', 'name': 'YouTube Likes', 'price_per_1000': 12.00, 'min_quantity': 50, 'max_quantity': 50000, 'average_time': '0-24 hours', 'quality': 'standard'},
    {'platform': 'youtube', 'category': 'comments', 'name': 'YouTube Custom Comments', 'price_per_1000': 50.00, 'min_quantity': 5, 'max_quantity': 500, 'average_time': '1-3 days', 'quality': 'real'},

    # Twitter/X Services
    {'platform': 'twitter', 'category': 'followers', 'name': 'Twitter Followers [Standard]', 'price_per_1000': 5.00, 'min_quantity': 100, 'max_quantity': 50000, 'average_time': '0-24 hours', 'quality': 'standard'},
    {'platform': 'twitter', 'category': 'followers', 'name': 'Twitter Followers [High Quality]', 'price_per_1000': 10.00, 'min_quantity': 100, 'max_quantity': 20000, 'average_time': '1-3 days', 'quality': 'high'},
    {'platform': 'twitter', 'category': 'likes', 'name': 'Twitter Likes', 'price_per_1000': 3.00, 'min_quantity': 50, 'max_quantity': 50000, 'average_time': '0-6 hours', 'quality': 'standard'},
    {'platform': 'twitter', 'category': 'shares', 'name': 'Twitter Retweets', 'price_per_1000': 4.00, 'min_quantity': 50, 'max_quantity': 50000, 'average_time': '0-12 hours', 'quality': 'standard'},
    {'platform': 'twitter', 'category': 'views', 'name': 'Twitter Video Views', 'price_per_1000': 1.00, 'min_quantity': 500, 'max_quantity': 1000000, 'average_time': '0-1 hour', 'quality': 'standard'},

    # Facebook Services
    {'platform': 'facebook', 'category': 'followers', 'name': 'Facebook Page Followers', 'price_per_1000': 6.00, 'min_quantity': 100, 'max_quantity': 50000, 'average_time': '0-24 hours', 'quality': 'standard'},
    {'platform': 'facebook', 'category': 'likes', 'name': 'Facebook Post Likes', 'price_per_1000': 2.50, 'min_quantity': 50, 'max_quantity': 50000, 'average_time': '0-6 hours', 'quality': 'standard'},
    {'platform': 'facebook', 'category': 'views', 'name': 'Facebook Video Views', 'price_per_1000': 1.00, 'min_quantity': 500, 'max_quantity': 1000000, 'average_time': '0-6 hours', 'quality': 'standard'},
    {'platform': 'facebook', 'category': 'shares', 'name': 'Facebook Post Shares', 'price_per_1000': 8.00, 'min_quantity': 50, 'max_quantity': 10000, 'average_time': '1-24 hours', 'quality': 'standard'},
]

print("\nCreating services...")
for s in services_data:
    platform = platforms[s.pop('platform')]
    category = categories[s.pop('category')]
    service, created = Service.objects.get_or_create(
        platform=platform,
        category=category,
        name=s['name'],
        defaults=s
    )
    print(f"  {'Created' if created else 'Exists'}: {service.name}")

print("\n✅ Seed data created successfully!")
print(f"   Platforms: {Platform.objects.count()}")
print(f"   Categories: {ServiceCategory.objects.count()}")
print(f"   Services: {Service.objects.count()}")
