"""
Script to add sample email accounts to the market
Run: python add_email_accounts.py
"""
from social.models import SocialAccountListing
from django.contrib.auth.models import User

# Get admin user
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    print("❌ No admin user found! Create one first with: python manage.py createsuperuser")
    exit(1)

print(f"✅ Adding accounts as: {admin.username}")

# Gmail Accounts
gmail_accounts = [
    {
        "title": "USA Gmail Account | Fresh | Recovery Email Included",
        "description": "✅ Fresh Gmail account created in USA\n✅ Recovery email included\n✅ Full access - email + password + recovery\n✅ Never used for marketing\n✅ Perfect for business or personal use\n\nFormat: email:password:recovery_email:recovery_pass",
        "price": 3000,
        "countries": "United States"
    },
    {
        "title": "UK Gmail Account | Phone Verified | Ready to Use",
        "description": "✅ UK Gmail account with phone verification\n✅ Clean history, never flagged\n✅ Includes recovery options\n✅ Instant delivery after payment\n\nFormat: email:password:phone_number:recovery_email",
        "price": 3500,
        "countries": "United Kingdom"
    },
    {
        "title": "Canada Gmail | Aged 2023 | High Trust Score",
        "description": "✅ Aged Gmail from 2023\n✅ High trust score, established history\n✅ Phone + recovery email verified\n✅ Perfect for Google Ads, YouTube\n\nFormat: email:password:phone:recovery:2fa_backup_codes",
        "price": 4500,
        "countries": "Canada"
    },
]

for acc in gmail_accounts:
    SocialAccountListing.objects.create(
        platform="gmail",
        title=acc["title"],
        description=acc["description"],
        price_ngn=acc["price"],
        countries=acc["countries"],
        account_url="https://mail.google.com",  # Generic URL for email accounts
        created_by=admin
    )
print(f"✅ Added {len(gmail_accounts)} Gmail accounts")

# Outlook Accounts
outlook_accounts = [
    {
        "title": "USA Outlook Account | 2024 | Phone Verified",
        "description": "✅ Fresh USA Outlook/Hotmail account\n✅ Phone verified for security\n✅ Full Microsoft account access\n✅ Works with OneDrive, Office 365\n\nFormat: email:password:phone:recovery_email",
        "price": 3000,
        "countries": "United States"
    },
    {
        "title": "UK Outlook | Business Ready | 2FA Enabled",
        "description": "✅ UK Outlook with 2FA setup\n✅ Business-ready account\n✅ High security, trusted sender\n✅ OneDrive 5GB storage included\n\nFormat: email:password:2fa_backup_codes:recovery",
        "price": 4000,
        "countries": "United Kingdom"
    },
]

for acc in outlook_accounts:
    SocialAccountListing.objects.create(
        platform="outlook",
        title=acc["title"],
        description=acc["description"],
        price_ngn=acc["price"],
        countries=acc["countries"],
        account_url="https://outlook.live.com",
        created_by=admin
    )
print(f"✅ Added {len(outlook_accounts)} Outlook accounts")

# Yahoo Accounts
yahoo_accounts = [
    {
        "title": "Global Yahoo Mail | Phone Verified | Clean",
        "description": "✅ Yahoo Mail account with phone verification\n✅ Clean inbox, no spam history\n✅ Recovery options configured\n✅ Good for newsletters, signups\n\nFormat: email:password:phone:security_questions",
        "price": 2500,
        "countries": "Global"
    },
]

for acc in yahoo_accounts:
    SocialAccountListing.objects.create(
        platform="yahoo",
        title=acc["title"],
        description=acc["description"],
        price_ngn=acc["price"],
        countries=acc["countries"],
        account_url="https://mail.yahoo.com",
        created_by=admin
    )
print(f"✅ Added {len(yahoo_accounts)} Yahoo accounts")

# ProtonMail (Secure Email)
proton_accounts = [
    {
        "title": "ProtonMail Secure | Switzerland | Encrypted",
        "description": "🔒 End-to-end encrypted ProtonMail account\n✅ Based in Switzerland (privacy laws)\n✅ No phone number required\n✅ Anonymous registration\n✅ Perfect for privacy-conscious users\n\nFormat: email:password:recovery_phrase",
        "price": 5000,
        "countries": "Switzerland"
    },
]

for acc in proton_accounts:
    SocialAccountListing.objects.create(
        platform="protonmail",
        title=acc["title"],
        description=acc["description"],
        price_ngn=acc["price"],
        countries=acc["countries"],
        account_url="https://proton.me",
        created_by=admin
    )
print(f"✅ Added {len(proton_accounts)} ProtonMail accounts")

total = len(gmail_accounts) + len(outlook_accounts) + len(yahoo_accounts) + len(proton_accounts)
print(f"\n🎉 Total email accounts added: {total}")
print("📊 Breakdown:")
print(f"   Gmail: {len(gmail_accounts)}")
print(f"   Outlook: {len(outlook_accounts)}")
print(f"   Yahoo: {len(yahoo_accounts)}")
print(f"   ProtonMail: {len(proton_accounts)}")
print("\n✅ Done! Check your Accounts Market to see them.")
