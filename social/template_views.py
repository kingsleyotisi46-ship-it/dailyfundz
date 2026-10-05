"""
Django views for DAILYFUNDZBOOST - Template-based views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from decimal import Decimal

from .models import (
    Wallet, Transaction, Platform, ServiceCategory, 
    Service, Order, Deposit, Profile, VirtualNumberOrder,
    SiteSettings, SocialAccountListing, SocialAccountPurchase
)
from .smm_provider import smm_provider
from .grizzly_provider import GrizzlySMSProvider as GrizzlyProvider
from .emails import (
    send_welcome_email, send_admin_new_deposit_notification,
    send_admin_new_user_notification, send_admin_new_ticket_notification
)


def get_wallet_context(user):
    """Get wallet info for navbar"""
    if user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return {
            'wallet': wallet,
            'wallet_balance': wallet.balance_ngn,
        }
    return {}


def home(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def user_login(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')


def user_register(request):
    """Registration page"""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        ref_code = request.POST.get('ref') or request.GET.get('ref', '')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html', {'ref': ref_code})
        
        # Validate password strength using Django validators
        try:
            # Create temporary user object for validation
            temp_user = User(username=username, email=email)
            validate_password(password1, temp_user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'register.html', {'ref': ref_code})
        
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'register.html', {'ref': ref_code})
        
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html', {'ref': ref_code})
        
        # Validate username format
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters')
            return render(request, 'register.html', {'ref': ref_code})
        
        if not username.replace('_', '').isalnum():
            messages.error(request, 'Username can only contain letters, numbers, and underscores')
            return render(request, 'register.html', {'ref': ref_code})
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        Profile.objects.create(user=user)
        Wallet.objects.create(user=user)
        
        # Process referral code
        if ref_code:
            _process_referral(user, ref_code)
        
        # Send welcome email to user
        send_welcome_email(user)
        
        # Send notification to admin about new user
        send_admin_new_user_notification(user)
        
        login(request, user)
        messages.success(request, 'Account created successfully! Welcome to DAILYFUNDZBOOST!')
        return redirect('dashboard')
    
    ref_code = request.GET.get('ref', '')
    return render(request, 'register.html', {'ref': ref_code})


def _process_referral(new_user, ref_code):
    """Process referral code during registration"""
    from .models import Referral, Profile
    
    try:
        # Find referrer by their referral code (stored in Profile)
        referrer_profile = Profile.objects.filter(referral_code=ref_code).first()
        if not referrer_profile:
            return False
        
        referrer = referrer_profile.user
        
        # Don't allow self-referral
        if referrer == new_user:
            return False
        
        # Check if already referred
        if Referral.objects.filter(referred=new_user).exists():
            return False
        
        # Create referral relationship
        Referral.objects.create(
            referrer=referrer,
            referred=new_user,
            referral_code=ref_code,
            commission_rate=5.00  # 5% commission
        )
        return True
    except Exception:
        return False


def user_logout(request):
    """Logout user"""
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('home')


@login_required
def main_panel(request):
    """User main panel (formerly dashboard)"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    orders = Order.objects.filter(user=request.user)
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    pending_orders = orders.filter(status='pending').count()
    
    recent_orders = orders[:5]
    pending_deposits = Deposit.objects.filter(user=request.user, status='pending')[:5]
    
    # Get services for calculator
    services_for_calc = Service.objects.filter(is_active=True).select_related('platform')[:50]
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'pending_deposits': pending_deposits,
        'services': services_for_calc,
    }
    return render(request, 'main_panel.html', context)


