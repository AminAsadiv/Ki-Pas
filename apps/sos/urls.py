from django.urls import path
from . import views

app_name = 'sos'

urlpatterns = [
    path('', views.SOSView.as_view(), name='sos'),
]
