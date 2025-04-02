from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import jwt
from django.contrib.auth import get_user_model
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from rest_framework.permissions import BasePermission

class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication class.
    Inherits the base authentication class and override the authenticate method
    gets the prefix and token from the request header.
    checks if prefix is Bearer or not
    validates the JWT token and retrive the user if valid
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()
            if prefix != 'Bearer':
                raise AuthenticationFailed('Invalid token prefix')

            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.DecodeError, ValueError) as e:
            raise AuthenticationFailed('Invalid token')

        user = get_user_model().objects.filter(id=payload['user_id']).first()
        if not user:
            raise AuthenticationFailed('User not found')

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'

class JWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'core.authentication.JWTAuthentication'  
    name = 'JWTAuth'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix='Bearer'
        )
    
class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """
    def has_permission(self, request, view):
        return not request.user.is_authenticated