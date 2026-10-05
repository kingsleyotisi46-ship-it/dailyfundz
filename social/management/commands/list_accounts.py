"""
Django management command to list all social account listings
Usage: python manage.py list_accounts
"""
from django.core.management.base import BaseCommand
from social.models import SocialAccountListing
from django.db.models import Count


class Command(BaseCommand):
    help = 'List all social media accounts for sale'

    def add_arguments(self, parser):
        parser.add_argument(
            '--platform',
            type=str,
            default=None,
            help='Filter by platform (facebook, instagram, tiktok, telegram)',
        )
        parser.add_argument(
            '--status',
            type=str,
            default=None,
            help='Filter by status (available, sold, reserved)',
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export to CSV file',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('📋 SOCIAL ACCOUNT LISTINGS'))
        self.stdout.write('='*80)
        
        # Base queryset
        queryset = SocialAccountListing.objects.all()
        
        # Apply filters
        if options.get('platform'):
            queryset = queryset.filter(platform__iexact=options['platform'])
            self.stdout.write(f"Filtered by platform: {options['platform']}")
        
        if options.get('status'):
            queryset = queryset.filter(status=options['status'])
            self.stdout.write(f"Filtered by status: {options['status']}")
        
        # Get statistics
        total = queryset.count()
        self.stdout.write(f"\n✅ Total listings: {total}\n")
        
        # Count by platform
        platforms = queryset.values('platform').annotate(count=Count('id')).order_by('-count')
        self.stdout.write(self.style.SUCCESS('📊 By Platform:'))
        for p in platforms:
            self.stdout.write(f"   • {p['platform']}: {p['count']} accounts")
        
        # Count by status
        statuses = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        self.stdout.write(self.style.SUCCESS('\n📊 By Status:'))
        for s in statuses:
            self.stdout.write(f"   • {s['status']}: {s['count']} accounts")
        
        # Show all listings
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.HTTP_INFO('📋 ALL LISTINGS:'))
        self.stdout.write('='*80)
        
        for listing in queryset.order_by('platform', '-price'):
            status_color = self.style.SUCCESS if listing.status == 'available' else self.style.WARNING
            self.stdout.write(
                f"ID: {listing.id:4d} | "
                f"{listing.platform:12s} | "
                f"₦{listing.price:8,.0f} | "
                f"{listing.account_type:20s} | "
                f"{status_color(listing.status)}"
            )
        
        self.stdout.write('='*80)
        
        # Export to CSV if requested
        if options.get('export'):
            import csv
            from datetime import datetime
            
            filename = f'account_listings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Platform', 'Account Type', 'Price (NGN)', 'Followers', 'Status', 'Created'])
                
                for listing in queryset:
                    writer.writerow([
                        listing.id,
                        listing.platform,
                        listing.account_type,
                        listing.price,
                        listing.followers,
                        listing.status,
                        listing.created_at.strftime('%Y-%m-%d %H:%M'),
                    ])
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Exported to: {filename}'))
