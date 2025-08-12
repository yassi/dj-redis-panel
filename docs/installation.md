# Installation

This guide will walk you through installing and setting up Django Redis Panel in your Django project.

## Prerequisites

Before installing Django Redis Panel, make sure you have:

- Python 3.9 or higher
- Django 4.2 or higher
- A running Redis server
- redis-py 4.0 or higher

## Installation Steps

### 1. Install the Package

Install Django Redis Panel using pip:

```bash
pip install dj-redis-panel
```

### 2. Add to Django Settings

Add `dj_redis_panel` to your `INSTALLED_APPS` in your Django settings file:

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dj_redis_panel',  # Add this line
    # ... your other apps
]
```

!!! note
    Django Redis Panel doesn't require any database migrations as it doesn't define any Django models.

### 3. Configure Redis Instances

Add your Redis configuration to your Django settings:

=== "Single Instance"

    ```python
    # settings.py
    DJ_REDIS_PANEL_SETTINGS = {
        "INSTANCES": {
            "default": {
                "description": "Default Redis Instance",
                "host": "127.0.0.1",
                "port": 6379,
            }
        }
    }
    ```

=== "Multiple Instances"

    ```python
    # settings.py
    DJ_REDIS_PANEL_SETTINGS = {
        "INSTANCES": {
            "default": {
                "description": "Default Redis Instance",
                "host": "127.0.0.1",
                "port": 6379,
            },
            "cache": {
                "description": "Cache Redis Instance",
                "host": "127.0.0.1",
                "port": 6379,
            },
            "sessions": {
                "description": "Session Store",
                "url": "redis://127.0.0.1:6379",
            }
        }
    }
    ```

=== "With Authentication"

    ```python
    # settings.py
    DJ_REDIS_PANEL_SETTINGS = {
        "INSTANCES": {
            "secure": {
                "description": "Secure Redis Instance",
                "host": "127.0.0.1",
                "port": 6379,
                "password": "your-redis-password",
            },
            "ssl_instance": {
                "description": "SSL Redis Instance",
                "url": "rediss://user:password@host:6380",
            }
        }
    }
    ```

### 4. Include URLs

Add the Django Redis Panel URLs to your main `urls.py` file:

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/redis/', include('dj_redis_panel.urls')),  # Add this line
    path('admin/', admin.site.urls),
]
```

!!! tip
    You can change the URL path from `admin/redis/` to any path you prefer, such as `redis/` or `db/redis/`.

### 5. Create Admin User (if needed)

If you don't already have a Django admin superuser, create one:

```bash
python manage.py createsuperuser
```

### 6. Start the Development Server

Start your Django development server:

```bash
python manage.py runserver
```

### 7. Access the Panel

1. Navigate to the Django admin at `http://127.0.0.1:8000/admin/`
2. Log in with your admin credentials
3. Look for the **"DJ_REDIS_PANEL"** section in the admin interface
4. Click **"Manage Redis keys and values"** to start browsing your Redis instances

## Verification

To verify that everything is working correctly:

1. Check that you can see the Redis Panel section in your Django admin
2. Click on "Manage Redis keys and values"
3. You should see a list of your configured Redis instances
4. Click on an instance to view its overview and browse keys

## Troubleshooting

### Common Issues

**Redis connection errors**
: Make sure your Redis server is running and accessible at the configured host and port.

**Permission denied**
: Ensure you're logged in as a staff user with admin access.

**Module not found**
: Make sure `dj_redis_panel` is properly installed and added to `INSTALLED_APPS`.

**URLs not found**
: Verify that you've included the Redis Panel URLs in your main `urls.py` file.

### Getting Help

If you encounter any issues during installation:

- Check the [Configuration](configuration.md) guide for detailed settings
- Review the [Quick Start](quick-start.md) guide
- [Open an issue on GitHub](https://github.com/yassi/dj-redis-panel/issues)

## Next Steps

Now that you have Django Redis Panel installed, learn how to:

- [Configure advanced settings](configuration.md)
- [Follow the quick start guide](quick-start.md)
- [Explore all features](features.md)
