from django.urls import path
from .views import ResourceListView

app_name = 'resources'

urlpatterns = [
    path('', ResourceListView.as_view(), name='list'),
]
