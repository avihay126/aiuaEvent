from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from core.models import Photographer


class CookieAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('auth_token')
        if not token:
            return None

        try:
            photographer = Photographer.objects.get(secret=token)
        except Photographer.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        return (photographer, None)
