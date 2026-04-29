from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import HomeView

# ── REST API imports ──────────────────────────────────────────────────────────
from apps.accounts.api_views import api_login, api_register, api_me
from apps.resources.api_views import api_resource_list, api_resource_detail
from apps.bookings.api_views import api_booking_list, api_booking_detail, api_booking_cancel
from rest_framework_simplejwt.views import TokenRefreshView

api_urlpatterns = [
    # Auth
    path('auth/login/',    api_login,    name='api-login'),
    path('auth/register/', api_register, name='api-register'),
    path('auth/me/',       api_me,       name='api-me'),
    path('auth/refresh/',  TokenRefreshView.as_view(), name='api-token-refresh'),

    # Resources
    path('resources/',       api_resource_list,   name='api-resource-list'),
    path('resources/<int:pk>/', api_resource_detail, name='api-resource-detail'),

    # Bookings
    path('bookings/',            api_booking_list,   name='api-booking-list'),
    path('bookings/<int:pk>/',   api_booking_detail, name='api-booking-detail'),
    path('bookings/<int:pk>/cancel/', api_booking_cancel, name='api-booking-cancel'),
]

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # REST API (consumed by Flutter app)
    path('api/', include((api_urlpatterns, 'api'))),

    # All auth URLs (login, logout, signup, password-reset) handled in accounts app
    path('accounts/', include('apps.accounts.urls')),

    # Other Apps
    path('resources/', include('apps.resources.urls')),
    path('bookings/',  include('apps.bookings.urls')),

    # Homepage (must be last to avoid catching other URLs)
    path('', HomeView.as_view(), name='home'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)