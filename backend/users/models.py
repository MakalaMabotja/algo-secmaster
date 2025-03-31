from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.db.models import DecimalField
from django.conf import settings

# Base model for common fields
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# AddressDetails Model
class AddressDetails(BaseModel):
    address_id = models.BigAutoField(primary_key=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['country']),
        ]
        verbose_name_plural = 'Address Details'

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state_province}, {self.country}"

# TaxResidencyDetails Model
class TaxResidencyDetails(BaseModel):
    tax_residency_id = models.BigAutoField(primary_key=True)
    passport_country = models.CharField(max_length=255)
    id_number = models.CharField(max_length=255)
    tax_country = models.CharField(max_length=255)
    tax_number = models.CharField(max_length=255)
    is_valid = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Tax Residency Details'

    def __str__(self):
        return f"{self.passport_country} - {self.tax_country}"

# BankingDetails Model
class BankingDetails(BaseModel):
    banking_details_id = models.BigAutoField(primary_key=True)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)  # Implement encryption in save method
    branch_code = models.CharField(max_length=30, null=True, blank=True)
    swift_code = models.CharField(max_length=15)  # Extended for longer SWIFT codes
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Banking Details'

    def __str__(self):
        # Don't expose full account number in string representation
        masked_account = 'xxxx' + self.account_number[-4:] if self.account_number else 'xxxx'
        return f"{self.bank_name} - {masked_account}"
    
    def save(self, *args, **kwargs):
        # Implement encryption for account_number here
        # This is a placeholder - use a proper encryption method in production
        # Consider django-encrypted-fields or similar package
        super().save(*args, **kwargs)

# Account Model - Breaking circular dependency by defining User model first
class Account(BaseModel):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        # Add more currencies as needed
    ]
    
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('checking', 'Checking'),
        ('investment', 'Investment'),
        ('retirement', 'Retirement'),
        # Add more types as needed
    ]
    
    account_id = models.BigAutoField(primary_key=True)
    account_nickname = models.CharField(max_length=255)
    account_type = models.CharField(max_length=100, choices=ACCOUNT_TYPES)
    balance = DecimalField(max_digits=19, decimal_places=4, default=0)  # Increased precision
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    is_open = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['account_type']),
            models.Index(fields=['currency']),
        ]

    def __str__(self):
        return f"{self.account_nickname} - {self.account_type} ({self.currency})"

# User Model (Custom AbstractUser)
class User(AbstractUser):
    USER_ROLES = [
        ('customer', 'Customer'),
        ('admin', 'Administrator'),
        ('support', 'Customer Support'),
        ('manager', 'Account Manager'),
        # Add more roles as needed
    ]
    
    # E.164 validator with better support for international formats
    phone_validator = RegexValidator(
        r'^\+?[1-9]\d{1,14}$', 
        _("Enter a valid E.164 phone number starting with + and country code")
    )
    
    phone_number = models.CharField(
        max_length=20,  # Increased to accommodate longer formats
        unique=True, 
        null=True, 
        blank=True, 
        validators=[phone_validator]
    )
    
    address = models.ForeignKey(
        AddressDetails, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    tax_residency = models.ForeignKey(
        TaxResidencyDetails, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    banking_details = models.ForeignKey(
        BankingDetails, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    # Note: User and Account now have a one-to-many relationship
    # Each User can have multiple Accounts
    
    user_role = models.CharField(
        max_length=100, 
        choices=USER_ROLES,
        default='customer'
    )
    
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_role']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

# Now update Account to reference User (no circular dependency)
Account.user = models.ForeignKey(
    User, 
    on_delete=models.CASCADE, 
    related_name='accounts'
)

# TransactionSource Model
class TransactionSource(BaseModel):
    transaction_source_id = models.BigAutoField(primary_key=True)
    source_name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['source_type']),
        ]

    def __str__(self):
        return f"{self.source_name} - {self.source_type}"

# Transactions Model
class Transaction(BaseModel):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('dividend', 'Dividend'),
        ('transfer', 'Transfer'),
        ('fee', 'Fee'),
        # Add more types as needed
    ]
    
    TRANSACTION_STATUSES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        # Add more statuses as needed
    ]
    
    transaction_id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(
        Account, 
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_amount = DecimalField(max_digits=19, decimal_places=4)
    reference = models.CharField(max_length=255, null=True, blank=True)
    transaction_source = models.ForeignKey(
        TransactionSource, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='transactions'
    )
    transaction_status = models.CharField(max_length=50, choices=TRANSACTION_STATUSES)

    class Meta:
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_status']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_amount} ({self.transaction_status})"
    
    def save(self, *args, **kwargs):
        # Update account balance when transaction is completed
        is_new = self.pk is None
        old_status = None
        
        # Get the old status if this is an existing transaction
        if not is_new:
            old_instance = Transaction.objects.get(pk=self.pk)
            old_status = old_instance.transaction_status
        
        # Save the transaction first
        super().save(*args, **kwargs)
        
        # Update the account balance if transaction is newly completed
        if (is_new and self.transaction_status == 'completed') or \
           (not is_new and old_status != 'completed' and self.transaction_status == 'completed'):
            self._update_account_balance()
    
    def _update_account_balance(self):
        """Update the related account balance based on transaction type."""
        if self.transaction_status != 'completed':
            return
            
        account = self.account
        
        # Adjust balance based on transaction type
        if self.transaction_type in ['deposit', 'dividend']:
            account.balance += self.transaction_amount
        elif self.transaction_type in ['withdrawal', 'fee']:
            account.balance -= self.transaction_amount
        # For transfers, you might need more complex logic
            
        account.save()