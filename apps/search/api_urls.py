from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.SearchAPIView.as_view(), name='search_api'),
]
