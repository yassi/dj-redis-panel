# Django Redis Panel

[![Tests](https://github.com/yassi/dj-redis-panel/actions/workflows/test.yml/badge.svg)](https://github.com/yassi/dj-redis-panel/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/yassi/dj-redis-panel/branch/main/graph/badge.svg)](https://codecov.io/gh/yassi/dj-redis-panel)
[![PyPI version](https://badge.fury.io/py/dj-redis-panel.svg)](https://badge.fury.io/py/dj-redis-panel)
[![Python versions](https://img.shields.io/pypi/pyversions/dj-redis-panel.svg)](https://pypi.org/project/dj-redis-panel/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Django Admin panel for browsing, inspecting, and managing Redis keys. No postgres/mysql models or changes required.

![Django Redis Panel - Instance List](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/instances_list.png)

## Features

- 🔍 **Browse Redis Keys**: Search and filter Redis keys with pattern matching
- 📊 **Instance Overview**: Monitor Redis instance metrics and database statistics  
- 🔧 **Key Management**: View, edit, and delete Redis keys with support for all data types
- 🎛️ **Feature Toggles**: Granular control over operations (delete, edit, TTL updates)
- 📄 **Pagination**: Both traditional page-based and cursor-based pagination support
- 🎨 **Django Admin Integration**: Seamless integration with Django admin styling and dark mode
- 🔒 **Permission Control**: Respects Django admin permissions and staff-only access
- 🌐 **Multiple Instances**: Support for multiple Redis instances with different configurations

## Supported Redis Data Types

- **String**: View and edit string values
- **List**: Browse list items with pagination
- **Set**: View set members
- **Hash**: Display hash fields and values in a table format
- **Sorted Set**: Show sorted set members with scores

### Project Structure

```
dj-redis-panel/
├── dj_redis_panel/          # Main package
│   ├── templates/           # Django templates
│   ├── redis_utils.py       # Redis utilities
│   ├── views.py            # Django views
│   └── urls.py             # URL patterns
├── example_project/         # Example Django project
├── tests/                   # Test suite
├── images/                  # Screenshots for README
└── requirements.txt         # Development dependencies
```

## Requirements

- Python 3.9+
- Django 4.2+
- Redis 4.0+
- redis-py 4.0+



## Screenshots

### Django Admin Integration
Seamlessly integrated into your Django admin interface. A new section for dj-redis-panel
will appear in the same places where your models appear.

**NOTE:** This application does not actually introduce any model or migrations.

![Admin Home](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/admin_home.png)

### Instance Overview
Monitor your Redis instances with detailed metrics and database information.

![Instance Overview](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/instance_overview.png)

### Key Search - Page-based Pagination
Search for keys with traditional page-based navigation.

![Key Search - Page Index](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_search_page_index.png)

### Key Search - Cursor-based Pagination  
Efficient cursor-based pagination for large datasets.

![Key Search - Cursor](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_search_cursor.png)

### Key Detail - String Values
View and edit string key values with TTL management.

![Key Detail - String](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_detail_string.png)

### Key Detail - Other data structures
Browse keys with more complex data structures such as hashes, lists, etc. 

![Key Detail - Hash](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_detail_hash.png)


## Installation

### 1. Install the Package

```bash
pip install dj-redis-panel
```

### 2. Add to Django Settings

Add `dj_redis_panel` to your `INSTALLED_APPS`:

```python
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

### 3. Configure Redis Instances

Add the Django Redis Panel configuration to your Django settings:

```python
DJ_REDIS_PANEL_SETTINGS = {
    # Global feature flags (can be overridden per instance)
    "ALLOW_KEY_DELETE": False,
    "ALLOW_KEY_EDIT": True,
    "ALLOW_TTL_UPDATE": True,
    "CURSOR_PAGINATED_SCAN": False,
    
    "INSTANCES": {
        "default": {
            "description": "Default Redis Instance",
            "host": "127.0.0.1",
            "port": 6379,
            "db": 0,
            # Optional: override global settings for this instance
            "features": {
                "ALLOW_KEY_DELETE": True,
                "CURSOR_PAGINATED_SCAN": True,
            },
        },
        "other_instance": {
            "description": "Cache Redis Instance",
            "url": "rediss://127.0.0.1:6379",
        },
    }
}
```

### 4. Include URLs

Add the Redis Panel URLs to your main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/redis/', include('dj_redis_panel.urls')),  # Add this line
]
```

### 5. Run Migrations and Create Superuser

```bash
python manage.py migrate
python manage.py createsuperuser  # If you don't have an admin user
```

### 6. Access the Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the Django admin at `http://127.0.0.1:8000/admin/`

3. Look for the "DJ_REDIS_PANEL" section in the admin interface

4. Click "Manage Redis keys and values" to start browsing your Redis instances

## Configuration Options

### Global Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `ALLOW_KEY_DELETE` | `False` | Allow deletion of Redis keys |
| `ALLOW_KEY_EDIT` | `True` | Allow editing of key values |
| `ALLOW_TTL_UPDATE` | `True` | Allow updating key TTL (expiration) |
| `CURSOR_PAGINATED_SCAN` | `False` | Use cursor-based pagination instead of page-based |

### Instance Configuration

Each Redis instance can be configured with:

#### Connection via Host/Port:
```python
"instance_name": {
    "description": "Human-readable description",
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,                    # Optional, default: 0
    "password": "password",     # Optional
    "features": {               # Optional: override global settings
        "ALLOW_KEY_DELETE": True,
    },
}
```

#### Connection via URL:
```python
"instance_name": {
    "description": "Human-readable description", 
    "url": "redis://user:password@host:port/db",
    "features": {               # Optional: override global settings
        "CURSOR_PAGINATED_SCAN": True,
    },
}
```

### Feature Flags

Feature flags can be set globally and overridden per instance:

- **`ALLOW_KEY_DELETE`**: Controls whether the delete button is enabled
- **`ALLOW_KEY_EDIT`**: Controls whether key values can be modified
- **`ALLOW_TTL_UPDATE`**: Controls whether key expiration can be updated
- **`CURSOR_PAGINATED_SCAN`**: Chooses pagination method (cursor vs. page-based)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Development Setup

If you want to contribute to this project or set it up for local development:

### Prerequisites

- Python 3.9 or higher
- Redis server running locally
- Git
- Autoconf

### 1. Clone the Repository

```bash
git clone https://github.com/yassi/dj-redis-panel.git
cd dj-redis-panel
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dj-redis-panel inside of your virtualenv

A make file is included in the repository root with multiple commands for building
and maintaining this project. The best approach is to start by using one of the
package installation commands found below:
```bash
# Build and install a wheel for this project
# Also install all dev dependencies such as pytest and other utilities
make install_dev

# Build and install a wheel for this project
make install

# build and install all dev dependencies and run all tests
make test
```

### 4. Set Up Example Project

The repository includes an example Django project for development and testing:

```bash
cd example_project
python manage.py migrate
python manage.py createsuperuser
```

### 5. Populate Test Data (Optional)
An optional CLI tool for populating redis keys automatically is included in the
example django project in this code base.

```bash
python manage.py populate_redis
```

This command will populate your Redis instance with sample data for testing.

### 6. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the Django admin with Redis Panel.

### 7. Running Tests

The project includes a comprehensive test suite. You can run them by using make or
by invoking pytest directly:

```bash
# run using make which will also install all dependencies (recommended)
make test

# run using pytest directly
pytest tests/

# Run with coverage
pytest tests/ --cov=dj_redis_panel

# Run specific test file
pytest tests/test_views.py
```

**Note**: Tests require a running Redis server on `127.0.0.1:6379`. The tests use databases 13, 14, and 15 for isolation and automatically clean up after each test.

### 8. Dockerized Redis

Test for this project (as well as any active development) require an active redis installation.
Although not required, a docker-compose file is included to allow for easy creation of local
redis instances.

```bash
# Start Redis on localhost and the usual port 6379
docker-compose up redis -d
```
