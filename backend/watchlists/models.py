from django.db import models
from users.models import User

# Create your models here.
class Watchlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='watchlist')
    name = models.CharField(max_length=100, default='My Watchlist', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Always set name to 'My Watchlist'
        self.name = 'My Watchlist'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    
class WatchlistStock(models.Model):
    """Junction table for Watchlist-Stock many-to-many relationship"""
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE)
    stock = models.ForeignKey('stocks.Stock', on_delete=models.CASCADE)
    
    # When user added this stock to watchlist
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['watchlist', 'stock']
        ordering = ['added_at']
        
    