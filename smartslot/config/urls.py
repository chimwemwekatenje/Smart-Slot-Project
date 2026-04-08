from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import HomeView

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # All auth URLs (login, logout, signup, password-reset) handled in accounts app
    path('accounts/', include('apps.accounts.urls')),

    # Other Apps
    path('resources/', include('apps.resources.urls')),
    path('bookings/', include('apps.bookings.urls')),

    # Homepage (must be last to avoid catching other URLs)
    path('', HomeView.as_view(), name='home'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)