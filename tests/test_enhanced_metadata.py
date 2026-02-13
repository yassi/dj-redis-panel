"""
Tests for enhanced instance metadata in Django Redis Panel.

These tests verify the new fields added to instance metadata:
- role (master/slave/sentinel)
- connected_slaves
- type field in instance overview context
"""
import os
from unittest.mock import patch, MagicMock
from django.urls import reverse
from .base import RedisTestCase


class TestEnhancedInstanceMetadata(RedisTestCase):
    """Test cases for enhanced instance metadata fields."""

    def test_hero_numbers_includes_role(self):
        """Test that hero_numbers includes role field."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        hero_numbers = response.context['hero_numbers']
        
        # Should include role field
        self.assertIn('role', hero_numbers)
        
        # Role should be a string
        self.assertIsInstance(hero_numbers['role'], str)
        
        # For standalone Redis, role is typically 'master' or 'single'
        self.assertIn(hero_numbers['role'], ['master', 'slave', 'single'])

    def test_hero_numbers_includes_connected_slaves(self):
        """Test that hero_numbers includes connected_slaves field."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        hero_numbers = response.context['hero_numbers']
        
        # Should include connected_slaves field
        self.assertIn('connected_slaves', hero_numbers)
        
        # Should be an integer
        self.assertIsInstance(hero_numbers['connected_slaves'], int)
        
        # Should be >= 0
        self.assertGreaterEqual(hero_numbers['connected_slaves'], 0)

    def test_hero_numbers_defaults_for_role(self):
        """Test that role defaults to 'single' when not available in INFO."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        # Mock redis connection that doesn't return role in INFO
        with patch.object(RedisPanelUtils, 'get_redis_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            
            # Mock INFO response without role
            mock_conn.info.return_value = {
                'redis_version': '6.0.0',
                'used_memory_human': '1M',
                'used_memory_peak_human': '2M',
                'connected_clients': 1,
                'uptime_in_seconds': 3600,
                'total_commands_processed': 1000,
                'connected_slaves': 0,
                # 'role' is missing - should default to 'single'
                'cluster_enabled': 0,
            }
            
            metadata = RedisPanelUtils.get_instance_meta_data('test_redis')
            hero_numbers = metadata['hero_numbers']
            
            # Should default to 'single'
            self.assertEqual(hero_numbers['role'], 'single')

    def test_hero_numbers_defaults_for_connected_slaves(self):
        """Test that connected_slaves defaults to 0 when not in INFO."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        # Mock redis connection that doesn't return connected_slaves in INFO
        with patch.object(RedisPanelUtils, 'get_redis_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            
            # Mock INFO response without connected_slaves
            mock_conn.info.return_value = {
                'redis_version': '6.0.0',
                'used_memory_human': '1M',
                'used_memory_peak_human': '2M',
                'connected_clients': 1,
                'uptime_in_seconds': 3600,
                'total_commands_processed': 1000,
                'role': 'master',
                # 'connected_slaves' is missing - should default to 0
                'cluster_enabled': 0,
            }
            
            metadata = RedisPanelUtils.get_instance_meta_data('test_redis')
            hero_numbers = metadata['hero_numbers']
            
            # Should default to 0
            self.assertEqual(hero_numbers['connected_slaves'], 0)

    def test_instance_overview_context_includes_type(self):
        """Test that instance overview context includes type field."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Check that type is in context
        self.assertIn('type', response.context)
        
        # For test_redis, type should be 'single' (default)
        self.assertEqual(response.context['type'], 'single')

    def test_instance_overview_type_for_cluster(self):
        """Test that type is correctly set for cluster instances."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        instances = RedisPanelUtils.get_instances()
        if "test_cluster" not in instances:
            self.skipTest("Redis cluster not configured for testing")
        
        url = reverse('dj_redis_panel:instance_overview', args=['test_cluster'])
        response = self.client.get(url)
        
        # Type should be 'cluster'
        self.assertEqual(response.context['type'], 'cluster')

    def test_instance_overview_type_defaults_to_single(self):
        """Test that type defaults to 'single' when not specified."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # When type is not specified in config, it should default to 'single'
        self.assertEqual(response.context['type'], 'single')

    def test_template_displays_type_field(self):
        """Test that the template displays the type field."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Check that 'Redis Type' appears in the template
        self.assertContains(response, 'Redis Type')
        
        # Check that the type value appears
        type_value = response.context['type']
        self.assertContains(response, type_value)

    def test_template_shows_sentinel_details_for_sentinel_type(self):
        """Test that sentinel-specific details are shown for sentinel instances."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        # Create a mock sentinel instance with proper metadata
        with patch.object(RedisPanelUtils, 'get_settings') as mock_settings:
            mock_settings.return_value = {
                "INSTANCES": {
                    "test_sentinel": {
                        "description": "Test Sentinel",
                        "type": "sentinel",
                        "sentinels": [("sentinel-1", 26379)],
                        "master": "mymaster",
                    }
                }
            }
            
            with patch.object(RedisPanelUtils, 'get_redis_connection') as mock_get_conn:
                mock_conn = MagicMock()
                mock_get_conn.return_value = mock_conn
                
                # Mock INFO for a master with slaves
                mock_conn.info.return_value = {
                    'redis_version': '6.0.0',
                    'used_memory_human': '1M',
                    'used_memory_peak_human': '2M',
                    'connected_clients': 5,
                    'uptime_in_seconds': 3600,
                    'total_commands_processed': 10000,
                    'role': 'master',
                    'connected_slaves': 2,
                    'cluster_enabled': 0,
                }
                mock_conn.ping.return_value = True
                
                url = reverse('dj_redis_panel:instance_overview', args=['test_sentinel'])
                response = self.client.get(url)
                
                # Check that sentinel-specific content appears
                self.assertEqual(response.context['type'], 'sentinel')
                
                # Template should show role and slaves for sentinel
                self.assertContains(response, 'role')
                self.assertContains(response, 'slaves')
                
                hero_numbers = response.context['hero_numbers']
                self.assertEqual(hero_numbers['role'], 'master')
                self.assertEqual(hero_numbers['connected_slaves'], 2)

    def test_hero_numbers_structure_with_new_fields(self):
        """Test that hero_numbers maintains proper structure with new fields."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        hero_numbers = response.context['hero_numbers']
        
        # Check all expected fields including new ones
        expected_fields = [
            'version',
            'memory_used',
            'memory_peak',
            'connected_clients',
            'uptime',
            'total_commands_processed',
            'connected_slaves',  # New field
            'role',              # New field
            'cluster_enabled',
        ]
        
        for field in expected_fields:
            self.assertIn(field, hero_numbers, f"Missing field: {field}")

    def test_metadata_for_master_with_slaves(self):
        """Test metadata when Redis instance is a master with slaves."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        with patch.object(RedisPanelUtils, 'get_redis_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            
            # Mock INFO for a master with 3 slaves
            mock_conn.info.return_value = {
                'redis_version': '6.2.0',
                'used_memory_human': '10M',
                'used_memory_peak_human': '20M',
                'connected_clients': 10,
                'uptime_in_seconds': 86400,
                'total_commands_processed': 100000,
                'role': 'master',
                'connected_slaves': 3,
                'cluster_enabled': 0,
            }
            mock_conn.ping.return_value = True
            
            metadata = RedisPanelUtils.get_instance_meta_data('test_redis')
            hero_numbers = metadata['hero_numbers']
            
            self.assertEqual(hero_numbers['role'], 'master')
            self.assertEqual(hero_numbers['connected_slaves'], 3)

    def test_metadata_for_slave_instance(self):
        """Test metadata when Redis instance is a slave."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        with patch.object(RedisPanelUtils, 'get_redis_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            
            # Mock INFO for a slave
            mock_conn.info.return_value = {
                'redis_version': '6.2.0',
                'used_memory_human': '10M',
                'used_memory_peak_human': '20M',
                'connected_clients': 5,
                'uptime_in_seconds': 43200,
                'total_commands_processed': 50000,
                'role': 'slave',
                'connected_slaves': 0,  # Slaves don't have slaves
                'cluster_enabled': 0,
            }
            mock_conn.ping.return_value = True
            
            metadata = RedisPanelUtils.get_instance_meta_data('test_redis')
            hero_numbers = metadata['hero_numbers']
            
            self.assertEqual(hero_numbers['role'], 'slave')
            self.assertEqual(hero_numbers['connected_slaves'], 0)

    def test_index_page_shows_type_column(self):
        """Test that the index page includes the type column."""
        url = reverse('dj_redis_panel:index')
        response = self.client.get(url)
        
        # Check that Type column header appears
        self.assertContains(response, 'Type')
        
        # The type value may be empty string, None, or a type name like 'single', 'cluster', 'sentinel'
        # Just verify the Type column is present in the template
        self.assertEqual(response.status_code, 200)

    def test_get_instance_meta_data_includes_all_new_fields(self):
        """Test that get_instance_meta_data returns all new fields."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        metadata = RedisPanelUtils.get_instance_meta_data('test_redis')
        
        # Check hero_numbers has new fields
        hero_numbers = metadata.get('hero_numbers')
        self.assertIsNotNone(hero_numbers)
        self.assertIn('role', hero_numbers)
        self.assertIn('connected_slaves', hero_numbers)

    def test_info_field_in_instance_overview_context(self):
        """Test that info field is included in instance overview context."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        # Check that info is in context
        self.assertIn('info', response.context)
        
        # Info should be a dict when connection succeeds
        info = response.context['info']
        if info:  # If connection succeeded
            self.assertIsInstance(info, dict)

    def test_cluster_enabled_field_in_hero_numbers(self):
        """Test that cluster_enabled field is included in hero_numbers."""
        url = reverse('dj_redis_panel:instance_overview', args=['test_redis'])
        response = self.client.get(url)
        
        hero_numbers = response.context['hero_numbers']
        
        # Should include cluster_enabled
        self.assertIn('cluster_enabled', hero_numbers)
        
        # For standalone instance, should be False
        self.assertFalse(hero_numbers['cluster_enabled'])

    def test_sentinel_type_with_mock_config(self):
        """Test that sentinel type configuration is properly handled."""
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        with patch.object(RedisPanelUtils, 'get_settings') as mock_settings:
            mock_settings.return_value = {
                "INSTANCES": {
                    "mock_sentinel": {
                        "description": "Mock Sentinel Instance",
                        "type": "sentinel",
                        "sentinels": [("sentinel-1", 26379)],
                        "master": "mymaster",
                    }
                }
            }
            
            instances = RedisPanelUtils.get_instances()
            instance_config = instances.get('mock_sentinel', {})
            
            # Type should be 'sentinel'
            self.assertEqual(instance_config.get('type'), 'sentinel')
