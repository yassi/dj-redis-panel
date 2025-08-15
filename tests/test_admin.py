"""
Tests for Django Admin integration with Django Redis Panel.

The Django Redis Panel integrates with Django Admin through a placeholder model
that appears in the admin interface and redirects to the Redis Panel when clicked.
"""
import redis
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from dj_redis_panel.admin import RedisPanelPlaceholderAdmin
from dj_redis_panel.models import RedisPanelPlaceholder
from .base import RedisTestCase


User = get_user_model()


class TestAdminIntegration(RedisTestCase):
    """Test cases for Django Admin integration."""
    
    def test_redis_panel_appears_in_admin_index(self):
        """Test that the Redis Panel appears in the Django admin index page."""
        response = self.client.get('/admin/')
        
        self.assertEqual(response.status_code, 200)
        # Check for the app name and model
        self.assertContains(response, 'dj_redis_panel')
        
        # Check that the link to the changelist exists
        changelist_url = reverse('admin:dj_redis_panel_redispanelplaceholder_changelist')
        self.assertContains(response, changelist_url)
    
    def test_redis_panel_changelist_redirects_to_index(self):
        """Test that clicking the Redis Panel in admin redirects to the Redis Panel index."""
        changelist_url = reverse('admin:dj_redis_panel_redispanelplaceholder_changelist')
        response = self.client.get(changelist_url)
        
        # Should redirect to the Redis Panel index
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('dj_redis_panel:index')
        self.assertRedirects(response, expected_url)
    
    def test_unauthenticated_user_cannot_access_admin_redis_panel(self):
        """Test that unauthenticated users cannot access the Redis Panel through admin."""
        client = self.create_unauthenticated_client()
        changelist_url = reverse('admin:dj_redis_panel_redispanelplaceholder_changelist')
        response = client.get(changelist_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_non_staff_user_cannot_access_admin_redis_panel(self):
        """Test that non-staff users cannot access the Redis Panel through admin."""
        # Create a non-staff user
        user = User.objects.create_user(
            username='regular_user',
            password='testpass123',
            is_staff=False
        )
        
        client = Client()
        client.force_login(user)
        
        changelist_url = reverse('admin:dj_redis_panel_redispanelplaceholder_changelist')
        response = client.get(changelist_url)
        
        # Should redirect to login page or show permission denied
        self.assertIn(response.status_code, [302, 403])
