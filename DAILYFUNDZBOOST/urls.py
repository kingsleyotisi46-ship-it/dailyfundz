"""
URL configuration for DAILYFUNDZBOOST project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from social import template_views
import json

# Custom admin views
def admin_analytics(request):
    from django.contrib.auth.models import User
    from social.models import Order, Deposit, Service
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    last_7_days = today - timedelta(days=7)
    
    context = {
        'title': 'Analytics Dashboard',
        'total_users': User.objects.count(),
        'new_users_7d': User.objects.filter(date_joined__date__gte=last_7_days).count(),
        'total_orders': Order.objects.count(),
        'orders_7d': Order.objects.filter(created_at__date__gte=last_7_days).count(),
        'completed_orders': Order.objects.filter(status='completed').count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'total_revenue': Deposit.objects.filter(status='approved').aggregate(total=Sum('amount'))['total'] or 0,
        'revenue_7d': Deposit.objects.filter(status='approved', created_at__date__gte=last_7_days).aggregate(total=Sum('amount'))['total'] or 0,
        'pending_deposits': Deposit.objects.filter(status='pending').count(),
        'pending_amount': Deposit.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0,
        'chart_labels': [(last_7_days + timedelta(days=i)).strftime('%b %d') for i in range(8)],
        'chart_data': [Order.objects.filter(created_at__date=last_7_days + timedelta(days=i)).count() for i in range(8)],
        'top_services': Service.objects.annotate(order_count=Count('order')).order_by('-order_count')[:5],
    }
    return render(request, 'admin/analytics.html', context)

def admin_api_health(request):
    import requests
    
    apis = []
    
    # JAP API
    jap_status = {'name': 'JustAnotherPanel (SMM)', 'status': 'unknown', 'message': ''}
    try:
        jap_url = getattr(settings, 'SMM_PROVIDER_URL', '')
        jap_key = getattr(settings, 'SMM_PROVIDER_KEY', '')
        if jap_url and jap_key:
            resp = requests.post(jap_url, data={'key': jap_key, 'action': 'balance'}, timeout=10)
            data = resp.json()
            if 'balance' in data:
                jap_status = {'name': 'JustAnotherPanel (SMM)', 'status': 'healthy', 'message': f"Balance: ${data['balance']}"}
            else:
                jap_status = {'name': 'JustAnotherPanel (SMM)', 'status': 'error', 'message': str(data.get('error', 'Unknown'))}
        else:
            jap_status = {'name': 'JustAnotherPanel (SMM)', 'status': 'not_configured', 'message': 'API credentials not set'}
    except Exception as e:
        jap_status = {'name': 'JustAnotherPanel (SMM)', 'status': 'error', 'message': str(e)}
    apis.append(jap_status)
    
    # GrizzlySMS
    grizzly_status = {'name': 'GrizzlySMS (Virtual Numbers)', 'status': 'unknown', 'message': ''}
    try:
        grizzly_key = getattr(settings, 'GRIZZLY_API_KEY', '')
        if grizzly_key:
            resp = requests.get('https://api.grizzlysms.com/stubs/handler_api.php', 
                              params={'api_key': grizzly_key, 'action': 'getBalance'}, timeout=10)
            if 'ACCESS_BALANCE' in resp.text:
                balance = resp.text.split(':')[1] if ':' in resp.text else resp.text
                grizzly_status = {'name': 'GrizzlySMS (Virtual Numbers)', 'status': 'healthy', 'message': f"Balance: ${balance}"}
            else:
                grizzly_status = {'name': 'GrizzlySMS (Virtual Numbers)', 'status': 'error', 'message': resp.text}
        else:
            grizzly_status = {'name': 'GrizzlySMS (Virtual Numbers)', 'status': 'not_configured', 'message': 'API key not set'}
    except Exception as e:
        grizzly_status = {'name': 'GrizzlySMS (Virtual Numbers)', 'status': 'error', 'message': str(e)}
    apis.append(grizzly_status)
    
    # Database
    apis.append({'name': 'Database', 'status': 'healthy', 'message': 'Connected'})
    
    return render(request, 'admin/api_health.html', {'title': 'API Health Check', 'apis': apis})


@staff_member_required
def admin_profit_report(request):
    """Profit and earnings report for admin"""
    from social.models import Order, Service, Deposit, Transaction
    from django.db.models import Sum, F, DecimalField
    from django.db.models.functions import Coalesce
    from decimal import Decimal
    
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Calculate profits from markup
    # Provider cost vs what user paid
    orders = Order.objects.filter(status='completed').select_related('service')
    
    total_revenue = Decimal('0')
    total_cost = Decimal('0')
    
    for order in orders:
        total_revenue += order.price
        if order.service.provider_price:
            # Calculate provider cost for this order
            provider_cost = (order.service.provider_price / 1000) * order.quantity
            total_cost += provider_cost
    
    total_profit = total_revenue - total_cost
    
    # Last 30 days
    orders_30d = Order.objects.filter(status='completed', created_at__date__gte=last_30_days).select_related('service')
    revenue_30d = Decimal('0')
    cost_30d = Decimal('0')
    
    for order in orders_30d:
        revenue_30d += order.price
        if order.service.provider_price:
            cost_30d += (order.service.provider_price / 1000) * order.quantity
    
    profit_30d = revenue_30d - cost_30d
    
    # Last 7 days
    orders_7d = Order.objects.filter(status='completed', created_at__date__gte=last_7_days).select_related('service')
    revenue_7d = Decimal('0')
    cost_7d = Decimal('0')
    
    for order in orders_7d:
        revenue_7d += order.price
        if order.service.provider_price:
            cost_7d += (order.service.provider_price / 1000) * order.quantity
    
    profit_7d = revenue_7d - cost_7d
    
    # Top profitable services
    profitable_services = []
    for service in Service.objects.filter(provider_price__gt=0):
        service_orders = Order.objects.filter(service=service, status='completed')
        if service_orders.exists():
            service_revenue = sum(o.price for o in service_orders)
            service_cost = sum((service.provider_price / 1000) * o.quantity for o in service_orders)
            service_profit = service_revenue - service_cost
            profitable_services.append({
                'service': service,
                'orders': service_orders.count(),
                'revenue': service_revenue,
                'cost': service_cost,
                'profit': service_profit,
                'margin': (service_profit / service_revenue * 100) if service_revenue > 0 else 0
            })
    
    profitable_services.sort(key=lambda x: x['profit'], reverse=True)
    
    # Deposits summary
    total_deposits = Deposit.objects.filter(status='approved').aggregate(
        total=Coalesce(Sum('amount'), Decimal('0'))
    )['total']
    
    deposits_30d = Deposit.objects.filter(
        status='approved', 
        created_at__date__gte=last_30_days
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']
    
    context = {
        'title': 'Profit Report',
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profit_margin': (total_profit / total_revenue * 100) if total_revenue > 0 else 0,
        'revenue_30d': revenue_30d,
        'cost_30d': cost_30d,
        'profit_30d': profit_30d,
        'revenue_7d': revenue_7d,
        'cost_7d': cost_7d,
        'profit_7d': profit_7d,
        'total_deposits': total_deposits,
        'deposits_30d': deposits_30d,
        'profitable_services': profitable_services[:10],
        'total_orders': Order.objects.filter(status='completed').count(),
        'orders_30d': orders_30d.count(),
        'orders_7d': orders_7d.count(),
    }
    return render(request, 'admin/profit_report.html', context)


@staff_member_required
def admin_shell(request):
    """Admin shell interface"""
    return render(request, 'admin/shell.html', {'title': 'Admin Shell'})


@csrf_protect
@staff_member_required
def admin_shell_execute(request):
    """Execute shell commands - ADMIN ONLY"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Superuser access required'})
    
    try:
        data = json.loads(request.body)
        command = data.get('command', '').strip()
        mode = data.get('mode', 'django')
        
        if not command:
            return JsonResponse({'success': False, 'error': 'No command provided'})
        
        # Execute based on mode
        if mode == 'django':
            output = execute_django_command(command)
        elif mode == 'python':
            output = execute_python_code(command)
        elif mode == 'sql':
            output = execute_sql_query(command)
        elif mode == 'system':
            output = execute_system_info(command)
        else:
            output = execute_quick_command(command)
        
        return JsonResponse({'success': True, 'output': output})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def execute_django_command(command):
    """Execute Django management commands"""
    from django.core.management import call_command
    from io import StringIO
    
    parts = command.split()
    cmd_name = parts[0]
    args = parts[1:]
    
    allowed_commands = [
        'migrate', 'makemigrations', 'showmigrations', 'collectstatic',
        'sync_services', 'check', 'inspectdb', 'clearsessions'
    ]
    
    if cmd_name not in allowed_commands:
        return f"Command '{cmd_name}' not allowed. Allowed: {', '.join(allowed_commands)}"
    
    out = StringIO()
    err = StringIO()
    
    try:
        kwargs = {}
        positional = []
        for arg in args:
            if arg.startswith('--'):
                if '=' in arg:
                    key, val = arg[2:].split('=', 1)
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                    kwargs[key.replace('-', '_')] = val
                else:
                    kwargs[arg[2:].replace('-', '_')] = True
            else:
                positional.append(arg)
        
        call_command(cmd_name, *positional, stdout=out, stderr=err, **kwargs)
        
        output = out.getvalue()
        errors = err.getvalue()
        
        if errors:
            output += f"\n{errors}"
        
        return output if output else "Command executed successfully"
        
    except Exception as e:
        return f"Error: {str(e)}"


