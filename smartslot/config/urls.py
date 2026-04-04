from django.contrib import admin
from django.urls import path

from apps.accounts.views import HomeView
from apps.resources.views import ResourceListView
from apps.bookings.views import BookingListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('resources/', ResourceListView.as_view(), name='resource_list'),
    path('bookings/', BookingListView.as_view(), name='booking_list'),
]