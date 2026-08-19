from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/create/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/edit/', views.EventEditView.as_view(), name='event_edit'),
    path('events/<int:pk>/join/', views.EventJoinView.as_view(), name='event_join'),
    path('events/<int:pk>/leave/', views.EventLeaveView.as_view(), name='event_leave'),
    path('events/<int:pk>/like/', views.EventLikeView.as_view(), name='event_like'),
    path('events/<int:pk>/save/', views.EventSaveView.as_view(), name='event_save'),
    path('events/<int:pk>/checkin/', views.EventCheckinView.as_view(), name='event_checkin'),
    path('events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
]
