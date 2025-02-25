from django.urls import path, include, re_path
from . import views
app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create-user'),
    path('me/', views.ManageUserView.as_view(), name='me'),
    path('me/update/', views.ManageUserUpdateView.as_view(), name='me-update'),
    path('token/', views.AuthTokenView.as_view(), name='token'),
    path('token/refresh/', views.RefreshTokenView.as_view(), name='refresh-token'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('activate/', views.ActivateUserView.as_view(), name='activate'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    re_path(r'^oauth/', include('social_django.urls', namespace='social')),
]

