from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Stock


class StockModelTests(TestCase):
    """Test cases for Stock model"""
    
    def setUp(self):
        """Set up test data"""
        self.stock_data = {
            'symbol': 'AAPL',
            'name': 'Apple Inc.'
        }
        # Create a stock for read-only tests
        self.existing_stock = Stock.objects.create(**self.stock_data)
    
    def test_stock_str_method(self):
        """Test Stock __str__ method"""
        expected_str = "AAPL - Apple Inc."
        self.assertEqual(str(self.existing_stock), expected_str)
    
    def test_symbol_max_length(self):
        """Test symbol field max length constraint"""
        long_symbol_data = {
            'symbol': 'VERYLONGSYMBOL',  # More than 10 characters
            'name': 'Test Company'
        }
        
        stock = Stock(**long_symbol_data)
        with self.assertRaises(ValidationError):
            stock.full_clean()
    
    def test_name_max_length(self):
        """Test name field max length constraint"""
        long_name_data = {
            'symbol': 'TEST',
            'name': 'A' * 201  # More than 200 characters
        }
        
        stock = Stock(**long_name_data)
        with self.assertRaises(ValidationError):
            stock.full_clean()
    
    def test_empty_fields_validation(self):
        """Test validation with empty required fields"""
        # Test empty symbol
        with self.assertRaises(ValidationError):
            stock = Stock(symbol='', name='Test Company')
            stock.full_clean()
        
        # Test empty name
        with self.assertRaises(ValidationError):
            stock = Stock(symbol='TEST', name='')
            stock.full_clean()


class StockQueryTests(TestCase):
    """Test cases for Stock model queries and database operations"""
    
    def setUp(self):
        """Set up test data"""
        self.stocks = [
            Stock.objects.create(symbol='AAPL', name='Apple Inc.'),
            Stock.objects.create(symbol='GOOGL', name='Alphabet Inc.'),
            Stock.objects.create(symbol='MSFT', name='Microsoft Corporation'),
            Stock.objects.create(symbol='TSLA', name='Tesla Inc.'),
            Stock.objects.create(symbol='NVDA', name='NVIDIA Corporation')
        ]
    
    def test_get_stock_by_symbol(self):
        """Test getting stock by symbol"""
        stock = Stock.objects.get(symbol='AAPL')
        self.assertEqual(stock.name, 'Apple Inc.')
    
    def test_filter_stocks_by_name_contains(self):
        """Test filtering stocks by name containing text"""
        results = Stock.objects.filter(name__icontains='Inc')
        
        # Should return Apple, Tesla, and potentially others with 'Inc'
        symbols = [stock.symbol for stock in results]
        self.assertIn('AAPL', symbols)
        self.assertIn('TSLA', symbols)
    
    def test_filter_stocks_by_symbol_startswith(self):
        """Test filtering stocks by symbol starting with letters"""
        results = Stock.objects.filter(symbol__startswith='A')
        symbols = [stock.symbol for stock in results]
        self.assertIn('AAPL', symbols)
    
    def test_order_stocks_by_symbol(self):
        """Test ordering stocks by symbol"""
        ordered_stocks = Stock.objects.order_by('symbol')
        symbols = [stock.symbol for stock in ordered_stocks]
        
        # Should be in alphabetical order
        self.assertEqual(symbols, sorted(symbols))
    
    def test_order_stocks_by_name(self):
        """Test ordering stocks by name"""
        ordered_stocks = Stock.objects.order_by('name')
        names = [stock.name for stock in ordered_stocks]
        
        # Should be in alphabetical order
        self.assertEqual(names, sorted(names))
    
    def test_count_stocks(self):
        """Test counting stocks"""
        count = Stock.objects.count()
        self.assertEqual(count, 5)
    
    def test_stock_exists(self):
        """Test checking if stock exists"""
        exists = Stock.objects.filter(symbol='AAPL').exists()
        not_exists = Stock.objects.filter(symbol='NONEXISTENT').exists()
        
        self.assertTrue(exists)
        self.assertFalse(not_exists)


class StockValidationTests(TestCase):
    """Test cases for Stock model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.stock = Stock.objects.create(symbol='AAPL', name='Apple Inc.')
    
    def test_model_field_attributes(self):
        """Test model field attributes are set correctly"""
        symbol_field = Stock._meta.get_field('symbol')
        name_field = Stock._meta.get_field('name')
        
        # Test symbol field attributes
        self.assertEqual(symbol_field.max_length, 10)
        self.assertTrue(symbol_field.unique)
        self.assertTrue(symbol_field.db_index)
        
        # Test name field attributes
        self.assertEqual(name_field.max_length, 200)
        self.assertFalse(name_field.unique)
    
    def test_existing_stock_properties(self):
        """Test properties of existing stock"""
        self.assertEqual(self.stock.symbol, 'AAPL')
        self.assertEqual(self.stock.name, 'Apple Inc.')
        self.assertIsNotNone(self.stock.id)
