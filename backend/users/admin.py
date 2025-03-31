from django.contrib import admin
from .models import User, Transaction, TransactionSource, TaxResidencyDetails, Account, AddressDetails, BankingDetails

# Register your models here.
admin.site.register([User, Transaction, TransactionSource, TaxResidencyDetails, Account, AddressDetails, BankingDetails])