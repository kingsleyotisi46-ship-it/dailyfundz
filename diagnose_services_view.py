"""
Manual diagnostic for the services page.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from social.models import Service, Platform, ServiceCategory, Wallet
from django.contrib.auth.models import User

print("=" * 60)
print("SERVICES DISPLAY DIAGNOSTIC")
print("=" * 60)

# Check if user exists
user = User.objects.first()
if not user:
    print("❌ No users found in database!")
    print("   Create a user first with: python manage.py createsuperuser")
else:
    print(f"✅ Testing with user: {user.username}")

print("\n" + "=" * 60)
print("DATABASE COUNTS")
print("=" * 60)
print(f"Total Services: {Service.objects.count()}")
print(f"Active Services: {Service.objects.filter(is_active=True).count()}")
print(f"Active Platforms: {Platform.objects.filter(is_active=True).count()}")
print(f"Service Categories: {ServiceCategory.objects.count()}")

print("\n" + "=" * 60)
print("PLATFORM DETAILS")
print("=" * 60)
platforms = Platform.objects.filter(is_active=True)
for p in platforms:
    service_count = p.services.filter(is_active=True).count()
    print(f"{p.icon} {p.name:15} | Slug: {p.slug:15} | Services: {service_count:4}")

print("\n" + "=" * 60)
print("CATEGORY DETAILS (First 10)")
print("=" * 60)
categories = ServiceCategory.objects.all()[:10]
for c in categories:
    service_count = c.services.filter(is_active=True).count()
    slug = getattr(c, 'slug', 'NO SLUG!')
    print(f"{c.name:20} | Slug: {slug:20} | Services: {service_count:4}")

print("\n" + "=" * 60)
print("SAMPLE SERVICES (First 5)")
print("=" * 60)
services = Service.objects.filter(is_active=True)[:5]
for s in services:
    print(f"ID: {s.id:5} | {s.name[:50]:50}")
    print(f"       Platform: {s.platform.name} | Category: {s.category.name}")
    print(f"       Price: ${s.price_per_1000} | Provider: ${s.provider_price}")
    print(f"       Markup: {s.markup_percentage}%")
    print()

print("=" * 60)
print("SIMULATING VIEW QUERY")
print("=" * 60)
services_qs = Service.objects.filter(is_active=True).select_related('platform', 'category')
print(f"Query returned {services_qs.count()} services")

# Add NGN price
exchange_rate = Wallet.EXCHANGE_RATE
print(f"Exchange rate: {exchange_rate}")

# Check if query can iterate
print("\nIterating first 3 services:")
for service in services_qs[:3]:
    service.price_ngn = service.price_per_1000 * exchange_rate
    print(f"  - {service.name[:40]}")
    print(f"    Price: ${service.price_per_1000} = ₦{service.price_ngn:.2f}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
print("\nIf all checks pass above, the issue is likely:")
print("1. Login required - make sure you're logged in")
print("2. Browser cache - clear cache and hard refresh")
print("3. Static files - run: python manage.py collectstatic")
print("4. Template syntax error - check browser console for JS errors")
