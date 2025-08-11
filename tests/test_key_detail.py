"""
Tests for the Django Redis Panel key detail view using Django TestCase.

The key detail view displays detailed information about a specific Redis key
and provides CRUD operations (view, edit value, update TTL, delete) with
feature flag support.
"""
import redis
from django.urls import reverse
from .base import RedisTestCase


class TestKeyDetailView(RedisTestCase):
    """Test cases for the key detail view using Django TestCase."""
    
    def test_key_detail_requires_staff_permission(self):
        """Test that key detail requires staff permission."""
        # Use unauthenticated client
        client = self.create_unauthenticated_client()
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        response = client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_key_detail_success(self):
        """Test successful key detail rendering with real Redis data."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test:string')
        
        # Check template used
        self.assertTemplateUsed(response, 'admin/dj_redis_panel/key_detail.html')
        
        # Check context data
        self.assertIn('key_data', response.context)
        key_data = response.context['key_data']
        
        self.assertEqual(key_data['name'], 'test:string')
        self.assertEqual(key_data['type'], 'string')
        self.assertEqual(key_data['value'], 'test_value')
        self.assertTrue(key_data['exists'])
        
        # Check feature flags
        self.assertTrue(response.context['allow_key_delete'])
        self.assertTrue(response.context['allow_key_edit'])
        self.assertTrue(response.context['allow_ttl_update'])
    
    def test_key_detail_nonexistent_instance(self):
        """Test key detail with nonexistent instance raises 404."""
        url = reverse('dj_redis_panel:key_detail', args=['nonexistent', 15, 'test_key'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_key_detail_nonexistent_key(self):
        """Test key detail with nonexistent key raises 404."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'nonexistent_key'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_key_detail_different_key_types(self):
        """Test key detail view with different Redis key types."""
        key_tests = [
            ('test:string', 'string'),
            ('test:list', 'list'),
            ('test:set', 'set'),
            ('test:hash', 'hash'),
            ('test:zset', 'zset'),
        ]
        
        for key_name, expected_type in key_tests:
            with self.subTest(key=key_name, type=expected_type):
                url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['key_data']['type'], expected_type)
                self.assertEqual(response.context['key_data']['name'], key_name)
                self.assertTrue(response.context['key_data']['exists'])
    
    def test_key_detail_feature_flags_disabled(self):
        """Test key detail with feature flags disabled."""
        # First, create the key in database 14
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        conn_14.set('test:string', 'test_value')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, 'test:string'])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['allow_key_delete'])
            self.assertFalse(response.context['allow_key_edit'])
            self.assertFalse(response.context['allow_ttl_update'])
        finally:
            # Cleanup
            conn_14.delete('test:string')
    
    def test_key_detail_update_value_success(self):
        """Test successful key value update with real Redis."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        
        response = self.client.post(url, {
            'action': 'update_value',
            'new_value': 'updated_value'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Key value updated successfully")
        self.assertEqual(response.context['key_data']['value'], 'updated_value')
        
        # Verify the value was actually updated in Redis
        actual_value = self.redis_conn.get('test:string')
        self.assertEqual(actual_value, 'updated_value')
    
    def test_key_detail_update_value_disabled(self):
        """Test key value update when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        conn_14.set('test:string', 'original_value')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, 'test:string'])
            response = self.client.post(url, {
                'action': 'update_value',
                'new_value': 'updated_value'
            })
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
            
            # Verify the value was NOT updated in Redis
            actual_value = conn_14.get('test:string')
            self.assertEqual(actual_value, 'original_value')
        finally:
            # Cleanup
            conn_14.delete('test:string')
    
    def test_key_detail_update_value_non_string_key(self):
        """Test key value update on non-string key type."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:list'])
        
        response = self.client.post(url, {
            'action': 'update_value',
            'new_value': 'updated_value'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Direct editing not supported for list keys", response.context['error_message'])
    
    def test_key_detail_update_ttl_success(self):
        """Test successful TTL update with real Redis."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        
        response = self.client.post(url, {
            'action': 'update_ttl',
            'new_ttl': '7200'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "TTL set to 7200 seconds")
        self.assertEqual(response.context['key_data']['ttl'], 7200)
        
        # Verify the TTL was actually set in Redis
        actual_ttl = self.redis_conn.ttl('test:string')
        self.assertGreater(actual_ttl, 7190)  # Allow some margin for test execution time
    
    def test_key_detail_remove_ttl_success(self):
        """Test successful TTL removal (persist) with real Redis."""
        # First set a TTL on the key
        self.redis_conn.expire('test:string', 3600)
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        response = self.client.post(url, {
            'action': 'update_ttl',
            'new_ttl': ''  # Empty string removes TTL
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "TTL removed (key will not expire)")
        self.assertIsNone(response.context['key_data']['ttl'])
        
        # Verify the TTL was actually removed in Redis
        actual_ttl = self.redis_conn.ttl('test:string')
        self.assertEqual(actual_ttl, -1)  # -1 means no expiration
    
    def test_key_detail_update_ttl_invalid_value(self):
        """Test TTL update with invalid value."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        
        response = self.client.post(url, {
            'action': 'update_ttl',
            'new_ttl': 'invalid'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "TTL must be a valid number")
    
    def test_key_detail_update_ttl_negative_value(self):
        """Test TTL update with negative value."""
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:string'])
        
        response = self.client.post(url, {
            'action': 'update_ttl',
            'new_ttl': '-100'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "TTL must be a positive number")
    
    def test_key_detail_delete_key_success(self):
        """Test successful key deletion with real Redis."""
        # Create a test key specifically for deletion
        self.redis_conn.set('test:delete_me', 'to_be_deleted')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, 'test:delete_me'])
        response = self.client.post(url, {
            'action': 'delete_key'
        })
        
        # Should redirect to key search with success message
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse('dj_redis_panel:key_search', args=['test_redis', 15]) + '?deleted=1'
        self.assertEqual(response.url, expected_redirect)
        
        # Verify the key was actually deleted from Redis
        self.assertFalse(self.redis_conn.exists('test:delete_me'))
    
    def test_key_detail_delete_key_disabled(self):
        """Test key deletion when feature is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        conn_14.set('test:no_delete', 'protected_value')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, 'test:no_delete'])
            response = self.client.post(url, {
                'action': 'delete_key'
            })
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['error_message'], "Key deletion is disabled for this instance")
            
            # Verify the key was NOT deleted from Redis
            self.assertTrue(conn_14.exists('test:no_delete'))
        finally:
            # Cleanup
            conn_14.delete('test:no_delete')
    
    def test_key_detail_key_with_slashes(self):
        """Test key detail with key names containing slashes."""
        key_with_slashes = 'cache/user/123/data'
        
        # Create the key in Redis
        self.redis_conn.set(key_with_slashes, 'slash_test_value')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_with_slashes])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['key_data']['name'], key_with_slashes)
            self.assertEqual(response.context['key_data']['value'], 'slash_test_value')
        finally:
            # Cleanup
            self.redis_conn.delete(key_with_slashes)
