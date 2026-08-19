from django.urls import path
from . import api_views

urlpatterns = [
    path('follow/<str:username>/', api_views.FollowAPIView.as_view(), name='follow_api'),
    path('friend-request/<str:username>/', api_views.FriendRequestAPIView.as_view(), name='friend_request_api'),
    path('friend-request/<int:pk>/accept/', api_views.AcceptFriendAPIView.as_view(), name='accept_friend_api'),
    path('friend-request/<int:pk>/decline/', api_views.DeclineFriendAPIView.as_view(), name='decline_friend_api'),
    path('block/<str:username>/', api_views.BlockAPIView.as_view(), name='block_api'),
    path('friends/', api_views.FriendsListAPIView.as_view(), name='friends_list_api'),
]
