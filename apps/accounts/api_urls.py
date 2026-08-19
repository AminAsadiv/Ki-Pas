from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from . import api_views

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/logout/', TokenBlacklistView.as_view(), name='token_logout'),
    path('register/', api_views.RegisterAPIView.as_view(), name='register'),
    path('me/', api_views.MeAPIView.as_view(), name='me'),
    path('change-password/', api_views.ChangePasswordAPIView.as_view(), name='change_password'),
]
