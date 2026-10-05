from django.db import models, transaction
from django.contrib.auth.models import User
from decimal import Decimal
import random
import string


def generate_referral_code():
    """Generate unique referral code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        # Avoid circular import by checking Profile directly
        from django.apps import apps
        try:
            Referral = apps.get_model('social', 'Referral')
            if not Referral.objects.filter(referral_code=code).exists():
                return code
        except LookupError:
            return code


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    followers = models.ManyToManyField(User, related_name='following', blank=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} Profile'
    
    def get_referral_code(self):
        """Get or generate referral code for this user"""
        if not self.referral_code:
            self.referral_code = generate_referral_code()
            self.save()
        return self.referral_code


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=500)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username}: {self.content[:30]}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} on {self.post}'


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(max_length=1000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Message from {self.sender} to {self.receiver}'


class Report(models.Model):
    REPORT_TYPES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    reported_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Report by {self.reporter} - {self.report_type}'


# ============== SMM PANEL MODELS ==============

class Wallet(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('NGN', 'Nigerian Naira (₦)'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_ngn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    preferred_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    total_spent_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent_ngn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Exchange rate: 1 USD = X NGN (admin can update this)
    EXCHANGE_RATE = 1550  # Default rate

    def __str__(self):
        if self.preferred_currency == 'NGN':
            return f'{self.user.username} Wallet: ₦{self.balance_ngn}'
        return f'{self.user.username} Wallet: ${self.balance_usd}'

    @property
    def balance(self):
        """Legacy property for backward compatibility"""
        return self.balance_usd

    def add_funds(self, amount, currency='USD'):
        amount = Decimal(str(amount))
        if currency not in ('USD', 'NGN') or amount <= 0:
            raise ValueError('A positive amount and supported currency are required.')

        with transaction.atomic():
            wallet = type(self).objects.select_for_update().get(pk=self.pk)
            field = 'balance_ngn' if currency == 'NGN' else 'balance_usd'
            setattr(wallet, field, getattr(wallet, field) + amount)
            wallet.save(update_fields=[field, 'updated_at'])

        setattr(self, field, getattr(wallet, field))
        self.updated_at = wallet.updated_at

    def deduct_funds(self, amount, currency='USD'):
        amount = Decimal(str(amount))
        if currency not in ('USD', 'NGN') or amount <= 0:
            raise ValueError('A positive amount and supported currency are required.')

        with transaction.atomic():
            wallet = type(self).objects.select_for_update().get(pk=self.pk)
            balance_field = 'balance_ngn' if currency == 'NGN' else 'balance_usd'
            spent_field = 'total_spent_ngn' if currency == 'NGN' else 'total_spent_usd'
            if getattr(wallet, balance_field) < amount:
                return False

            setattr(wallet, balance_field, getattr(wallet, balance_field) - amount)
            setattr(wallet, spent_field, getattr(wallet, spent_field) + amount)
            wallet.save(update_fields=[balance_field, spent_field, 'updated_at'])

        setattr(self, balance_field, getattr(wallet, balance_field))
        setattr(self, spent_field, getattr(wallet, spent_field))
        self.updated_at = wallet.updated_at
        return True

    def get_balance_in_currency(self, currency):
        """Get total balance converted to specified currency"""
        if currency == 'NGN':
            usd_in_ngn = self.balance_usd * self.EXCHANGE_RATE
            return self.balance_ngn + usd_in_ngn
        else:
            ngn_in_usd = self.balance_ngn / self.EXCHANGE_RATE
            return self.balance_usd + ngn_in_usd


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('purchase', 'Service Purchase'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
        ('adjustment', 'Admin Adjustment'),
    ]
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('NGN', 'Nigerian Naira'),
    ]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        symbol = '₦' if self.currency == 'NGN' else '$'
        return f'{self.wallet.user.username}: {self.transaction_type} {symbol}{self.amount}'


class Deposit(models.Model):
    """
    Payment deposit requests via bank transfer (OPay)
    Users upload payment screenshot, admin approves/rejects
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('NGN', 'Nigerian Naira (₦)'),
    ]
    
    # Company Payment Details
    OPAY_ACCOUNT_NUMBER = '9070910294'
    OPAY_ACCOUNT_NAME = 'DAILYFUNDZBOOST'
    OPAY_BANK_NAME = 'OPay'
    COMPANY_EMAIL = 'support@dailyfundzboost.trade'
    WHATSAPP_NUMBER = '+2348105594678'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    payment_screenshot = models.ImageField(upload_to='deposits/', help_text='Upload payment receipt screenshot')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True, null=True, help_text='Admin note (visible to user)')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_deposits'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        symbol = '₦' if self.currency == 'NGN' else '$'
        return f'Deposit #{self.id} - {self.user.username} - {symbol}{self.amount} ({self.status})'

    def approve(self, admin_user, note=''):
        """Approve deposit and credit user wallet"""
        from django.utils import timezone

        with transaction.atomic():
            deposit = type(self).objects.select_for_update().get(pk=self.pk)
            if deposit.status != 'pending':
                return False

            wallet, _ = Wallet.objects.get_or_create(user=deposit.user)
            wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
            wallet.add_funds(deposit.amount, deposit.currency)

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='deposit',
                amount=deposit.amount,
                currency=deposit.currency,
                description=f'Bank deposit approved (Ref: #{deposit.id})',
                reference_id=f'DEP-{deposit.id}'
            )

            deposit.status = 'approved'
            deposit.admin_note = note
            deposit.reviewed_at = timezone.now()
            deposit.reviewed_by = admin_user
            deposit.save()

        self.status = deposit.status
        self.admin_note = deposit.admin_note
        self.reviewed_at = deposit.reviewed_at
        self.reviewed_by = deposit.reviewed_by
        return True

    def reject(self, admin_user, note=''):
        """Reject deposit"""
        from django.utils import timezone

        with transaction.atomic():
            deposit = type(self).objects.select_for_update().get(pk=self.pk)
            if deposit.status != 'pending':
                return False

            deposit.status = 'rejected'
            deposit.admin_note = note
            deposit.reviewed_at = timezone.now()
            deposit.reviewed_by = admin_user
            deposit.save()

        self.status = deposit.status
        self.admin_note = deposit.admin_note
        self.reviewed_at = deposit.reviewed_at
        self.reviewed_by = deposit.reviewed_by
        return True
    
    def generate_action_token(self):
        """Generate secure token for email action links"""
        from django.core.signing import TimestampSigner
        signer = TimestampSigner()
        return signer.sign(f'deposit-{self.id}')
    
    @classmethod
    def verify_action_token(cls, token, max_age=86400):
        """Verify token and return deposit ID (max_age in seconds, default 24 hours)"""
        from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
        signer = TimestampSigner()
        try:
            value = signer.unsign(token, max_age=max_age)
            if value.startswith('deposit-'):
                deposit_id = int(value.split('-')[1])
                return deposit_id
        except (SignatureExpired, BadSignature, ValueError):
            return None
        return None

    @classmethod
    def get_payment_info(cls):
        """Get OPay payment details for display"""
        return {
            'bank_name': cls.OPAY_BANK_NAME,
            'account_number': cls.OPAY_ACCOUNT_NUMBER,
            'account_name': cls.OPAY_ACCOUNT_NAME,
            'exchange_rate': Wallet.EXCHANGE_RATE,
            'company_email': cls.COMPANY_EMAIL,
            'whatsapp': cls.WHATSAPP_NUMBER,
        }


