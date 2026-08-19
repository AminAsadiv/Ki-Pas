from django.urls import path
from . import api_views

urlpatterns = [
    path('events/', api_views.MapEventsAPIView.as_view(), name='map_events'),
]
