"""Dashboard URL configuration."""
from django.urls import path
from .views import (
    OrganisationAdminDashboardView,
    DashboardResourceListView,
    DashboardBookingListView,
    DashboardOrgListView,
    DashboardOrgCreateView,
    DashboardOrgEditView,
    SuperAdminAnalysisView,
)

urlpatterns = [
    path('', OrganisationAdminDashboardView.as_view(), name='org_admin_dashboard'),
    path('resources/', DashboardResourceListView.as_view(), name='dashboard_resources'),
    path('bookings/', DashboardBookingListView.as_view(), name='dashboard_bookings'),
    path('organisations/', DashboardOrgListView.as_view(), name='dashboard_organisations'),
    path('organisations/create/', DashboardOrgCreateView.as_view(), name='dashboard_org_create'),
    path('organisations/<int:pk>/edit/', DashboardOrgEditView.as_view(), name='dashboard_org_edit'),
    path('analysis/', SuperAdminAnalysisView.as_view(), name='super_admin_analysis'),
]