class Platform(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default='📱')
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Service Categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Real provider price from API (admin sees this)
    provider_price = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='Real price from API provider per 1000 units (USD)')
    # Markup percentage that admin sets
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50, help_text='Markup percentage (e.g., 50 = 50% markup)')
    # User-facing price (automatically calculated from provider_price + markup)
    price_per_1000 = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price shown to users per 1000 units (USD)')
    min_quantity = models.IntegerField(default=100)
    max_quantity = models.IntegerField(default=10000)
    average_time = models.CharField(max_length=50, help_text='e.g., "1-24 hours"')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    quality = models.CharField(max_length=20, choices=[
        ('standard', 'Standard'),
        ('high', 'High Quality'),
        ('premium', 'Premium'),
        ('real', 'Real & Active'),
    ], default='standard')
    provider_service_id = models.CharField(max_length=50, blank=True, null=True, help_text='Service ID from SMM provider')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['platform', 'category', 'price_per_1000']

    def __str__(self):
        return f'{self.platform.name} - {self.name}'

    def calculate_price(self, quantity):
        return ((self.price_per_1000 / Decimal('1000')) * quantity).quantize(
            Decimal('0.01')
        )
    
    def calculate_user_price(self):
        """Calculate user-facing price from provider price + markup"""
        from decimal import Decimal
        if self.provider_price and self.provider_price > 0:
            markup_multiplier = Decimal('1') + (self.markup_percentage / Decimal('100'))
            return (self.provider_price * markup_multiplier).quantize(Decimal('0.0001'))
        return self.price_per_1000
    
    def save(self, *args, **kwargs):
        # Auto-calculate price_per_1000 from provider_price + markup
        if self.provider_price and self.provider_price > 0:
            self.price_per_1000 = self.calculate_user_price()
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('partial', 'Partial'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='orders')
    link = models.URLField(max_length=500, help_text='Link to post/profile')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_count = models.IntegerField(default=0, help_text='Count when order started')
    remains = models.IntegerField(default=0, help_text='Remaining quantity to deliver')
    provider_order_id = models.CharField(max_length=100, blank=True, null=True, help_text='Order ID from SMM provider')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.user.username} - {self.service.name}'
    
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'processing']
    
    def can_refund(self):
        """Check if order is eligible for refund"""
        return self.status in ['cancelled', 'partial']
    
    def cancel(self):
        """Cancel order and refund user"""
        with transaction.atomic():
            order = type(self).objects.select_for_update().get(pk=self.pk)
            if not order.can_cancel():
                return False, "Order cannot be cancelled"

            wallet, _ = Wallet.objects.get_or_create(user=order.user)
            wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
            wallet.add_funds(order.price, 'USD')

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='refund',
                amount=order.price,
                currency='USD',
                description=f'Cancelled order #{order.id} refund',
                reference_id=f'REFUND-{order.id}'
            )

            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])

        self.status = order.status
        return True, "Order cancelled and refunded"

    def refund_partial(self, refund_amount):
        """Refund partial amount for partial orders"""
        with transaction.atomic():
            order = type(self).objects.select_for_update().get(pk=self.pk)
            if not order.can_refund():
                return False, "Order not eligible for refund"

            if refund_amount <= 0 or refund_amount > order.price:
                return False, "Invalid refund amount"

            wallet, _ = Wallet.objects.get_or_create(user=order.user)
            wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
            wallet.add_funds(refund_amount, 'USD')

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='refund',
                amount=refund_amount,
                currency='USD',
                description=f'Partial refund for order #{order.id}',
                reference_id=f'REFUND-{order.id}'
            )

            order.status = 'refunded'
            order.save(update_fields=['status', 'updated_at'])

        self.status = order.status
        return True, f"Refunded ${refund_amount}"


