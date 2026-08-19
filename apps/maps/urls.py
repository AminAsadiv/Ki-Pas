from django.urls import path
from . import views

app_name = 'maps'

urlpatterns = [
    path('', views.MapView.as_view(), name='map'),
]
