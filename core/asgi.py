import os
from decouple import config
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', config('DJANGO_SETTINGS_MODULE', default='core.settings'))
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from notifications.middleware import JWTAuthMiddleware
import chat.routing
import notifications.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns +
            notifications.routing.websocket_urlpatterns
        )
    ),
})
