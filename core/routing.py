from channels.routing import ProtocolTypeRouter, URLRouter
from notifications.routing import websocket_urlpatterns
from notifications.consumers import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
