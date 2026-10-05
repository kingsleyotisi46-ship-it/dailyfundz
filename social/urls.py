from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .admin import provider_status_view
from .deposit_actions import deposit_action_view

router = DefaultRouter()
router.register(r'posts', views.PostViewSet)
router.register(r'orders', views.OrderViewSet, basename='orders')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', views.CurrentUserView.as_view(), name='current_user'),
    
    # Profile endpoints
    path('profile/', views.ProfileView.as_view(), name='my_profile'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/<str:username>/follow/', views.FollowUserView.as_view(), name='follow_user'),
    path('profile/<str:username>/posts/', views.UserPostsView.as_view(), name='user_posts'),
    
    # Feed
    path('feed/', views.FeedView.as_view(), name='feed'),
    
    # Reports
    path('reports/', views.ReportCreateView.as_view(), name='create_report'),
    
    # SMM Panel endpoints
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    path('wallet/add-funds/', views.AddFundsView.as_view(), name='add_funds'),
    path('wallet/transactions/', views.TransactionListView.as_view(), name='transactions'),
    
    # Payment & Deposits (OPay)
    path('payment/info/', views.PaymentInfoView.as_view(), name='payment_info'),
    path('deposits/', views.DepositListView.as_view(), name='deposit_list'),
    path('deposits/create/', views.DepositCreateView.as_view(), name='deposit_create'),
    path('deposits/<int:pk>/', views.DepositDetailView.as_view(), name='deposit_detail'),
    
    # Services
    path('platforms/', views.PlatformListView.as_view(), name='platforms'),
    path('categories/', views.ServiceCategoryListView.as_view(), name='categories'),
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('services/featured/', views.FeaturedServicesView.as_view(), name='featured_services'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    # Admin tools
    path('admin/provider-status/', provider_status_view, name='provider_status'),
    
    # Deposit action links from email
    path('deposits/<str:action>/<str:token>/', deposit_action_view, name='deposit_action'),
    
    # Router URLs (posts, orders CRUD)
    path('', include(router.urls)),
]
