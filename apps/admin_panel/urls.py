from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.AdminUsersView.as_view(), name='users'),
    path('events/', views.AdminEventsView.as_view(), name='events'),
    path('reports/', views.AdminReportsView.as_view(), name='reports'),
]
