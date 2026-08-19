from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('me/', views.MyProfileView.as_view(), name='my_profile'),
    path('settings/', views.ProfileSettingsView.as_view(), name='settings'),
    path('<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),
]
