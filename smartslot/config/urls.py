from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('resources/', include('apps.resources.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('payments/', include('apps.payments.urls')),
    path('verify/', include('apps.verification.urls')),
    path('dashboard/', include('apps.core.dashboard_urls')),
    path('', HomeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
