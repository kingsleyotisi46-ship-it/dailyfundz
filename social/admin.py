from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from .models import (
    Profile, Post, Comment, Message, Report,
    Wallet, Transaction, Platform, ServiceCategory, Service, Order, Deposit,
    VirtualNumberOrder, Referral, ReferralEarning, SupportTicket, TicketMessage,
    SiteSettings, SocialAccountListing, SocialAccountPurchase
)
from .emails import (
    send_deposit_approved_email, send_deposit_rejected_email,
    send_order_completed_email, send_referral_earning_email
)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class WalletInline(admin.StackedInline):
    model = Wallet
    can_delete = False
    verbose_name_plural = 'Wallet'
    fields = ['balance_usd', 'balance_ngn', 'preferred_currency', 'total_spent_usd', 'total_spent_ngn']
    readonly_fields = ['total_spent_usd', 'total_spent_ngn']
    extra = 0
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline, WalletInline]
    list_display = ['username', 'email', 'get_wallet_balance', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    
    def get_wallet_balance(self, obj):
        try:
            wallet = Wallet.objects.filter(user=obj).first()
            if wallet:
                return format_html(
                    '<span style="color: green; font-weight: bold;">₦{:.2f}</span>',
                    wallet.balance_ngn
                )
            return format_html('<span style="color: gray;">No wallet</span>')
        except Exception:
            return format_html('<span style="color: red;">Error</span>')
    get_wallet_balance.short_description = 'Wallet Balance'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_followers_count', 'created_at']
    search_fields = ['user__username', 'bio']
    readonly_fields = ['created_at']

    def get_followers_count(self, obj):
        return obj.followers.count()
    get_followers_count.short_description = 'Followers'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'short_content', 'get_likes_count', 'get_comments_count', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'

    def get_likes_count(self, obj):
        return obj.likes.count()
    get_likes_count.short_description = 'Likes'

    def get_comments_count(self, obj):
        return obj.comments.count()
    get_comments_count.short_description = 'Comments'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'short_content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at']

    def short_content(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    short_content.short_description = 'Content'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'receiver__username']
    readonly_fields = ['created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'report_type', 'reported_user', 'reported_post', 'status', 'created_at']
    list_filter = ['status', 'report_type', 'created_at']
    search_fields = ['description', 'reporter__username', 'reported_user__username']
    readonly_fields = ['created_at']
    actions = ['mark_reviewed', 'mark_resolved', 'mark_dismissed']

    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
    mark_reviewed.short_description = 'Mark selected reports as reviewed'

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
    mark_resolved.short_description = 'Mark selected reports as resolved'

    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
    mark_dismissed.short_description = 'Mark selected reports as dismissed'


admin.site.site_header = 'DAILYFUNDZBOOST Admin'
admin.site.site_title = 'DAILYFUNDZBOOST'
admin.site.index_title = 'Social Media Management'


# ============== SMM PANEL ADMIN ==============

# Add custom admin view for provider status
from django.urls import path
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def provider_status_view(request):
    from .smm_provider import smm_provider
    if not smm_provider.is_configured():
        return JsonResponse({'error': 'Provider not configured'})
    result = smm_provider.get_balance()
    return JsonResponse(result)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance_usd_colored', 'balance_ngn_colored', 'preferred_currency', 'total_spent_usd', 'total_spent_ngn', 'created_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['preferred_currency', 'created_at']
    readonly_fields = ['total_spent_usd', 'total_spent_ngn', 'created_at', 'updated_at']
    actions = ['add_bonus_usd', 'add_bonus_ngn', 'add_500_ngn', 'add_1000_ngn', 'add_1500_ngn', 'add_2000_ngn', 'add_2500_ngn', 'add_3000_ngn', 'add_4000_ngn', 'add_5000_ngn', 'add_10000_ngn']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Balance (Editable)', {
            'fields': ('balance_usd', 'balance_ngn'),
            'description': 'You can directly edit these balances. Changes will create admin adjustment transactions.'
        }),
        ('Settings', {
            'fields': ('preferred_currency',)
        }),
        ('Statistics (Read-only)', {
            'fields': ('total_spent_usd', 'total_spent_ngn', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def balance_usd_colored(self, obj):
        color = 'green' if obj.balance_usd > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:.2f}</span>',
            color, obj.balance_usd
        )
    balance_usd_colored.short_description = 'Balance USD'
    
    def balance_ngn_colored(self, obj):
        color = 'green' if obj.balance_ngn > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">₦{:.2f}</span>',
            color, obj.balance_ngn
        )
    balance_ngn_colored.short_description = 'Balance NGN'
    
    def save_model(self, request, obj, form, change):
        """Track when admin manually changes balance"""
        if change:
            # Get original balance
            original = Wallet.objects.get(pk=obj.pk)
            usd_diff = obj.balance_usd - original.balance_usd
            ngn_diff = obj.balance_ngn - original.balance_ngn
            
            # Create transaction for balance changes
            if usd_diff != 0:
                Transaction.objects.create(
                    wallet=obj,
                    transaction_type='adjustment',
                    amount=abs(usd_diff),
                    currency='USD',
                    description=f'Admin manual adjustment by {request.user.username} ({"+" if usd_diff > 0 else "-"}${abs(usd_diff):.2f})'
                )
            
            if ngn_diff != 0:
                Transaction.objects.create(
                    wallet=obj,
                    transaction_type='adjustment',
                    amount=abs(ngn_diff),
                    currency='NGN',
                    description=f'Admin manual adjustment by {request.user.username} ({"+" if ngn_diff > 0 else "-"}₦{abs(ngn_diff):.2f})'
                )
        
        super().save_model(request, obj, form, change)

    def add_bonus_usd(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(10, 'USD')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=10,
                currency='USD',
                description=f'Admin bonus by {request.user.username} ($10 USD)'
            )
        self.message_user(request, f'Added $10 USD bonus to {queryset.count()} wallet(s)')
    add_bonus_usd.short_description = '💰 Add $10 USD bonus'

    def add_bonus_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(5000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=5000,
                currency='NGN',
                description=f'Admin bonus by {request.user.username} (₦5,000 NGN)'
            )
        self.message_user(request, f'Added ₦5,000 NGN bonus to {queryset.count()} wallet(s)')
    add_bonus_ngn.short_description = '💰 Add ₦5,000 NGN bonus'
    
    def add_500_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(500, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=500,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦500)'
            )
        self.message_user(request, f'Added ₦500 to {queryset.count()} wallet(s)')
    add_500_ngn.short_description = '➕ Add ₦500'
    
    def add_1000_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(1000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=1000,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦1,000)'
            )
        self.message_user(request, f'Added ₦1,000 to {queryset.count()} wallet(s)')
    add_1000_ngn.short_description = '➕ Add ₦1,000'
    
    def add_1500_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(1500, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=1500,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦1,500)'
            )
        self.message_user(request, f'Added ₦1,500 to {queryset.count()} wallet(s)')
    add_1500_ngn.short_description = '➕ Add ₦1,500'
    
    def add_2000_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(2000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=2000,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦2,000)'
            )
        self.message_user(request, f'Added ₦2,000 to {queryset.count()} wallet(s)')
    add_2000_ngn.short_description = '➕ Add ₦2,000'
    
    def add_2500_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(2500, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=2500,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦2,500)'
            )
        self.message_user(request, f'Added ₦2,500 to {queryset.count()} wallet(s)')
    add_2500_ngn.short_description = '➕ Add ₦2,500'
    
    def add_3000_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(3000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=3000,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦3,000)'
            )
        self.message_user(request, f'Added ₦3,000 to {queryset.count()} wallet(s)')
    add_3000_ngn.short_description = '➕ Add ₦3,000'
    
    def add_4000_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(4000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=4000,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦4,000)'
            )
        self.message_user(request, f'Added ₦4,000 to {queryset.count()} wallet(s)')
    add_4000_ngn.short_description = '➕ Add ₦4,000'
    
    def add_5000_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(5000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=5000,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦5,000)'
            )
        self.message_user(request, f'Added ₦5,000 to {queryset.count()} wallet(s)')
    add_5000_ngn.short_description = '➕ Add ₦5,000'
    
    def add_10000_ngn(self, request, queryset):
        for wallet in queryset:
            wallet.add_funds(10000, 'NGN')
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bonus',
                amount=10000,
                currency='NGN',
                description=f'Admin top-up by {request.user.username} (₦10,000)'
            )
        self.message_user(request, f'Added ₦10,000 to {queryset.count()} wallet(s)')
    add_10000_ngn.short_description = '➕ Add ₦10,000'


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'formatted_amount', 'status', 'screenshot_preview', 'created_at', 'reviewed_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email', 'admin_note']
    readonly_fields = ['user', 'amount', 'currency', 'payment_screenshot', 'screenshot_preview_large', 'created_at', 'reviewed_at', 'reviewed_by']
    date_hierarchy = 'created_at'
    actions = ['approve_deposits', 'reject_deposits']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Deposit Info', {
            'fields': ('user', 'amount', 'currency', 'status')
        }),
        ('Payment Proof', {
            'fields': ('payment_screenshot', 'screenshot_preview_large')
        }),
        ('Review', {
            'fields': ('admin_note', 'reviewed_at', 'reviewed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def formatted_amount(self, obj):
        symbol = '₦' if obj.currency == 'NGN' else '$'
        return f'{symbol}{obj.amount:,.2f}'
    formatted_amount.short_description = 'Amount'

    def screenshot_preview(self, obj):
        if obj.payment_screenshot:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.payment_screenshot.url)
        return '-'
    screenshot_preview.short_description = 'Screenshot'

    def screenshot_preview_large(self, obj):
        if obj.payment_screenshot:
            return format_html('<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px;" />', obj.payment_screenshot.url)
        return 'No screenshot uploaded'
    screenshot_preview_large.short_description = 'Payment Screenshot'

    def approve_deposits(self, request, queryset):
        approved = 0
        for deposit in queryset.filter(status='pending'):
            if deposit.approve(request.user, 'Approved by admin'):
                approved += 1
                # Send email notification
                send_deposit_approved_email(deposit)
                # Pay referral commission if applicable
                self._pay_referral_commission(deposit)
        self.message_user(request, f'Approved {approved} deposits and credited to user wallets')
    approve_deposits.short_description = '✅ Approve and credit to wallet'

    def reject_deposits(self, request, queryset):
        rejected = 0
        for deposit in queryset.filter(status='pending'):
            if deposit.reject(request.user, 'Rejected by admin'):
                rejected += 1
                # Send email notification
                send_deposit_rejected_email(deposit)
        self.message_user(request, f'Rejected {rejected} deposits')
    reject_deposits.short_description = '❌ Reject deposits'
    
    def _pay_referral_commission(self, deposit):
        """Pay referral commission when deposit is approved"""
        try:
            referral = Referral.objects.filter(referred=deposit.user, is_active=True).first()
            if not referral:
                return
            
            # Calculate commission
            commission_rate = referral.commission_rate / 100
            commission_amount = deposit.amount * commission_rate
            
            # Credit referrer's wallet
            referrer_wallet, _ = Wallet.objects.get_or_create(user=referral.referrer)
            referrer_wallet.add_funds(commission_amount, deposit.currency)
            
            # Record transaction
            Transaction.objects.create(
                wallet=referrer_wallet,
                transaction_type='bonus',
                amount=commission_amount,
                currency=deposit.currency,
                description=f'Referral commission from {deposit.user.username}',
                reference_id=f'REF-{referral.id}'
            )
            
            # Update referral total earned
            referral.total_earned += commission_amount
            referral.save()
            
            # Record earning
            ReferralEarning.objects.create(
                referral=referral,
                amount=commission_amount,
                currency=deposit.currency
            )
            
            # Send notification email
            send_referral_earning_email(referral, commission_amount, deposit.currency)
        except Exception:
            pass  # Don't fail deposit approval if referral fails


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'formatted_amount', 'currency', 'description', 'created_at']
    list_filter = ['transaction_type', 'currency', 'created_at']
    search_fields = ['wallet__user__username', 'description', 'reference_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def formatted_amount(self, obj):
        symbol = '₦' if obj.currency == 'NGN' else '$'
        return f'{symbol}{obj.amount:,.2f}'
    formatted_amount.short_description = 'Amount'


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'slug', 'is_active', 'order', 'get_services_count']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}

    def get_services_count(self, obj):
        return obj.services.count()
    get_services_count.short_description = 'Services'


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'category', 'provider_price', 'markup_percentage', 'price_per_1000', 'profit_display', 'min_quantity', 'max_quantity', 'quality', 'provider_service_id', 'is_active', 'is_featured']
    list_filter = ['platform', 'category', 'quality', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'provider_service_id']
    list_editable = ['is_active', 'is_featured', 'markup_percentage', 'price_per_1000', 'min_quantity', 'max_quantity', 'quality', 'provider_service_id']
    actions = ['set_markup_25', 'set_markup_50', 'set_markup_75', 'set_markup_100', 'sync_prices_from_provider', 'activate_services', 'deactivate_services', 'mark_featured', 'unmark_featured']
    ordering = ['platform', 'category', 'price_per_1000']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('platform', 'category', 'name', 'description', 'quality')
        }),
        ('Pricing', {
            'fields': ('provider_price', 'markup_percentage', 'price_per_1000'),
            'description': 'Set price_per_1000 manually OR set provider_price + markup to auto-calculate'
        }),
        ('Quantity Limits', {
            'fields': ('min_quantity', 'max_quantity', 'average_time')
        }),
        ('Status & Provider', {
            'fields': ('is_active', 'is_featured', 'provider_service_id')
        }),
    )
    
    def profit_display(self, obj):
        """Show profit per 1000 units"""
        if obj.provider_price and obj.provider_price > 0:
            profit = obj.price_per_1000 - obj.provider_price
            return f'${profit:.2f}'
        return '-'
    profit_display.short_description = 'Profit/1K'
    
    def set_markup_25(self, request, queryset):
        from decimal import Decimal
        count = 0
        for service in queryset:
            service.markup_percentage = Decimal('25')
            service.save()
            count += 1
        self.message_user(request, f'Set 25% markup for {count} services')
    set_markup_25.short_description = '💰 Set 25% markup'
    
    def set_markup_50(self, request, queryset):
        from decimal import Decimal
        count = 0
        for service in queryset:
            service.markup_percentage = Decimal('50')
            service.save()
            count += 1
        self.message_user(request, f'Set 50% markup for {count} services')
    set_markup_50.short_description = '💰 Set 50% markup'
    
    def set_markup_75(self, request, queryset):
        from decimal import Decimal
        count = 0
        for service in queryset:
            service.markup_percentage = Decimal('75')
            service.save()
            count += 1
        self.message_user(request, f'Set 75% markup for {count} services')
    set_markup_75.short_description = '💰 Set 75% markup'
    
    def set_markup_100(self, request, queryset):
        from decimal import Decimal
        count = 0
        for service in queryset:
            service.markup_percentage = Decimal('100')
            service.save()
            count += 1
        self.message_user(request, f'Set 100% markup (2x) for {count} services')
    set_markup_100.short_description = '💰 Set 100% markup (2x)'
    
    def sync_prices_from_provider(self, request, queryset):
        """Recalculate user prices from current provider prices and markup"""
        count = 0
        for service in queryset:
            if service.provider_price and service.provider_price > 0:
                service.save()  # This triggers recalculation
                count += 1
        self.message_user(request, f'Synced {count} services (prices recalculated from provider price + markup)')
    sync_prices_from_provider.short_description = '🔄 Recalculate prices from markup'

    def double_prices(self, request, queryset):
        from decimal import Decimal
        count = queryset.count()
        for service in queryset:
            service.price_per_1000 = service.price_per_1000 * Decimal('2')
            service.save()
        self.message_user(request, f'Doubled prices for {count} services (2x markup)')
    double_prices.short_description = '💰 Double prices (2x)'

    def increase_50_percent(self, request, queryset):
        from decimal import Decimal
        count = queryset.count()
        for service in queryset:
            service.price_per_1000 = service.price_per_1000 * Decimal('1.5')
            service.save()
        self.message_user(request, f'Increased prices by 50% for {count} services (1.5x markup)')
    increase_50_percent.short_description = '💰 Increase 50% (1.5x)'

    def increase_25_percent(self, request, queryset):
        from decimal import Decimal
        count = queryset.count()
        for service in queryset:
            service.price_per_1000 = service.price_per_1000 * Decimal('1.25')
            service.save()
        self.message_user(request, f'Increased prices by 25% for {count} services (1.25x markup)')
    increase_25_percent.short_description = '💰 Increase 25% (1.25x)'

    def activate_services(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'Activated {count} services')
    activate_services.short_description = '✅ Activate services'

    def deactivate_services(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} services')
    deactivate_services.short_description = '❌ Deactivate services'

    def mark_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'Marked {count} services as featured')
    mark_featured.short_description = '⭐ Mark as featured'

    def unmark_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f'Removed featured status from {count} services')
    unmark_featured.short_description = '⭐ Remove featured status'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'quantity', 'price', 'status', 'provider_order_id', 'created_at']
    list_filter = ['status', 'service__platform', 'created_at']
    search_fields = ['user__username', 'link', 'service__name', 'provider_order_id']
    readonly_fields = ['created_at', 'updated_at', 'provider_order_id']
    date_hierarchy = 'created_at'
    actions = ['mark_completed', 'mark_processing', 'mark_cancelled', 'sync_status_from_provider']

    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', remains=0, completed_at=timezone.now())
    mark_completed.short_description = 'Mark as Completed'

    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_processing.short_description = 'Mark as Processing'

    def mark_cancelled(self, request, queryset):
        for order in queryset.filter(status='pending'):
            wallet, _ = Wallet.objects.get_or_create(user=order.user)
            # Refund to USD balance (orders are in USD)
            wallet.balance_usd += order.price
            if wallet.total_spent_usd >= order.price:
                wallet.total_spent_usd -= order.price
            wallet.save()
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='refund',
                amount=order.price,
                currency='USD',
                description=f'Refund for cancelled order #{order.id}'
            )
            order.status = 'cancelled'
            order.save()
    mark_cancelled.short_description = 'Cancel & Refund'

    def sync_status_from_provider(self, request, queryset):
        from .smm_provider import sync_order_status
        synced = 0
        for order in queryset.filter(provider_order_id__isnull=False):
            sync_order_status(order)
            synced += 1
        self.message_user(request, f'Synced {synced} orders from provider')
    sync_status_from_provider.short_description = 'Sync status from provider'


