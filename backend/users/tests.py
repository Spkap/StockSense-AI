from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import User

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'firebase_uid': 'test_firebase_uid_123',
            'first_name': 'Test',
            'last_name': 'User',
            'picture': 'https://example.com/avatar.jpg',
            'email_verified': True
        }
    
    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser@example.com')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.firebase_uid, 'test_firebase_uid_123')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.picture, 'https://example.com/avatar.jpg')
        self.assertTrue(user.email_verified)
    
    def test_user_str_method(self):
        """Test User __str__ method returns email"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser@example.com')
    
    def test_firebase_uid_unique(self):
        """Test firebase_uid is unique"""
        User.objects.create_user(**self.user_data)
        
        # Try to create another user with same firebase_uid
        duplicate_data = self.user_data.copy()
        duplicate_data['username'] = 'different@example.com'
        duplicate_data['email'] = 'different@example.com'
        
        with self.assertRaises(Exception):
            User.objects.create_user(**duplicate_data)
    
    def test_user_fields_optional(self):
        """Test that picture and email_verified fields are optional"""
        minimal_data = {
            'username': 'minimal@example.com',
            'email': 'minimal@example.com',
            'firebase_uid': 'minimal_firebase_uid'
        }
        user = User.objects.create_user(**minimal_data)
        
        self.assertEqual(user.picture, None)
        self.assertFalse(user.email_verified)


class UserMethodTests(TestCase):
    """Test cases for User model methods and properties"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            firebase_uid='test_firebase_uid_123',
            first_name='Test',
            last_name='User'
        )
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        full_name = self.user.get_full_name()
        self.assertEqual(full_name, 'Test User')
    
    def test_get_short_name(self):
        """Test get_short_name method"""
        short_name = self.user.get_short_name()
        self.assertEqual(short_name, 'Test')
    
    def test_is_authenticated_property(self):
        """Test is_authenticated property"""
        self.assertTrue(self.user.is_authenticated)
    
    def test_is_anonymous_property(self):
        """Test is_anonymous property"""
        self.assertFalse(self.user.is_anonymous)


class UserQueryTests(TestCase):
    """Test cases for User model queries and database operations"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            firebase_uid='uid_1',
            email_verified=True
        )
        self.user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            firebase_uid='uid_2',
            email_verified=False
        )
    
    def test_filter_by_firebase_uid(self):
        """Test filtering users by firebase_uid"""
        user = User.objects.filter(firebase_uid='uid_1').first()
        self.assertEqual(user, self.user1)
    
    def test_filter_by_email_verified(self):
        """Test filtering users by email_verified status"""
        verified_users = User.objects.filter(email_verified=True)
        unverified_users = User.objects.filter(email_verified=False)
        
        self.assertIn(self.user1, verified_users)
        self.assertNotIn(self.user2, verified_users)
        self.assertIn(self.user2, unverified_users)
        self.assertNotIn(self.user1, unverified_users)
    
    def test_get_user_by_email(self):
        """Test getting user by email"""
        user = User.objects.get(email='user1@example.com')
        self.assertEqual(user, self.user1)
    
    def test_user_count(self):
        """Test counting users"""
        count = User.objects.count()
        self.assertEqual(count, 2)
    
    def test_user_exists(self):
        """Test checking if user exists"""
        exists = User.objects.filter(firebase_uid='uid_1').exists()
        not_exists = User.objects.filter(firebase_uid='nonexistent').exists()
        
        self.assertTrue(exists)
        self.assertFalse(not_exists)
