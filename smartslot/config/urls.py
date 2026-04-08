from django.contrib import admin
from django.urls import path, include
<<<<<<< HEAD
from apps.accounts.views import HomeView
=======
from django.conf import settings
from django.conf.urls.static import static
>>>>>>> 3866a6e38bb550f841754e8170fe0abcc3448923

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
<<<<<<< HEAD

    # 4. Homepage
    path('', HomeView.as_view(), name='home'),
]
=======
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> 3866a6e38bb550f841754e8170fe0abcc3448923