def execute_python_code(code):
    """Execute Python/Django ORM code"""
    from django.contrib.auth.models import User
    from social.models import (
        Profile, Post, Comment, Message, Report,
        Wallet, Transaction, Platform, ServiceCategory, 
        Service, Order, Deposit, VirtualNumberOrder,
        Referral, ReferralEarning
    )
    from django.db.models import Sum, Count, Avg, Max, Min, F, Q
    from decimal import Decimal
    from datetime import datetime, timedelta
    import io
    import sys
    
    local_vars = {
        'User': User, 'Profile': Profile, 'Post': Post, 'Comment': Comment,
        'Message': Message, 'Report': Report, 'Wallet': Wallet,
        'Transaction': Transaction, 'Platform': Platform,
        'ServiceCategory': ServiceCategory, 'Service': Service,
        'Order': Order, 'Deposit': Deposit, 'VirtualNumberOrder': VirtualNumberOrder,
        'Referral': Referral, 'ReferralEarning': ReferralEarning,
        'Sum': Sum, 'Count': Count, 'Avg': Avg, 'Max': Max, 'Min': Min, 'F': F, 'Q': Q,
        'Decimal': Decimal, 'datetime': datetime, 'timedelta': timedelta,
    }
    
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    try:
        try:
            result = eval(code, {"__builtins__": {}}, local_vars)
            sys.stdout = old_stdout
            
            if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                items = list(result)[:50]
                if items:
                    output_lines = [f"Results ({len(items)} items):"]
                    for i, item in enumerate(items, 1):
                        output_lines.append(f"  {i}. {item}")
                    return '\n'.join(output_lines)
                return "Empty QuerySet"
            
            return str(result)
            
        except SyntaxError:
            exec(code, {"__builtins__": {'print': print, 'len': len, 'str': str, 'int': int, 'float': float, 'list': list, 'dict': dict, 'range': range}}, local_vars)
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            return output if output else "Executed successfully"
            
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {str(e)}"


