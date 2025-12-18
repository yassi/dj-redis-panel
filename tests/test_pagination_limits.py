"""
Tests for configurable pagination limits (MAX_KEYS_PAGINATED_SCAN and MAX_SCAN_ITERATIONS)
"""

import pytest
from django.test import override_settings
from dj_redis_panel.redis_utils import RedisPanelUtils


class TestPaginationLimits:
    """Test configurable pagination limits"""

    def test_default_max_keys_paginated_scan(self):
        """Test that default MAX_KEYS_PAGINATED_SCAN is 100000"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                    }
                }
            }
        ):
            max_keys = RedisPanelUtils.get_max_keys_paginated_scan("test")
            assert max_keys == 100000

    def test_default_max_scan_iterations(self):
        """Test that default MAX_SCAN_ITERATIONS is 2000"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                    }
                }
            }
        ):
            max_iterations = RedisPanelUtils.get_max_scan_iterations("test")
            assert max_iterations == 2000

    def test_global_max_keys_paginated_scan(self):
        """Test that global MAX_KEYS_PAGINATED_SCAN setting is respected"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "MAX_KEYS_PAGINATED_SCAN": 200000,
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                    }
                },
            }
        ):
            max_keys = RedisPanelUtils.get_max_keys_paginated_scan("test")
            assert max_keys == 200000

    def test_global_max_scan_iterations(self):
        """Test that global MAX_SCAN_ITERATIONS setting is respected"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "MAX_SCAN_ITERATIONS": 5000,
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                    }
                },
            }
        ):
            max_iterations = RedisPanelUtils.get_max_scan_iterations("test")
            assert max_iterations == 5000

    def test_instance_specific_max_keys_paginated_scan(self):
        """Test that instance-specific MAX_KEYS_PAGINATED_SCAN overrides global"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "MAX_KEYS_PAGINATED_SCAN": 100000,
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                        "MAX_KEYS_PAGINATED_SCAN": 300000,
                    }
                },
            }
        ):
            max_keys = RedisPanelUtils.get_max_keys_paginated_scan("test")
            assert max_keys == 300000

    def test_instance_specific_max_scan_iterations(self):
        """Test that instance-specific MAX_SCAN_ITERATIONS overrides global"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "MAX_SCAN_ITERATIONS": 2000,
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                        "MAX_SCAN_ITERATIONS": 10000,
                    }
                },
            }
        ):
            max_iterations = RedisPanelUtils.get_max_scan_iterations("test")
            assert max_iterations == 10000

    def test_mixed_global_and_instance_settings(self):
        """Test that different instances can have different limits"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "MAX_KEYS_PAGINATED_SCAN": 100000,
                "MAX_SCAN_ITERATIONS": 2000,
                "INSTANCES": {
                    "default": {
                        "host": "127.0.0.1",
                        "port": 6379,
                    },
                    "large_db": {
                        "host": "127.0.0.1",
                        "port": 6379,
                        "MAX_KEYS_PAGINATED_SCAN": 500000,
                        "MAX_SCAN_ITERATIONS": 10000,
                    },
                },
            }
        ):
            # Default instance uses global settings
            assert RedisPanelUtils.get_max_keys_paginated_scan("default") == 100000
            assert RedisPanelUtils.get_max_scan_iterations("default") == 2000

            # Large DB instance uses custom settings
            assert RedisPanelUtils.get_max_keys_paginated_scan("large_db") == 500000
            assert RedisPanelUtils.get_max_scan_iterations("large_db") == 10000

    def test_string_values_are_converted_to_int(self):
        """Test that string values in settings are properly converted to integers"""
        with override_settings(
            DJ_REDIS_PANEL_SETTINGS={
                "MAX_KEYS_PAGINATED_SCAN": "250000",
                "MAX_SCAN_ITERATIONS": "3000",
                "INSTANCES": {
                    "test": {
                        "host": "127.0.0.1",
                        "port": 6379,
                    }
                },
            }
        ):
            max_keys = RedisPanelUtils.get_max_keys_paginated_scan("test")
            max_iterations = RedisPanelUtils.get_max_scan_iterations("test")

            assert isinstance(max_keys, int)
            assert isinstance(max_iterations, int)
            assert max_keys == 250000
            assert max_iterations == 3000
