from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework import permissions
from django.db.models import Q
from .models import Stock
from .serializers import StockSerializer


class StockListCreateView(ListCreateAPIView):
    """
    GET: List all stocks (with search functionality)
    POST: Create a new stock
    """
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Stock.objects.all()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(symbol__icontains=search) | Q(name__icontains=search)
            )
        
        return queryset.order_by('symbol')


