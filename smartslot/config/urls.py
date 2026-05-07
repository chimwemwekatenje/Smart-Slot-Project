from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import HomeView
from apps.core.views import OrganisationAdminDashboardView, SuperAdminAnalysisView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('resources/', include('apps.resources.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('payments/', include('apps.payments.urls')),
    path('dashboard/', OrganisationAdminDashboardView.as_view(), name='org_admin_dashboard'),
    path('analysis/', SuperAdminAnalysisView.as_view(), name='super_admin_analysis'),
    path('', HomeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
