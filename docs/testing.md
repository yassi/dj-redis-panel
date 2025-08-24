# Testing

Django Redis Panel includes a comprehensive test suite to ensure reliability and prevent regressions. This guide covers running tests, writing new tests, and understanding the testing infrastructure.

## Test Overview

### Test Structure

The test suite is organized in the `tests/` directory:

```
tests/
├── __init__.py
├── base.py                 # Base test classes
├── conftest.py            # Pytest configuration
├── test_index.py          # Index view tests
├── test_instance_overview.py  # Instance overview tests
├── test_key_detail.py     # Key detail view tests
└── test_key_search.py     # Key search tests
```

### Test Types

- **View Tests**: Most test are created as functional tests that are directly
calling views.

## Running Tests

### Prerequisites

Before running tests, ensure you have:

- **Redis server** running on `127.0.0.1:6379` - consider running `docker compose up redis -d`
- **Test databases** 12-15 available
- **Development dependencies** run `make install`

### Quick Test Commands

```bash
# Run all tests
make test

# Run with coverage report
make test_coverage

# Run specific test file
pytest tests/test_views.py

# Run tests in parallel
pytest -n auto
```

### Detailed Test Commands

```bash
# Run tests with specific markers
pytest -m "not slow"

# Run tests matching pattern
pytest -k "test_key_detail"

# Run tests with debugging
pytest --pdb

# Run tests with coverage and HTML report
pytest --cov=dj_redis_panel --cov-report=html

# Run tests with timing information
pytest --durations=10
```

## Test Configuration

### Pytest Configuration

Tests are configured in `pytest.ini`:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = example_project.settings
testpaths = tests
addopts = --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
```

### Django Test Settings

The example project includes test-specific settings that are useful for manual testing

```python
# example_project/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database for tests
    }
}

# Redis test configuration
DJ_REDIS_PANEL_SETTINGS = {
    "INSTANCES": {
        "test": {
            "description": "Test Redis Instance",
            "host": "127.0.0.1",
            "port": 6379,
            "db": 13,  # Use database 13 for tests
        }
    }
}
```

### Test Database Setup

Tests use Redis databases 12, 13, 14, and 15 to avoid interfering with development data:

- **Database 12**: Reserved for large collection testing (e.g. pagination related tests)
- **Database 13**: Primary test database
- **Database 14**: Secondary test database for multi-instance tests
- **Database 15**: Reserved for special test cases

### Manual Testing
For manually testing dj-redis-panel, a cli utiliy has been created in order to easily
create sample data in a redis instance. For safety reasons, this utility is part
of the example project within the repo and not directly part of the dj-redis-panel
package.

```bash
# run from the example project directory
python manage.py populate redis
```
