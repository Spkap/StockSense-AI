from django.urls import path
from .views import (
    WatchlistView,
    WatchlistStockView
)

urlpatterns = [
    # Single watchlist per user
    path('', WatchlistView.as_view(), name='user-watchlist'),
    
    # Stock operations within the user's watchlist
    path('stocks/', WatchlistStockView.as_view(), name='watchlist-add-stock'),
    path('stocks/<int:stock_id>/', WatchlistStockView.as_view(), name='watchlist-remove-stock'),
]
