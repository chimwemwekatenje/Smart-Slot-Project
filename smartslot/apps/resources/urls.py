from django.urls import path
from .views import ResourceListView, resource_book_redirect

urlpatterns = [
    path('', ResourceListView.as_view(), name='resource_list'),
    path('<int:resource_pk>/book/', resource_book_redirect, name='resource_book_redirect'),
]
