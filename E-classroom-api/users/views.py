from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework import parsers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import jwt
import datetime
from core.authentication import IsNotAuthenticated
from core.models import BlacklistedToken
from .serializers import *


@extend_schema(tags=["User Management"])
class CreateUserView(generics.CreateAPIView):
    """
    API for registering a new user.
    Sends an activation Token on the user email.
    """
    serializer_class = UserCreateRetriveSerializer
    permission_classes = [IsNotAuthenticated]
    parser_classes =  [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        user.set_email_token()
        user.save()

        subject = 'Activate your account'
        message = f'Hi {user.username}, activate your account \n token: {user.email_token}'

        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        email.send()

        return Response({"message": "Activation token has been sent to your email address. Please check your inbox."}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["User Management"])
class ActivateUserView(APIView):
    """
    API for activating a user account via email token.
    gets the token from serializer, token which user got from confirmation email after register
    activates the user if token is valid
    """
    serializer_class = ActivateUserSerializer
    permission_classes = [IsNotAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        user = get_user_model().objects.filter(email_token=token).first()

        if user and user.is_email_token_valid(token):
            user.is_active = True
            user.clear_email_token()
            user.save()

            return Response({"message": "Your account has been activated."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["User Management"])
class ForgotPasswordView(APIView):
    """
    API for requesting a password reset token
    Supported method: post
    gets the email from serializer and user from it
    sends the token to email for confirmation which user have to enter while reseting the password
    """
    serializer_class = ForgotPasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = get_user_model().objects.filter(email=email).first()

        if user:
            user.set_email_token()
            user.save()

            subject = 'Password Reset'
            message = f'Use the token below to reset password: \n Token: {user.email_token}'

            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.send()
            return Response({"message": "We have sent a token to your email. Use it to reset your password."}, status=status.HTTP_200_OK)
        else:
            return Response({'message':"user with this email does not exists"}, status=status.HTTP_200_OK)

@extend_schema(tags=["User Management"])
class ResetPasswordView(APIView):
    """
    API for resetting a user's password 
    Gets the token from serializer which is sent to user email for confirmation
    Also gets the password from serializer
    validate the token and resets the password if valid
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        user = get_user_model().objects.filter(email_token=token).first()

        if user and user.is_email_token_valid(token):
            user.set_password(serializer.validated_data['password'])
            user.clear_email_token()
            user.save()

            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["User Management"])
class AuthTokenView(APIView):
    """
    API for authenticating users and generating a token.
    Supported methods: post
    Gets the user from the authtoken serializers and generates the JWT tokens
    returns the access and refresh token
    """
    serializer_class = ObtainAuthTokenSerializer
    permission_classes = [IsNotAuthenticated]

    def post(self, request):
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        access_payload = {
            'user_id': user.id,
            'exp': timezone.now()  + datetime.timedelta(seconds=settings.JWT_ACCESS_EXP_DELTA_SECONDS),
            'iat': timezone.now()
        }
        access_token = jwt.encode(access_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        refresh_payload = {
            'user_id': user.id,
            'exp': timezone.now()  + datetime.timedelta(days=settings.JWT_REFRESH_EXP_DELTA_DAYS),
            'iat': timezone.now()
        }
        refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return Response({'access_token': access_token, 'refresh_token': refresh_token}, status=status.HTTP_200_OK)

@extend_schema(tags=["User Management"])
class RefreshTokenView(APIView):
    """
    refreshes the access token
    supported methods: Post
    Gets the user and refresh token from the serializer 
    Blacklist the existing refresh token and generates both new access and refresh tokens
    returns the tokens
    """
    serializer_class = RefreshTokenSerializer
    permission_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get('refresh_token')

        user = serializer.validated_data.get('user')
        BlacklistedToken.objects.create(user=user, token=refresh_token)
        
        new_access_payload = {
            'user_id':user.id,
            'exp':timezone.now() + datetime.timedelta(seconds=settings.JWT_ACCESS_EXP_DELTA_SECONDS),
            'iat':timezone.now()
        }
        new_access_token = jwt.encode(new_access_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        new_refresh_payload = {
            'user_id': user.id,
            'exp': timezone.now()  + datetime.timedelta(days=settings.JWT_REFRESH_EXP_DELTA_DAYS),
            'iat': timezone.now()
        }
        new_refresh_token = jwt.encode(new_refresh_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return Response({'access_token': new_access_token, 'refresh_token':new_refresh_token}, status=status.HTTP_200_OK)

@extend_schema(tags=["User Management"])
class LogoutView(APIView):
    """
    Blacklist refresh token on logout
    Supported method: post
    gets the auth header from the request header
    gets auth prefix and refresh token from that auth header
    validates the prefix and refresh token, if valid then blacklist it
    """
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        auth_header = request.headers.get('Authorization')
        try:
            prefix, refresh_token = auth_header.split()
            if prefix != 'Bearer':
                return Response({'error': 'Invalid token prefix'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Invalid Authorization header format'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not refresh_token:
            return Response({'error': 'Refresh token not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        BlacklistedToken.objects.create(token=refresh_token, user=request.user)

        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

@extend_schema(tags=["User Profile"])
class ManageUserView(generics.RetrieveAPIView):
    """
    API for retrieving the authenticated user's profile.
    """
    serializer_class = UserCreateRetriveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["User Profile"])
class ManageUserUpdateView(generics.UpdateAPIView):
    """
    API for updating the authenticated user's profile.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes =  [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_object(self):
        return self.request.user
    



