from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.EventListCreateAPIView.as_view(), name='event_list_api'),
    path('<int:pk>/', api_views.EventDetailAPIView.as_view(), name='event_detail_api'),
    path('<int:pk>/join/', api_views.EventJoinAPIView.as_view(), name='event_join_api'),
    path('<int:pk>/leave/', api_views.EventLeaveAPIView.as_view(), name='event_leave_api'),
    path('<int:pk>/like/', api_views.EventLikeAPIView.as_view(), name='event_like_api'),
    path('<int:pk>/save/', api_views.EventSaveAPIView.as_view(), name='event_save_api'),
    path('categories/', api_views.CategoryListAPIView.as_view(), name='category_list_api'),
    path('feed/', api_views.FeedAPIView.as_view(), name='feed_api'),
]
