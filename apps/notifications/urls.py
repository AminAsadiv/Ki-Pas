from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationsView.as_view(), name='list'),
    path('<int:pk>/read/', views.MarkReadView.as_view(), name='mark_read'),
    path('read-all/', views.MarkAllReadView.as_view(), name='mark_all_read'),
    path('friend/<int:pk>/accept/', views.AcceptFriendView.as_view(), name='accept_friend'),
    path('friend/<int:pk>/decline/', views.DeclineFriendView.as_view(), name='decline_friend'),
]
