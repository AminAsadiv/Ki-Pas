import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings

if settings.DEBUG:
    from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
    from django.core.asgi import get_asgi_application
    http_app = ASGIStaticFilesHandler(get_asgi_application())
else:
    from django.core.asgi import get_asgi_application
    http_app = get_asgi_application()

from apps.messaging.routing import websocket_urlpatterns as chat_ws
from apps.notifications.routing import websocket_urlpatterns as notif_ws

application = ProtocolTypeRouter({
    'http': http_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(chat_ws + notif_ws)
    ),
})
