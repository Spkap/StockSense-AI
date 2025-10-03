from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404

from .models import Watchlist, WatchlistStock
from stocks.models import Stock
from .serializers import (
    WatchlistSerializer, 
    WatchlistStockSerializer
)


class WatchlistView(APIView):
    """
    GET: Get the user's single watchlist (create if doesn't exist)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get or create user's watchlist"""
        watchlist, created = Watchlist.objects.get_or_create(
            user=request.user,
            defaults={'name': 'My Watchlist'}
        )
        serializer = WatchlistSerializer(watchlist)
        return Response(serializer.data)


class WatchlistStockView(APIView):
    """
    POST: Add a stock to the user's watchlist
    DELETE: Remove a stock from the user's watchlist
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Add stock to user's watchlist"""
        watchlist, created = Watchlist.objects.get_or_create(
            user=request.user,
            defaults={'name': 'My Watchlist'}
        )
        
        stock_symbol = request.data.get('symbol')
        stock_id = request.data.get('stock_id')
        
        if not stock_symbol and not stock_id:
            return Response(
                {"detail": "Either 'symbol' or 'stock_id' is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if stock_id:
                stock = get_object_or_404(Stock, id=stock_id)
            else:
                # Try to find stock by symbol, create if doesn't exist
                stock, created = Stock.objects.get_or_create(
                    symbol=stock_symbol.upper(),
                    defaults={'name': request.data.get('name', stock_symbol.upper())}
                )
            
            # Check if stock is already in watchlist
            if WatchlistStock.objects.filter(watchlist=watchlist, stock=stock).exists():
                return Response(
                    {"detail": "Stock already exists in your watchlist"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add stock to watchlist
            watchlist_stock = WatchlistStock.objects.create(
                watchlist=watchlist,
                stock=stock
            )
            
            serializer = WatchlistStockSerializer(watchlist_stock)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"detail": f"Error adding stock: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, stock_id):
        """Remove stock from user's watchlist"""
        try:
            # Get user's watchlist
            watchlist = get_object_or_404(Watchlist, user=request.user)
            
            # Find and delete the watchlist stock entry
            watchlist_stock = get_object_or_404(
                WatchlistStock, 
                watchlist=watchlist, 
                stock_id=stock_id
            )
            watchlist_stock.delete()
            
            return Response(
                {"detail": "Stock removed from watchlist"}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        except WatchlistStock.DoesNotExist:
            return Response(
                {"detail": "Stock not found in your watchlist"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Watchlist.DoesNotExist:
            return Response(
                {"detail": "Watchlist not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )