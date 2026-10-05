from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import (
    Profile, Post, Comment, Message, Report,
    Wallet, Transaction, Platform, ServiceCategory, Service, Order, Deposit
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio', 'profile_picture', 'followers_count', 'following_count', 'is_following', 'created_at']

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.user.following.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.id).exists()
        return False


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        return user


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']
        read_only_fields = ['author']


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'image', 'created_at', 'updated_at', 
                  'likes_count', 'is_liked', 'comments', 'comments_count']
        read_only_fields = ['author']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_comments_count(self, obj):
        return obj.comments.count()


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'image']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'is_read', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'reporter', 'reported_user', 'reported_post', 'report_type', 
                  'description', 'status', 'created_at']
        read_only_fields = ['reporter', 'status']


# ============== SMM PANEL SERIALIZERS ==============

class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='balance_usd')
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='total_spent_usd')
    exchange_rate = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = [
            'id', 'balance_usd', 'balance_ngn', 'preferred_currency',
            'total_spent_usd', 'total_spent_ngn', 'exchange_rate',
            'balance', 'total_spent',  # Legacy fields
            'created_at', 'updated_at'
        ]
        read_only_fields = ['balance_usd', 'balance_ngn', 'total_spent_usd', 'total_spent_ngn']

    def get_exchange_rate(self, obj):
        return Wallet.EXCHANGE_RATE


class TransactionSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'currency', 'currency_symbol', 'description', 'reference_id', 'created_at']

    def get_currency_symbol(self, obj):
        return '₦' if obj.currency == 'NGN' else '$'


class DepositSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Deposit
        fields = [
            'id', 'amount', 'currency', 'currency_symbol', 'payment_screenshot',
            'status', 'status_display', 'admin_note', 'created_at', 'reviewed_at'
        ]
        read_only_fields = ['status', 'admin_note', 'reviewed_at']

    def get_currency_symbol(self, obj):
        return '₦' if obj.currency == 'NGN' else '$'


class DepositCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ['amount', 'currency', 'payment_screenshot']

    def validate_amount(self, value):
        if value < 100:
            raise serializers.ValidationError('Minimum deposit is 100')
        if value > 10000000:
            raise serializers.ValidationError('Maximum deposit is 10,000,000')
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Deposit.objects.create(**validated_data)


class PaymentInfoSerializer(serializers.Serializer):
    bank_name = serializers.CharField()
    account_number = serializers.CharField()
    account_name = serializers.CharField()
    exchange_rate = serializers.IntegerField()
    company_email = serializers.EmailField()
    whatsapp = serializers.CharField()


class PlatformSerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = Platform
        fields = ['id', 'name', 'icon', 'slug', 'services_count']

    def get_services_count(self, obj):
        return obj.services.filter(is_active=True).count()


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'slug', 'description']


class ServiceSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'platform', 'category', 'name', 'description',
            'price_per_1000', 'min_quantity', 'max_quantity',
            'average_time', 'quality', 'is_featured'
        ]


class ServiceListSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    platform_icon = serializers.CharField(source='platform.icon', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'platform_name', 'platform_icon', 'category_name',
            'name', 'description', 'price_per_1000', 'min_quantity',
            'max_quantity', 'average_time', 'quality', 'is_featured'
        ]


class OrderSerializer(serializers.ModelSerializer):
    service = ServiceListSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'service', 'link', 'quantity', 'price',
            'status', 'start_count', 'remains', 'created_at', 'completed_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['service', 'link', 'quantity']

    def validate(self, attrs):
        service = attrs['service']
        quantity = attrs['quantity']

        if not service.is_active:
            raise serializers.ValidationError({'service': 'This service is not available'})

        if quantity < service.min_quantity:
            raise serializers.ValidationError({
                'quantity': f'Minimum quantity is {service.min_quantity}'
            })

        if quantity > service.max_quantity:
            raise serializers.ValidationError({
                'quantity': f'Maximum quantity is {service.max_quantity}'
            })

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        service = validated_data['service']
        quantity = validated_data['quantity']
        price = service.calculate_price(quantity)

        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
            if not wallet.deduct_funds(price, 'USD'):
                raise serializers.ValidationError({
                    'balance': (
                        f'Insufficient balance. Need ${price:.2f}, '
                        f'have ${wallet.balance_usd:.2f}'
                    )
                })

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='purchase',
                amount=price,
                currency='USD',
                description=f'Order: {service.name} x {quantity}'
            )

            order = Order.objects.create(
                user=user,
                service=service,
                link=validated_data['link'],
                quantity=quantity,
                price=price,
                remains=quantity
            )

        # Submit to SMM provider (if configured)
        try:
            from .smm_provider import place_provider_order
            place_provider_order(order)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to submit to provider: {e}")

        return order
