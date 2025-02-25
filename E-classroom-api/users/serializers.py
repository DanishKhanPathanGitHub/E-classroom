from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.contrib.auth import authenticate

from core.models import BlacklistedToken
from core.utils import file_validator, image_validator, combine_file_validator
import jwt
from django.conf import settings

class UserCreateRetriveSerializer(serializers.ModelSerializer):
    """
    What it does:
    -------------
        This serializer is used for creating and retriving the user
        Fields: all fields of user model and confirm password for the creat(post request)
        Image validator is being attached to the profile_pic field 

    Validation:
    -----------
        password and confirm password match check and minimum length(8) check
    """
    confirm_password = serializers.CharField(
        style={"input_type":"password"},
        trim_whitespace=False,
        required=True,
        write_only=True
    )
    profile_pic = serializers.ImageField(validators=[image_validator], required=False)

    class Meta:
        model=get_user_model()
        fields = ['email', 'username', 'profile_pic', 'role', 'password', 'confirm_password','is_active']
        extra_kwargs={
            'password' : {
                'write_only':True,
                'trim_whitespace':False,
            },
            'is_active':{'read_only':True},
        }

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if len(password) < 8:
            msg = _("password should be atleast 8 character long")
            raise serializers.ValidationError(msg, code="password error")
        elif password != confirm_password:
            msg = _("passwords does not match")
            raise serializers.ValidationError(msg, code="password mismatch")
            
        return attrs
            
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        validated_data.pop('is_active', None)
        return get_user_model().objects.create_user(**validated_data)
    

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    What it does:
    -------------
        This serializer is used for updating the user
        Fields: username and profile_pic of user model
        Image validator is being attached to the profile_pic field 
    """
    profile_pic = serializers.ImageField(validators=[image_validator], required=False)
    
    class Meta:
        model=get_user_model()
        fields=['username', 'profile_pic']

class ActivateUserSerializer(serializers.Serializer):
    """
    What it does:
    -------------
        Gets the token which user got in his email to activate his account
    """
    token=serializers.CharField(write_only=True)

    
class RefreshTokenSerializer(serializers.Serializer):
    """
    What it does:
    -------------
        Gets the refresh token and validate if it's Blacklisted, expired or invalid
    """
    refresh_token = serializers.CharField(max_length=500)

    def validate(self, attrs):
        refresh_token = attrs.get('refresh_token')

        try:
            BlacklistedToken.objects.get(token=refresh_token)
            msg = _('Invalid token')
            raise serializers.ValidationError(msg)
        except:
            pass

        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALORITHM])
        except jwt.ExpiredSignatureError:
            msg = _('Expired token')
            raise serializers.ValidationError(msg)
        except jwt.DecodeError:
            msg = _('Invalid token')
            raise serializers.ValidationError(msg)
        
        user = get_user_model().objects.filter(id=payload['user_id'])
        if not user:
            msg = _("User not found")
            raise serializers.ValidationError(msg)
        
        attrs['user'] = user
        return attrs
        

class ObtainAuthTokenSerializer(serializers.Serializer):
    """
    What it does:
    -------------
    This serializeer will be used for obtaining the Authtoken
    for that user need to verify email and password

    Validation:
    -----------
        authenticate the user via entered details, if failed then raises error
        else adds the user to attrs and return the attrs
    """
    email=serializers.EmailField()
    password=serializers.CharField(trim_whitespace=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate with prvided credentials')
            raise serializers.ValidationError(msg)
        else:
            attrs['user'] = user
            return attrs
        
class ForgotPasswordSerializer(serializers.Serializer):
    """
    What it does:
    -------------
        User have to enter the email for getting the token to verify account
    """
    email=serializers.EmailField(write_only=True)

class ResetPasswordSerializer(serializers.Serializer):
    """
    What it does:
    -------------
        User will enter password, confirm_password and token he got in his email for verification to reset password

    Validation:
    -----------
        password and confirm password match check and minimum length(8) check
    """

    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password and len(password) < 6:
            msg = _('Password should be atleast 6 character long')
            raise serializers.ValidationError(msg, code="password_error")
        elif password and confirm_password and password != confirm_password:
            msg = _('Password and confirm password does not match')
            raise serializers.ValidationError(msg, code="password_error")

        return attrs
    