class VirtualNumberOrder(models.Model):
    """Orders for virtual phone numbers via GrizzlySMS"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active - Waiting for SMS'),
        ('received', 'SMS Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    SERVICE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('google', 'Google/Gmail'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter/X'),
        ('amazon', 'Amazon'),
        ('paypal', 'PayPal'),
        ('apple', 'Apple'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='virtual_number_orders')
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    country = models.CharField(max_length=50)
    country_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    sms_code = models.CharField(max_length=20, blank=True, null=True)
    activation_id = models.CharField(max_length=50, blank=True, null=True, help_text='GrizzlySMS activation ID')
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    price_ngn = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'VN#{self.id} - {self.service} - {self.country}'


class Referral(models.Model):
    """Referral system - users earn commission on referrals"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referred = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referred_by')
    referral_code = models.CharField(max_length=20, unique=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # 5% default
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.referrer.username} -> {self.referred.username}'


class ReferralEarning(models.Model):
    """Track individual referral earnings"""
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    source_transaction = models.ForeignKey('Transaction', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'₦{self.amount} from {self.referral.referred.username}'


class SupportTicket(models.Model):
    """Support ticket system"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    CATEGORY_CHOICES = [
        ('order', 'Order Issue'),
        ('deposit', 'Deposit Issue'),
        ('refund', 'Refund Request'),
        ('account', 'Account Issue'),
        ('technical', 'Technical Problem'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    related_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    related_deposit = models.ForeignKey('Deposit', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resolved_tickets'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Ticket #{self.id} - {self.subject}'


class TicketMessage(models.Model):
    """Messages within a support ticket"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='ticket_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Message on Ticket #{self.ticket.id}'


class SiteSettings(models.Model):
    """Site-wide settings editable by admin"""
    
    # Crypto Wallet Addresses
    usdt_trc20_address = models.CharField(
        max_length=100, 
        blank=True, 
        default='',
        verbose_name='USDT TRC20 Wallet',
        help_text='Your USDT wallet address on Tron network'
    )
    usdt_bep20_address = models.CharField(
        max_length=100, 
        blank=True, 
        default='',
        verbose_name='USDT BEP20 Wallet',
        help_text='Your USDT wallet address on BSC network'
    )
    btc_address = models.CharField(
        max_length=100, 
        blank=True, 
        default='',
        verbose_name='Bitcoin Wallet',
        help_text='Your Bitcoin wallet address'
    )
    eth_address = models.CharField(
        max_length=100, 
        blank=True, 
        default='',
        verbose_name='Ethereum Wallet',
        help_text='Your Ethereum wallet address'
    )
    
    # Bank Details
    bank_name = models.CharField(max_length=100, default='OPay', verbose_name='Bank Name')
    account_number = models.CharField(max_length=20, default='9070910294', verbose_name='Account Number')
    account_name = models.CharField(max_length=100, default='DAILYFUNDZBOOST', verbose_name='Account Name')
    
    # Contact Info
    whatsapp_number = models.CharField(max_length=20, default='+2348105594678', verbose_name='WhatsApp Number')
    support_email = models.EmailField(default='support@dailyfundzboost.trade', verbose_name='Support Email')
    
    # Settings
    exchange_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1550.00,
        verbose_name='USD to NGN Rate',
        help_text='Exchange rate: 1 USD = X NGN'
    )
    min_deposit_ngn = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    min_deposit_usd = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return 'Site Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


