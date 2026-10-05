from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch
from rest_framework.test import APIClient
from .models import Deposit, Order, Platform, Service, ServiceCategory, Transaction, Wallet


class ServicesViewTests(TestCase):
    def test_homepage_uses_absolute_static_asset_urls(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/')

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(reverse('services'))

        self.assertRedirects(response, f'{reverse("login")}?next={reverse("services")}')

    def test_authenticated_user_can_render_services_page(self):
        user = User.objects.create_user(username='service-user', password='test-password')
        self.client.force_login(user)

        response = self.client.get(reverse('services'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services.html')
        self.assertIn('services', response.context)


class WalletAndDepositTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='customer', password='test-password')
        self.staff = User.objects.create_user(
            username='staff',
            password='test-password',
            is_staff=True,
        )

    def test_legacy_add_funds_endpoint_cannot_credit_wallet(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post('/api/wallet/add-funds/', {'amount': '1000'})

        self.assertEqual(response.status_code, 410)
        self.assertFalse(Wallet.objects.filter(user=self.user).exists())
        self.assertFalse(Transaction.objects.exists())

    def test_stale_wallet_instance_cannot_overspend(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.add_funds(Decimal('5.00'), 'USD')
        stale_copy = Wallet.objects.get(pk=wallet.pk)

        self.assertTrue(wallet.deduct_funds(Decimal('4.00'), 'USD'))
        self.assertFalse(stale_copy.deduct_funds(Decimal('4.00'), 'USD'))

        wallet.refresh_from_db()
        self.assertEqual(wallet.balance_usd, Decimal('1.00'))
        self.assertEqual(wallet.total_spent_usd, Decimal('4.00'))

    def test_api_order_debits_wallet_and_records_charge(self):
        service = self._create_service()
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.add_funds(Decimal('5.00'), 'USD')
        client = APIClient()
        client.force_authenticate(user=self.user)

        with patch('social.smm_provider.place_provider_order'):
            response = client.post('/api/orders/', {
                'service': service.pk,
                'link': 'https://example.com/post',
                'quantity': 1000,
            }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance_usd, Decimal('4.00'))
        self.assertEqual(Transaction.objects.get(wallet=wallet).amount, Decimal('1.00'))
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)

    def test_api_order_with_insufficient_balance_creates_no_order(self):
        service = self._create_service()
        client = APIClient()
        client.force_authenticate(user=self.user)

        with patch('social.smm_provider.place_provider_order'):
            response = client.post('/api/orders/', {
                'service': service.pk,
                'link': 'https://example.com/post',
                'quantity': 1000,
            }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.assertFalse(Transaction.objects.exists())

    def test_deposit_action_link_get_does_not_approve_deposit(self):
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            currency='NGN',
        )
        self.client.force_login(self.staff)

        response = self.client.get(self._action_url(deposit, 'approve'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/deposit_action_confirm.html')
        deposit.refresh_from_db()
        self.assertEqual(deposit.status, 'pending')
        self.assertFalse(Wallet.objects.filter(user=self.user).exists())

    def test_deposit_action_post_requires_csrf(self):
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            currency='NGN',
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        action_url = self._action_url(deposit, 'approve')
        confirmation = client.get(action_url)

        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual(
            client.post(action_url, {'admin_note': 'Payment verified'}).status_code,
            403,
        )
        token = confirmation.cookies['csrftoken'].value
        with patch('social.deposit_actions.send_deposit_approved_email'):
            response = client.post(
                action_url,
                {'admin_note': 'Payment verified', 'csrfmiddlewaretoken': token},
                HTTP_X_CSRFTOKEN=token,
            )

        self.assertEqual(response.status_code, 200)
        deposit.refresh_from_db()
        self.assertEqual(deposit.status, 'approved')

    def test_staff_post_approves_deposit_only_once(self):
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            currency='NGN',
        )
        self.client.force_login(self.staff)
        action_url = self._action_url(deposit, 'approve')

        with patch('social.deposit_actions.send_deposit_approved_email'):
            response = self.client.post(action_url, {'admin_note': 'Payment verified'})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Successfully approved')

            response = self.client.post(action_url, {'admin_note': 'Duplicate request'})

        self.assertEqual(response.status_code, 200)
        deposit.refresh_from_db()
        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(deposit.status, 'approved')
        self.assertEqual(deposit.reviewed_by, self.staff)
        self.assertEqual(wallet.balance_ngn, Decimal('1000.00'))
        self.assertEqual(Transaction.objects.filter(wallet=wallet).count(), 1)

    def test_stale_deposit_instance_cannot_credit_wallet_twice(self):
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            currency='NGN',
        )
        stale_copy = Deposit.objects.get(pk=deposit.pk)

        self.assertTrue(deposit.approve(self.staff, 'Verified'))
        self.assertFalse(stale_copy.approve(self.staff, 'Duplicate approval'))

        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance_ngn, Decimal('1000.00'))
        self.assertEqual(Transaction.objects.filter(wallet=wallet).count(), 1)

    def test_stale_order_instance_cannot_refund_twice(self):
        service = self._create_service()
        order = Order.objects.create(
            user=self.user,
            service=service,
            link='https://example.com/post',
            quantity=1000,
            price=Decimal('5.00'),
        )
        stale_copy = Order.objects.get(pk=order.pk)

        self.assertEqual(order.cancel(), (True, 'Order cancelled and refunded'))
        self.assertEqual(stale_copy.cancel(), (False, 'Order cannot be cancelled'))

        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance_usd, Decimal('5.00'))
        self.assertEqual(Transaction.objects.filter(wallet=wallet).count(), 1)

    @staticmethod
    def _create_service():
        platform = Platform.objects.create(name='Test', slug='test')
        category = ServiceCategory.objects.create(name='Test', slug='test')
        return Service.objects.create(
            platform=platform,
            category=category,
            name='Test service',
            price_per_1000=Decimal('1.00'),
            average_time='1 hour',
        )

    def test_non_staff_cannot_process_deposit_action(self):
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            currency='NGN',
        )
        self.client.force_login(self.user)

        response = self.client.post(self._action_url(deposit, 'approve'))

        self.assertEqual(response.status_code, 403)
        deposit.refresh_from_db()
        self.assertEqual(deposit.status, 'pending')
        self.assertFalse(Wallet.objects.filter(user=self.user).exists())

    @staticmethod
    def _action_url(deposit, action):
        return reverse(
            'deposit_action',
            kwargs={'action': action, 'token': deposit.generate_action_token()},
        )
