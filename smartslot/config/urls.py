from django.contrib import admin
from django.urls import path, include
from apps.accounts.views import HomeView

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # 1. Built-in Authentication URLs (must come first!)
    path('accounts/', include('django.contrib.auth.urls')),

    # 2. Custom Account URLs (registration, profile, dashboard)
    path('accounts/', include('apps.accounts.urls')),

    # 3. Other Apps
    path('resources/', include('apps.resources.urls')),
    path('bookings/', include('apps.bookings.urls')),

    # 4. Homepage
    path('', HomeView.as_view(), name='home'),
]