class SocialAccountListing(models.Model):
    """Social media accounts for sale - admin posts, users buy"""
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter/X'),
        ('snapchat', 'Snapchat'),
        ('youtube', 'YouTube'),
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('gmail', 'Gmail/Google'),
        ('outlook', 'Outlook/Hotmail'),
        ('yahoo', 'Yahoo Mail'),
        ('protonmail', 'ProtonMail'),
        ('icloud', 'iCloud Mail'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('reserved', 'Reserved'),
        ('unavailable', 'Unavailable'),
    ]
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    title = models.CharField(max_length=200, help_text='E.g., SINGAPORE 🇸🇬 FB | (0-50 friends) (2025)')
    description = models.TextField(help_text='Account details, features, login info format, etc.')
    price_ngn = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Price (₦)')
    countries = models.CharField(max_length=255, default='Global', help_text='Countries or Global. E.g., Nigeria, USA, Singapore or Global')
    account_url = models.URLField(max_length=500, help_text='The account URL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # For tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='account_listings_created')
    purchased_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='account_purchases')
    purchased_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Social Account Listing'
        verbose_name_plural = 'Social Account Listings'
    
    def __str__(self):
        return f'{self.get_platform_display()} - {self.title} - ₦{self.price_ngn}'


class SocialAccountPurchase(models.Model):
    """Track purchases of social accounts"""
    STATUS_CHOICES = [
        ('pending', 'Pending - Awaiting Details'),
        ('processing', 'Processing - Support Working'),
        ('completed', 'Completed - Details Sent'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_account_purchases')
    listing = models.ForeignKey(SocialAccountListing, on_delete=models.CASCADE, related_name='purchases')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin provides login details here
    login_details = models.TextField(blank=True, help_text='Login credentials provided by admin')
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Social Account Purchase'
        verbose_name_plural = 'Social Account Purchases'
    
    def __str__(self):
        return f'Purchase #{self.id} - {self.user.username} - {self.listing.platform}'