@login_required
def services(request):
    """Services listing page"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    platforms = Platform.objects.filter(is_active=True)
    categories = ServiceCategory.objects.all()
    
    services_qs = Service.objects.filter(is_active=True).select_related('platform', 'category')
    
    # Filters
    selected_platform = request.GET.get('platform', '')
    selected_category = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    
    if selected_platform:
        services_qs = services_qs.filter(platform__slug=selected_platform)
    
    if selected_category:
        services_qs = services_qs.filter(category__slug=selected_category)
    
    if search_query:
        services_qs = services_qs.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    # Add NGN price
    exchange_rate = Wallet.EXCHANGE_RATE
    for service in services_qs:
        service.price_ngn = service.price_per_1000 * exchange_rate
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
        'platforms': platforms,
        'categories': categories,
        'services': services_qs,
        'selected_platform': selected_platform,
        'selected_category': selected_category,
        'search_query': search_query,
    }
    return render(request, 'services.html', context)


@login_required
def place_order(request):
    """Handle order placement"""
    if request.method != 'POST':
        return redirect('services')
    
    service_id = request.POST.get('service_id')
    link = request.POST.get('link')
    quantity = request.POST.get('quantity')
    
    try:
        service = Service.objects.get(id=service_id, is_active=True)
        quantity = int(quantity)
        
        if quantity < service.min_quantity or quantity > service.max_quantity:
            messages.error(request, f'Quantity must be between {service.min_quantity} and {service.max_quantity}')
            return redirect('services')
        
        # Calculate price in USD
        price_usd = service.calculate_price(quantity)
        
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        # Check balance (convert NGN to USD equivalent if needed)
        total_balance_usd = wallet.get_balance_in_currency('USD')
        
        if total_balance_usd < price_usd:
            messages.error(request, 'Insufficient balance. Please add funds.')
            return redirect('add_funds')
        
        # Deduct from wallet (prefer USD, then NGN)
        if wallet.balance_usd >= price_usd:
            if not wallet.deduct_funds(price_usd, 'USD'):
                messages.error(request, 'Insufficient balance. Please add funds.')
                return redirect('add_funds')
            currency_used = 'USD'
        else:
            price_ngn = price_usd * Wallet.EXCHANGE_RATE
            if not wallet.deduct_funds(price_ngn, 'NGN'):
                messages.error(request, 'Insufficient balance. Please add funds.')
                return redirect('add_funds')
            currency_used = 'NGN'
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            service=service,
            link=link,
            quantity=quantity,
            price=price_usd,
            status='pending'
        )
        
        # Record transaction
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='purchase',
            amount=price_usd if currency_used == 'USD' else price_usd * Wallet.EXCHANGE_RATE,
            currency=currency_used,
            description=f'Order #{order.id} - {service.name}',
            reference_id=str(order.id)
        )
        
        # Submit to provider if configured
        if smm_provider.is_configured() and service.provider_service_id:
            result = smm_provider.create_order(
                service_id=service.provider_service_id,
                link=link,
                quantity=quantity
            )
            if 'order' in result:
                order.provider_order_id = result['order']
                order.status = 'processing'
                order.save()
        
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('orders')
        
    except Service.DoesNotExist:
        messages.error(request, 'Service not found')
    except ValueError:
        messages.error(request, 'Invalid quantity')
    except Exception as e:
        messages.error(request, f'Error placing order: {str(e)}')
    
    return redirect('services')


@login_required
def orders(request):
    """Orders listing page"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    orders_qs = Order.objects.filter(user=request.user).select_related('service', 'service__platform')
    
    # Stats
    total_orders = orders_qs.count()
    completed_orders = orders_qs.filter(status='completed').count()
    pending_orders = orders_qs.filter(status='pending').count()
    processing_orders = orders_qs.filter(status__in=['processing', 'in_progress']).count()
    
    # Filters
    status_filter = request.GET.get('status', '')
    platform_filter = request.GET.get('platform', '')
    
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)
    
    if platform_filter:
        orders_qs = orders_qs.filter(service__platform__slug=platform_filter)
    
    # Pagination
    paginator = Paginator(orders_qs, 10)
    page = request.GET.get('page', 1)
    orders_page = paginator.get_page(page)
    
    platforms = Platform.objects.filter(is_active=True)
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
        'orders': orders_page,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'status_filter': status_filter,
        'platform_filter': platform_filter,
        'platforms': platforms,
    }
    return render(request, 'orders.html', context)