def execute_sql_query(query):
    """Execute raw SQL queries"""
    from django.db import connection
    
    query = query.strip()
    
    dangerous = ['DROP DATABASE', 'DROP TABLE', 'TRUNCATE', 'ALTER TABLE']
    for kw in dangerous:
        if kw.upper() in query.upper():
            return f"Blocked: {kw} not allowed"
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()[:100]
                
                if not rows:
                    return "No results"
                
                output_lines = [' | '.join(columns)]
                output_lines.append('-' * len(output_lines[0]))
                
                for row in rows:
                    output_lines.append(' | '.join(str(val)[:50] for val in row))
                
                output_lines.append(f"\n({len(rows)} rows)")
                return '\n'.join(output_lines)
            else:
                return f"Query executed. Rows affected: {cursor.rowcount}"
                
    except Exception as e:
        return f"SQL Error: {str(e)}"


def execute_system_info(command):
    """Get system information"""
    import platform
    from django.db import connection
    
    if command in ['info', 'system', 'sysinfo']:
        return f"""
System Information:
==================
OS: {platform.system()} {platform.release()}
Python: {platform.python_version()}
Django: {__import__('django').__version__}
Database: {connection.vendor}
Debug Mode: {settings.DEBUG}
"""
    
    return "Unknown command. Try: info, sysinfo"


