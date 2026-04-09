from django.urls import path
from .views import (
    RegisterView, LoginView,
    OrganisationListView,
    ResourceListView,
    MyBookingListView, BookingCreateView, BookingUpdateView,
    OrgResourceListView, OrgBookingListView,
    ResourceScheduleView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('organisations/', OrganisationListView.as_view(), name='api-organisations'),
    path('resources/', ResourceListView.as_view(), name='api-resources'),
    path('resources/<int:pk>/schedule/', ResourceScheduleView.as_view(), name='api-resource-schedule'),
    path('bookings/', BookingCreateView.as_view(), name='api-booking-create'),
    path('bookings/my/', MyBookingListView.as_view(), name='api-my-bookings'),
    path('bookings/<int:pk>/', BookingUpdateView.as_view(), name='api-booking-update'),
    path('org/resources/', OrgResourceListView.as_view(), name='api-org-resources'),
    path('org/bookings/', OrgBookingListView.as_view(), name='api-org-bookings'),
]
