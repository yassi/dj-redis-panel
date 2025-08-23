# Development Setup

This guide will help you set up Django Redis Panel for local development and contribution.

## Prerequisites

Before setting up the development environment, make sure you have:

- **Python 3.9+**: The minimum supported Python version
- **Redis Server**: A running Redis instance for testing
- **Git**: For version control
- **Make**: For using the included Makefile commands

### System Dependencies

=== "macOS"
    ```bash
    # Install Python (if not already installed)
    brew install python@3.11
    
    # Install Redis
    brew install redis
    
    # Start Redis
    brew services start redis
    ```

=== "Ubuntu/Debian"
    ```bash
    # Install Python and pip
    sudo apt update
    sudo apt install python3 python3-pip python3-venv
    
    # Install Redis
    sudo apt install redis-server
    
    # Start Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    ```

=== "CentOS/RHEL"
    ```bash
    # Install Python
    sudo dnf install python3 python3-pip
    
    # Install Redis
    sudo dnf install redis
    
    # Start Redis
    sudo systemctl start redis
    sudo systemctl enable redis
    ```

=== "Docker"
    ```bash
    # Use the included docker-compose file
    docker-compose up redis -d
    ```

## Getting the Source Code

### 1. Fork and Clone

1. **Fork the repository** on GitHub: [yassi/dj-redis-panel](https://github.com/yassi/dj-redis-panel)

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dj-redis-panel.git
   cd dj-redis-panel
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/yassi/dj-redis-panel.git
   ```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Development Installation

The project includes a Makefile with several useful commands for development.

### Quick Setup

```bash
# Install in development mode with all dependencies
make install_dev
```

This command will:
- Build and install the package in development mode
- Install all development dependencies (pytest, coverage, etc.)
- Set up the package for local development

### Manual Setup

If you prefer manual installation:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or install from requirements
pip install -r requirements.txt
```

### Available Make Commands

```bash
# Build and install the package
make install

# Run all tests
make test

# Run tests with coverage
make test_coverage

# Clean build artifacts
make clean

# Build distribution packages
make build

# Upload to PyPI (maintainers only)
make publish

# Serve documentation locally
make docs_serve
```

## Project Structure

Understanding the project layout:

```
dj-redis-panel/
├── dj_redis_panel/          # Main package
│   ├── __init__.py
│   ├── admin.py             # Django admin integration
│   ├── apps.py              # Django app configuration
│   ├── models.py            # Django models (empty)
│   ├── redis_utils.py       # Redis utility functions
│   ├── urls.py              # URL patterns
│   ├── views.py             # Django views
│   └── templates/           # Django templates
│       └── admin/
│           └── dj_redis_panel/
│               ├── base.html
│               ├── index.html
│               ├── instance_overview.html
│               ├── key_detail.html
│               ├── key_search.html
│               └── styles.css
├── example_project/         # Example Django project
│   ├── manage.py
│   └── example_project/
│       ├── __init__.py
│       ├── settings.py      # Django settings
│       ├── urls.py          # URL configuration
│       ├── wsgi.py
│       └── management/      # Custom management commands
│           └── commands/
│               └── populate_redis.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── base.py              # Test base classes
│   ├── conftest.py          # Pytest configuration
│   ├── test_index.py        # Index view tests
│   ├── test_instance_overview.py
│   ├── test_key_detail.py
│   └── test_key_search.py
├── docs/                    # Documentation
├── images/                  # Screenshots for README
├── pyproject.toml          # Project configuration
├── requirements.txt        # Development dependencies
├── Makefile               # Development commands
└── README.md              # Project documentation
```

## Example Project Setup

The repository includes an example Django project for development and testing.

### 1. Set Up the Example Project

```bash
cd example_project

# Run migrations (creates Django tables, not Redis Panel tables)
python manage.py migrate

# Create a superuser
python manage.py createsuperuser
```

### 2. Populate Test Data

```bash
# Populate Redis with sample data for testing
python manage.py populate_redis
```

This command creates various types of Redis keys for testing:
- String keys with different formats (JSON, plain text)
- Hash keys with user profiles
- List keys with notifications
- Set keys with tags and permissions
- Sorted set keys with leaderboards

### 3. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the Django admin with Redis Panel.


## Documentation Development

### Building Documentation

The documentation is built with MkDocs:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Writing Documentation

Documentation is written in Markdown and located in the `docs/` directory:

- Follow the existing structure and style
- Include code examples for new features
- Add screenshots for UI changes
- Update the navigation in `mkdocs.yml`


## Getting Help

### Development Questions

- **GitHub Discussions**: [Project discussions](https://github.com/yassi/dj-redis-panel/discussions)
- **Issues**: [Report bugs or request features](https://github.com/yassi/dj-redis-panel/issues)
- **Email**: Contact maintainers directly for sensitive issues

### Resources

- **Django Documentation**: [Django Project](https://docs.djangoproject.com/)
- **Redis Documentation**: [Redis Commands](https://redis.io/commands)
- **Python Packaging**: [PyPA Guides](https://packaging.python.org/)
- **Testing**: [Pytest Documentation](https://docs.pytest.org/)

Thank you for contributing to Django Redis Panel! 🎉
