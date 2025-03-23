from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Trader

User = get_user_model()

class TraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = ['customer_id', 'username', 'email', 'password', 'id_number', 'tax_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Trader.objects.create_user(**validated_data)
        return user
