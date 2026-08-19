from django.urls import path
from . import api_views

urlpatterns = [
    path('host/<str:username>/', api_views.HostReviewListAPIView.as_view(), name='host_reviews_api'),
    path('host/<str:username>/create/', api_views.CreateHostReviewAPIView.as_view(), name='create_host_review_api'),
    path('event/<int:event_id>/', api_views.EventReviewListAPIView.as_view(), name='event_reviews_api'),
    path('event/<int:event_id>/create/', api_views.CreateEventReviewAPIView.as_view(), name='create_event_review_api'),
]