@login_required
def add_funds(request):
    """Add funds page with deposit form"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    site_settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        currency = request.POST.get('currency', 'NGN')
        amount = request.POST.get('amount')
        screenshot = request.FILES.get('payment_screenshot')
        
        try:
            amount = Decimal(amount)
            
            if currency == 'NGN' and amount < site_settings.min_deposit_ngn:
                messages.error(request, f'Minimum deposit is ₦{site_settings.min_deposit_ngn}')
                return redirect('add_funds')
            
            if currency == 'USD' and amount < site_settings.min_deposit_usd:
                messages.error(request, f'Minimum deposit is ${site_settings.min_deposit_usd}')
                return redirect('add_funds')
            
            if not screenshot:
                messages.error(request, 'Please upload payment screenshot')
                return redirect('add_funds')
            
            # Create deposit
            deposit = Deposit.objects.create(
                user=request.user,
                amount=amount,
                currency=currency,
                payment_screenshot=screenshot,
                status='pending'
            )
            
            # Send admin notification about new deposit
            send_admin_new_deposit_notification(deposit)
            
            messages.success(request, f'Deposit request submitted! We will review it shortly.')
            return redirect('add_funds')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount')
    
    pending_deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
        'exchange_rate': site_settings.exchange_rate,
        'pending_deposits': pending_deposits,
        'site_settings': site_settings,
    }
    return render(request, 'add_funds.html', context)


@login_required
def transactions(request):
    """Transaction history"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    transactions_qs = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    paginator = Paginator(transactions_qs, 20)
    page = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page)
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
        'transactions': transactions_page,
    }
    return render(request, 'transactions.html', context)


