from django.db import models

# Create your models here.
class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    
        
    def __str__(self):
        return f"{self.symbol} - {self.name}"