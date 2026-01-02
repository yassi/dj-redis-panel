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
    ```

=== "Ubuntu/Debian"
    ```bash
    # Install Python and pip
    sudo apt update
    sudo apt install python3 python3-pip python3-venv
    ```

=== "CentOS/RHEL"
    ```bash
    # Install Python
    sudo dnf install python3 python3-pip    
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
If you want to work on your host machine using a virtualenv

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
# This will bring up all docker containers for this project and set up a dev
# environment to run the example project in as well.
make test

# then log into the dev environment with:
make docker_shell

# from the example project directory
python manage.py runserver 0.0.0.0:8000

# You can proceed to look at this project's /admin url
# don't forget to setup a superuser as well
python manage.py createsuperuser
```
### Manual Setup

If you prefer manual installation on the host machine

```bash
# Install dj-redis-panel into your environment
pip install -e .

# Install other development only packages
pip install -r requirements.txt
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

## SSL/TLS Cluster Testing (Optional)

By default, the Redis cluster runs without SSL. To test SSL/TLS connections (e.g., for AWS ElastiCache compatibility):

### 1. Generate SSL Certificates

```bash
# Generate certificates using mkcert (recommended) or openssl
make generate_ssl_certs
```

This creates certificates in the `ssl-certs/` directory. You only need to do this once.

### 2. Start Clusters

You can run the SSL cluster alone or alongside the non-SSL cluster:

```bash
# Option A: Start both clusters simultaneously (recommended for testing)
make docker_up_all

# Option B: Start SSL cluster only
make docker_up_ssl

# Option C: Start non-SSL cluster only (default)
make docker_up
```

### 3. Verify Connections

```bash
# Non-SSL cluster (ports 9000-9002)
docker compose exec redis-node-0 redis-cli -c -p 6379 cluster info

# SSL cluster non-SSL port (ports 9100-9102)
docker compose exec redis-node-0-ssl redis-cli -c -p 6379 cluster info

# SSL cluster SSL port (ports 9110-9112)
docker compose exec redis-node-0-ssl redis-cli -c -p 6380 \
  --tls --insecure cluster info
```

### 4. Test in Django Admin

When running with SSL, you'll see these cluster instances:
- **redis-cluster**: Non-SSL connection (ports 9000-9002)
- **redis-cluster-url**: Non-SSL URL connection
- **redis-cluster-ssl**: SSL/TLS connection using `rediss://` protocol (ports 9110-9112)

### Stop All Clusters

```bash
make docker_down
```

**Note**: SSL testing is completely optional. All tests and development work without SSL certificates.

For detailed SSL setup instructions, see [SSL Cluster Setup Guide](ssl-cluster-setup.md).

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
