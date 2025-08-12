# Configuration

This page covers all the configuration options available in Django Redis Panel.

## Basic Configuration

Django Redis Panel is configured through the `DJ_REDIS_PANEL_SETTINGS` dictionary in your Django settings file.

```python
# settings.py
DJ_REDIS_PANEL_SETTINGS = {
    # Global feature flags
    "ALLOW_KEY_DELETE": False,
    "ALLOW_KEY_EDIT": True,
    "ALLOW_TTL_UPDATE": True,
    "CURSOR_PAGINATED_SCAN": False,
    
    # Redis instances configuration
    "INSTANCES": {
        # ... instance configurations
    }
}
```

## Global Settings

These settings apply to all Redis instances unless overridden at the instance level.

| Setting | Default | Description |
|---------|---------|-------------|
| `ALLOW_KEY_DELETE` | `False` | Allow deletion of Redis keys |
| `ALLOW_KEY_EDIT` | `True` | Allow editing of key values |
| `ALLOW_TTL_UPDATE` | `True` | Allow updating key TTL (expiration) |
| `CURSOR_PAGINATED_SCAN` | `False` | Use cursor-based pagination instead of page-based |

### Feature Flags Details

#### `ALLOW_KEY_DELETE`

Controls whether users can delete Redis keys through the interface.

- **`True`**: Shows delete buttons and allows key deletion
- **`False`**: Hides delete functionality (recommended for production)

!!! warning "Production Safety"
    It's recommended to set this to `False` in production environments to prevent accidental data loss.

#### `ALLOW_KEY_EDIT`

Controls whether users can modify Redis key values.

- **`True`**: Allows editing of key values
- **`False`**: Makes the interface read-only for key values

#### `ALLOW_TTL_UPDATE`

Controls whether users can modify key expiration times.

- **`True`**: Shows TTL controls and allows expiration updates
- **`False`**: Hides TTL modification functionality

#### `CURSOR_PAGINATED_SCAN`

Controls the pagination method for browsing keys.

- **`True`**: Uses Redis SCAN command with cursor-based pagination (more efficient for large datasets)
- **`False`**: Uses traditional page-based pagination with KEYS command

!!! tip "Performance"
    Use cursor-based pagination (`True`) for Redis instances with many keys for better performance.

## Instance Configuration

Each Redis instance is configured under the `INSTANCES` key. You can define multiple instances with different settings.

### Connection Methods

#### Host/Port Configuration

```python
"instance_name": {
    "description": "Human-readable description",
    "host": "127.0.0.1",
    "port": 6379,
    "password": "password",     # Optional
}
```

#### URL Configuration

```python
"instance_name": {
    "description": "Human-readable description", 
    "url": "redis://user:password@host:port/db",
}
```

#### SSL/TLS Configuration

```python
"secure_instance": {
    "description": "Secure Redis Instance",
    "url": "rediss://user:password@host:6380",  # Note: rediss:// for SSL
}
```

### Per-Instance Feature Overrides

You can override global feature flags for individual instances:

```python
"instance_name": {
    "description": "Production Redis",
    "host": "prod-redis.example.com",
    "port": 6379,
    "features": {
        "ALLOW_KEY_DELETE": False,      # Override global setting
        "CURSOR_PAGINATED_SCAN": True,  # Use cursor pagination for this instance
    },
}
```

## Complete Configuration Examples

### Development Environment

```python
DJ_REDIS_PANEL_SETTINGS = {
    # Permissive settings for development
    "ALLOW_KEY_DELETE": True,
    "ALLOW_KEY_EDIT": True,
    "ALLOW_TTL_UPDATE": True,
    "CURSOR_PAGINATED_SCAN": False,
    
    "INSTANCES": {
        "default": {
            "description": "Local Development Redis",
            "host": "127.0.0.1",
            "port": 6379,
        },
        "cache": {
            "description": "Local Cache Redis",
            "host": "127.0.0.1",
            "port": 6379,
        },
    }
}
```

### Production Environment

```python
DJ_REDIS_PANEL_SETTINGS = {
    # Restrictive settings for production
    "ALLOW_KEY_DELETE": False,
    "ALLOW_KEY_EDIT": False,
    "ALLOW_TTL_UPDATE": False,
    "CURSOR_PAGINATED_SCAN": True,
    
    "INSTANCES": {
        "primary": {
            "description": "Primary Redis Cluster",
            "url": "rediss://user:password@redis-primary.example.com:6380/0",
        },
        "cache": {
            "description": "Cache Redis Instance",
            "url": "rediss://user:password@redis-cache.example.com:6380/0",
            "features": {
                "ALLOW_KEY_EDIT": True,  # Allow cache key editing
            },
        },
        "sessions": {
            "description": "Session Storage",
            "url": "rediss://user:password@redis-sessions.example.com:6380/0",
        },
    }
}
```

### Mixed Environment (Staging)

```python
DJ_REDIS_PANEL_SETTINGS = {
    # Balanced settings for staging
    "ALLOW_KEY_DELETE": False,
    "ALLOW_KEY_EDIT": True,
    "ALLOW_TTL_UPDATE": True,
    "CURSOR_PAGINATED_SCAN": True,
    
    "INSTANCES": {
        "staging": {
            "description": "Staging Redis",
            "host": "staging-redis.example.com",
            "port": 6379,
            "password": "staging-password",
        },
        "debug": {
            "description": "Debug Redis (Full Access)",
            "host": "127.0.0.1",
            "port": 6379,
            "features": {
                "ALLOW_KEY_DELETE": True,  # Allow deletion for debugging
            },
        },
    }
}
```

## Environment-Specific Configuration

You can use different configurations based on your Django environment:

```python
# settings.py
import os

# Base configuration
DJ_REDIS_PANEL_SETTINGS = {
    "ALLOW_KEY_EDIT": True,
    "ALLOW_TTL_UPDATE": True,
    "CURSOR_PAGINATED_SCAN": True,
    "INSTANCES": {
        "default": {
            "description": "Default Redis",
            "host": os.getenv("REDIS_HOST", "127.0.0.1"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "password": os.getenv("REDIS_PASSWORD"),
        }
    }
}

# Environment-specific overrides
if os.getenv("DJANGO_ENV") == "production":
    DJ_REDIS_PANEL_SETTINGS["ALLOW_KEY_DELETE"] = False
    DJ_REDIS_PANEL_SETTINGS["ALLOW_KEY_EDIT"] = False
else:
    DJ_REDIS_PANEL_SETTINGS["ALLOW_KEY_DELETE"] = True
```

## Configuration Validation

Django Redis Panel validates your configuration on startup. Common validation errors include:

- **Missing INSTANCES**: At least one Redis instance must be configured
- **Invalid connection parameters**: Host/port or URL must be provided
- **Connection failures**: Redis instances must be accessible

## Security Considerations

### Production Recommendations

1. **Disable destructive operations**:
   ```python
   "ALLOW_KEY_DELETE": False
   ```

2. **Use read-only mode for sensitive data**:
   ```python
   "ALLOW_KEY_EDIT": False
   ```

3. **Use SSL/TLS connections**:
   ```python
   "url": "rediss://user:password@host:6380/0"
   ```

4. **Restrict admin access**: Ensure only trusted staff users have admin access

5. **Use environment variables** for sensitive data like passwords

### Network Security

- Use Redis AUTH when possible
- Restrict Redis server access to trusted networks
- Use SSL/TLS for connections over untrusted networks
- Consider using Redis ACLs for fine-grained access control

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with your configured instances
- [Features Overview](features.md) - Learn about all available features
- [Development Setup](development.md) - Set up for local development
