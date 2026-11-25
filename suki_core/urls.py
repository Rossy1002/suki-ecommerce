from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from marketplace.views import (
    storefront_view, api_login_view, api_register_view, public_shops_api, currency_rates_api, UserProfileViewSet, ProductViewSet,
    WishlistViewSet, CartViewSet, OrderViewSet, ReviewViewSet, SupportViewSet
)

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'support', SupportViewSet, basename='support')

urlpatterns = [
    path('', storefront_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/login/', api_login_view, name='api-login'),
    path('api/register/', api_register_view, name='api-register'),
    path('api/shops/', public_shops_api, name='public-shops'),
    path('api/exchange-rates/', currency_rates_api, name='exchange-rates'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
