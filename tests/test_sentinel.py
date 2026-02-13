"""
Tests for Redis Sentinel support in Django Redis Panel.

These tests verify that the panel can connect to Redis instances
configured via Redis Sentinel for high availability.
"""
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from dj_redis_panel.redis_utils import RedisPanelUtils


class TestSentinelSupport(TestCase):
    """Test cases for Redis Sentinel connection support."""

    def setUp(self):
        """Set up test configuration for sentinel tests."""
        self.redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
        
        # Create sentinel configuration
        self.sentinel_config = {
            "description": "Test Redis Sentinel",
            "type": "sentinel",
            "sentinels": [
                ("sentinel-1", 26379),
                ("sentinel-2", 26379),
                ("sentinel-3", 26379),
            ],
            "master": "mymaster",
            "password": "redis_password",
            "sentinel_kwargs": {
                "socket_timeout": 0.5,
            },
            "socket_timeout": 5.0,
            "socket_connect_timeout": 3.0,
        }

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_sentinel_connection_creation(self, mock_sentinel_class, mock_get_settings):
        """Test that sentinel connection is created with correct parameters."""
        # Setup mocks
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": self.sentinel_config
            }
        }
        
        # Create connection
        conn = RedisPanelUtils._create_sentinel_connection(self.sentinel_config)
        
        # Verify Sentinel was initialized correctly
        mock_sentinel_class.assert_called_once_with(
            [("sentinel-1", 26379), ("sentinel-2", 26379), ("sentinel-3", 26379)],
            sentinel_kwargs={"socket_timeout": 0.5},
            socket_timeout=5.0,
            password="redis_password",
        )
        
        # Verify master_for was called
        mock_sentinel_instance.master_for.assert_called_once_with(
            "mymaster",
            socket_timeout=5.0,
            socket_connect_timeout=3.0,
        )
        
        # Verify connection is returned
        self.assertEqual(conn, mock_master_connection)

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_sentinel_connection_without_password(self, mock_sentinel_class, mock_get_settings):
        """Test sentinel connection creation without password."""
        # Setup config without password
        config_no_password = self.sentinel_config.copy()
        del config_no_password["password"]
        
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": config_no_password
            }
        }
        
        # Create connection
        RedisPanelUtils._create_sentinel_connection(config_no_password)
        
        # Verify Sentinel was initialized without password
        call_kwargs = mock_sentinel_class.call_args[1]
        self.assertNotIn('password', call_kwargs)

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    def test_sentinel_connection_missing_sentinels(self, mock_get_settings):
        """Test that missing sentinels raises an exception."""
        config_invalid = {
            "type": "sentinel",
            "master": "mymaster",
            # missing "sentinels"
        }
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": config_invalid
            }
        }
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            RedisPanelUtils._create_sentinel_connection(config_invalid)
        
        self.assertIn("sentinels", str(context.exception))
        self.assertIn("master", str(context.exception))

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    def test_sentinel_connection_missing_master(self, mock_get_settings):
        """Test that missing master name raises an exception."""
        config_invalid = {
            "type": "sentinel",
            "sentinels": [("sentinel-1", 26379)],
            # missing "master"
        }
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": config_invalid
            }
        }
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            RedisPanelUtils._create_sentinel_connection(config_invalid)
        
        self.assertIn("sentinels", str(context.exception))
        self.assertIn("master", str(context.exception))

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_sentinel_connection_uses_default_timeouts(self, mock_sentinel_class, mock_get_settings):
        """Test that sentinel connection uses default timeouts when not specified."""
        # Setup config without timeout values
        config_no_timeouts = {
            "type": "sentinel",
            "sentinels": [("sentinel-1", 26379)],
            "master": "mymaster",
        }
        
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        # Global settings without timeouts
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": config_no_timeouts
            }
        }
        
        # Create connection
        RedisPanelUtils._create_sentinel_connection(config_no_timeouts)
        
        # Verify default timeouts are used
        call_kwargs = mock_sentinel_class.call_args[1]
        self.assertEqual(call_kwargs['socket_timeout'], 5.0)  # DEFAULT_SOCKET_TIMEOUT
        
        # Verify master_for uses default timeouts
        master_call_kwargs = mock_sentinel_instance.master_for.call_args[1]
        self.assertEqual(master_call_kwargs['socket_timeout'], 5.0)
        self.assertEqual(master_call_kwargs['socket_connect_timeout'], 3.0)

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_sentinel_connection_uses_global_timeouts(self, mock_sentinel_class, mock_get_settings):
        """Test that sentinel connection uses global timeout settings."""
        # Setup config without instance-level timeouts
        config_no_timeouts = {
            "type": "sentinel",
            "sentinels": [("sentinel-1", 26379)],
            "master": "mymaster",
        }
        
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        # Global settings with custom timeouts
        mock_get_settings.return_value = {
            "socket_timeout": 10.0,
            "socket_connect_timeout": 5.0,
            "INSTANCES": {
                "test_sentinel": config_no_timeouts
            }
        }
        
        # Create connection
        RedisPanelUtils._create_sentinel_connection(config_no_timeouts)
        
        # Verify global timeouts are used
        call_kwargs = mock_sentinel_class.call_args[1]
        self.assertEqual(call_kwargs['socket_timeout'], 10.0)
        
        master_call_kwargs = mock_sentinel_instance.master_for.call_args[1]
        self.assertEqual(master_call_kwargs['socket_timeout'], 10.0)
        self.assertEqual(master_call_kwargs['socket_connect_timeout'], 5.0)

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_sentinel_with_custom_sentinel_kwargs(self, mock_sentinel_class, mock_get_settings):
        """Test that custom sentinel_kwargs are passed correctly."""
        # Config with custom sentinel_kwargs
        config = {
            "type": "sentinel",
            "sentinels": [("sentinel-1", 26379)],
            "master": "mymaster",
            "sentinel_kwargs": {
                "socket_timeout": 2.0,
                "socket_connect_timeout": 1.0,
                "db": 0,
            },
        }
        
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": config
            }
        }
        
        # Create connection
        RedisPanelUtils._create_sentinel_connection(config)
        
        # Verify sentinel_kwargs are passed
        call_args = mock_sentinel_class.call_args
        self.assertEqual(
            call_args[1]['sentinel_kwargs'],
            {
                "socket_timeout": 2.0,
                "socket_connect_timeout": 1.0,
                "db": 0,
            }
        )

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_get_redis_connection_with_sentinel(self, mock_sentinel_class, mock_get_settings):
        """Test get_redis_connection method with sentinel configuration."""
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": self.sentinel_config
            }
        }
        
        # Get connection via main method
        conn = RedisPanelUtils.get_redis_connection("test_sentinel")
        
        # Verify we got the master connection
        self.assertEqual(conn, mock_master_connection)

    @patch('dj_redis_panel.redis_utils.RedisPanelUtils.get_settings')
    @patch('dj_redis_panel.redis_utils.Sentinel')
    def test_sentinel_connection_empty_sentinel_kwargs(self, mock_sentinel_class, mock_get_settings):
        """Test sentinel connection with empty sentinel_kwargs."""
        config = {
            "type": "sentinel",
            "sentinels": [("sentinel-1", 26379)],
            "master": "mymaster",
            # No sentinel_kwargs - should default to empty dict
        }
        
        mock_sentinel_instance = MagicMock()
        mock_sentinel_class.return_value = mock_sentinel_instance
        mock_master_connection = MagicMock()
        mock_sentinel_instance.master_for.return_value = mock_master_connection
        
        mock_get_settings.return_value = {
            "INSTANCES": {
                "test_sentinel": config
            }
        }
        
        # Create connection
        RedisPanelUtils._create_sentinel_connection(config)
        
        # Verify empty sentinel_kwargs are used
        call_kwargs = mock_sentinel_class.call_args[1]
        self.assertEqual(call_kwargs['sentinel_kwargs'], {})
