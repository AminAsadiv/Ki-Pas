from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.MessagesView.as_view(), name='inbox'),
    path('new/<str:username>/', views.NewConversationView.as_view(), name='new_conversation'),
    path('group/create/', views.CreateGroupView.as_view(), name='create_group'),
    path('group/<int:conversation_id>/settings/', views.GroupSettingsView.as_view(), name='group_settings'),
    path('group/<int:conversation_id>/create-event/', views.GroupEventRedirectView.as_view(), name='group_event'),
    path('<int:conversation_id>/send/', views.SendMessageView.as_view(), name='send_message'),
    path('<int:conversation_id>/', views.ConversationView.as_view(), name='conversation'),
]
