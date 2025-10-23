from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"].decode()
        token = None
        if "token=" in query_string:
            token = query_string.split("token=")[1]

        if token:
            try:
                UntypedToken(token)  # validate JWT
                decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user = await database_sync_to_async(User.objects.get)(id=decoded_data["user_id"])
                scope["user"] = user
            except Exception:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
