from social.models import SocialAccountListing
from django.contrib.auth.models import User
admin = User.objects.filter(is_superuser=True).first()

# Singapore FB - 5500 each
sg_fb = [
    "https://www.facebook.com/61587624062964",
    "https://www.facebook.com/61580848187561",
    "https://www.facebook.com/61585057673582",
    "https://www.facebook.com/61585014141014",
    "https://www.facebook.com/61586391088916",
    "https://www.facebook.com/61585020440344",
    "https://www.facebook.com/61586553632474",
    "https://www.facebook.com/61587606814915",
    "https://www.facebook.com/61557500595201",
    "https://www.facebook.com/61588053280068",
    "https://www.facebook.com/61587734406235",
    "https://www.facebook.com/61587284793529",
]
for url in sg_fb:
    SocialAccountListing.objects.create(
        platform="facebook",
        title="SINGAPORE FB | (0-50 friends) (2025)",
        description="(user-pass-2fa-mail-pass-cookies) Most has marketplace - amazing features. Allow account to soak for some hours on your device before use.",
        price_ngn=5500,
        countries="Singapore",
        account_url=url,
        created_by=admin
    )
print(f"Added {len(sg_fb)} SG FB accounts")
