"""
Base test class for Django Redis Panel tests.

This module provides a base test class with common setup and teardown logic
for Redis connections, Django settings mocking, and test data management.
"""
import redis
from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch


class RedisTestCase(TestCase):
    """
    Base test class for Django Redis Panel tests.
    
    Provides common setup for:
    - Redis connectivity checking
    - Test user creation
    - Redis test data cleanup
    - Django settings mocking
    - Common test data setup
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with Redis connection check."""
        super().setUpClass()
        # Test Redis connectivity
        try:
            cls.redis_conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=True)
            cls.redis_conn.ping()
        except redis.ConnectionError:
            cls.redis_available = False
        else:
            cls.redis_available = True
    
    def setUp(self):
        """Set up test data before each test."""
        if not self.redis_available:
            self.skipTest("Redis server not available for testing")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create authenticated client
        self.client = Client()
        self.client.login(username='admin', password='testpass123')
        
        # Clean test databases
        self.cleanup_test_databases()
        
        # Set up Redis test data
        self.setup_redis_test_data()
        
        # Set up Django settings mock
        self.setup_settings_mock()
    
    def tearDown(self):
        """Clean up after each test."""
        # Stop the settings mock
        if hasattr(self, 'settings_patcher'):
            self.settings_patcher.stop()
        
        # Clean test databases
        if self.redis_available:
            self.cleanup_test_databases()
    
    def cleanup_test_databases(self):
        """Clean up test Redis databases."""
        test_dbs = [13, 14, 15]
        for db_num in test_dbs:
            test_conn = redis.Redis(host='127.0.0.1', port=6379, db=db_num, decode_responses=True)
            try:
                test_conn.flushdb()
            except redis.ConnectionError:
                pass  # Ignore connection errors during cleanup
    
    def setup_redis_test_data(self):
        """
        Set up basic Redis test data.
        
        Override this method in subclasses to add specific test data:
        
        Example:
            def setup_redis_test_data(self):
                super().setup_redis_test_data()  # Get base data
                self.redis_conn.set('custom:key', 'custom_value')
        """
        # Set up test data in Redis database 15 (main test database)
        self.redis_conn.select(15)
        
        # Basic string keys
        basic_data = {
            'test:string': 'test_value',
            'user:123': 'john_doe',
            'user:456': 'jane_doe',
            'cache:data': 'cached_content',
            'session:abc123': 'session_data',
            'temp:key': 'temporary_value',
        }
        
        for key, value in basic_data.items():
            self.redis_conn.set(key, value)
        
        # Set TTL on some keys
        self.redis_conn.expire('session:abc123', 3600)
        self.redis_conn.expire('temp:key', 1800)
        
        # Create different data types
        self.redis_conn.lpush('test:list', 'item1', 'item2', 'item3')
        self.redis_conn.sadd('test:set', 'member1', 'member2', 'member3')
        self.redis_conn.hset('test:hash', mapping={
            'field1': 'value1',
            'field2': 'value2',
            'field3': 'value3'
        })
        self.redis_conn.zadd('test:zset', {
            'member1': 1.0,
            'member2': 2.0,
            'member3': 3.0
        })
        
        # Add test data to other databases for multi-database testing
        self.setup_multi_database_test_data()
    
    def setup_multi_database_test_data(self):
        """Set up test data across multiple Redis databases."""
        # Database 13 - URL-based connection testing
        conn_13 = redis.Redis(host='127.0.0.1', port=6379, db=13, decode_responses=True)
        conn_13.set('url_test:key1', 'value1')
        conn_13.set('url_test:key2', 'value2')
        
        # Database 14 - Feature-disabled testing
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        conn_14.set('no_features:string', 'test_value')
        conn_14.set('no_features:counter', '42')
        conn_14.set('no_features:session', 'session_data')
    
    def setup_settings_mock(self):
        """Set up Django settings mock with test Redis configuration."""
        self.redis_test_settings = self.get_test_settings()
        
        # Start the settings mock
        self.settings_patcher = patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
        self.mock_get_settings = self.settings_patcher.start()
        self.mock_get_settings.return_value = self.redis_test_settings
    
    def get_test_settings(self):
        """
        Get test Redis settings configuration.
        
        Override this method in subclasses to customize settings:
        
        Example:
            def get_test_settings(self):
                settings = super().get_test_settings()
                settings["ALLOW_KEY_DELETE"] = False
                return settings
        """
        return {
            "ALLOW_KEY_DELETE": True,
            "ALLOW_KEY_EDIT": True,
            "ALLOW_TTL_UPDATE": True,
            "CURSOR_PAGINATED_SCAN": False,
            "INSTANCES": {
                "test_redis": {
                    "description": "Test Redis Instance",
                    "host": "127.0.0.1",
                    "port": 6379,
                    "db": 15,  # Use test database 15
                    "features": {
                        "ALLOW_KEY_DELETE": True,
                        "ALLOW_KEY_EDIT": True,
                        "ALLOW_TTL_UPDATE": True,
                        "CURSOR_PAGINATED_SCAN": False,
                    },
                },
                "test_redis_no_features": {
                    "description": "Test Redis Instance - No Features",
                    "host": "127.0.0.1",
                    "port": 6379,
                    "db": 14,  # Use test database 14
                    "features": {
                        "ALLOW_KEY_DELETE": False,
                        "ALLOW_KEY_EDIT": False,
                        "ALLOW_TTL_UPDATE": False,
                        "CURSOR_PAGINATED_SCAN": True,
                    },
                },
                "test_redis_url": {
                    "description": "Test Redis from URL",
                    "url": "redis://127.0.0.1:6379/13",  # Use test database 13
                },
 def cleanup_test_databases(self):
     """Clean up test Redis databases."""
    test_dbs = [12, 13, 14, 15]
     for db_num in test_dbs:
         test_conn = redis.Redis(host='127.0.0.1', port=6379, db=db_num, decode_responses=True)
         try:
             test_conn.flushdb()
         except redis.ConnectionError:
             pass  # Ignore connection errors during cleanup
            }
        }
    
    def create_unauthenticated_client(self):
        """Create an unauthenticated Django test client."""
        return Client()
    
    def add_test_key(self, key, value, db=15, ttl=None):
        """
        Helper method to add a test key to Redis.
        
        Args:
            key: Redis key name
            value: Redis key value
            db: Database number (default: 15)
            ttl: Time to live in seconds (optional)
        """
        conn = redis.Redis(host='127.0.0.1', port=6379, db=db, decode_responses=True)
        if ttl:
            conn.setex(key, ttl, value)
        else:
            conn.set(key, value)
    
    def delete_test_key(self, key, db=15):
        """
        Helper method to delete a test key from Redis.
        
        Args:
            key: Redis key name
            db: Database number (default: 15)
        """
        conn = redis.Redis(host='127.0.0.1', port=6379, db=db, decode_responses=True)
        conn.delete(key)
    
    def key_exists(self, key, db=15):
        """
        Helper method to check if a key exists in Redis.
        
        Args:
            key: Redis key name
            db: Database number (default: 15)
            
        Returns:
            bool: True if key exists, False otherwise
        """
        conn = redis.Redis(host='127.0.0.1', port=6379, db=db, decode_responses=True)
        return bool(conn.exists(key))
    
    def get_key_value(self, key, db=15):
        """
        Helper method to get a key value from Redis.
        
        Args:
            key: Redis key name
            db: Database number (default: 15)
            
        Returns:
            str: Key value or None if key doesn't exist
        """
        conn = redis.Redis(host='127.0.0.1', port=6379, db=db, decode_responses=True)
        return conn.get(key)
