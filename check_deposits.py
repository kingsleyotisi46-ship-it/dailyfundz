import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from django.contrib.auth.models import User
from social.models import Deposit, Wallet
from decimal import Decimal

# Find user by email (partial match)
email_search = 'chinereywau'
users = User.objects.filter(email__icontains=email_search)
print(f'Searching for users with email containing: {email_search}')
print(f'Users found: {list(users.values_list("id", "username", "email"))}')

# Show all pending deposits
print('\n--- All Pending Deposits ---')
pending = Deposit.objects.filter(status='pending')
for d in pending:
    print(f'ID: {d.id} | {d.user.username} ({d.user.email}) | {d.currency} {d.amount}')

# Find deposit with 1550
print('\n--- Looking for deposit of 1550 ---')
target_deposits = Deposit.objects.filter(amount=Decimal('1550'), status='pending')
for d in target_deposits:
    print(f'Found: ID {d.id} for {d.user.username}')

# If you want to approve a specific deposit, uncomment below:
# deposit_id = 123  # Change this to actual ID
# deposit = Deposit.objects.get(id=deposit_id)
# admin = User.objects.get(username='admin')
# deposit.approve(admin, 'Approved by admin')
# print(f'Deposit {deposit_id} approved!')
