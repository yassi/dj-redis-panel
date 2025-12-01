"""
Tests for Redis Cluster support.

These tests require a Redis cluster to be running and are marked with @pytest.mark.cluster.
They can be run individually or together with all other tests.

Run these tests with:
    make test_cluster       # Run only cluster tests
    make test_all          # Run all tests including cluster tests

Or directly with pytest:
    pytest tests/test_cluster.py -m cluster


NOTE: these tests are not exhaustive like the standalone redis tests are. Currently, they are
focused on making sure that the cluster connections work basic operations on clusters are supported.
"""

import pytest
from .base import RedisTestCase


@pytest.mark.cluster
class TestClusterBasicOperations(RedisTestCase):
    """Test basic operations against a Redis cluster."""

    def test_cluster_connection(self):
        """Test that we can connect to the cluster."""
        from dj_redis_panel.redis_utils import RedisPanelUtils

        # Get cluster instance metadata
        metadata = RedisPanelUtils.get_instance_meta_data("test_cluster")

        self.assertEqual(metadata["status"], "connected")
        self.assertIsNotNone(metadata["info"])
        self.assertTrue(metadata["hero_numbers"]["cluster_enabled"])
        self.assertEqual(metadata["hero_numbers"]["cluster_enabled"], True)

    def test_cluster_url_connection(self):
        """Test that we can connect to cluster using URL method."""
        from dj_redis_panel.redis_utils import RedisPanelUtils

        # Get cluster instance metadata via URL
        metadata = RedisPanelUtils.get_instance_meta_data("test_cluster_url")

        self.assertEqual(metadata["status"], "connected")
        self.assertIsNotNone(metadata["info"])
        self.assertTrue(metadata["hero_numbers"]["cluster_enabled"])

    def test_cluster_key_operations(self):
        """Test basic key operations on cluster."""
        from dj_redis_panel.redis_utils import RedisPanelUtils

        # Set a key
        result = RedisPanelUtils.update_string_value(
            "test_cluster", 0, "test_cluster_key", "test_value"
        )
        self.assertTrue(result["success"])

        # Get the key
        key_data = RedisPanelUtils.get_key_data("test_cluster", 0, "test_cluster_key")
        self.assertTrue(key_data["exists"])
        self.assertEqual(key_data["value"], "test_value")
        self.assertEqual(key_data["type"], "string")

    def test_cluster_scan_operations(self):
        """
        Test SCAN operations on cluster using cursor pagination.
        NOTE: this is really testing scan_iter functionality on clusters since
        we don't support full scans on clusters.
        """
        from dj_redis_panel.redis_utils import RedisPanelUtils

        # Add some test keys
        for i in range(5):
            RedisPanelUtils.update_string_value(
                "test_cluster", 0, f"cluster_scan_test:{i}", f"value_{i}"
            )

        # Verify paginated_scan correctly returns an error for clusters
        page_scan_result = RedisPanelUtils.paginated_scan(
            "test_cluster", 0, pattern="cluster_scan_test:*", page=1, per_page=10
        )
        self.assertIsNotNone(page_scan_result["error"])
        self.assertIn("not supported on clusters", page_scan_result["error"])

        # Use cursor pagination (the correct way for clusters)
        cursor_result = RedisPanelUtils.cursor_paginated_scan(
            "test_cluster", 0, pattern="cluster_scan_test:*", cursor="0", per_page=10
        )

        self.assertIsNone(cursor_result["error"])
        self.assertGreaterEqual(len(cursor_result["keys"]), 5)

    def test_cluster_database_restriction(self):
        """Test that clusters only support database 0."""
        from dj_redis_panel.redis_utils import RedisPanelUtils

        metadata = RedisPanelUtils.get_instance_meta_data("test_cluster")

        # Cluster should only have database 0
        self.assertEqual(len(metadata["databases"]), 1)
        self.assertEqual(metadata["databases"][0]["db_number"], 0)