@login_required
def profile(request):
    """User profile page"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update profile
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        
        profile_obj.bio = request.POST.get('bio', '')
        if 'profile_picture' in request.FILES:
            profile_obj.profile_picture = request.FILES['profile_picture']
        profile_obj.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
        'profile': profile_obj,
    }
    return render(request, 'profile.html', context)


@login_required
def change_password(request):
    """Change password for logged-in users"""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        
        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect')
            return render(request, 'change_password.html', {'wallet': wallet, 'wallet_balance': wallet.balance_ngn})
        
        # Check new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match')
            return render(request, 'change_password.html', {'wallet': wallet, 'wallet_balance': wallet.balance_ngn})
        
        # Validate password strength
        try:
            validate_password(new_password1, request.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'change_password.html', {'wallet': wallet, 'wallet_balance': wallet.balance_ngn})
        
        # Check if new password is same as old
        if request.user.check_password(new_password1):
            messages.error(request, 'New password cannot be the same as current password')
            return render(request, 'change_password.html', {'wallet': wallet, 'wallet_balance': wallet.balance_ngn})
        
        # Update password
        request.user.set_password(new_password1)
        request.user.save()
        
        # Keep user logged in after password change
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('profile')
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet.balance_ngn,
    }
    return render(request, 'change_password.html', context)


@login_required
def virtual_numbers(request):
    """Virtual number orders page with real API pricing"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    grizzly = GrizzlyProvider()
    
    # Get services and countries from provider
    services = GrizzlyProvider.get_service_list()
    countries = GrizzlyProvider.get_country_list()
    
    # Virtual number markup percentage (admin can change in SiteSettings)
    VN_MARKUP = Decimal('100')  # 100% markup = 2x price
    NGN_RATE = Decimal('1550')  # USD to NGN rate
    
    # Cache for prices (in production, use Redis/cache)
    price_cache = {}
    
    def get_price_with_markup(base_price_usd):
        """Apply markup and convert to NGN"""
        markup_multiplier = Decimal('1') + (VN_MARKUP / Decimal('100'))
        final_usd = Decimal(str(base_price_usd)) * markup_multiplier
        final_ngn = final_usd * NGN_RATE
        return final_usd.quantize(Decimal('0.01')), final_ngn.quantize(Decimal('0.01'))
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'get_price':
            # AJAX endpoint to get real-time price
            service_code = request.POST.get('service', 'whatsapp')
            country_code = request.POST.get('country', 'usa')
            
            try:
                # Get price from GrizzlySMS API
                result = grizzly.get_prices(service_code, country_code)
                if result.get('success') and isinstance(result.get('data'), dict):
                    # Parse price from response
                    base_price = Decimal('0.50')  # Default if not found
                    for country_id, services_prices in result['data'].items():
                        if isinstance(services_prices, dict):
                            for svc_code, price in services_prices.items():
                                base_price = Decimal(str(price))
                                break
                            break
                    
                    final_usd, final_ngn = get_price_with_markup(base_price)
                    return JsonResponse({
                        'success': True,
                        'price_usd': float(final_usd),
                        'price_ngn': float(final_ngn),
                        'provider_price': float(base_price)
                    })
                else:
                    return JsonResponse({'success': False, 'error': 'Price not available'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'order':
            service_code = request.POST.get('service')
            country_code = request.POST.get('country')
            
            # Find country name
            country_name = next((c['name'] for c in countries if c['code'] == country_code), 'Unknown')
            
            # Get real price from API or use estimate
            try:
                result = grizzly.get_prices(service_code, country_code)
                if result.get('success'):
                    base_price = Decimal('0.50')
                    # Try to parse price
                    if isinstance(result.get('data'), dict):
                        for country_id, services_prices in result['data'].items():
                            if isinstance(services_prices, dict):
                                for svc_code, price in services_prices.items():
                                    base_price = Decimal(str(price))
                                    break
                                break
                else:
                    base_price = Decimal('0.50')
            except:
                base_price = Decimal('0.50')
            
            price_usd, price_ngn = get_price_with_markup(base_price)
            
            # Check balance
            if wallet.balance_ngn < price_ngn:
                messages.error(request, f'Insufficient balance. You need ₦{price_ngn:.0f}')
                return redirect('virtual_numbers')
            
            # Try to get number from GrizzlySMS
            try:
                result = grizzly.get_number(service_code, country_code)
                
                if result.get('success'):
                    # Deduct from wallet
                    wallet.balance_ngn -= price_ngn
                    wallet.save()
                    
                    # Record transaction
                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='purchase',
                        amount=price_ngn,
                        currency='NGN',
                        description=f'Virtual number: {service_code.title()} ({country_name})',
                        reference_id=f'VN-{result.get("activation_id", "")}'
                    )
                    
                    # Create order with expiry (20 minutes)
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    order = VirtualNumberOrder.objects.create(
                        user=request.user,
                        service=service_code,
                        country=country_name,
                        country_code=country_code,
                        phone_number=result.get('phone'),
                        activation_id=result.get('activation_id'),
                        price_usd=price_usd,
                        price_ngn=price_ngn,
                        status='active',
                        expires_at=timezone.now() + timedelta(minutes=20)
                    )
                    
                    messages.success(request, f'✅ Number purchased! Use +{order.phone_number} for verification.')
                else:
                    error_msg = result.get('error', 'No numbers available')
                    if 'NO_NUMBERS' in str(error_msg):
                        messages.error(request, f'No numbers available for {service_code.title()} in {country_name}. Try another country.')
                    elif 'NO_BALANCE' in str(error_msg):
                        messages.error(request, 'Service temporarily unavailable. Please try again later.')
                    else:
                        messages.error(request, f'Failed to get number: {error_msg}')
            except Exception as e:
                messages.error(request, f'Service temporarily unavailable: {str(e)}')
        
        elif action == 'check_sms':
            order_id = request.POST.get('order_id')
            order = get_object_or_404(VirtualNumberOrder, id=order_id, user=request.user)
            
            if order.activation_id and order.status == 'active':
                result = grizzly.get_status(order.activation_id)
                
                if result.get('success'):
                    status = result.get('status', '')
                    code = result.get('code')
                    
                    if code:
                        order.sms_code = code
                        order.status = 'received'
                        order.save()
                        
                        # Confirm activation complete
                        grizzly.confirm_sms_received(order.activation_id)
                        
                        # Return JSON for AJAX
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': True, 'code': code, 'status': 'received'})
                        messages.success(request, f'✅ SMS received! Code: {code}')
                    elif status == 'WAIT_CODE':
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': True, 'code': None, 'status': 'waiting'})
                        messages.info(request, '⏳ Waiting for SMS... Please use the number for verification.')
                    elif status == 'CANCEL':
                        order.status = 'cancelled'
                        order.save()
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'status': 'cancelled'})
                        messages.error(request, 'Number was cancelled.')
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Could not check status'})
                    messages.error(request, 'Could not check SMS status.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Invalid order'})
                messages.error(request, 'Invalid order')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False})
        
        elif action == 'resend_sms':
            order_id = request.POST.get('order_id')
            order = get_object_or_404(VirtualNumberOrder, id=order_id, user=request.user)
            
            if order.activation_id and order.status == 'active':
                result = grizzly.request_another_sms(order.activation_id)
                if result.get('success'):
                    messages.success(request, '📩 Requested another SMS. Please wait...')
                else:
                    messages.error(request, 'Could not request another SMS.')
            
        elif action == 'cancel':
            order_id = request.POST.get('order_id')
            order = get_object_or_404(VirtualNumberOrder, id=order_id, user=request.user)
            
            if order.status == 'active' and order.activation_id:
                result = grizzly.cancel_activation(order.activation_id)
                if result.get('success') or 'STATUS_CANCEL' in str(result):
                    # Refund to wallet
                    wallet.balance_ngn += order.price_ngn
                    wallet.save()
                    
                    # Record refund transaction
                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='refund',
                        amount=order.price_ngn,
                        currency='NGN',
                        description=f'Virtual number refund: {order.service.title()}',
                        reference_id=f'VN-REFUND-{order.id}'
                    )
                    
                    order.status = 'cancelled'
                    order.save()
                    messages.success(request, '✅ Order cancelled and ₦{:.0f} refunded.'.format(order.price_ngn))
                else:
                    messages.error(request, 'Could not cancel. SMS may have been sent already.')
            else:
                messages.error(request, 'Cannot cancel this order')
        
        elif action == 'complete':
            order_id = request.POST.get('order_id')
            order = get_object_or_404(VirtualNumberOrder, id=order_id, user=request.user)
            
            if order.status in ['active', 'received']:
                if order.activation_id:
                    grizzly.confirm_sms_received(order.activation_id)
                order.status = 'completed'
                order.save()
                messages.success(request, '✅ Order marked as complete.')
        
        return redirect('virtual_numbers')
    
    # Get user's orders
    active_orders = VirtualNumberOrder.objects.filter(
        user=request.user,
        status__in=['pending', 'active', 'received']
    ).order_by('-created_at')[:10]
    
    all_orders = VirtualNumberOrder.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    # Check GrizzlySMS balance for admin notice
    grizzly_balance = None
    if request.user.is_staff:
        try:
            bal_result = grizzly.get_balance()
            if bal_result.get('success'):
                grizzly_balance = bal_result.get('balance', 0)
        except:
            pass
    
    context = {
        **get_wallet_context(request.user),
        'services': services,
        'countries': countries,
        'active_orders': active_orders,
        'all_orders': all_orders,
        'grizzly_balance': grizzly_balance,
    }
    return render(request, 'virtual_numbers.html', context)