def execute_quick_command(command):
    """Execute quick helper commands with natural language support"""
    from django.contrib.auth.models import User
    from social.models import Wallet, Order, Deposit, Service, Transaction, SupportTicket
    from django.db.models import Sum
    from decimal import Decimal, InvalidOperation
    from datetime import datetime, timedelta
    import requests
    import re
    
    try:
        original_command = command
        command_lower = command.lower().strip()
        parts = command_lower.split()
        cmd = parts[0] if parts else ''
        
        # Help command - check first
        if cmd == 'help' or command_lower == 'help':
            return """
📚 Admin Shell - Natural Language Commands
═══════════════════════════════════════════════════════════

💰 BALANCE COMMANDS:
  "add 5000 naira to john"     - Add NGN to user
  "give john $50"              - Add USD to user
  
📋 DEPOSIT COMMANDS:
  "show pending deposits"      - List pending deposits
  "approve deposit 123"        - Approve a deposit
  "reject deposit 123"         - Reject a deposit
  
📦 ORDER COMMANDS:
  "show orders"                - List recent orders
  "refund order 123"           - Cancel and refund order
  
👥 USER COMMANDS:
  "show users"                 - List recent users
  "ban user john"              - Disable user account
  "unban john"                 - Re-enable user
  
📱 SERVICE & PRICING COMMANDS:
  "show services"              - List all active services
  "show instagram services"    - List Instagram services only
  "show api services"          - Fetch services from JustAnotherPanel API
  "set price service 123 to 5" - Set service #123 price to $5/1K
  "set markup to 60"           - Set 60% markup on all services
  "syncservices"               - Import services from API
  "checkbalance"               - Check API provider balance
  
🎫 SUPPORT:
  "show tickets"               - List open tickets
  
📊 OVERVIEW:
  "stats" or "dashboard"       - Show system summary

═══════════════════════════════════════════════════════════
"""
        
        # ===== SHOW COMMANDS =====
        
        # "show stats" or "statistics" or "dashboard"
        if any(x in command_lower for x in ['stat', 'dashboard', 'overview', 'summary']):
            try:
                pending_deposits = Deposit.objects.filter(status='pending').count()
                pending_amount = Deposit.objects.filter(status='pending').aggregate(
                    total=Sum('amount'))['total'] or 0
                return f"""
📊 Dashboard Summary
═══════════════════════════════════════
👥 Users: {User.objects.count()} total
📦 Orders: {Order.objects.count()} total, {Order.objects.filter(status='pending').count()} pending
💰 Pending Deposits: {pending_deposits} (₦{pending_amount:,.0f})
🛠️ Active Services: {Service.objects.filter(is_active=True).count()}
🎫 Open Tickets: {SupportTicket.objects.filter(status__in=['open', 'in_progress']).count()}
═══════════════════════════════════════
"""
            except Exception as e:
                return f"❌ Error loading stats: {str(e)}"
        
        # "show pending deposits" or "list deposits"
        if any(x in command_lower for x in ['pending deposit', 'show deposit', 'list deposit', 'view deposit']):
            try:
                deposits = Deposit.objects.filter(status='pending').order_by('-created_at')[:10]
                if not deposits:
                    return "✅ No pending deposits"
                lines = ["📋 Pending Deposits:"]
                lines.append("-" * 60)
                for d in deposits:
                    lines.append(f"  #{d.id} | {d.user.username} | ₦{d.amount:,.0f} | {d.created_at.strftime('%b %d %H:%M')}")
                lines.append("-" * 60)
                lines.append(f"\n💡 To approve: approve deposit <id>")
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error loading deposits: {str(e)}"
        
        # "show orders" or "list recent orders"
        if any(x in command_lower for x in ['show order', 'list order', 'recent order', 'view order']):
            try:
                orders = Order.objects.select_related('user', 'service').order_by('-created_at')[:10]
                if not orders:
                    return "✅ No orders found"
                lines = ["📦 Recent Orders:"]
                lines.append("-" * 70)
                for o in orders:
                    status_icon = {'completed': '✅', 'pending': '⏳', 'processing': '🔄', 'cancelled': '❌', 'refunded': '💸'}.get(o.status, '❓')
                    service_name = o.service.name[:25] if o.service else 'Unknown'
                    lines.append(f"  #{o.id} | {o.user.username} | {service_name} | ${o.price} {status_icon}")
                lines.append("-" * 70)
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error loading orders: {str(e)}"
        
        # "show users" or "list users"
        if any(x in command_lower for x in ['show user', 'list user', 'recent user', 'view user']):
            try:
                users = User.objects.order_by('-date_joined')[:10]
                if not users:
                    return "✅ No users found"
                lines = ["👥 Recent Users:"]
                lines.append("-" * 60)
                for u in users:
                    try:
                        wallet = Wallet.objects.get(user=u)
                        balance = f"₦{wallet.balance_ngn:,.0f}"
                    except Wallet.DoesNotExist:
                        balance = "No wallet"
                    status = "🟢" if u.is_active else "🔴"
                    lines.append(f"  {status} {u.username} | {u.email or 'No email'} | {balance}")
                lines.append("-" * 60)
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error loading users: {str(e)}"
        
        # "show tickets" or "pending tickets"
        if any(x in command_lower for x in ['show ticket', 'list ticket', 'pending ticket', 'support ticket']):
            try:
                tickets = SupportTicket.objects.filter(status__in=['open', 'in_progress']).order_by('-created_at')[:10]
                if not tickets:
                    return "✅ No open support tickets"
                lines = ["🎫 Open Support Tickets:"]
                lines.append("-" * 60)
                for t in tickets:
                    lines.append(f"  #{t.id} | {t.user.username} | {t.subject[:30]} | {t.get_status_display()}")
                lines.append("-" * 60)
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error loading tickets: {str(e)}"
        
        # "show services" or "list services"
        if any(x in command_lower for x in ['show service', 'list service', 'view service', 'active service']):
            try:
                services = Service.objects.filter(is_active=True).select_related('platform')[:20]
                if not services:
                    return "❌ No active services found"
                lines = ["📱 Active Services (first 20):"]
                lines.append("-" * 70)
                for s in services:
                    platform_name = s.platform.name[:10] if s.platform else 'Unknown'
                    lines.append(f"  #{s.id} | {platform_name:10} | {s.name[:30]:30} | ${s.price_per_1000:.2f}/1K")
                lines.append("-" * 70)
                lines.append(f"Total: {Service.objects.filter(is_active=True).count()} active services")
                lines.append("\n💡 To edit price: set price service <id> to <amount>")
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error loading services: {str(e)}"
        
        # "show api services" - get from JustAnotherPanel
        if any(x in command_lower for x in ['api service', 'fetch service', 'provider service', 'jap service']):
            try:
                from social.smm_provider import smm_provider
                if not smm_provider.is_configured():
                    return "❌ SMM Provider API not configured. Set SMM_PROVIDER_URL and SMM_PROVIDER_KEY in environment."
                
                result = smm_provider.get_services()
                if isinstance(result, dict) and 'error' in result:
                    return f"❌ API Error: {result['error']}"
                
                if not result:
                    return "❌ No services returned from API"
                
                lines = ["🌐 Services from JustAnotherPanel API:"]
                lines.append("-" * 80)
                
                count = 0
                for svc in result[:25]:
                    svc_id = str(svc.get('service', ''))[:6]
                    category = str(svc.get('category', ''))[:20]
                    name = str(svc.get('name', ''))[:30]
                    rate = f"${svc.get('rate', 0)}"
                    lines.append(f"  {svc_id:6} | {category:20} | {name:30} | {rate}")
                    count += 1
                
                lines.append("-" * 80)
                lines.append(f"Showing {count} of {len(result)} services")
                lines.append("\n💡 Use 'syncservices' to import these to your database")
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error fetching API services: {str(e)}"
        
        # "show instagram services" or platform-specific
        platform_search = re.search(r'show\s+(instagram|tiktok|facebook|youtube|twitter|telegram|spotify)\s*service', command_lower)
        if platform_search:
            try:
                platform_name = platform_search.group(1).title()
                services = Service.objects.filter(
                    is_active=True, 
                    platform__name__icontains=platform_name
                ).select_related('platform')[:15]
                if not services:
                    return f"❌ No {platform_name} services found"
                lines = [f"📱 {platform_name} Services:"]
                lines.append("-" * 70)
                for s in services:
                    lines.append(f"  #{s.id} | {s.name[:40]:40} | ${s.price_per_1000:.2f}/1K")
                lines.append("-" * 70)
                lines.append(f"\n💡 To edit price: set price service <id> to <amount>")
                return '\n'.join(lines)
            except Exception as e:
                return f"❌ Error loading {platform_name} services: {str(e)}"
        
        # ===== ACTION COMMANDS =====
        
        # "approve deposit 5" or "approve deposit #5"
        approve_match = re.search(r'(?:approve|accept|confirm)\s+(?:deposit|payment)?\s*#?\s*(\d+)', command_lower)
        if approve_match:
            deposit_id = int(approve_match.group(1))
            try:
                deposit = Deposit.objects.select_related('user').get(id=deposit_id)
                if deposit.status == 'approved':
                    return f"⚠️ Deposit #{deposit_id} is already approved"
                if deposit.status == 'rejected':
                    return f"⚠️ Deposit #{deposit_id} was rejected. Cannot approve."
                
                # Update deposit status
                deposit.status = 'approved'
                deposit.save()
                
                # Credit wallet
                wallet, created = Wallet.objects.get_or_create(user=deposit.user)
                if deposit.currency == 'USD':
                    wallet.balance_usd += deposit.amount
                else:
                    wallet.balance_ngn += deposit.amount
                wallet.save()
                
                # Log transaction
                Transaction.objects.create(
                    wallet=wallet, 
                    transaction_type='deposit', 
                    amount=deposit.amount,
                    currency=deposit.currency or 'NGN', 
                    description=f'Deposit #{deposit_id} approved'
                )
                
                currency_symbol = '$' if deposit.currency == 'USD' else '₦'
                return f"✅ Approved deposit #{deposit_id}\n   {currency_symbol}{deposit.amount:,.0f} added to {deposit.user.username}'s wallet"
            except Deposit.DoesNotExist:
                return f"❌ Deposit #{deposit_id} not found"
            except Exception as e:
                return f"❌ Error approving deposit: {str(e)}"
        
        # "reject deposit 5"
        reject_match = re.search(r'(?:reject|decline|deny)\s+(?:deposit|payment)?\s*#?\s*(\d+)', command_lower)
        if reject_match:
            deposit_id = int(reject_match.group(1))
            try:
                deposit = Deposit.objects.get(id=deposit_id)
                if deposit.status != 'pending':
                    return f"⚠️ Deposit #{deposit_id} is already {deposit.status}"
                deposit.status = 'rejected'
                deposit.save()
                return f"✅ Rejected deposit #{deposit_id}"
            except Deposit.DoesNotExist:
                return f"❌ Deposit #{deposit_id} not found"
            except Exception as e:
                return f"❌ Error rejecting deposit: {str(e)}"
        
        # "add 5000 naira to john" - NGN balance
        add_ngn_match = re.search(r'(?:add|give|credit)\s+(?:₦|ngn|naira)?\s*(\d+(?:\.\d+)?)\s*(?:₦|ngn|naira)\s*(?:to|for)?\s*(\w+)', command_lower)
        if add_ngn_match:
            try:
                amount = Decimal(add_ngn_match.group(1))
                username = add_ngn_match.group(2)
                user = User.objects.get(username__iexact=username)
                wallet, _ = Wallet.objects.get_or_create(user=user)
                wallet.balance_ngn += amount
                wallet.save()
                Transaction.objects.create(
                    wallet=wallet, transaction_type='bonus', amount=amount,
                    currency='NGN', description='Admin credit via shell'
                )
                return f"✅ Added ₦{amount:,.0f} to {user.username}\n   New balance: ₦{wallet.balance_ngn:,.0f}"
            except User.DoesNotExist:
                return f"❌ User '{username}' not found"
            except InvalidOperation:
                return f"❌ Invalid amount"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # "give john $50" or "add $50 to john" - USD balance
        add_usd_match = re.search(r'(?:add|give|credit)\s+(?:\$|usd)?\s*(\d+(?:\.\d+)?)\s*(?:\$|usd|dollars?)?\s*(?:to|for)?\s*(\w+)', command_lower)
        if add_usd_match and '$' in command_lower or 'usd' in command_lower or 'dollar' in command_lower:
            try:
                amount = Decimal(add_usd_match.group(1))
                username = add_usd_match.group(2)
                user = User.objects.get(username__iexact=username)
                wallet, _ = Wallet.objects.get_or_create(user=user)
                wallet.balance_usd += amount
                wallet.save()
                Transaction.objects.create(
                    wallet=wallet, transaction_type='bonus', amount=amount,
                    currency='USD', description='Admin credit via shell'
                )
                return f"✅ Added ${amount:.2f} to {user.username}\n   New balance: ${wallet.balance_usd:.2f}"
            except User.DoesNotExist:
                return f"❌ User '{username}' not found"
            except InvalidOperation:
                return f"❌ Invalid amount"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # "ban user john" or "disable john"
        ban_match = re.search(r'(?:ban|disable|deactivate|block)\s+(?:user)?\s*(\w+)', command_lower)
        if ban_match:
            username = ban_match.group(1)
            if username in ['user', 'the']:  # Skip common words
                return f"❌ Please specify a username. Example: ban user john"
            try:
                user = User.objects.get(username__iexact=username)
                if user.is_superuser:
                    return f"❌ Cannot ban superuser '{username}'"
                if not user.is_active:
                    return f"⚠️ User '{username}' is already banned"
                user.is_active = False
                user.save()
                return f"✅ Banned user '{username}'"
            except User.DoesNotExist:
                return f"❌ User '{username}' not found"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # "unban john" or "enable john"
        unban_match = re.search(r'(?:unban|enable|activate|unblock)\s+(?:user)?\s*(\w+)', command_lower)
        if unban_match:
            username = unban_match.group(1)
            if username in ['user', 'the']:
                return f"❌ Please specify a username. Example: unban john"
            try:
                user = User.objects.get(username__iexact=username)
                if user.is_active:
                    return f"⚠️ User '{username}' is already active"
                user.is_active = True
                user.save()
                return f"✅ Unbanned user '{username}'"
            except User.DoesNotExist:
                return f"❌ User '{username}' not found"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # "reset password john to newpass123" or "set password for john newpass"
        password_match = re.search(r'(?:reset|set|change)\s+password\s+(?:for)?\s*(\w+)\s+(?:to)?\s*(\S+)', command_lower)
        if password_match:
            username = password_match.group(1)
            # Get the actual password from original command to preserve case
            new_password = re.search(r'(?:to)?\s*(\S+)\s*$', original_command).group(1)
            if username in ['for', 'user', 'the']:
                return f"❌ Please specify: reset password <username> to <newpassword>"
            try:
                user = User.objects.get(username__iexact=username)
                user.set_password(new_password)
                user.save()
                return f"✅ Password reset for '{user.username}'\n   New password: {new_password}"
            except User.DoesNotExist:
                return f"❌ User '{username}' not found"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # "set markup to 60" or "change markup 60%"
        markup_match = re.search(r'(?:set|change|update)\s+markup\s+(?:to)?\s*(\d+)', command_lower)
        if markup_match:
            try:
                markup = Decimal(markup_match.group(1))
                if markup < 0 or markup > 500:
                    return f"❌ Markup must be between 0% and 500%"
                count = Service.objects.filter(provider_price__gt=0).update(markup_percentage=markup)
                # Recalculate prices
                for service in Service.objects.filter(provider_price__gt=0):
                    service.save()
                return f"✅ Set {markup}% markup for {count} services\n   Prices have been recalculated"
            except Exception as e:
                return f"❌ Error setting markup: {str(e)}"
        
        # "set price service 123 to 5.50"
        price_match = re.search(r'(?:set|change|update)\s+price\s+(?:service|for)?\s*#?\s*(\d+)\s+(?:to)?\s*\$?\s*(\d+(?:\.\d+)?)', command_lower)
        if price_match:
            try:
                service_id = int(price_match.group(1))
                new_price = Decimal(price_match.group(2))
                if new_price < 0:
                    return f"❌ Price cannot be negative"
                service = Service.objects.get(id=service_id)
                old_price = service.price_per_1000
                service.price_per_1000 = new_price
                service.save()
                return f"✅ Updated service #{service_id}\n   {service.name[:35]}\n   ${old_price}/1K → ${new_price}/1K"
            except Service.DoesNotExist:
                return f"❌ Service #{service_id} not found"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # "refund order 123"
        refund_match = re.search(r'(?:refund|cancel)\s+order\s*#?\s*(\d+)', command_lower)
        if refund_match:
            order_id = int(refund_match.group(1))
            try:
                order = Order.objects.select_related('user', 'service').get(id=order_id)
                if order.status in ['cancelled', 'refunded']:
                    return f"⚠️ Order #{order_id} is already {order.status}"
                
                wallet, _ = Wallet.objects.get_or_create(user=order.user)
                wallet.balance_usd += order.price
                wallet.save()
                
                order.status = 'refunded'
                order.save()
                
                Transaction.objects.create(
                    wallet=wallet, transaction_type='refund', amount=order.price,
                    currency='USD', description=f'Order #{order_id} refunded'
                )
                return f"✅ Refunded order #{order_id}\n   ${order.price} returned to {order.user.username}"
            except Order.DoesNotExist:
                return f"❌ Order #{order_id} not found"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # ===== QUICK COMMANDS =====
        
        if cmd == 'syncservices':
            try:
                from django.core.management import call_command
                from io import StringIO
                out = StringIO()
                call_command('sync_services', limit=50, markup=50, stdout=out)
                result = out.getvalue()
                return result if result else "✅ Services synced successfully"
            except Exception as e:
                return f"❌ Error syncing services: {str(e)}"
        
        if cmd == 'checkbalance':
            try:
                jap_url = getattr(settings, 'SMM_PROVIDER_URL', '')
                jap_key = getattr(settings, 'SMM_PROVIDER_KEY', '')
                if not jap_url or not jap_key:
                    return "⚠️ API not configured. Set SMM_PROVIDER_URL and SMM_PROVIDER_KEY."
                resp = requests.post(jap_url, data={'key': jap_key, 'action': 'balance'}, timeout=10)
                data = resp.json()
                if 'balance' in data:
                    return f"💰 JustAnotherPanel Balance: ${data['balance']}"
                return f"❌ API Error: {data.get('error', 'Unknown error')}"
            except requests.Timeout:
                return "❌ API request timed out"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # Legacy shorthand commands
        if cmd == 'stats':
            return execute_quick_command('show stats')
        if cmd == 'showusers':
            return execute_quick_command('show users')
        if cmd == 'showorders':
            return execute_quick_command('show orders')
        if cmd == 'showdeposits':
            return execute_quick_command('show deposits')
        
        # Unknown command
        return f"❓ I don't understand: '{original_command}'\n\n💡 Try these:\n• show deposits\n• approve deposit 123\n• add 5000 naira to john\n• show stats\n\nType 'help' for all commands."
        
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}\n\nPlease try again or type 'help' for available commands."


