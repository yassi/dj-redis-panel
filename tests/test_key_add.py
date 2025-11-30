"""
Tests for the Django Redis Panel key addition view using Django TestCase.

The key add view allows users to create new Redis keys of different types
with feature flag support and proper validation.
"""
import os
import redis
from django.urls import reverse
from .base import RedisTestCase


class TestKeyAddView(RedisTestCase):
    """Test cases for the key add view using Django TestCase."""
    
    def test_key_add_requires_staff_permission(self):
        """Test that key add requires staff permission."""
        # Use unauthenticated client
        client = self.create_unauthenticated_client()
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        response = client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_key_add_get_success(self):
        """Test successful key add form rendering."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Key')
        self.assertContains(response, 'Redis Key Types:')
        
        # Check template used
        self.assertTemplateUsed(response, 'admin/dj_redis_panel/key_add.html')
        
        # Check context data
        self.assertEqual(response.context['instance_alias'], 'test_redis')
        self.assertEqual(response.context['selected_db'], 15)
        self.assertTrue(response.context['allow_key_edit'])
        self.assertIsNone(response.context['error_message'])
        self.assertIsNone(response.context['success_message'])

    def test_key_add_nonexistent_instance(self):
        """Test key add with nonexistent instance raises 404."""
        url = reverse('dj_redis_panel:key_add', args=['nonexistent', 15])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_key_add_feature_disabled(self):
        """Test key add when ALLOW_KEY_EDIT feature is disabled."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis_no_features', 14])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['allow_key_edit'])
        self.assertContains(response, 'Key creation is disabled for this instance')
        self.assertContains(response, 'Back to Key Search')
    
    def test_key_add_string_success(self):
        """Test successful string key creation."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Ensure key doesn't exist
        self.assertFalse(self.redis_conn.exists('test:new_string'))
        
        response = self.client.post(url, {
            'key_name': 'test:new_string',
            'key_type': 'string'
        })
        
        # Should redirect to key detail view
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:new_string'])
        self.assertEqual(response.url, expected_redirect)
        
        # Verify key was created in Redis
        self.assertTrue(self.redis_conn.exists('test:new_string'))
        self.assertEqual(self.redis_conn.type('test:new_string'), 'string')
        self.assertEqual(self.redis_conn.get('test:new_string'), '')  # Empty string
        
        # Cleanup
        self.redis_conn.delete('test:new_string')
    
    def test_key_add_list_success(self):
        """Test successful list key creation."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Ensure key doesn't exist
        self.assertFalse(self.redis_conn.exists('test:new_list'))
        
        response = self.client.post(url, {
            'key_name': 'test:new_list',
            'key_type': 'list'
        })
        
        # Should redirect to key detail view
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:new_list'])
        self.assertEqual(response.url, expected_redirect)
        
        # Verify key was created in Redis
        self.assertTrue(self.redis_conn.exists('test:new_list'))
        self.assertEqual(self.redis_conn.type('test:new_list'), 'list')
        self.assertEqual(self.redis_conn.llen('test:new_list'), 1)
        self.assertEqual(self.redis_conn.lindex('test:new_list', 0), '[Edit or delete this placeholder item]')
        
        # Cleanup
        self.redis_conn.delete('test:new_list')
    
    def test_key_add_set_success(self):
        """Test successful set key creation."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Ensure key doesn't exist
        self.assertFalse(self.redis_conn.exists('test:new_set'))
        
        response = self.client.post(url, {
            'key_name': 'test:new_set',
            'key_type': 'set'
        })
        
        # Should redirect to key detail view
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:new_set'])
        self.assertEqual(response.url, expected_redirect)
        
        # Verify key was created in Redis
        self.assertTrue(self.redis_conn.exists('test:new_set'))
        self.assertEqual(self.redis_conn.type('test:new_set'), 'set')
        self.assertEqual(self.redis_conn.scard('test:new_set'), 1)
        self.assertTrue(self.redis_conn.sismember('test:new_set', '[Edit or delete this placeholder member]'))
        
        # Cleanup
        self.redis_conn.delete('test:new_set')
    
    def test_key_add_zset_success(self):
        """Test successful sorted set key creation."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Ensure key doesn't exist
        self.assertFalse(self.redis_conn.exists('test:new_zset'))
        
        response = self.client.post(url, {
            'key_name': 'test:new_zset',
            'key_type': 'zset'
        })
        
        # Should redirect to key detail view
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:new_zset'])
        self.assertEqual(response.url, expected_redirect)
        
        # Verify key was created in Redis
        self.assertTrue(self.redis_conn.exists('test:new_zset'))
        self.assertEqual(self.redis_conn.type('test:new_zset'), 'zset')
        self.assertEqual(self.redis_conn.zcard('test:new_zset'), 1)
        self.assertEqual(self.redis_conn.zscore('test:new_zset', '[Edit or delete this placeholder member]'), 0.0)
        
        # Cleanup
        self.redis_conn.delete('test:new_zset')
    
    def test_key_add_hash_success(self):
        """Test successful hash key creation."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Ensure key doesn't exist
        self.assertFalse(self.redis_conn.exists('test:new_hash'))
        
        response = self.client.post(url, {
            'key_name': 'test:new_hash',
            'key_type': 'hash'
        })
        
        # Should redirect to key detail view
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:new_hash'])
        self.assertEqual(response.url, expected_redirect)
        
        # Verify key was created in Redis
        self.assertTrue(self.redis_conn.exists('test:new_hash'))
        self.assertEqual(self.redis_conn.type('test:new_hash'), 'hash')
        self.assertEqual(self.redis_conn.hlen('test:new_hash'), 1)
        self.assertEqual(self.redis_conn.hget('test:new_hash', '[placeholder_field]'), '[Edit or delete this placeholder field]')
        
        # Cleanup
        self.redis_conn.delete('test:new_hash')
    
    def test_key_add_empty_key_name(self):
        """Test key creation with empty key name."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        response = self.client.post(url, {
            'key_name': '',
            'key_type': 'string'
        })
        
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Key name is required')
        self.assertIsNone(response.context['success_message'])
    
    def test_key_add_whitespace_only_key_name(self):
        """Test key creation with whitespace-only key name."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        response = self.client.post(url, {
            'key_name': '   \t\n   ',
            'key_type': 'string'
        })
        
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Key name is required')
        self.assertIsNone(response.context['success_message'])
    
    def test_key_add_invalid_key_type(self):
        """Test key creation with invalid key type."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        response = self.client.post(url, {
            'key_name': 'test:invalid_type',
            'key_type': 'invalid_type'
        })
        
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Invalid key type selected')
        self.assertIsNone(response.context['success_message'])
    
    def test_key_add_existing_key(self):
        """Test key creation when key already exists."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Key already exists from setup_redis_test_data
        response = self.client.post(url, {
            'key_name': 'test:string',  # This key already exists
            'key_type': 'string'
        })
        
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key 'test:string' already exists")
        self.assertIsNone(response.context['success_message'])
    
    def test_key_add_feature_disabled_post(self):
        """Test POST request when ALLOW_KEY_EDIT feature is disabled."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis_no_features', 14])
        
        response = self.client.post(url, {
            'key_name': 'test:disabled_feature',
            'key_type': 'string'
        })
        
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Key creation is disabled for this instance')
        self.assertIsNone(response.context['success_message'])
        
        # Verify key was NOT created
        conn_14 = redis.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=14, decode_responses=True)
        self.assertFalse(conn_14.exists('test:disabled_feature'))
    
    def test_key_add_special_characters_in_name(self):
        """Test key creation with special characters in key name."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        special_key_names = [
            'test:key-with-dashes',
            'test:key_with_underscores',
            'test:key.with.dots',
            'test:key/with/slashes',
            'test:key:with:colons',
            'test:key with spaces',
            'test:key@with#symbols$',
            'test:key[with]brackets',
            'test:key{with}braces',
            'test:key(with)parentheses',
        ]
        
        for key_name in special_key_names:
            with self.subTest(key_name=key_name):
                # Ensure key doesn't exist
                self.assertFalse(self.redis_conn.exists(key_name))
                
                response = self.client.post(url, {
                    'key_name': key_name,
                    'key_type': 'string'
                })
                
                # Should redirect to key detail view
                self.assertEqual(response.status_code, 302)
                expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
                self.assertEqual(response.url, expected_redirect)
                
                # Verify key was created in Redis
                self.assertTrue(self.redis_conn.exists(key_name))
                self.assertEqual(self.redis_conn.type(key_name), 'string')
                
                # Cleanup
                self.redis_conn.delete(key_name)
    
    def test_key_add_unicode_characters_in_name(self):
        """Test key creation with Unicode characters in key name."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        unicode_key_names = [
            'test:café',
            'test:naïve',
            'test:résumé',
            'test:测试',
            'test:テスト',
            'test:тест',
            'test:🔑key',
            'test:مفتاح',
        ]
        
        for key_name in unicode_key_names:
            with self.subTest(key_name=key_name):
                # Ensure key doesn't exist
                self.assertFalse(self.redis_conn.exists(key_name))
                
                response = self.client.post(url, {
                    'key_name': key_name,
                    'key_type': 'string'
                })
                
                # Should redirect to key detail view
                self.assertEqual(response.status_code, 302)
                expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
                self.assertEqual(response.url, expected_redirect)
                
                # Verify key was created in Redis
                self.assertTrue(self.redis_conn.exists(key_name))
                self.assertEqual(self.redis_conn.type(key_name), 'string')
                
                # Cleanup
                self.redis_conn.delete(key_name)
    
    def test_key_add_very_long_key_name(self):
        """Test key creation with very long key name."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        # Create a very long key name (Redis supports up to 512MB key names)
        long_key_name = 'test:' + 'x' * 1000
        
        # Ensure key doesn't exist
        self.assertFalse(self.redis_conn.exists(long_key_name))
        
        response = self.client.post(url, {
            'key_name': long_key_name,
            'key_type': 'string'
        })
        
        # Should redirect to key detail view
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, long_key_name])
        self.assertEqual(response.url, expected_redirect)
        
        # Verify key was created in Redis
        self.assertTrue(self.redis_conn.exists(long_key_name))
        self.assertEqual(self.redis_conn.type(long_key_name), 'string')
        
        # Cleanup
        self.redis_conn.delete(long_key_name)
    
    def test_key_add_all_key_types_comprehensive(self):
        """Test creating all key types and verify their initial state."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        test_cases = [
            ('string', 'test:comprehensive_string', lambda conn, key: conn.get(key) == ''),
            ('list', 'test:comprehensive_list', lambda conn, key: (
                conn.llen(key) == 1 and 
                conn.lindex(key, 0) == '[Edit or delete this placeholder item]'
            )),
            ('set', 'test:comprehensive_set', lambda conn, key: (
                conn.scard(key) == 1 and 
                conn.sismember(key, '[Edit or delete this placeholder member]')
            )),
            ('zset', 'test:comprehensive_zset', lambda conn, key: (
                conn.zcard(key) == 1 and 
                conn.zscore(key, '[Edit or delete this placeholder member]') == 0.0
            )),
            ('hash', 'test:comprehensive_hash', lambda conn, key: (
                conn.hlen(key) == 1 and 
                conn.hget(key, '[placeholder_field]') == '[Edit or delete this placeholder field]'
            )),
        ]
        
        for key_type, key_name, validator in test_cases:
            with self.subTest(key_type=key_type):
                # Ensure key doesn't exist
                self.assertFalse(self.redis_conn.exists(key_name))
                
                response = self.client.post(url, {
                    'key_name': key_name,
                    'key_type': key_type
                })
                
                # Should redirect to key detail view
                self.assertEqual(response.status_code, 302)
                expected_redirect = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
                self.assertEqual(response.url, expected_redirect)
                
                # Verify key was created with correct type
                self.assertTrue(self.redis_conn.exists(key_name))
                self.assertEqual(self.redis_conn.type(key_name), key_type)
                
                # Verify key has expected initial content
                self.assertTrue(validator(self.redis_conn, key_name), 
                              f"Key {key_name} of type {key_type} does not have expected initial content")
                
                # Cleanup
                self.redis_conn.delete(key_name)
    
    def test_key_add_breadcrumbs_and_context(self):
        """Test that breadcrumbs and context are properly set."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check breadcrumbs are rendered
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Redis Instances')
        self.assertContains(response, 'test_redis')
        self.assertContains(response, 'Search Keys (db:15)')
        self.assertContains(response, 'Add New Key')
        
        # Check context variables
        self.assertEqual(response.context['title'], 'Add New Key - test_redis::DB15')
        self.assertEqual(response.context['instance_alias'], 'test_redis')
        self.assertEqual(response.context['selected_db'], 15)
        self.assertTrue(response.context['has_permission'])
        self.assertIsNotNone(response.context['site_title'])
        self.assertIsNotNone(response.context['site_header'])
    
    def test_key_add_form_preserves_input_on_error(self):
        """Test that form preserves user input when there's an error."""
        url = reverse('dj_redis_panel:key_add', args=['test_redis', 15])
        
        response = self.client.post(url, {
            'key_name': '',  # Invalid: empty name
            'key_type': 'hash'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Key name is required')
        
        # Check that the selected key type is preserved in the form
        self.assertContains(response, 'value="hash" selected')
        
        # Try again with existing key
        response = self.client.post(url, {
            'key_name': 'test:string',  # Existing key
            'key_type': 'list'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", response.context['error_message'])
        
        # Check that both key name and type are preserved
        self.assertContains(response, 'value="test:string"')
        self.assertContains(response, 'value="list" selected')
