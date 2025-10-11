"""
Tests for the Django Redis Panel index view using Django TestCase.

The index view displays a list of configured Redis instances with their
status, connection information, and basic metrics.
"""
from django.urls import reverse
from .base import RedisTestCase


class TestIndexView(RedisTestCase):
    """Test cases for the main index view using Django TestCase."""
    
    def test_index_requires_staff_permission(self):
        """Test that index view requires staff permission."""
        # Use unauthenticated client
        client = self.create_unauthenticated_client()
        url = reverse('dj_redis_panel:index')
        response = client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_index_view_success(self):
        """Test successful index view rendering with real Redis."""
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/dj_redis_panel/index.html')
        
        # Check context data
        self.assertIn('redis_instances', response.context)
        redis_instances = response.context['redis_instances']
        
        # Should have instances from test settings
        self.assertEqual(len(redis_instances), 4)  # test_redis, test_redis_no_features, test_redis_url, test_redis_cursor
        
        # Check instance structure
        for instance in redis_instances:
            self.assertIn('alias', instance)
            self.assertIn('config', instance)
            self.assertIn('status', instance)
            self.assertIn(instance['alias'], ['test_redis', 'test_redis_no_features', 'test_redis_url', 'test_redis_cursor'])
            
            # For connected instances, check they have real data
            if instance['status'] == 'connected':
                self.assertIn('hero_numbers', instance)
                self.assertIn('databases', instance)
                self.assertIsNotNone(instance['hero_numbers'])
    
    def test_index_view_with_connection_error(self):
        """Test index view when Redis connection fails."""
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
        
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        # Should still render successfully
        self.assertEqual(response.status_code, 200)
        
        # Check error handling
        redis_instances = response.context['redis_instances']
        self.assertEqual(len(redis_instances), 1)
        instance = redis_instances[0]
        self.assertEqual(instance['status'], 'disconnected')
        self.assertIsNotNone(instance['error'])
    
    def test_index_view_context_structure(self):
        """Test that index view provides correct context structure."""
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        # Check required context fields
        context = response.context
        required_fields = [
            'title', 'opts', 'has_permission', 'site_title', 
            'site_header', 'site_url', 'user', 'redis_instances'
        ]
        
        for field in required_fields:
            self.assertIn(field, context, f"Missing context field: {field}")
        
        # Check title
        self.assertEqual(context['title'], "DJ Redis Panel - Instances")
        
        # Check redis_instances structure
        redis_instances = context['redis_instances']
        for instance in redis_instances:
            required_instance_fields = [
                'alias', 'config', 'status', 'info', 'error',
                'total_keys', 'hero_numbers', 'databases'
            ]
            for field in required_instance_fields:
                self.assertIn(field, instance, f"Missing instance field: {field}")
    
    def test_index_view_multiple_instances(self):
        """Test index view with multiple Redis instances."""
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        # Check all instances are present
        redis_instances = response.context['redis_instances']
        self.assertEqual(len(redis_instances), 4)
        
        # Check instance aliases are correct
        instance_aliases = {inst['alias'] for inst in redis_instances}
        expected_aliases = {'test_redis', 'test_redis_no_features', 'test_redis_url', 'test_redis_cursor'}
        self.assertEqual(instance_aliases, expected_aliases)
        
        # Check that at least some instances are connected (those using test databases)
        connected_instances = [inst for inst in redis_instances if inst['status'] == 'connected']
        self.assertGreaterEqual(len(connected_instances), 2)  # test_redis and test_redis_no_features should connect
    
    def test_index_view_no_instances_configured(self):
        """Test index view when no Redis instances are configured."""
        # Mock empty instances
        empty_settings = {"INSTANCES": {}}
        self.mock_get_settings.return_value = empty_settings
        
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['redis_instances'], [])
    
    
    def test_index_view_database_information(self):
        """Test that database information is properly populated."""
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        redis_instances = response.context['redis_instances']
        
        for instance in redis_instances:
            if instance['status'] == 'connected':
                databases = instance['databases']
                
                # Should have at least one database with keys
                self.assertGreater(len(databases), 0)
                
                # Check database structure
                for db in databases:
                    required_db_fields = ['db_number', 'keys', 'is_default']
                    for field in required_db_fields:
                        self.assertIn(field, db)
                    
                    # Check that db_number is an integer
                    self.assertIsInstance(db['db_number'], int)
                    
                    # Check that keys count is an integer
                    self.assertIsInstance(db['keys'], int)
                    
                    # Check that is_default is boolean
                    self.assertIsInstance(db['is_default'], bool)
                
                # Database 0 should be marked as default if present
                db_zero = next((db for db in databases if db['db_number'] == 0), None)
                if db_zero:
                    self.assertTrue(db_zero['is_default'])
    
    def test_index_view_instance_alias_is_clickable_link(self):
        """Test that instance alias is rendered as a clickable link for connected instances."""
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Get the HTML content
        content = response.content.decode('utf-8')
        
        # For connected instances, the alias should be a clickable link
        redis_instances = response.context['redis_instances']
        for instance in redis_instances:
            if instance['status'] == 'connected':
                # Check that the instance overview URL is present
                expected_url = reverse('dj_redis_panel:instance_overview', args=[instance['alias']])
                self.assertIn(expected_url, content)
                
                # Check that the alias appears within a link tag
                link_pattern = f'<a href="{expected_url}" class="default">'
                self.assertIn(link_pattern, content)
            else:
                # For disconnected instances, alias should not be a link
                # Just verify the alias is shown as plain text
                self.assertIn(f'<strong>{instance["alias"]}</strong>', content)
        
        # Verify the Actions column header is removed
        self.assertNotIn('{% trans \'Actions\' %}', content)
        # Verify the "Browse Instance" link text is not present in Actions column
        # (it might still be in breadcrumbs or elsewhere, but not as a separate action)
        # We can check that the pattern doesn't appear with the 'Browse Instance' translation
        self.assertNotIn('<td>\n                        {% if instance.status', content)

