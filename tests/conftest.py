"""
Pytest configuration for Django Redis Panel tests.

This configuration enables pytest-django to work with Django TestCase classes.
"""
import os
import sys
import django
from django.conf import settings

def pytest_configure(config):
    """Configure Django for pytest."""
    # Add the example_project directory to Python path for Django settings
    example_project_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'example_project')
    if example_project_path not in sys.path:
        sys.path.insert(0, example_project_path)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example_project.settings')
    
    # Setup Django
    if not settings.configured:
        django.setup()
