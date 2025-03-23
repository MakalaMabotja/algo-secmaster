from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework import status
from .models import Trader
from .serializers import TraderSerializer
from django.contrib.auth import authenticate
from rest_framework import serializers, status
from rest_framework.response import Response

User = get_user_model()

# Register View
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = TraderSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"message": "User registered successfully", "user": response.data}, status=status.HTTP_201_CREATED)

# Login View (JWT)
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Assuming you want to return the user data on successful login
        serializer = TraderSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Token Refresh View
class TokenRefresh(TokenRefreshView):
    pass
