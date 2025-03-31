from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from .models import (
    AddressDetails, TaxResidencyDetails, BankingDetails,
    Account, Transaction, TransactionSource
)
from .serializers import (
    AddressDetailsSerializer, TaxResidencyDetailsSerializer, BankingDetailsSerializer,
    AccountSerializer, TransactionSerializer, TransactionSourceSerializer,
    UserSerializer, UserCreateSerializer, PasswordChangeSerializer,
    TransactionCreateSerializer, AccountSummarySerializer
)

User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class AddressDetailsViewSet(viewsets.ModelViewSet):
    queryset = AddressDetails.objects.all()
    serializer_class = AddressDetailsSerializer
    permission_classes = [IsAuthenticated]


class TaxResidencyDetailsViewSet(viewsets.ModelViewSet):
    queryset = TaxResidencyDetails.objects.all()
    serializer_class = TaxResidencyDetailsSerializer
    permission_classes = [IsAuthenticated]


class BankingDetailsViewSet(viewsets.ModelViewSet):
    queryset = BankingDetails.objects.all()
    serializer_class = BankingDetailsSerializer
    permission_classes = [IsAuthenticated]


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only accounts owned by the authenticated user"""
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Returns a simplified summary of an account"""
        account = self.get_object()
        serializer = AccountSummarySerializer(account)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions based on the authenticated user's accounts"""
        return self.queryset.filter(account__user=self.request.user)
    

class TransactionSourceViewSet(viewsets.ModelViewSet):
    queryset = TransactionSource.objects.all()
    serializer_class = TransactionSourceSerializer
    permission_classes = [IsAuthenticated]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Restrict users to self-view only"""
        return self.queryset.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retrieve the authenticated user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserCreateView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not check_password(serializer.validated_data['current_password'], user.password):
                return Response({"current_password": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save()
            return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