@admin.register(VirtualNumberOrder)
class VirtualNumberOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'country', 'phone_number', 'sms_code', 'price_ngn', 'status', 'created_at']
    list_filter = ['status', 'service', 'country', 'created_at']
    search_fields = ['user__username', 'phone_number', 'activation_id']
    readonly_fields = ['created_at', 'updated_at', 'activation_id']
    date_hierarchy = 'created_at'
    actions = ['mark_completed', 'mark_cancelled', 'refund_orders']

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f'Marked {queryset.count()} orders as completed')
    mark_completed.short_description = '✅ Mark as Completed'

    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f'Marked {queryset.count()} orders as cancelled')
    mark_cancelled.short_description = '❌ Mark as Cancelled'

    def refund_orders(self, request, queryset):
        refunded = 0
        for order in queryset.filter(status__in=['pending', 'active', 'cancelled']):
            wallet = Wallet.objects.get(user=order.user)
            wallet.balance_ngn += order.price_ngn
            wallet.balance_usd += order.price_usd
            wallet.save()
            order.status = 'cancelled'
            order.save()
            refunded += 1
        self.message_user(request, f'Refunded {refunded} virtual number orders')
    refund_orders.short_description = '💰 Cancel & Refund'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred', 'referral_code', 'commission_rate', 'total_earned', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['referrer__username', 'referred__username', 'referral_code']
    readonly_fields = ['total_earned', 'created_at']


