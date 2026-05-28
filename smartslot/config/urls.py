from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import HomeView
from apps.verification.views import PublicReceiptView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('resources/', include('apps.resources.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('payments/', include('apps.payments.urls')),
    path('verify/', include('apps.verification.urls')),
    path('dashboard/', include('apps.core.dashboard_urls')),
    path('api/', include('apps.api.urls')),
    path('api/verification/', include('apps.verification.urls')),
    # Public receipt page — scanned by anyone with the QR code
    path('receipt/<str:qr_token>/', PublicReceiptView.as_view(), name='public-receipt'),
    path('', HomeView.as_view(), name='home'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

