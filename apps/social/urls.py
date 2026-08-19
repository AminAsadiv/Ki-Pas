from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('friend/<str:username>/', views.SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friend/<int:pk>/accept/', views.AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('friend/<int:pk>/decline/', views.DeclineFriendRequestView.as_view(), name='decline_friend_request'),
    path('follow/<str:username>/', views.FollowView.as_view(), name='follow'),
    path('block/<str:username>/', views.BlockView.as_view(), name='block'),
]
