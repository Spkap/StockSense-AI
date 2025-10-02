from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Watchlist, WatchlistStock
from stocks.models import Stock

User = get_user_model()


class WatchlistModelTests(TestCase):
    """Test cases for Watchlist model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            firebase_uid='test_firebase_uid'
        )
    
    def test_create_watchlist(self):
        """Test creating a new watchlist"""
        watchlist = Watchlist.objects.create(user=self.user)
        
        self.assertEqual(watchlist.user, self.user)
        self.assertEqual(watchlist.name, 'My Watchlist')
        self.assertTrue(isinstance(watchlist.created_at, type(timezone.now())))
        self.assertTrue(isinstance(watchlist.updated_at, type(timezone.now())))
    
    def test_watchlist_str_method(self):
        """Test Watchlist __str__ method"""
        watchlist = Watchlist.objects.create(user=self.user)
        expected_str = f"{self.user.email} - My Watchlist"
        self.assertEqual(str(watchlist), expected_str)
    
    def test_watchlist_name_auto_set(self):
        """Test that watchlist name is automatically set to 'My Watchlist'"""
        watchlist = Watchlist.objects.create(
            user=self.user,
            name='Custom Name'  # This should be overridden
        )
        self.assertEqual(watchlist.name, 'My Watchlist')
    
    def test_watchlist_save_method(self):
        """Test that save method always sets name to 'My Watchlist'"""
        watchlist = Watchlist.objects.create(user=self.user)
        
        # Try to change the name
        watchlist.name = 'Different Name'
        watchlist.save()
        
        # Should still be 'My Watchlist'
        watchlist.refresh_from_db()
        self.assertEqual(watchlist.name, 'My Watchlist')
    
    def test_one_to_one_relationship(self):
        """Test one-to-one relationship between User and Watchlist"""
        watchlist1 = Watchlist.objects.create(user=self.user)
        
        # Try to create another watchlist for the same user
        with self.assertRaises(IntegrityError):
            Watchlist.objects.create(user=self.user)
    
    def test_watchlist_cascade_delete(self):
        """Test that watchlist is deleted when user is deleted"""
        watchlist = Watchlist.objects.create(user=self.user)
        watchlist_id = watchlist.id
        
        # Delete the user
        self.user.delete()
        
        # Watchlist should be deleted too
        with self.assertRaises(Watchlist.DoesNotExist):
            Watchlist.objects.get(id=watchlist_id)
    
    def test_related_name_access(self):
        """Test accessing watchlist through user's related name"""
        watchlist = Watchlist.objects.create(user=self.user)
        
        # Access watchlist through user
        user_watchlist = self.user.watchlist
        self.assertEqual(user_watchlist, watchlist)


