"""
Direct test of services page rendering
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from social.template_views import services

print("Testing services view rendering...")
print()

# Create a test client
client = Client()

# Get a user
user = User.objects.first()
if not user:
    print("❌ No user found. Create one first.")
    exit(1)

# Login
client.force_login(user)

# Request services page
print(f"✅ Logged in as: {user.username}")
print(f"📄 Requesting /services/ page...")
response = client.get('/services/')

print(f"📊 Status Code: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    
    # Check for key elements
    print("\n🔍 Checking rendered content:")
    print(f"  - Contains 'service-card': {content.count('service-card')} times")
    print(f"  - Contains 'empty-state': {'empty-state' in content}")
    print("  - Contains unresolved Django tags: {}".format('{%' in content))
    print(f"  - Page size: {len(content):,} bytes")
    
    # Check if services are in context
    if hasattr(response, 'context') and response.context:
        services_in_context = response.context.get('services')
        if services_in_context:
            if hasattr(services_in_context, 'count'):
                service_count = services_in_context.count()
            else:
                service_count = len(list(services_in_context))
            print(f"\n✅ Services in context: {service_count}")
        else:
            print(f"\n❌ No 'services' in context!")
            print(f"   Context keys: {list(response.context.keys())}")
    
    # Save a sample for inspection
    with open('services_page_output.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n💾 Full HTML saved to: services_page_output.html")
    
    # Extract first 500 chars of services grid section
    if 'services-grid' in content:
        grid_start = content.find('services-grid')
        grid_section = content[grid_start:grid_start+1000]
        print(f"\n📋 Services Grid Section Preview:")
        print(grid_section)

else:
    print(f"❌ Error: Got status {response.status_code}")
    print(response.content.decode('utf-8')[:500])
