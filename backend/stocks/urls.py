from django.urls import path
from .views import StockListCreateView

urlpatterns = [
    path('', StockListCreateView.as_view(), name='stock-list-create'),
]
