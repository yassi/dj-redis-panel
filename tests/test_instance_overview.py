"""
Tests for the Django Redis Panel instance overview view using Django TestCase.

The instance overview view displays detailed information about a specific Redis 
instance including connection status, database information, and key metrics.
"""
import os
import redis
from django.urls import reverse
from .base import RedisTestCase


class TestInstanceOverviewView(RedisTestCase):
    """Test cases for the instance overview view using Django TestCase."""
    
    def get_test_settings(self):
        """Get test settings with additional instance for multi-database testing."""
        settings = super().get_test_settings()
        # Add additional instance for instance overview testing
        settings["INSTANCES"]["test_redis_multi_db"] = {
            "description": "Test Redis Instance - Multiple DBs",
            "host": "127.0.0.1",
            "port": 6379,
            "db": 14,  # Use test database 14
            "features": {
                "ALLOW_KEY_DELETE": False,
                "ALLOW_KEY_EDIT": False,
                "ALLOW_TTL_UPDATE": False,
                "CURSOR_PAGINATED_SCAN": True,
            },
        }
        return settings
    
    def setup_redis_test_data(self):
        """Set up test data specific to instance overview tests."""
        # Call parent to get base test data
        super().setup_redis_test_data()
        
        # Add instance-overview specific test data
        self.redis_conn.select(15)
        
        # Additional keys for instance overview testing
        overview_data = {
            'overview:string': 'string_value',
            'overview:user:123': 'john_doe',
            'overview:user:456': 'jane_doe',
            'overview:cache': 'cached_content',
            'overview:temp': 'temporary_value',
        }
        
        for key, value in overview_data.items():
            self.redis_conn.set(key, value)
        
        # Add key with TTL and additional data types
        self.redis_conn.setex('overview:temp_ttl', 3600, 'temp_with_ttl')
        self.redis_conn.lpush('overview:list', 'item1', 'item2', 'item3')
        self.redis_conn.sadd('overview:set', 'member1', 'member2')
        self.redis_conn.hset('overview:hash', mapping={'field1': 'value1', 'field2': 'value2'})
        self.redis_conn.zadd('overview:zset', {'member1': 1.0, 'member2': 2.0})
        
        # Add specific data to database 14 for multi-database testing
        conn_14 = redis.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=14, decode_responses=True)
        multi_db_data = {
            'multi_db:string': 'test_value',
            'multi_db:counter': '42',
            'multi_db:session': 'session_data',
        }
        for key, value in multi_db_data.items():
            conn_14.set(key, value)
    
    def test_instance_overview_requires_staff_permission(self):
        """Test that instance overview requires staff permission."""
        # Use unauthenticated client
        client = self.create_unauthenticated_client()
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_instance_overview_success(self):
        """Test successful instance overview rendering with real Redis data."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/dj_redis_panel/instance_overview.html')
        
        # Check context data
        context = response.context
        self.assertEqual(context['title'], "Instance Overview: test_redis")
        self.assertEqual(context['instance_alias'], 'test_redis')
        self.assertIn('instance_config', context)
        self.assertIn('hero_numbers', context)
        self.assertIn('databases', context)
        self.assertIsNone(context['error_message'])
        
        # Check hero numbers are populated
        hero_numbers = context['hero_numbers']
        self.assertIn('version', hero_numbers)
        self.assertIn('memory_used', hero_numbers)
        self.assertIn('connected_clients', hero_numbers)
        self.assertIn('uptime', hero_numbers)
        
        # Check databases information
        databases = context['databases']
        self.assertGreater(len(databases), 0)
        
        # Should find database 15 with our test keys
        db15_found = False
        for db in databases:
            if db['db_number'] == 15:
                db15_found = True
                self.assertGreater(db['keys'], 0)  # Should have our test keys
                break
        self.assertTrue(db15_found, "Database 15 should be present in databases list")
    
    def test_instance_overview_nonexistent_instance(self):
        """Test instance overview with nonexistent instance raises 404."""
        url = reverse('dj_redis_panel:instance_overview', args=['nonexistent_instance'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_instance_overview_connection_error(self):
        """Test instance overview when Redis connection fails."""
        # Create a disconnected instance configuration
        disconnected_settings = {
            "INSTANCES": {
                "disconnected_redis": {
                    "description": "Disconnected Redis Instance",
                    "host": "127.0.0.1",
                    "port": 9999,  # Non-existent port
                    "features": {
                        "ALLOW_KEY_DELETE": True,
                        "ALLOW_KEY_EDIT": True,
                        "ALLOW_TTL_UPDATE": True,
                        "CURSOR_PAGINATED_SCAN": False,
                    },
                }
            }
        }
        
        # Update the mock to return disconnected settings
        self.mock_get_settings.return_value = disconnected_settings
        
        url = reverse('dj_redis_panel:instance_overview', args=['disconnected_redis'])
        response = self.client.get(url)
        
        # Should still render successfully but show error
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error_message'])
        # When connection fails, hero_numbers and databases are None, not empty dict/list
        self.assertIsNone(response.context['hero_numbers'])
        self.assertEqual(response.context['databases'], [])
    
    def test_instance_overview_context_structure(self):
        """Test that instance overview provides correct context structure."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Check required context fields
        context = response.context
        required_fields = [
            'title', 'opts', 'has_permission', 'site_title', 
            'site_header', 'site_url', 'user', 'instance_alias',
            'instance_config', 'hero_numbers', 'databases', 'error_message'
        ]
        
        for field in required_fields:
            self.assertIn(field, context, f"Missing context field: {field}")
        
        # Check title format
        self.assertEqual(context['title'], "Instance Overview: test_redis")
        
        # Check instance config structure
        instance_config = context['instance_config']
        self.assertIn('description', instance_config)
        self.assertEqual(instance_config['description'], "Test Redis Instance")
    
    def test_instance_overview_hero_numbers_structure(self):
        """Test that hero numbers contain expected fields and types."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        hero_numbers = response.context['hero_numbers']
        
        # Check that hero numbers contain expected fields
        expected_fields = [
            'version', 'memory_used', 'memory_peak', 
            'connected_clients', 'uptime', 'total_commands_processed'
        ]
        
        for field in expected_fields:
            self.assertIn(field, hero_numbers, f"Missing hero number field: {field}")
        
        # Check data types
        self.assertIsInstance(hero_numbers['version'], str)
        self.assertIsInstance(hero_numbers['connected_clients'], int)
        self.assertIsInstance(hero_numbers['uptime'], int)
        self.assertIsInstance(hero_numbers['total_commands_processed'], int)
        
        # Check that numeric values are reasonable
        self.assertGreaterEqual(hero_numbers['connected_clients'], 0)
        self.assertGreaterEqual(hero_numbers['uptime'], 0)
        self.assertGreaterEqual(hero_numbers['total_commands_processed'], 0)
    
    def test_instance_overview_databases_structure(self):
        """Test that databases information has correct structure."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        databases = response.context['databases']
        self.assertGreater(len(databases), 0)
        
        # Check database structure
        for db in databases:
            required_db_fields = ['db_number', 'keys', 'is_default']
            for field in required_db_fields:
                self.assertIn(field, db, f"Missing database field: {field}")
            
            # Check data types
            self.assertIsInstance(db['db_number'], int)
            self.assertIsInstance(db['keys'], int)
            self.assertIsInstance(db['is_default'], bool)
            
            # Check ranges
            self.assertGreaterEqual(db['db_number'], 0)
            self.assertLessEqual(db['db_number'], 15)  # Redis default max DBs
            self.assertGreaterEqual(db['keys'], 0)
        
        # Database 0 should be marked as default if present
        db_zero = next((db for db in databases if db['db_number'] == 0), None)
        if db_zero:
            self.assertTrue(db_zero['is_default'])
        
        # Non-zero databases should not be default
        non_zero_dbs = [db for db in databases if db['db_number'] != 0]
        for db in non_zero_dbs:
            self.assertFalse(db['is_default'])
    
    def test_instance_overview_multiple_databases(self):
        """Test instance overview with multiple databases containing data."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        databases = response.context['databases']
        
        # Should find our test databases with keys
        db_numbers_with_keys = [db['db_number'] for db in databases if db['keys'] > 0]
        
        # Should include databases 13, 14, 15 since we added test data
        expected_dbs = {13, 14, 15}
        found_dbs = set(db_numbers_with_keys)
        
        # Check that we found at least some of our test databases
        self.assertTrue(expected_dbs.intersection(found_dbs), 
                       f"Expected to find databases {expected_dbs}, but found {found_dbs}")
    
    def test_instance_overview_url_based_instance(self):
        """Test instance overview with URL-based Redis configuration."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis_url'])
        response = self.client.get(url)
        
        # Should work with URL-based configuration
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['instance_alias'], 'test_redis_url')
        
        # Should have hero numbers and database info
        self.assertIsNotNone(response.context['hero_numbers'])
        self.assertGreater(len(response.context['databases']), 0)
    
    def test_instance_overview_database_key_counts(self):
        """Test that database key counts are accurate."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        databases = response.context['databases']
        
        # Find database 15 (our main test database)
        db15 = next((db for db in databases if db['db_number'] == 15), None)
        self.assertIsNotNone(db15, "Database 15 should be present")
        
        # Should have multiple keys from our test data
        # We created: overview:string, overview:user:123, overview:user:456, 
        # overview:cache, overview:temp, overview:temp_ttl, overview:list, 
        # overview:set, overview:hash, overview:zset = 10 keys
        self.assertGreaterEqual(db15['keys'], 10)
    
    def test_instance_overview_empty_database(self):
        """Test instance overview with database that has no keys."""
        # Clean database 15 completely
        self.redis_conn.select(15)
        self.redis_conn.flushdb()
        
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Should still work, but database 15 might not appear in the list
        # (Redis only shows databases with keys or DB 0)
        self.assertEqual(response.status_code, 200)
        
        databases = response.context['databases']
        db15 = next((db for db in databases if db['db_number'] == 15), None)
        
        if db15:
            # If DB 15 appears, it should have 0 keys
            self.assertEqual(db15['keys'], 0)
    
    def test_instance_overview_template_content(self):
        """Test that instance overview template contains expected content."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Check that important content is present
        self.assertContains(response, 'test_redis')
        # Check for generic Redis instance overview content
        self.assertContains(response, 'Instance Overview')
        # Check for hero numbers section content (these should be present)
        hero_numbers = response.context['hero_numbers']
        if hero_numbers and 'version' in hero_numbers:
            self.assertContains(response, hero_numbers['version'])
        # Check for databases section
        self.assertContains(response, 'Database')
        
        # Should contain links to key search for databases with keys
        databases = response.context['databases']
        for db in databases:
            if db['keys'] > 0:
                expected_search_url = reverse('dj_redis_panel:key_search', 
                                            args=['test_redis', db['db_number']])
                # The URL should appear in the response (as a link)
                self.assertContains(response, f'href="{expected_search_url}"')
    
    def test_instance_overview_different_instances(self):
        """Test instance overview with different instance configurations."""
        test_instances = ['test_redis', 'test_redis_multi_db', 'test_redis_url']
        
        for instance_alias in test_instances:
            with self.subTest(instance=instance_alias):
                url = reverse('dj_redis_panel:instance_overview', args=[instance_alias])
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['instance_alias'], instance_alias)
                self.assertIn('hero_numbers', response.context)
                self.assertIn('databases', response.context)
    
    def test_instance_overview_redis_info_integration(self):
        """Test that Redis INFO command data is properly integrated."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        hero_numbers = response.context['hero_numbers']
        
        # Version should be a valid Redis version string
        version = hero_numbers['version']
        self.assertIsInstance(version, str)
        self.assertNotEqual(version, 'Unknown')
        
        # Memory values should be present and formatted
        memory_used = hero_numbers['memory_used']
        self.assertIsInstance(memory_used, str)
        self.assertNotEqual(memory_used, 'Unknown')
        
        # Should contain typical Redis memory format (e.g., "1.23M", "456K")
        self.assertTrue(any(char.isdigit() for char in memory_used))
