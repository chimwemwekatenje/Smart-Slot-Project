from django.urls import path
from django.contrib.auth import views as auth_views
from .views import organisation_signup_view, signup_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('signup/organisation/', organisation_signup_view, name='organisation_signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
