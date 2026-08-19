from django.urls import path
from . import api_views

urlpatterns = [
    path('<str:username>/', api_views.UserProfileAPIView.as_view(), name='user_profile_api'),
]
