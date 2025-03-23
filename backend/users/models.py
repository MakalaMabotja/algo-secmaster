from django.db import models
from django.contrib.auth.models import AbstractUser

class Trader(AbstractUser):
    customer_id = models.BigAutoField(primary_key=True)  # Auto-generated ID
    phone_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    id_number = models.CharField(max_length=13, unique=True, null=False, blank=False)
    date_of_birth = models.DateField(null=True, blank=True)
    tax_number = models.CharField(max_length=8, unique=True)
    address_line1 = models.CharField(max_length=255)  # Max length is required
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.username} ({self.customer_id})"

class TraderAccount(models.Model):
    customer = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name="accounts")
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False)
    date_opened = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Account {self.id} - {self.customer.username}"

class Transaction(models.Model):
    account = models.ForeignKey(TraderAccount, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=50, choices=[("deposit", "Deposit"), ("withdrawal", "Withdrawal")])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} on {self.timestamp}"

    
