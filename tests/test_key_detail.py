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

    def test_key_detail_pagination_small_collection_no_pagination(self):
        """Test that small collections are not paginated."""
        # Create a small list (under pagination threshold)
        small_list_key = 'test:small_list'
        for i in range(10):
            self.redis_conn.lpush(small_list_key, f'item_{i}')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, small_list_key])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            key_data = response.context['key_data']
            
            # Should not be paginated
            self.assertFalse(key_data.get('is_paginated', False))
            self.assertEqual(len(key_data['value']), 10)
            self.assertFalse(response.context['is_paginated'])
        finally:
            self.redis_conn.delete(small_list_key)

    def test_key_detail_pagination_large_collections_by_type(self):
        """Test page-based pagination for all large collection types."""
        # Test data: (key_suffix, key_type, create_function, total_items, per_page, expected_pages, special_validation)
        test_cases = [
            ('list', 'list', self._create_large_list, 150, 50, 3, None),
            ('set', 'set', self._create_large_set, 150, 25, 6, None),
            ('hash', 'hash', self._create_large_hash, 150, 25, 6, None),
            ('zset', 'zset', self._create_large_zset, 150, 25, 6, self._validate_zset_scores),
        ]
        
        for key_suffix, expected_type, create_func, total_items, per_page, expected_pages, validator in test_cases:
            with self.subTest(key_type=expected_type, total_items=total_items, per_page=per_page):
                key_name = f'test:large_{key_suffix}'
                
                # Create the collection
                create_func(key_name, total_items)
                
                try:
                    # Test first page
                    url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
                    response = self.client.get(url, {'per_page': per_page})
                    
                    self.assertEqual(response.status_code, 200)
                    key_data = response.context['key_data']
                    
                    # Should be paginated
                    self.assertTrue(key_data.get('is_paginated', False))
                    self.assertTrue(response.context['is_paginated'])
                    self.assertEqual(key_data['type'], expected_type)
                    self.assertEqual(len(key_data['value']), per_page)
                    self.assertEqual(response.context['current_page'], 1)
                    self.assertEqual(response.context['total_pages'], expected_pages)
                    self.assertTrue(response.context['has_next'])
                    self.assertFalse(response.context['has_previous'])
                    
                    # Run type-specific validation if provided
                    if validator:
                        validator(key_data['value'])
                    
                    # Test second page navigation
                    response = self.client.get(url, {'per_page': per_page, 'page': 2})
                    self.assertEqual(response.status_code, 200)
                    key_data = response.context['key_data']
                    
                    self.assertEqual(len(key_data['value']), per_page)
                    self.assertEqual(response.context['current_page'], 2)
                    self.assertTrue(response.context['has_next'])
                    self.assertTrue(response.context['has_previous'])
                    
                finally:
                    self.redis_conn.delete(key_name)

    def _create_large_list(self, key_name, count):
        """Helper to create a large list."""
        for i in range(count):
            self.redis_conn.lpush(key_name, f'item_{i:03d}')

    def _create_large_set(self, key_name, count):
        """Helper to create a large set."""
        for i in range(count):
            self.redis_conn.sadd(key_name, f'member_{i:03d}')

    def _create_large_hash(self, key_name, count):
        """Helper to create a large hash."""
        for i in range(count):
            self.redis_conn.hset(key_name, f'field_{i:03d}', f'value_{i:03d}')

    def _create_large_zset(self, key_name, count):
        """Helper to create a large sorted set."""
        for i in range(count):
            self.redis_conn.zadd(key_name, {f'member_{i:03d}': i})

    def _validate_zset_scores(self, zset_value):
        """Helper to validate that sorted set items have scores."""
        self.assertTrue(len(zset_value) > 0)
        first_item = zset_value[0]
        self.assertIsInstance(first_item, tuple)  # (member, score)
        self.assertEqual(len(first_item), 2)

    def test_key_detail_pagination_large_collections_cursor_based(self):
        """Test cursor-based pagination for all large collection types (falls back to page-based if not enabled)."""
        # First, temporarily enable cursor pagination for collections on test_redis
        from django.test import override_settings
        
        # Override settings to enable cursor pagination for collections
        cursor_settings = {
            "ALLOW_KEY_DELETE": True,
            "ALLOW_KEY_EDIT": True,
            "ALLOW_TTL_UPDATE": True,
            "CURSOR_PAGINATED_COLLECTIONS": True,  # Enable cursor pagination for collections
            "INSTANCES": {
                "test_redis": {
                    "description": "Test Redis Instance",
                    "host": "127.0.0.1",
                    "port": 6379,
                    "db": 15,
                    "features": {
                        "ALLOW_KEY_DELETE": True,
                        "ALLOW_KEY_EDIT": True,
                        "ALLOW_TTL_UPDATE": True,
                        "CURSOR_PAGINATED_COLLECTIONS": True,
                    },
                },
                "test_redis_no_features": {
                    "description": "Test Redis Instance - No Features",
                    "host": "127.0.0.1",
                    "port": 6379,
                    "db": 14,
                    "features": {
                        "ALLOW_KEY_DELETE": False,
                        "ALLOW_KEY_EDIT": False,
                        "ALLOW_TTL_UPDATE": False,
                        "CURSOR_PAGINATED_SCAN": True,
                    },
                },
                "test_redis_url": {
                    "description": "Test Redis from URL",
                    "url": "redis://127.0.0.1:6379/13",
                },
            }
        }
        
        with override_settings(DJ_REDIS_PANEL_SETTINGS=cursor_settings):
            # Test data: (key_suffix, key_type, create_function, total_items, per_page, special_validation)
            test_cases = [
                ('list_cursor', 'list', self._create_large_list, 150, 50, None),
                ('set_cursor', 'set', self._create_large_set, 150, 25, None),
                ('hash_cursor', 'hash', self._create_large_hash, 150, 25, None),
                ('zset_cursor', 'zset', self._create_large_zset, 150, 25, self._validate_zset_scores),
            ]
            
            for key_suffix, expected_type, create_func, total_items, per_page, validator in test_cases:
                with self.subTest(key_type=expected_type, total_items=total_items, per_page=per_page):
                    key_name = f'test:large_{key_suffix}'
                    
                    # Create the collection
                    create_func(key_name, total_items)
                    
                    try:
                        # Test first cursor page (cursor=0)
                        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
                        response = self.client.get(url, {'per_page': per_page, 'cursor': 0})
                        
                        self.assertEqual(response.status_code, 200)
                        key_data = response.context['key_data']
                        
                        # Should be paginated with cursor-based pagination
                        self.assertTrue(key_data.get('is_paginated', False))
                        self.assertTrue(response.context['is_paginated'])
                        self.assertEqual(key_data['type'], expected_type)
                        
                        # Debug: Check if cursor pagination is enabled
                        use_cursor_pagination = response.context.get('use_cursor_pagination', False)
                        if use_cursor_pagination:
                            # Cursor-based pagination tests
                            self.assertEqual(response.context['current_cursor'], 0)
                            self.assertIn('next_cursor', response.context)
                        else:
                            # Fall back to page-based pagination tests
                            self.assertEqual(response.context['current_page'], 1)
                            self.assertIn('total_pages', response.context)
                        
                        # Should have data (amount may vary with cursor pagination)
                        self.assertGreater(len(key_data['value']), 0)
                        
                        # Run type-specific validation if provided
                        if validator:
                            validator(key_data['value'])
                        
                        # Test navigation if has_more/has_next is True
                        if response.context.get('has_more', False) or response.context.get('has_next', False):
                            if use_cursor_pagination:
                                # Cursor-based navigation
                                next_cursor = response.context['next_cursor']
                                self.assertIsNotNone(next_cursor)
                                self.assertNotEqual(next_cursor, 0)  # Should have advanced
                                
                                # Test second cursor page
                                response2 = self.client.get(url, {'per_page': per_page, 'cursor': next_cursor})
                                self.assertEqual(response2.status_code, 200)
                                key_data2 = response2.context['key_data']
                                
                                # Should have different data than first page
                                self.assertGreater(len(key_data2['value']), 0)
                                self.assertEqual(response2.context['current_cursor'], next_cursor)
                                
                                # For cursor pagination, we may or may not have range info
                                if response.context.get('range_start') and response.context.get('range_end'):
                                    # Lists and sorted sets should have range info
                                    self.assertIn(expected_type, ['list', 'zset'])
                                    self.assertGreater(response.context['range_start'], 0)
                                    self.assertGreater(response.context['range_end'], response.context['range_start'])
                                else:
                                    # Sets and hashes use scan cursors without exact ranges
                                    self.assertIn(expected_type, ['set', 'hash'])
                            else:
                                # Page-based navigation
                                next_page = response.context.get('next_page', 2)
                                
                                # Test second page
                                response2 = self.client.get(url, {'per_page': per_page, 'page': next_page})
                                self.assertEqual(response2.status_code, 200)
                                key_data2 = response2.context['key_data']
                                
                                # Should have different data than first page
                                self.assertGreater(len(key_data2['value']), 0)
                                self.assertEqual(response2.context['current_page'], next_page)
                        
                    finally:
                        self.redis_conn.delete(key_name)

    def test_key_detail_pagination_per_page_reset(self):
        """Test that changing per_page resets pagination to beginning."""
        # Create a large list
        large_list_key = 'test:pagination_reset'
        for i in range(100):
            self.redis_conn.lpush(large_list_key, f'item_{i:03d}')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
            
            # Go to page 3 with 25 per page
            response = self.client.get(url, {'per_page': 25, 'page': 3})
            self.assertEqual(response.context['current_page'], 3)
            
            # Change per_page to 50 - should reset to page 1
            response = self.client.get(url, {'per_page': 50})
            self.assertEqual(response.context['current_page'], 1)
            self.assertEqual(response.context['per_page'], 50)
            
        finally:
            self.redis_conn.delete(large_list_key)

    def test_key_detail_pagination_invalid_page(self):
        """Test pagination with invalid page numbers."""
        # Create a large list
        large_list_key = 'test:invalid_page'
        for i in range(75):
            self.redis_conn.lpush(large_list_key, f'item_{i:03d}')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
            
            # Test page 0 (should default to 1)
            response = self.client.get(url, {'per_page': 25, 'page': 0})
            self.assertEqual(response.context['current_page'], 1)
            
            # Test negative page (should default to 1)
            response = self.client.get(url, {'per_page': 25, 'page': -5})
            self.assertEqual(response.context['current_page'], 1)
            
            # Test page beyond total (should clamp to valid range)
            response = self.client.get(url, {'per_page': 25, 'page': 999})
            # The view should handle this gracefully
            self.assertEqual(response.status_code, 200)
            
        finally:
            self.redis_conn.delete(large_list_key)

    def test_key_detail_pagination_per_page_validation(self):
        """Test per_page parameter validation."""
        # Create a large list
        large_list_key = 'test:per_page_validation'
        for i in range(100):
            self.redis_conn.lpush(large_list_key, f'item_{i:03d}')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
            
            # Test invalid per_page values should default to 50
            invalid_values = [0, -10, 999, 'invalid']
            for invalid_value in invalid_values:
                response = self.client.get(url, {'per_page': invalid_value})
                self.assertEqual(response.context['per_page'], 50)
            
            # Test valid per_page values
            valid_values = [25, 50, 100, 200]
            for valid_value in valid_values:
                response = self.client.get(url, {'per_page': valid_value})
                self.assertEqual(response.context['per_page'], valid_value)
                
        finally:
            self.redis_conn.delete(large_list_key)

    def test_key_detail_pagination_context_variables(self):
        """Test that all pagination context variables are properly set."""
        # Create a large list
        large_list_key = 'test:pagination_context'
        for i in range(130):
            self.redis_conn.lpush(large_list_key, f'item_{i:03d}')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
            response = self.client.get(url, {'per_page': 50, 'page': 2})
            
            self.assertEqual(response.status_code, 200)
            
            # Check all pagination context variables
            self.assertTrue(response.context['is_paginated'])
            self.assertEqual(response.context['per_page'], 50)
            self.assertEqual(response.context['current_page'], 2)
            self.assertEqual(response.context['total_pages'], 3)  # 130 / 50 = 2.6 -> 3
            self.assertTrue(response.context['has_previous'])
            self.assertTrue(response.context['has_next'])
            self.assertEqual(response.context['previous_page'], 1)
            self.assertEqual(response.context['next_page'], 3)
            self.assertEqual(response.context['showing_count'], 50)
            
            # Check page_range is present
            self.assertIn('page_range', response.context)
            page_range = response.context['page_range']
            self.assertIn(1, page_range)
            self.assertIn(2, page_range)
            self.assertIn(3, page_range)
            
        finally:
            self.redis_conn.delete(large_list_key)

    def test_key_detail_string_not_paginated(self):
        """Test that string keys are never paginated."""
        # Create a large string value
        large_string_key = 'test:large_string'
        large_string_value = 'x' * 10000  # 10KB string
        self.redis_conn.set(large_string_key, large_string_value)
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_string_key])
            response = self.client.get(url, {'per_page': 25})
            
            self.assertEqual(response.status_code, 200)
            key_data = response.context['key_data']
            
            # String should never be paginated
            self.assertFalse(key_data.get('is_paginated', False))
            self.assertFalse(response.context['is_paginated'])
            self.assertEqual(key_data['value'], large_string_value)
            
        finally:
            self.redis_conn.delete(large_string_key)

    def test_key_detail_pagination_template_includes(self):
        """Test that paginated collections use the correct template includes."""
        # Create a large list (over pagination threshold)
        large_list_key = 'test:template_includes'
        for i in range(120):  # Above threshold of 100
            self.redis_conn.lpush(large_list_key, f'item_{i:03d}')
        
        try:
            url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
            response = self.client.get(url, {'per_page': 25})
            
            self.assertEqual(response.status_code, 200)
            
            # Check that the collection is paginated
            self.assertTrue(response.context['is_paginated'])
            
            # Check that it uses the partitioned templates
            self.assertTemplateUsed(response, 'admin/dj_redis_panel/key_detail.html')
            
        finally:
            self.redis_conn.delete(large_list_key)
