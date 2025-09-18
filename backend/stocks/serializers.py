from rest_framework import serializers
from .models import Stock


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name']
        
    def create(self, validated_data):
        # Ensure symbol is uppercase
        validated_data['symbol'] = validated_data['symbol'].upper()
        return super().create(validated_data)