class WatchlistStockModelTests(TestCase):
    """Test cases for WatchlistStock model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            firebase_uid='test_firebase_uid'
        )
        self.watchlist = Watchlist.objects.create(user=self.user)
        self.stock = Stock.objects.create(symbol='AAPL', name='Apple Inc.')
    
    def test_create_watchlist_stock(self):
        """Test creating a new watchlist stock entry"""
        watchlist_stock = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stock
        )
        
        self.assertEqual(watchlist_stock.watchlist, self.watchlist)
        self.assertEqual(watchlist_stock.stock, self.stock)
        self.assertTrue(isinstance(watchlist_stock.added_at, type(timezone.now())))
    
    def test_watchlist_stock_unique_together(self):
        """Test unique_together constraint on watchlist and stock"""
        WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stock
        )
        
        # Try to create duplicate entry
        with self.assertRaises(IntegrityError):
            WatchlistStock.objects.create(
                watchlist=self.watchlist,
                stock=self.stock
            )
    
    def test_watchlist_stock_cascade_delete_watchlist(self):
        """Test cascade delete when watchlist is deleted"""
        watchlist_stock = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stock
        )
        entry_id = watchlist_stock.id
        
        # Delete watchlist
        self.watchlist.delete()
        
        # WatchlistStock entry should be deleted
        with self.assertRaises(WatchlistStock.DoesNotExist):
            WatchlistStock.objects.get(id=entry_id)
    
    def test_watchlist_stock_cascade_delete_stock(self):
        """Test cascade delete when stock is deleted"""
        watchlist_stock = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stock
        )
        entry_id = watchlist_stock.id
        
        # Delete stock
        self.stock.delete()
        
        # WatchlistStock entry should be deleted
        with self.assertRaises(WatchlistStock.DoesNotExist):
            WatchlistStock.objects.get(id=entry_id)
    
    def test_watchlist_stock_ordering(self):
        """Test ordering by added_at field"""
        stock2 = Stock.objects.create(symbol='GOOGL', name='Alphabet Inc.')
        
        # Create entries with slight delay
        entry1 = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stock
        )
        entry2 = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=stock2
        )
        
        # Get ordered entries
        entries = WatchlistStock.objects.filter(watchlist=self.watchlist)
        
        # Should be ordered by added_at (earliest first)
        self.assertEqual(list(entries), [entry1, entry2])


class WatchlistQueryTests(TestCase):
    """Test cases for Watchlist and WatchlistStock queries"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            firebase_uid='uid_1'
        )
        self.user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            firebase_uid='uid_2'
        )
        
        self.watchlist1 = Watchlist.objects.create(user=self.user1)
        self.watchlist2 = Watchlist.objects.create(user=self.user2)
        
        self.stocks = [
            Stock.objects.create(symbol='AAPL', name='Apple Inc.'),
            Stock.objects.create(symbol='GOOGL', name='Alphabet Inc.'),
            Stock.objects.create(symbol='MSFT', name='Microsoft Corporation')
        ]
        
        # Add stocks to watchlists
        WatchlistStock.objects.create(watchlist=self.watchlist1, stock=self.stocks[0])
        WatchlistStock.objects.create(watchlist=self.watchlist1, stock=self.stocks[1])
        WatchlistStock.objects.create(watchlist=self.watchlist2, stock=self.stocks[0])
    
    def test_get_watchlist_by_user(self):
        """Test getting watchlist by user"""
        watchlist = Watchlist.objects.get(user=self.user1)
        self.assertEqual(watchlist, self.watchlist1)
    
    def test_get_stocks_in_watchlist(self):
        """Test getting all stocks in a watchlist"""
        watchlist_stocks = WatchlistStock.objects.filter(watchlist=self.watchlist1)
        stock_symbols = [ws.stock.symbol for ws in watchlist_stocks]
        
        self.assertIn('AAPL', stock_symbols)
        self.assertIn('GOOGL', stock_symbols)
        self.assertNotIn('MSFT', stock_symbols)
    
    def test_check_stock_in_watchlist(self):
        """Test checking if a stock is in a watchlist"""
        exists = WatchlistStock.objects.filter(
            watchlist=self.watchlist1,
            stock=self.stocks[0]
        ).exists()
        
        not_exists = WatchlistStock.objects.filter(
            watchlist=self.watchlist1,
            stock=self.stocks[2]
        ).exists()
        
        self.assertTrue(exists)
        self.assertFalse(not_exists)
    
    def test_count_stocks_in_watchlist(self):
        """Test counting stocks in a watchlist"""
        count1 = WatchlistStock.objects.filter(watchlist=self.watchlist1).count()
        count2 = WatchlistStock.objects.filter(watchlist=self.watchlist2).count()
        
        self.assertEqual(count1, 2)
        self.assertEqual(count2, 1)
    
    def test_get_watchlists_containing_stock(self):
        """Test getting all watchlists that contain a specific stock"""
        watchlists_with_aapl = WatchlistStock.objects.filter(
            stock=self.stocks[0]
        ).values_list('watchlist', flat=True)
        
        self.assertIn(self.watchlist1.id, watchlists_with_aapl)
        self.assertIn(self.watchlist2.id, watchlists_with_aapl)
    
    def test_get_or_create_watchlist(self):
        """Test get_or_create functionality for watchlist"""
        # Test getting existing watchlist
        watchlist1, created1 = Watchlist.objects.get_or_create(
            user=self.user1,
            defaults={'name': 'My Watchlist'}
        )
        self.assertFalse(created1)
        self.assertEqual(watchlist1, self.watchlist1)
        
        # Test creating new watchlist for user without one
        user3 = User.objects.create_user(
            username='user3@example.com',
            email='user3@example.com',
            firebase_uid='uid_3'
        )
        watchlist3, created3 = Watchlist.objects.get_or_create(
            user=user3,
            defaults={'name': 'My Watchlist'}
        )
        self.assertTrue(created3)
        self.assertEqual(watchlist3.user, user3)


class WatchlistBusinessLogicTests(TestCase):
    """Test cases for business logic related to watchlists"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            firebase_uid='test_firebase_uid'
        )
        self.watchlist = Watchlist.objects.create(user=self.user)
        self.stocks = [
            Stock.objects.create(symbol='AAPL', name='Apple Inc.'),
            Stock.objects.create(symbol='GOOGL', name='Alphabet Inc.'),
            Stock.objects.create(symbol='MSFT', name='Microsoft Corporation')
        ]
    
    def test_add_stock_to_watchlist(self):
        """Test adding a stock to watchlist"""
        initial_count = WatchlistStock.objects.filter(watchlist=self.watchlist).count()
        
        WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stocks[0]
        )
        
        new_count = WatchlistStock.objects.filter(watchlist=self.watchlist).count()
        self.assertEqual(new_count, initial_count + 1)
    
    def test_remove_stock_from_watchlist(self):
        """Test removing a stock from watchlist"""
        # Add stock first
        watchlist_stock = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stocks[0]
        )
        
        initial_count = WatchlistStock.objects.filter(watchlist=self.watchlist).count()
        
        # Remove stock
        watchlist_stock.delete()
        
        new_count = WatchlistStock.objects.filter(watchlist=self.watchlist).count()
        self.assertEqual(new_count, initial_count - 1)
    
    def test_bulk_add_stocks_to_watchlist(self):
        """Test adding multiple stocks to watchlist"""
        watchlist_stocks = [
            WatchlistStock(watchlist=self.watchlist, stock=stock)
            for stock in self.stocks
        ]
        
        WatchlistStock.objects.bulk_create(watchlist_stocks)
        
        count = WatchlistStock.objects.filter(watchlist=self.watchlist).count()
        self.assertEqual(count, len(self.stocks))
    
    def test_watchlist_stock_timestamps(self):
        """Test that timestamps are set correctly"""
        before_creation = timezone.now()
        
        watchlist_stock = WatchlistStock.objects.create(
            watchlist=self.watchlist,
            stock=self.stocks[0]
        )
        
        after_creation = timezone.now()
        
        # Check that added_at is between before and after creation
        self.assertGreaterEqual(watchlist_stock.added_at, before_creation)
        self.assertLessEqual(watchlist_stock.added_at, after_creation)
    
    def test_watchlist_updated_at_auto_update(self):
        """Test that updated_at is automatically updated"""
        original_updated_at = self.watchlist.updated_at
        
        # Save the watchlist again
        self.watchlist.save()
        
        self.watchlist.refresh_from_db()
        self.assertGreater(self.watchlist.updated_at, original_updated_at)