@login_required
def referral(request):
    """Referral program page"""
    from .models import Referral, ReferralEarning, Profile
    
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Get or generate user's referral code (now stored in profile)
    referral_code = profile.get_referral_code()
    
    # Get referrals made by this user
    referrals = Referral.objects.filter(referrer=request.user).select_related('referred')
    
    # Calculate totals
    total_referrals = referrals.count()
    total_earned = sum(ref.total_earned for ref in referrals)
    
    context = {
        **get_wallet_context(request.user),
        'referral_code': referral_code,
        'referrals': referrals,
        'total_referrals': total_referrals,
        'total_earned': total_earned,
    }
    return render(request, 'referral.html', context)


def offline(request):
    """Offline page for PWA"""
    return render(request, 'offline.html')


# Password Reset Views
def password_reset_request(request):
    """Request password reset"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address')
            return render(request, 'password_reset.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from .emails import send_password_reset_email
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')
            
            # Send email
            if send_password_reset_email(user, reset_url):
                messages.success(request, 'Password reset link sent to your email!')
            else:
                messages.error(request, 'Failed to send email. Please try again or contact support.')
                
        except User.DoesNotExist:
            # Don't reveal if email exists
            messages.success(request, 'If an account exists with this email, you will receive a reset link.')
        
        return redirect('password_reset')
    
    return render(request, 'password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """Confirm password reset with token"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'Invalid or expired reset link. Please request a new one.')
        return redirect('password_reset')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'password_reset_confirm.html', {'validlink': True})
        
        # Validate password strength using Django validators
        try:
            validate_password(password1, user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'password_reset_confirm.html', {'validlink': True})
        
        user.set_password(password1)
        user.save()
        
        messages.success(request, 'Password reset successful! You can now login.')
        return redirect('login')
    
    return render(request, 'password_reset_confirm.html', {'validlink': True})


