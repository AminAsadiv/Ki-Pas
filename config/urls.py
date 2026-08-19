from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # Frontend pages
    path('', include('apps.events.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('profile/', include('apps.profiles.urls')),
    path('messages/', include('apps.messaging.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('map/', include('apps.maps.urls')),
    path('search/', include('apps.search.urls')),
    path('admin-panel/', include('apps.admin_panel.urls')),
    path('sos/', include('apps.sos.urls')),
    path('social/', include('apps.social.urls')),

    # REST API v1
    path('api/v1/', include([
        path('auth/', include('apps.accounts.api_urls')),
        path('users/', include('apps.profiles.api_urls')),
        path('events/', include('apps.events.api_urls')),
        path('social/', include('apps.social.api_urls')),
        path('messages/', include('apps.messaging.api_urls')),
        path('notifications/', include('apps.notifications.api_urls')),
        path('reviews/', include('apps.reviews.api_urls')),
        path('search/', include('apps.search.api_urls')),
        path('map/', include('apps.maps.api_urls')),
        path('sos/', include('apps.sos.api_urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
