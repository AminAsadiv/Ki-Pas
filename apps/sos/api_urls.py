from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.SOSListAPIView.as_view(), name='sos_list_api'),
    path('create/', api_views.SOSCreateAPIView.as_view(), name='sos_create_api'),
    path('<int:pk>/resolve/', api_views.SOSResolveAPIView.as_view(), name='sos_resolve_api'),
]