@admin.register(ReferralEarning)
class ReferralEarningAdmin(admin.ModelAdmin):
    list_display = ['referral', 'amount', 'currency', 'created_at']
    list_filter = ['currency', 'created_at']
    readonly_fields = ['created_at']


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    readonly_fields = ['sender', 'created_at']
    fields = ['sender', 'message', 'is_staff_reply', 'created_at']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subject', 'category', 'priority', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'category', 'priority', 'created_at']
    search_fields = ['user__username', 'subject']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    date_hierarchy = 'created_at'
    inlines = [TicketMessageInline]
    actions = ['mark_in_progress', 'mark_resolved', 'mark_closed']
    
    fieldsets = (
        ('Ticket Info', {
            'fields': ('user', 'subject', 'category', 'priority', 'status')
        }),
        ('Related Items', {
            'fields': ('related_order', 'related_deposit'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
        self.message_user(request, f'Marked {queryset.count()} tickets as In Progress')
    mark_in_progress.short_description = '🔄 Mark as In Progress'
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'Marked {queryset.count()} tickets as Resolved')
    mark_resolved.short_description = '✅ Mark as Resolved'
    
    def mark_closed(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f'Marked {queryset.count()} tickets as Closed')
    mark_closed.short_description = '🔒 Mark as Closed'
    
    def save_formset(self, request, form, formset, change):
        """Auto-set staff reply flag for admin messages"""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:  # New message
                instance.sender = request.user
                instance.is_staff_reply = True
            instance.save()
        formset.save_m2m()


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'is_staff_reply', 'created_at']
    list_filter = ['is_staff_reply', 'created_at']
    search_fields = ['ticket__subject', 'sender__username', 'message']
    readonly_fields = ['created_at']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for site-wide settings - singleton model"""
    
    fieldsets = (
        ('💰 Crypto Wallet Addresses', {
            'fields': ('usdt_trc20_address', 'usdt_bep20_address', 'btc_address', 'eth_address'),
            'description': 'Enter your crypto wallet addresses for receiving payments'
        }),
        ('🏦 Bank Details', {
            'fields': ('bank_name', 'account_number', 'account_name'),
        }),
        ('📞 Contact Information', {
            'fields': ('whatsapp_number', 'support_email'),
        }),
        ('⚙️ Settings', {
            'fields': ('exchange_rate', 'min_deposit_ngn', 'min_deposit_usd'),
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Redirect to the single instance edit page
        settings = SiteSettings.get_settings()
        from django.shortcuts import redirect
        return redirect(f'/admin/social/sitesettings/{settings.pk}/change/')


# Custom Admin Dashboard
class DAILYFUNDZBOOSTAdminSite(admin.AdminSite):
    site_header = 'DAILYFUNDZBOOST Admin'
    site_title = 'DAILYFUNDZBOOST'
    index_title = 'Dashboard'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
            path('api-health/', self.admin_view(self.api_health_view), name='api_health'),
        ]
        return custom_urls + urls

    def analytics_view(self, request):
        # Date ranges
        today = datetime.now().date()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)

        # User stats
        total_users = User.objects.count()
        new_users_7d = User.objects.filter(date_joined__date__gte=last_7_days).count()
        new_users_30d = User.objects.filter(date_joined__date__gte=last_30_days).count()

        # Order stats
        total_orders = Order.objects.count()
        orders_7d = Order.objects.filter(created_at__date__gte=last_7_days).count()
        completed_orders = Order.objects.filter(status='completed').count()
        pending_orders = Order.objects.filter(status='pending').count()

        # Revenue stats
        total_revenue = Deposit.objects.filter(status='approved').aggregate(
            total=Sum('amount'))['total'] or 0
        revenue_7d = Deposit.objects.filter(
            status='approved', created_at__date__gte=last_7_days
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Pending deposits
        pending_deposits = Deposit.objects.filter(status='pending').count()
        pending_amount = Deposit.objects.filter(status='pending').aggregate(
            total=Sum('amount'))['total'] or 0

        # Daily orders chart data (last 7 days)
        orders_by_day = Order.objects.filter(
            created_at__date__gte=last_7_days
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')

        chart_labels = [(last_7_days + timedelta(days=i)).strftime('%b %d') for i in range(8)]
        chart_data = [0] * 8
        for item in orders_by_day:
            idx = (item['day'] - last_7_days).days
            if 0 <= idx < 8:
                chart_data[idx] = item['count']

        # Top services
        top_services = Service.objects.annotate(
            order_count=Count('order')
        ).order_by('-order_count')[:5]

        context = {
            **self.each_context(request),
            'title': 'Analytics Dashboard',
            'total_users': total_users,
            'new_users_7d': new_users_7d,
            'new_users_30d': new_users_30d,
            'total_orders': total_orders,
            'orders_7d': orders_7d,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'revenue_7d': revenue_7d,
            'pending_deposits': pending_deposits,
            'pending_amount': pending_amount,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'top_services': top_services,
        }
        return render(request, 'admin/analytics.html', context)

    def api_health_view(self, request):
        import requests
        from django.conf import settings
        
        # Check JAP API
        jap_status = {'name': 'JustAnotherPanel (SMM)', 'status': 'unknown', 'message': ''}
        try:
            jap_url = getattr(settings, 'SMM_PROVIDER_URL', '')
            jap_key = getattr(settings, 'SMM_PROVIDER_KEY', '')
            if jap_url and jap_key:
                resp = requests.post(jap_url, data={'key': jap_key, 'action': 'balance'}, timeout=10)
                data = resp.json()
                if 'balance' in data:
                    jap_status['status'] = 'healthy'
                    jap_status['message'] = f"Balance: ${data['balance']}"
                else:
                    jap_status['status'] = 'error'
                    jap_status['message'] = str(data.get('error', 'Unknown error'))
            else:
                jap_status['status'] = 'not_configured'
                jap_status['message'] = 'API credentials not set'
        except Exception as e:
            jap_status['status'] = 'error'
            jap_status['message'] = str(e)

        # Check GrizzlySMS API
        grizzly_status = {'name': 'GrizzlySMS (Virtual Numbers)', 'status': 'unknown', 'message': ''}
        try:
            grizzly_key = getattr(settings, 'GRIZZLY_API_KEY', '')
            if grizzly_key:
                resp = requests.get(
                    'https://api.grizzlysms.com/stubs/handler_api.php',
                    params={'api_key': grizzly_key, 'action': 'getBalance'},
                    timeout=10
                )
                if resp.text.startswith('ACCESS_BALANCE:'):
                    balance = resp.text.replace('ACCESS_BALANCE:', '')
                    grizzly_status['status'] = 'healthy'
                    grizzly_status['message'] = f"Balance: ${balance}"
                else:
                    grizzly_status['status'] = 'error'
                    grizzly_status['message'] = resp.text
            else:
                grizzly_status['status'] = 'not_configured'
                grizzly_status['message'] = 'API key not set'
        except Exception as e:
            grizzly_status['status'] = 'error'
            grizzly_status['message'] = str(e)

        # Database check
        db_status = {'name': 'Database', 'status': 'healthy', 'message': ''}
        try:
            User.objects.count()
            db_status['message'] = 'Connected'
        except Exception as e:
            db_status['status'] = 'error'
            db_status['message'] = str(e)

        context = {
            **self.each_context(request),
            'title': 'API Health Check',
            'apis': [jap_status, grizzly_status, db_status],
        }
        return render(request, 'admin/api_health.html', context)


# Customize admin site title
admin.site.site_header = 'DAILYFUNDZBOOST Admin'
admin.site.site_title = 'DAILYFUNDZBOOST'
admin.site.index_title = 'Dashboard'


@admin.register(SocialAccountListing)
class SocialAccountListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'platform', 'title', 'price_ngn', 'countries', 'status', 'purchased_by', 'created_at']
    list_filter = ['platform', 'status', 'countries', 'created_at']
    search_fields = ['title', 'description', 'account_url', 'countries']
    list_editable = ['status', 'price_ngn']
    readonly_fields = ['created_by', 'purchased_by', 'purchased_at', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Account Details', {
            'fields': ('platform', 'title', 'description', 'account_url')
        }),
        ('Pricing & Location', {
            'fields': ('price_ngn', 'countries')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Tracking', {
            'fields': ('created_by', 'purchased_by', 'purchased_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SocialAccountPurchase)
class SocialAccountPurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_platform', 'get_listing_title', 'amount_paid', 'status', 'created_at']
    list_filter = ['status', 'listing__platform', 'created_at']
    search_fields = ['user__username', 'user__email', 'listing__title']
    list_editable = ['status']
    readonly_fields = ['user', 'listing', 'amount_paid', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Purchase Info', {
            'fields': ('user', 'listing', 'amount_paid', 'status')
        }),
        ('Login Details (Admin fills this)', {
            'fields': ('login_details', 'admin_notes'),
            'description': 'Provide login credentials here once ready. User will see this after you mark as Completed.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_platform(self, obj):
        return obj.listing.get_platform_display()
    get_platform.short_description = 'Platform'
    
    def get_listing_title(self, obj):
        return obj.listing.title[:50]
    get_listing_title.short_description = 'Account'
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'completed' and not obj.completed_at:
            from django.utils import timezone
            obj.completed_at = timezone.now()
        super().save_model(request, obj, form, change)
