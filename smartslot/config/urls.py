from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.verification.views import PublicReceiptView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('resources/', include('apps.resources.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('api/', include('apps.api.urls')),
    path('api/verification/', include('apps.verification.urls')),
    # Public receipt page — scanned by anyone with the QR code
    path('receipt/<str:qr_token>/', PublicReceiptView.as_view(), name='public-receipt'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)