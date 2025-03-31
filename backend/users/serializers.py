from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import (
    AddressDetails,
    TaxResidencyDetails,
    BankingDetails,
    Account,
    Transaction,
    TransactionSource
)

User = get_user_model()

class AddressDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressDetails
        fields = [
            'address_id', 'street_address', 'city', 'state_province',
            'zip_code', 'country', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['address_id', 'created_at', 'updated_at']


class TaxResidencyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxResidencyDetails
        fields = [
            'tax_residency_id', 'passport_country', 'id_number',
            'tax_country', 'tax_number', 'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['tax_residency_id', 'created_at', 'updated_at']


class BankingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankingDetails
        fields = [
            'banking_details_id', 'bank_name', 'account_number',
            'branch_code', 'swift_code', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['banking_details_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'account_number': {'write_only': True}  # Security: never expose account number in responses
        }

    def to_representation(self, instance):
        """Mask account number in responses"""
        ret = super().to_representation(instance)
        if 'account_number' in ret:
            ret['account_number'] = 'xxxx' + instance.account_number[-4:] if instance.account_number else None
        return ret


class TransactionSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSource
        fields = [
            'transaction_source_id', 'source_name', 'source_type',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_source_id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    transaction_source_name = serializers.CharField(source='transaction_source.source_name', read_only=True)
    account_nickname = serializers.CharField(source='account.account_nickname', read_only=True)
    currency = serializers.CharField(source='account.currency', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'account', 'account_nickname', 'transaction_type',
            'transaction_date', 'transaction_amount', 'currency', 'reference',
            'transaction_source', 'transaction_source_name', 'transaction_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['transaction_id', 'transaction_date', 'created_at', 'updated_at']


class AccountSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'account_id', 'user', 'account_nickname', 'account_type',
            'balance', 'currency', 'is_open', 'created_at', 'updated_at',
            'transactions'
        ]
        read_only_fields = ['account_id', 'balance', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """Customize to control the depth of nested transactions"""
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.query_params.get('include_transactions') != 'true':
            ret.pop('transactions', None)
        return ret


class UserSerializer(serializers.ModelSerializer):
    # Nested serializers for readable outputs but still accept IDs for input
    address_details = AddressDetailsSerializer(source='address', read_only=True)
    tax_residency_details = TaxResidencyDetailsSerializer(source='tax_residency', read_only=True)
    banking_details = BankingDetailsSerializer(source='banking_details', read_only=True)
    accounts = AccountSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'address', 'address_details', 'tax_residency', 'tax_residency_details',
            'banking_details', 'user_role', 'is_verified', 'is_active',
            'created_at', 'updated_at', 'accounts'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
        extra_kwargs = {
            'address': {'write_only': True},
            'tax_residency': {'write_only': True},
            'banking_details': {'write_only': True},
        }

    def to_representation(self, instance):
        """Customize to control the depth of nested accounts"""
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.query_params.get('include_accounts') != 'true':
            ret.pop('accounts', None)
        return ret


class UserCreateSerializer(serializers.ModelSerializer):
    """Separate serializer for user creation with password handling"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'user_role'
        ]
        extra_kwargs = {
            'user_role': {'default': 'customer'},
        }
    
    def validate(self, attrs):
        """Validate that the passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate that the new passwords match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Special serializer for creating transactions with balance checks"""
    class Meta:
        model = Transaction
        fields = [
            'account', 'transaction_type', 'transaction_amount',
            'reference', 'transaction_source', 'transaction_status'
        ]
    
    def validate(self, attrs):
        """Validate transaction data, especially for withdrawals"""
        account = attrs['account']
        transaction_type = attrs['transaction_type']
        amount = attrs['transaction_amount']
        
        # Ensure transaction amount is positive
        if amount <= 0:
            raise serializers.ValidationError({"transaction_amount": "Transaction amount must be positive."})
        
        # For withdrawals, check if the account has sufficient funds
        if transaction_type == 'withdrawal' and (account.balance < amount):
            raise serializers.ValidationError({"transaction_amount": "Insufficient funds in account."})
            
        return attrs


class AccountSummarySerializer(serializers.ModelSerializer):
    """Simplified account serializer for listings"""
    class Meta:
        model = Account
        fields = [
            'account_id', 'account_nickname', 'account_type',
            'balance', 'currency', 'is_open'
        ]