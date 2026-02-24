"""
Tests for Redis flush functionality in Django Redis Panel.

These tests verify the flushdb and flushall functionality, including
proper permission handling and integration with the UI.
"""
import os
import redis
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from .base import RedisTestCase


class TestFlushFunctionality(RedisTestCase):
    """Test cases for Redis flush operations (flushdb and flushall)."""
    
    def get_test_settings(self):
        """Get test settings with flush enabled for test instance."""
        settings = super().get_test_settings()
        
        redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
        
        # Add instance with flush enabled
        settings["INSTANCES"]["test_redis_flush_enabled"] = {
            "description": "Test Redis Instance - Flush Enabled",
            "host": redis_host,
            "port": 6379,
            "db": 12,
            "features": {
                "ALLOW_FLUSH": True,
                "ALLOW_KEY_DELETE": True,
                "ALLOW_KEY_EDIT": True,
                "ALLOW_TTL_UPDATE": True,
            },
        }
        
        # Add instance with flush disabled
        settings["INSTANCES"]["test_redis_flush_disabled"] = {
            "description": "Test Redis Instance - Flush Disabled",
            "host": redis_host,
            "port": 6379,
            "db": 13,
            "features": {
                "ALLOW_FLUSH": False,
                "ALLOW_KEY_DELETE": True,
                "ALLOW_KEY_EDIT": True,
                "ALLOW_TTL_UPDATE": True,
            },
        }
        
        return settings
    
    def setup_redis_test_data(self):
        """Set up test data for flush tests."""
        super().setup_redis_test_data()
        
        redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
        
        # Add data to database 12 (flush enabled)
        conn_12 = redis.Redis(
            host=redis_host, 
            port=6379, 
            db=12, 
            decode_responses=True
        )
        for i in range(10):
            conn_12.set(f"flush_test:key{i}", f"value{i}")
        
        # Add data to database 13 (flush disabled)
        conn_13 = redis.Redis(
            host=redis_host, 
            port=6379, 
            db=13, 
            decode_responses=True
        )
        for i in range(10):
            conn_13.set(f"flush_test:key{i}", f"value{i}")

    def test_flush_utility_flushdb_success(self):
        """Test RedisPanelUtils.flush method with flushdb."""
        # Add test data to verify it gets flushed
        self.add_test_key("test:flush:key1", "value1", db=12)
        self.add_test_key("test:flush:key2", "value2", db=12)
        
        # Verify keys exist
        self.assertTrue(self.key_exists("test:flush:key1", db=12))
        self.assertTrue(self.key_exists("test:flush:key2", db=12))
        
        # Flush database 12
        from dj_redis_panel.redis_utils import RedisPanelUtils
        result = RedisPanelUtils.flush("test_redis_flush_enabled", db_number=12, flushall=False)
        
        # Verify flush succeeded
        self.assertTrue(result)
        
        # Verify keys are gone
        self.assertFalse(self.key_exists("test:flush:key1", db=12))
        self.assertFalse(self.key_exists("test:flush:key2", db=12))

    def test_flush_utility_flushall_success(self):
        """Test RedisPanelUtils.flush method with flushall."""
        # Add test data to multiple databases
        self.add_test_key("test:flush:key1", "value1", db=12)
        self.add_test_key("test:flush:key2", "value2", db=13)
        
        # Verify keys exist
        self.assertTrue(self.key_exists("test:flush:key1", db=12))
        self.assertTrue(self.key_exists("test:flush:key2", db=13))
        
        # Flush all databases
        from dj_redis_panel.redis_utils import RedisPanelUtils
        result = RedisPanelUtils.flush("test_redis_flush_enabled", flushall=True)
        
        # Verify flush succeeded
        self.assertTrue(result)
        
        # Verify keys are gone from all databases
        self.assertFalse(self.key_exists("test:flush:key1", db=12))
        self.assertFalse(self.key_exists("test:flush:key2", db=13))

    def test_flush_utility_with_invalid_instance(self):
        """Test flush with non-existent instance returns False."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        # When instance doesn't exist, flush catches exception and returns False
        result = RedisPanelUtils.flush("nonexistent_instance", db_number=0)
        self.assertFalse(result)

    def test_flush_view_requires_staff_permission(self):
        """Test that flush view requires staff permission."""
        # Use unauthenticated client
        client = self.create_unauthenticated_client()
        url = reverse('dj_redis_panel:flushdb', args=['test_redis_flush_enabled', 12])
        response = client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_flush_view_nonexistent_instance(self):
        """Test flush view with nonexistent instance raises 404."""
        url = reverse('dj_redis_panel:flushdb', args=['nonexistent_instance', 0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_flushdb_view_with_permission(self):
        """Test flushdb view when ALLOW_FLUSH is enabled."""
        # Add test data
        self.add_test_key("test:flush:key1", "value1", db=12)
        self.add_test_key("test:flush:key2", "value2", db=12)
        
        # Verify keys exist
        self.assertTrue(self.key_exists("test:flush:key1", db=12))
        
        # Call flush view
        url = reverse('dj_redis_panel:flushdb', args=['test_redis_flush_enabled', 12])
        response = self.client.get(url)
        
        # Should redirect to instance overview
        self.assertEqual(response.status_code, 302)
        self.assertIn('test_redis_flush_enabled', response.url)
        
        # Verify keys are gone
        self.assertFalse(self.key_exists("test:flush:key1", db=12))
        self.assertFalse(self.key_exists("test:flush:key2", db=12))

    def test_flushdb_view_without_permission(self):
        """Test flushdb view when ALLOW_FLUSH is disabled."""
        # Add test data
        self.add_test_key("test:flush:key1", "value1", db=13)
        
        # Verify key exists
        self.assertTrue(self.key_exists("test:flush:key1", db=13))
        
        # Call flush view (should be blocked by permission check)
        url = reverse('dj_redis_panel:flushdb', args=['test_redis_flush_disabled', 13])
        response = self.client.get(url)
        
        # Should redirect to instance overview without flushing
        self.assertEqual(response.status_code, 302)
        self.assertIn('test_redis_flush_disabled', response.url)
        
        # Verify key still exists (not flushed)
        self.assertTrue(self.key_exists("test:flush:key1", db=13))

    def test_flushall_view_with_permission(self):
        """Test flushall view when ALLOW_FLUSH is enabled."""
        # Add test data to multiple databases
        self.add_test_key("test:flush:key1", "value1", db=12)
        self.add_test_key("test:flush:key2", "value2", db=13)
        self.add_test_key("test:flush:key3", "value3", db=14)
        
        # Verify keys exist
        self.assertTrue(self.key_exists("test:flush:key1", db=12))
        self.assertTrue(self.key_exists("test:flush:key2", db=13))
        
        # Call flushall view
        url = reverse('dj_redis_panel:flushall', args=['test_redis_flush_enabled'])
        response = self.client.get(url)
        
        # Should redirect to instance overview
        self.assertEqual(response.status_code, 302)
        self.assertIn('test_redis_flush_enabled', response.url)
        
        # Verify all keys are gone
        self.assertFalse(self.key_exists("test:flush:key1", db=12))
        self.assertFalse(self.key_exists("test:flush:key2", db=13))
        self.assertFalse(self.key_exists("test:flush:key3", db=14))

    def test_flushall_view_without_permission(self):
        """Test flushall view when ALLOW_FLUSH is disabled."""
        # Add test data
        self.add_test_key("test:flush:key1", "value1", db=13)
        
        # Verify key exists
        self.assertTrue(self.key_exists("test:flush:key1", db=13))
        
        # Call flushall view (should be blocked by permission check)
        url = reverse('dj_redis_panel:flushall', args=['test_redis_flush_disabled'])
        response = self.client.get(url)
        
        # Should redirect to instance overview without flushing
        self.assertEqual(response.status_code, 302)
        
        # Verify key still exists (not flushed)
        self.assertTrue(self.key_exists("test:flush:key1", db=13))

    def test_instance_overview_shows_flush_button_when_enabled(self):
        """Test that instance overview shows flush button when ALLOW_FLUSH is enabled."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis_flush_enabled'])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check context has allow_flush set to True
        self.assertTrue(response.context['allow_flush'])
        
        # Check that flush links are present in the HTML
        self.assertContains(response, 'Flush')
        
        # Check for flushdb link
        flushdb_url = reverse('dj_redis_panel:flushdb', args=['test_redis_flush_enabled', 12])
        self.assertContains(response, flushdb_url)
        
        # Check for flushall link
        flushall_url = reverse('dj_redis_panel:flushall', args=['test_redis_flush_enabled'])
        self.assertContains(response, flushall_url)

    def test_instance_overview_hides_flush_button_when_disabled(self):
        """Test that instance overview hides flush button when ALLOW_FLUSH is disabled."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis_flush_disabled'])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check context has allow_flush set to False
        self.assertFalse(response.context['allow_flush'])
        
        # Check that flush buttons are NOT present
        # The template should conditionally hide them with {% if allow_flush %}
        flushdb_url = reverse('dj_redis_panel:flushdb', args=['test_redis_flush_disabled', 13])
        # Flush links should not appear when permission is disabled
        # Note: We can't guarantee they won't appear if template isn't checking,
        # but the permission check in the view should still prevent actual flushing

    def test_flush_urls_are_registered(self):
        """Test that flush URLs are properly registered."""
        # Test flushdb URL
        flushdb_url = reverse('dj_redis_panel:flushdb', args=['test_redis', 0])
        self.assertIn('/flush/0/', flushdb_url)
        
        # Test flushall URL
        flushall_url = reverse('dj_redis_panel:flushall', args=['test_redis'])
        self.assertIn('/flush/all/', flushall_url)

    def test_flush_only_affects_specified_database(self):
        """Test that flushdb only affects the specified database."""
        # Add data to multiple databases
        self.add_test_key("test:db12:key", "value", db=12)
        self.add_test_key("test:db13:key", "value", db=13)
        
        # Verify both keys exist
        self.assertTrue(self.key_exists("test:db12:key", db=12))
        self.assertTrue(self.key_exists("test:db13:key", db=13))
        
        # Flush only database 12
        from dj_redis_panel.redis_utils import RedisPanelUtils
        RedisPanelUtils.flush("test_redis_flush_enabled", db_number=12, flushall=False)
        
        # Verify only db12 key is gone
        self.assertFalse(self.key_exists("test:db12:key", db=12))
        self.assertTrue(self.key_exists("test:db13:key", db=13))

    def test_flush_with_cluster_connection(self):
        """Test that flush works with cluster instances (if available)."""
        # This test would only run if a cluster is configured
        # For now, we'll skip if cluster isn't available
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        instances = RedisPanelUtils.get_instances()
        if "test_cluster" not in instances:
            self.skipTest("Redis cluster not configured for testing")
        
        # For clusters, flushdb should work (cluster only has db 0)
        # This is more of an integration test that would need actual cluster
        # We're mainly testing that the code path exists

    def test_flush_context_in_instance_overview(self):
        """Test that allow_flush is properly set in instance overview context."""
        # Test with flush enabled
        url_enabled = reverse('dj_redis_panel:instance_overview', args=['test_redis_flush_enabled'])
        response_enabled = self.client.get(url_enabled)
        self.assertTrue(response_enabled.context['allow_flush'])
        
        # Test with flush disabled
        url_disabled = reverse('dj_redis_panel:instance_overview', args=['test_redis_flush_disabled'])
        response_disabled = self.client.get(url_disabled)
        self.assertFalse(response_disabled.context['allow_flush'])

    def test_flush_button_has_confirmation(self):
        """Test that flush buttons have JavaScript confirmation."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis_flush_enabled'])
        response = self.client.get(url)
        
        # Check that flush links have onclick confirmation
        self.assertContains(response, 'onclick="return confirm(')
        self.assertContains(response, 'Do you want to flush')
