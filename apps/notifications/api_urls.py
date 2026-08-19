from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.NotificationListAPIView.as_view(), name='notification_list_api'),
    path('<int:pk>/read/', api_views.MarkReadAPIView.as_view(), name='notification_read_api'),
    path('read-all/', api_views.MarkAllReadAPIView.as_view(), name='notification_read_all_api'),
    path('unread-count/', api_views.UnreadCountAPIView.as_view(), name='notification_unread_count_api'),
]
