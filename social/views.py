from rest_framework import generics, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Profile, Post, Comment, Message, Report,
    Wallet, Transaction, Platform, ServiceCategory, Service, Order, Deposit
)
from .serializers import (
    UserSerializer, ProfileSerializer, RegisterSerializer,
    PostSerializer, PostCreateSerializer, CommentSerializer,
    MessageSerializer, ReportSerializer,
    WalletSerializer, TransactionSerializer, PlatformSerializer,
    ServiceCategorySerializer, ServiceSerializer, ServiceListSerializer,
    OrderSerializer, OrderCreateSerializer,
    DepositSerializer, DepositCreateSerializer, PaymentInfoSerializer
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'
    queryset = Profile.objects.all()


class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)
        if user_to_follow == request.user:
            return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile = user_to_follow.profile
        if profile.followers.filter(id=request.user.id).exists():
            profile.followers.remove(request.user)
            return Response({'status': 'unfollowed'})
        else:
            profile.followers.add(request.user)
            return Response({'status': 'followed'})


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            return Response({'status': 'unliked'})
        else:
            post.likes.add(request.user)
            return Response({'status': 'liked'})

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == 'GET':
            comments = post.comments.all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user, post=post)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        following_users = User.objects.filter(profile__followers=self.request.user)
        return Post.objects.filter(author__in=following_users) | Post.objects.filter(author=self.request.user)


class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)
        return Post.objects.filter(author=user)


class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ============== SMM PANEL VIEWS ==============

class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

    def patch(self, request):
        """Update wallet preferences (e.g., preferred_currency)"""
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        currency = request.data.get('preferred_currency')
        if currency in ['USD', 'NGN']:
            wallet.preferred_currency = currency
            wallet.save()
            serializer = WalletSerializer(wallet)
            return Response(serializer.data)
        return Response({'error': 'Invalid currency'}, status=status.HTTP_400_BAD_REQUEST)


class AddFundsView(APIView):
    """Disable legacy self-service wallet credits that bypass payment verification."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {
                'detail': (
                    'Direct wallet credits are disabled. Submit a deposit request '
                    'and wait for payment verification.'
                )
            },
            status=status.HTTP_410_GONE,
        )


class PaymentInfoView(APIView):
    """Get OPay bank payment details"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_info = Deposit.get_payment_info()
        serializer = PaymentInfoSerializer(payment_info)
        return Response(serializer.data)


class DepositCreateView(generics.CreateAPIView):
    """Create a new deposit request with payment screenshot"""
    serializer_class = DepositCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        return {'request': self.request}


class DepositListView(generics.ListAPIView):
    """List user's deposit history"""
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deposit.objects.filter(user=self.request.user)


class DepositDetailView(generics.RetrieveAPIView):
    """Get single deposit details"""
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deposit.objects.filter(user=self.request.user)


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return Transaction.objects.filter(wallet=wallet)


class PlatformListView(generics.ListAPIView):
    serializer_class = PlatformSerializer
    queryset = Platform.objects.filter(is_active=True)
    permission_classes = [AllowAny]


class ServiceCategoryListView(generics.ListAPIView):
    serializer_class = ServiceCategorySerializer
    queryset = ServiceCategory.objects.all()
    permission_classes = [AllowAny]


class ServiceListView(generics.ListAPIView):
    serializer_class = ServiceListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['platform__slug', 'category__slug', 'quality', 'is_featured']
    search_fields = ['name', 'description']

    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related('platform', 'category')


class ServiceDetailView(generics.RetrieveAPIView):
    serializer_class = ServiceSerializer
    queryset = Service.objects.filter(is_active=True)
    permission_classes = [AllowAny]


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('service__platform', 'service__category')

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        order = self.get_object()
        return Response({
            'id': order.id,
            'status': order.status,
            'start_count': order.start_count,
            'remains': order.remains
        })


class FeaturedServicesView(generics.ListAPIView):
    serializer_class = ServiceListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Service.objects.filter(is_active=True, is_featured=True)[:8]
