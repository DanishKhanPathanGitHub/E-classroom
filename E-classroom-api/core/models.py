from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import secrets
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):

    def create_user(self, email, username, role=1, profile_pic=None, password=None):
        if not email:
            raise ValueError("Email required")
        if not username:
            raise ValueError("username required")
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            role=role,
            profile_pic=profile_pic
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, role=1, profile_pic=None, password=None):
        user = self.create_user(
            username=username,
            email=email,
            role=role,
            profile_pic=profile_pic,
            password=password
        )
        user.is_active=True
        user.is_admin=True
        user.is_staff=True
        user.is_superadmin=True
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser):
    student = 1
    tutor = 2
    role_choices = (
        (student, "student"),
        (tutor, "tutor"),
    )

    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, unique=True)
    role = models.PositiveSmallIntegerField(choices=role_choices, default=1)
    profile_pic = models.ImageField(upload_to='students/profile_pics', blank=True, null=True, default='students/profile_pics/male.png')
    
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    email_token = models.CharField(max_length=64, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    token_expiration = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    objects = UserManager()
    
    def set_email_token(self):
        """Generates a new reset token and sets its expiration time."""
        self.email_token = secrets.token_hex(4)
        self.token_expiration = timezone.now() + timedelta(minutes=4)
        self.save()

    def clear_email_token(self):
        """Clears the reset token and its expiration time."""
        self.email_token = None
        self.token_expiration = None
        self.save()

    def is_email_token_valid(self, token):
        """Checks if the provided token is valid and not expired."""
        return self.email_token == token and self.token_expiration > timezone.now()

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True
    
    
class BlacklistedToken(models.Model):
    token=models.CharField(max_length=500, unique=True)
    user=models.ForeignKey('User', on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token