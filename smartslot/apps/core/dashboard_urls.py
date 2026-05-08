"""Dashboard URL configuration."""
from django.urls import path
from .views import (
    admin_login_view,
    OrganisationAdminDashboardView,
    DashboardResourceListView,
    DashboardBookingListView,
    DashboardOrgListView,
    DashboardOrgCreateView,
    DashboardOrgEditView,
    SuperAdminAnalysisView,
    dashboard_users_view,
    dashboard_org_users_view,
    dashboard_org_resources_view,
    dashboard_org_delete_view,
)

urlpatterns = [
    path('login/',                       admin_login_view,                          name='admin_login'),
    path('',                             OrganisationAdminDashboardView.as_view(),  name='org_admin_dashboard'),
    path('resources/',                   DashboardResourceListView.as_view(),       name='dashboard_resources'),
    path('bookings/',                    DashboardBookingListView.as_view(),        name='dashboard_bookings'),
    path('organisations/',               DashboardOrgListView.as_view(),            name='dashboard_organisations'),
    path('organisations/create/',        DashboardOrgCreateView.as_view(),          name='dashboard_org_create'),
    path('organisations/<int:pk>/edit/', DashboardOrgEditView.as_view(),            name='dashboard_org_edit'),
    path('organisations/<int:pk>/delete/', dashboard_org_delete_view,              name='dashboard_org_delete'),
    path('users/',                       dashboard_users_view,                      name='dashboard_users'),
    path('org/users/',                   dashboard_org_users_view,                  name='dashboard_org_users'),
    path('org/resources/',               dashboard_org_resources_view,              name='dashboard_org_resources'),
    path('analysis/',                    SuperAdminAnalysisView.as_view(),          name='super_admin_analysis'),
]
