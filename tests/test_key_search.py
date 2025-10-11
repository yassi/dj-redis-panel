"""
Tests for the Django Redis Panel key search view using Django TestCase.

The key search view provides paginated search functionality for Redis keys
with support for both traditional page-based and cursor-based pagination.
"""
import redis
from django.urls import reverse
from dj_redis_panel.views import _get_page_range

from .base import RedisTestCase


class TestKeySearchView(RedisTestCase):
    """Test cases for the key search view using Django TestCase."""
    
    def test_key_search_requires_staff_permission(self):
        """Test that key search requires staff permission."""
        # Use unauthenticated client
        client = self.create_unauthenticated_client()
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_key_search_success(self):
        """Test successful key search rendering with real Redis data."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/dj_redis_panel/key_search.html')
        
        # Check context data
        context = response.context
        self.assertEqual(context['title'], "test_redis::DB15::Key Search")
        self.assertEqual(context['selected_db'], 15)
        self.assertEqual(context['search_query'], "*")
        self.assertGreaterEqual(context['total_keys'], 10)  # Should find our test keys
        self.assertGreater(context['showing_keys'], 0)
        self.assertGreater(len(context['keys_data']), 0)
        self.assertIsNone(context['error_message'])
        self.assertFalse(context['use_cursor_pagination'])
    
    def test_key_search_nonexistent_instance(self):
        """Test key search with nonexistent instance raises 404."""
        url = reverse('dj_redis_panel:key_search', args=['nonexistent', 15])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_key_search_with_pattern(self):
        """Test key search with specific pattern."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url, {'q': 'user:*'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_query'], 'user:*')
        
        # Should find the user:123 and user:456 keys from our test data
        keys_data = response.context['keys_data']
        user_keys = [key for key in keys_data if key['key'].startswith('user:')]
        self.assertGreaterEqual(len(user_keys), 2)
    
    def test_key_search_pagination_parameters(self):
        """Test key search with pagination parameters."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url, {
            'page': '1',
            'per_page': '10'  # Use 10 instead of 5, as 5 is not in the allowed values
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['per_page'], 10)
        self.assertEqual(response.context['current_page'], 1)
        
        # Should limit results to 10 per page
        self.assertLessEqual(len(response.context['keys_data']), 10)
    
    def test_key_search_invalid_pagination_parameters(self):
        """Test key search with invalid pagination parameters."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url, {
            'page': 'invalid',
            'per_page': '999'  # Not in allowed values
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['per_page'], 25)  # Should default to 25
        self.assertEqual(response.context['current_page'], 1)  # Should default to 1
    
    def test_key_search_cursor_pagination(self):
        """Test key search with cursor-based pagination enabled."""
        # Set up data in database 14 for the cursor pagination instance
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        conn_14.set('cursor_test:1', 'value1')
        conn_14.set('cursor_test:2', 'value2')
        
        try:
            url = reverse('dj_redis_panel:key_search', args=['test_redis_no_features', 14])
            response = self.client.get(url, {'cursor': '0'})
            
            self.assertEqual(response.status_code, 200)
            
            # Check cursor-specific context
            self.assertTrue(response.context['use_cursor_pagination'])
            self.assertIn('current_cursor', response.context)
            self.assertIn('next_cursor', response.context)
        finally:
            # Cleanup
            conn_14.flushdb()
    
    def test_key_search_success_message(self):
        """Test key search with success message (e.g., after key deletion)."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url, {'deleted': '1'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Key deleted successfully")
        self.assertIsNone(response.context['error_message'])
    
    def test_key_search_context_structure(self):
        """Test that key search provides correct context structure."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url)
        
        # Check required context fields
        context = response.context
        required_fields = [
            'title', 'opts', 'has_permission', 'site_title', 
            'site_header', 'site_url', 'user', 'instance_alias',
            'instance_config', 'search_query', 'selected_db',
            'keys_data', 'total_keys', 'showing_keys', 'error_message',
            'success_message', 'per_page', 'current_page', 'total_pages',
            'has_previous', 'has_next', 'use_cursor_pagination'
        ]
        
        for field in required_fields:
            self.assertIn(field, context, f"Missing context field: {field}")
    
    def test_key_search_different_databases(self):
        """Test key search across different database numbers."""
        # Add data to different databases
        for db_num in [13, 14]:
            conn = redis.Redis(host='127.0.0.1', port=6379, db=db_num, decode_responses=True)
            conn.set(f'db_{db_num}_key', f'db_{db_num}_value')
        
        try:
            # Test DB 15 (already has data)
            url_db15 = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
            response_db15 = self.client.get(url_db15)
            
            self.assertEqual(response_db15.status_code, 200)
            self.assertEqual(response_db15.context['selected_db'], 15)
            self.assertEqual(response_db15.context['title'], "test_redis::DB15::Key Search")
            
            # Test DB 14 (with cursor pagination enabled)
            url_db14 = reverse('dj_redis_panel:key_search', args=['test_redis_no_features', 14])
            response_db14 = self.client.get(url_db14)
            
            self.assertEqual(response_db14.status_code, 200)
            self.assertEqual(response_db14.context['selected_db'], 14)
            self.assertEqual(response_db14.context['title'], "test_redis_no_features::DB14::Key Search")
        finally:
            # Cleanup
            for db_num in [13, 14]:
                conn = redis.Redis(host='127.0.0.1', port=6379, db=db_num, decode_responses=True)
                conn.flushdb()
    
    def test_key_search_per_page_options(self):
        """Test key search with different per_page options."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        valid_per_page_values = [10, 25, 50, 100]
        
        for per_page in valid_per_page_values:
            with self.subTest(per_page=per_page):
                response = self.client.get(url, {'per_page': str(per_page)})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['per_page'], per_page)
    
    def test_key_search_empty_results(self):
        """Test key search with no matching keys."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url, {'q': 'nonexistent:*'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_query'], 'nonexistent:*')
        
        # Should find no keys
        self.assertEqual(len(response.context['keys_data']), 0)
        self.assertEqual(response.context['total_keys'], 0)
        self.assertEqual(response.context['showing_keys'], 0)
    
    def test_key_search_key_types_displayed(self):
        """Test that different key types are properly displayed in search results."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url, {'q': 'test:*'})
        
        self.assertEqual(response.status_code, 200)
        
        keys_data = response.context['keys_data']
        
        # Should find our test keys of different types
        key_types_found = {key['type'] for key in keys_data}
        expected_types = {'string', 'list', 'set', 'hash', 'zset'}
        
        # Should find at least some of these types
        self.assertTrue(key_types_found.intersection(expected_types))
        
        # Check that each key has required fields
        for key_data in keys_data:
            required_fields = ['key', 'type', 'ttl', 'size']
            for field in required_fields:
                self.assertIn(field, key_data)
    
    def test_key_search_pagination_navigation(self):
        """Test key search pagination navigation with many keys."""
        # Add more keys to test pagination
        for i in range(50):
            self.redis_conn.set(f'pagination_test:{i}', f'value_{i}')
        
        try:
            url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
            response = self.client.get(url, {'per_page': '10', 'q': 'pagination_test:*'})
            
            self.assertEqual(response.status_code, 200)
            
            context = response.context
            self.assertEqual(context['per_page'], 10)
            self.assertGreaterEqual(context['total_keys'], 50)
            self.assertGreater(context['total_pages'], 1)
            
            # Should have pagination navigation
            self.assertIn('page_range', context)
            
            # Test second page
            response_page2 = self.client.get(url, {
                'per_page': '10', 
                'q': 'pagination_test:*',
                'page': '2'
            })
            
            self.assertEqual(response_page2.status_code, 200)
            self.assertEqual(response_page2.context['current_page'], 2)
            self.assertTrue(response_page2.context['has_previous'])
        finally:
            # Cleanup pagination test keys
            for i in range(50):
                self.redis_conn.delete(f'pagination_test:{i}')
    
    def test_key_search_key_name_is_clickable_link(self):
        """Test that key names are rendered as clickable links."""
        url = reverse('dj_redis_panel:key_search', args=['test_redis', 15])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Get the HTML content
        content = response.content.decode('utf-8')
        
        # For all keys, the key name should be a clickable link
        keys_data = response.context['keys_data']
        self.assertGreater(len(keys_data), 0, "Should have test keys")
        
        for key_info in keys_data:
            key_name = key_info['key']
            # Check that the key detail URL is present
            expected_url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, key_name])
            self.assertIn(expected_url, content)
            
            # Check that the key name appears within a link tag
            # The key name should be wrapped in both <a> and <strong> tags
            self.assertIn(f'<a href="{expected_url}" class="default">', content)
            self.assertIn(f'<strong>{key_name}</strong>', content)
        
        # Verify the Actions column header is removed
        # Actions column should not be present in the table headers
        self.assertNotIn('>Actions<', content)


class TestGetPageRange(RedisTestCase):
    """Test cases for the _get_page_range utility function."""
    
    def setUp(self):
        """
        Skip all the data setup for this test case
        """
        pass
    
    def test_get_page_range_scenarios(self):
        """Test _get_page_range with comprehensive test cases."""
        test_cases = [
            # Small page counts (≤ 10) - should return all pages
            {"current": 1, "total": 1, "expected": [1], "description": "Single page"},
            {"current": 1, "total": 2, "expected": [1, 2], "description": "Two pages"},
            {"current": 2, "total": 2, "expected": [1, 2], "description": "Two pages, current=2"},
            {"current": 1, "total": 5, "expected": [1, 2, 3, 4, 5], "description": "Five pages"},
            {"current": 5, "total": 10, "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "description": "Ten pages, current=5"},
            {"current": 10, "total": 10, "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "description": "Ten pages, current=10"},
            
            # Edge case: 11 pages (first large case)
            {"current": 1, "total": 11, "expected": [1, 2, 3, 4, 5, 6, "...", 11], "description": "11 pages, current=1"},
            {"current": 6, "total": 11, "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], "description": "11 pages, current=6 (no ellipsis)"},
            {"current": 11, "total": 11, "expected": [1, "...", 6, 7, 8, 9, 10, 11], "description": "11 pages, current=11"},
            
            # Large page counts - current page at beginning
            {"current": 1, "total": 100, "expected": [1, 2, 3, 4, 5, 6, "...", 100], "description": "100 pages, current=1"},
            {"current": 2, "total": 100, "expected": [1, 2, 3, 4, 5, 6, 7, "...", 100], "description": "100 pages, current=2"},
            {"current": 3, "total": 100, "expected": [1, 2, 3, 4, 5, 6, 7, 8, "...", 100], "description": "100 pages, current=3"},
            
            # Large page counts - current page at end
            {"current": 100, "total": 100, "expected": [1, "...", 95, 96, 97, 98, 99, 100], "description": "100 pages, current=100"},
            {"current": 99, "total": 100, "expected": [1, "...", 94, 95, 96, 97, 98, 99, 100], "description": "100 pages, current=99"},
            {"current": 98, "total": 100, "expected": [1, "...", 93, 94, 95, 96, 97, 98, 99, 100], "description": "100 pages, current=98"},
            
            # Large page counts - current page in middle
            {"current": 50, "total": 100, "expected": [1, "...", 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, "...", 100], "description": "100 pages, current=50"},
            {"current": 25, "total": 100, "expected": [1, "...", 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, "...", 100], "description": "100 pages, current=25"},
            {"current": 75, "total": 100, "expected": [1, "...", 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, "...", 100], "description": "100 pages, current=75"},
            
            # Range connection cases
            {"current": 4, "total": 20, "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, "...", 20], "description": "20 pages, current=4 (range includes first)"},
            {"current": 17, "total": 20, "expected": [1, "...", 12, 13, 14, 15, 16, 17, 18, 19, 20], "description": "20 pages, current=17 (range includes last)"},
            
            # Edge cases with invalid inputs
            {"current": 15, "total": 10, "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "description": "current > total (graceful handling)"},
            {"current": 0, "total": 10, "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "description": "current = 0 (graceful handling)"},
            {"current": 1, "total": 0, "expected": [], "description": "total = 0 (edge case)"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                result = _get_page_range(case["current"], case["total"])
                self.assertEqual(
                    result, 
                    case["expected"], 
                    f"Failed for {case['description']}: "
                    f"_get_page_range({case['current']}, {case['total']}) = {result}, "
                    f"expected {case['expected']}"
                )
