from rest_framework import serializers
from .models import Watchlist, WatchlistStock
from stocks.models import Stock
from stocks.serializers import StockSerializer


class WatchlistStockSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    stock_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = WatchlistStock
        fields = ['id', 'stock', 'stock_id', 'added_at']
        read_only_fields = ['added_at']


class WatchlistSerializer(serializers.ModelSerializer):
    stocks = WatchlistStockSerializer(source='watchliststock_set', many=True, read_only=True)
    stock_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Watchlist
        fields = ['id', 'name', 'created_at', 'updated_at', 'stocks', 'stock_count']
        read_only_fields = ['created_at', 'updated_at', 'name']  # name is read-only
    
    def get_stock_count(self, obj):
        return obj.watchliststock_set.count()
