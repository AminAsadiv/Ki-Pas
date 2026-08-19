from django.urls import path
from . import api_views

urlpatterns = [
    path('conversations/', api_views.ConversationListAPIView.as_view(), name='conversation_list_api'),
    path('conversations/<int:pk>/', api_views.ConversationDetailAPIView.as_view(), name='conversation_detail_api'),
    path('conversations/<int:pk>/messages/', api_views.MessageListAPIView.as_view(), name='message_list_api'),
    path('new/<str:username>/', api_views.StartConversationAPIView.as_view(), name='start_conversation_api'),
]