urlpatterns = [
    # Admin with custom views
    path('admin/shell/', admin_shell, name='admin_shell'),
    path('admin/shell/execute/', admin_shell_execute, name='admin_shell_execute'),
    path('admin/analytics/', admin_analytics, name='admin_analytics'),
    path('admin/api-health/', admin_api_health, name='admin_api_health'),
    path('admin/profit-report/', admin_profit_report, name='admin_profit_report'),
    path('admin/', admin.site.urls),
    
    # API endpoints (for any remaining API calls)
    path('api/', include('social.urls')),
    
    # Template-based views
    path('', template_views.home, name='home'),
    path('login/', template_views.user_login, name='login'),
    path('register/', template_views.user_register, name='register'),
    path('logout/', template_views.user_logout, name='logout'),
    path('home/', template_views.main_panel, name='main_panel'),
    path('dashboard/', template_views.main_panel, name='dashboard'),  # Backward compatibility
    path('services/', template_views.services, name='services'),
    path('order/', template_views.place_order, name='place_order'),
    path('orders/', template_views.orders, name='orders'),
    path('order/<int:order_id>/cancel/', template_views.cancel_order, name='cancel_order'),
    path('add-funds/', template_views.add_funds, name='add_funds'),
    path('transactions/', template_views.transactions, name='transactions'),
    path('profile/', template_views.profile, name='profile'),
    path('virtual-numbers/', template_views.virtual_numbers, name='virtual_numbers'),
    path('referral/', template_views.referral, name='referral'),
    path('offline/', template_views.offline, name='offline'),
    
    # Social Account Marketplace
    path('accounts-market/', template_views.accounts_market, name='accounts_market'),
    path('accounts-market/<int:listing_id>/buy/', template_views.buy_account, name='buy_account'),
    path('my-purchases/', template_views.my_purchases, name='my_purchases'),
    
    # Password Reset
    path('forgot-password/', template_views.password_reset_request, name='password_reset'),
    path('reset-password/<uidb64>/<token>/', template_views.password_reset_confirm, name='password_reset_confirm'),
    path('change-password/', template_views.change_password, name='change_password'),
    
    # Support Tickets
    path('support/', template_views.support_tickets, name='support'),
    path('support/ticket/<int:ticket_id>/', template_views.support_ticket_detail, name='support_ticket_detail'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in production with whitenoise (already configured)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
