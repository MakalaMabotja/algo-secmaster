from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    UserViewSet,
    AccountViewSet,
    TransactionViewSet,
    TransactionSourceViewSet,
    AddressDetailsViewSet,
    TaxResidencyDetailsViewSet,
    BankingDetailsViewSet,
    PasswordChangeView,
    UserCreateView,
    TransactionCreateView
)

# Using DRF's DefaultRouter for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'transaction-sources', TransactionSourceViewSet, basename='transaction_source')
router.register(r'addresses', AddressDetailsViewSet, basename='address_details')
router.register(r'tax-residency', TaxResidencyDetailsViewSet, basename='tax_residency_details')
router.register(r'banking-details', BankingDetailsViewSet, basename='banking_details')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', UserCreateView.as_view(), name='user-register'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction-create'),
]
