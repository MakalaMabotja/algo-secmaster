from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView
from .views import RegisterView, LoginView, TokenRefresh

app_name = 'users'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefresh.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
