#!/usr/bin/env python
"""
Approve pending deposit for chinereywauzoma@gmail.com - ₦1,550
Run on Render Shell: python approve_deposit.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from django.contrib.auth.models import User
from social.models import Deposit, Wallet
from decimal import Decimal

print("="*60)
print("DEPOSIT APPROVAL SCRIPT")
print("="*60)

# Find user by email
email = 'chinereywauzoma'
users = User.objects.filter(email__icontains=email)
print(f'\nSearching for: {email}')
print(f'Users found: {list(users.values_list("id", "username", "email"))}')

# Show all pending deposits
print('\n--- All Pending Deposits ---')
pending = Deposit.objects.filter(status='pending')
if not pending.exists():
    print('No pending deposits found!')
else:
    for d in pending:
        print(f'  ID: {d.id} | User: {d.user.username} | Email: {d.user.email} | Amount: ₦{d.amount}')

# Find and approve the 1550 deposit
print('\n--- Approving ₦1,550 Deposit ---')
target = Deposit.objects.filter(amount=Decimal('1550'), status='pending').first()

if not target:
    # Try broader search
    target = Deposit.objects.filter(status='pending', user__email__icontains=email).first()

if target:
    print(f'Found deposit ID: {target.id}')
    print(f'  User: {target.user.username} ({target.user.email})')
    print(f'  Amount: {target.currency} {target.amount}')
    
    # Get admin user
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        admin = User.objects.get(username='admin')
    
    # Approve it
    result = target.approve(admin, 'Payment verified and approved')
    
    if result:
        print(f'\n✅ SUCCESS! Deposit #{target.id} approved!')
        wallet = Wallet.objects.get(user=target.user)
        print(f'   New wallet balance: ₦{wallet.balance_ngn}')
    else:
        print(f'\n❌ Failed to approve (may already be processed)')
else:
    print('No matching pending deposit found!')
    print('\nTo manually add ₦1,550 to a wallet, use:')
    print('  wallet = Wallet.objects.get(user__email__icontains="chinereywau")')
    print('  wallet.add_funds(Decimal("1550"), "NGN")')
    print('  wallet.save()')

print("\n" + "="*60)