# Support Ticket Views
@login_required
def support_tickets(request):
    """List user's support tickets"""
    from .models import SupportTicket
    
    if request.method == 'POST':
        # Create new ticket
        subject = request.POST.get('subject', '').strip()
        category = request.POST.get('category', 'other')
        message_text = request.POST.get('message', '').strip()
        
        if not subject or not message_text:
            messages.error(request, 'Please fill in all required fields')
            return redirect('support')
        
        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=subject,
            category=category,
            status='open'
        )
        
        # Create initial message
        from .models import TicketMessage
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=message_text,
            is_staff_reply=False
        )
        
        # Add message attribute for notification
        ticket.message = message_text
        send_admin_new_ticket_notification(ticket)
        
        messages.success(request, f'Ticket #{ticket.id} created. We will respond soon!')
        return redirect('support_ticket_detail', ticket_id=ticket.id)
    
    tickets = SupportTicket.objects.filter(user=request.user)
    
    context = {
        **get_wallet_context(request.user),
        'tickets': tickets,
        'categories': SupportTicket.CATEGORY_CHOICES,
    }
    return render(request, 'support.html', context)


@login_required
def support_ticket_detail(request, ticket_id):
    """View and reply to ticket"""
    from .models import SupportTicket, TicketMessage
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        
        if message_text:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message_text,
                is_staff_reply=False
            )
            
            # Reopen if closed
            if ticket.status == 'closed':
                ticket.status = 'open'
                ticket.save()
            
            messages.success(request, 'Reply sent!')
        
        return redirect('support_ticket_detail', ticket_id=ticket.id)
    
    context = {
        **get_wallet_context(request.user),
        'ticket': ticket,
        'messages': ticket.messages.all(),
    }
    return render(request, 'support_ticket_detail.html', context)


# Order Cancellation
@login_required
def cancel_order(request, order_id):
    """Cancel an order and refund"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        success, message = order.cancel()
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('orders')


# ============== SOCIAL ACCOUNT MARKETPLACE ==============

@login_required
def accounts_market(request):
    """Browse social accounts for sale"""
    platform_filter = request.GET.get('platform', '')
    country_filter = request.GET.get('country', '')
    
    listings = SocialAccountListing.objects.filter(status='available')
    
    if platform_filter:
        listings = listings.filter(platform=platform_filter)
    
    if country_filter:
        listings = listings.filter(countries__icontains=country_filter)
    
    # Group by platform for better display
    platforms = SocialAccountListing.PLATFORM_CHOICES
    
    context = {
        **get_wallet_context(request.user),
        'listings': listings,
        'platforms': platforms,
        'selected_platform': platform_filter,
        'selected_country': country_filter,
    }
    return render(request, 'accounts_market.html', context)


@login_required
def buy_account(request, listing_id):
    """Purchase a social account"""
    listing = get_object_or_404(SocialAccountListing, id=listing_id, status='available')
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Check balance
        if wallet.balance_ngn < listing.price_ngn:
            messages.error(request, f'Insufficient balance. You need ₦{listing.price_ngn} but have ₦{wallet.balance_ngn}')
            return redirect('accounts_market')
        
        # Deduct balance
        wallet.balance_ngn -= listing.price_ngn
        wallet.total_spent_ngn += listing.price_ngn
        wallet.save()
        
        # Create transaction
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='purchase',
            amount=listing.price_ngn,
            currency='NGN',
            description=f'Account Purchase: {listing.platform.upper()} - {listing.title[:50]}'
        )
        
        # Create purchase record
        purchase = SocialAccountPurchase.objects.create(
            user=request.user,
            listing=listing,
            amount_paid=listing.price_ngn,
            status='pending'
        )
        
        # Mark listing as sold
        listing.status = 'sold'
        listing.purchased_by = request.user
        from django.utils import timezone
        listing.purchased_at = timezone.now()
        listing.save()
        
        messages.success(request, f'Account purchased successfully! Please wait for support to send you the login details. Check "My Purchases" for updates.')
        return redirect('my_purchases')
    
    context = {
        **get_wallet_context(request.user),
        'listing': listing,
    }
    return render(request, 'buy_account.html', context)


@login_required
def my_purchases(request):
    """View user's purchased accounts"""
    purchases = SocialAccountPurchase.objects.filter(user=request.user)
    
    context = {
        **get_wallet_context(request.user),
        'purchases': purchases,
    }
    return render(request, 'my_purchases.html', context)
