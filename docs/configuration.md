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
    "CURSOR_PAGINATED_COLLECTIONS": False,
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
| `ALLOW_KEY_EDIT` | `False` | Allow editing of key values |
| `ALLOW_TTL_UPDATE` | `False` | Allow updating key TTL (expiration) |
| `CURSOR_PAGINATED_SCAN` | `False` | Use cursor-based pagination instead of page-based |
| `CURSOR_PAGINATED_COLLECTIONS` | `False` | Use cursor-based pagination for key values like lists and hashes |
| `encoder` | `"utf-8"` | Encoding to use for decoding/encoding Redis values |
| `socket_timeout` | `5.0` | Socket timeout in seconds for Redis operations |
| `socket_connect_timeout` | `3.0` | Connection timeout in seconds for establishing Redis connections |

### Feature Flags Details

#### `ALLOW_KEY_DELETE`

Controls whether users can delete Redis keys through the interface.

- **`True`**: Shows delete buttons and allows key deletion
- **`False`**: Hides delete functionality (recommended for production)

!!! warning "Production Safety"
    It's recommended to set this to `False` in production environments to prevent accidental data loss.

#### `ALLOW_KEY_EDIT`

Controls whether users can modify Redis key values.

- **`True`**: Allows editing of key values and collections (e.g. allow updates and deletes on lists, etc.)
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

#### `CURSOR_PAGINATED_COLLECTIONS`

Controls the pagination method for key values such as lists, hashes, and sets

- **`True`**: Uses cursor to paginate across large collection based values
- **`False`**: Uses traditional page-based pagination

!!! tip "Performance"
    For very large collections (e.g. keeping a very large leader board) use the cursor paginated
    method in order perform too many expensive queries on your instance.

#### `socket_timeout`

Controls how long to wait for Redis socket operations to complete.

- **Default**: `5.0` seconds
- **Purpose**: Prevents browser tabs from hanging indefinitely when Redis operations are slow
- **Recommended values**: 
  - Development: `5.0` - `10.0` seconds
  - Production: `3.0` - `5.0` seconds

!!! info "Socket Timeout"
    This timeout applies to individual Redis commands after a connection has been established. If a Redis command takes longer than this timeout, it will fail with a timeout error instead of hanging the browser.

#### `socket_connect_timeout`

Controls how long to wait when establishing a connection to Redis.

- **Default**: `3.0` seconds  
- **Purpose**: Prevents long waits when Redis instances are unreachable
- **Recommended values**:
  - Local Redis: `1.0` - `3.0` seconds
  - Remote Redis: `3.0` - `5.0` seconds

!!! info "Connection Timeout"
    This timeout applies only to the initial connection establishment. Once connected, `socket_timeout` governs individual operations.

#### `ENCODER`

Controls how Redis values are decoded from bytes to strings and encoded back to bytes. When Redis returns binary data that can't be decoded with the specified encoding, it falls back to a bytes literal representation.

NOTE: More most setups, specifying this setting explicitly may not be needed. the default utf-8
encoding will usually be fine.

- **Default**: `"utf-8"` - Use UTF-8 encoding
- **Alternative encodings**: `"latin-1"`, `"utf-16"`, `"cp1252"`, etc.
- **Fallback behavior**: If encoding fails, returns a bytes literal representation (e.g., `b'\x80\x04...'`)

**Use Cases:**

- **Binary Data**: When Redis contains pickle, msgpack, or other binary data
- **Legacy Systems**: When dealing with data encoded in non-UTF-8 formats
- **International Data**: When data might be encoded in different character sets

!!! warning "Binary Data Handling"
    When the decoder encounters binary data that can't be decoded with any encoding in the pipeline, it displays the data as a bytes literal representation (e.g., `b'\x80\x04\x95...'`). This clearly indicates binary data and prevents UTF-8 decoding errors while still allowing you to see and manage the data.

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

You can override global feature flags, timeout settings, and encoder for individual instances:

```python
"instance_name": {
    "description": "Production Redis",
    "host": "prod-redis.example.com",
    "port": 6379,
    "features": {
        "ALLOW_KEY_DELETE": False,      # Override global setting
        "CURSOR_PAGINATED_SCAN": True,  # Use cursor pagination for this instance
    },
    # Instance-specific overrides
    "encoder": "latin-1",           # Use different encoding for this instance
    "socket_timeout": 10.0,         # Allow longer operations for this instance
    "socket_connect_timeout": 5.0,  # Allow more time to connect to remote server
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
    
    # Relaxed timeouts for development
    "socket_timeout": 10.0,
    "socket_connect_timeout": 5.0,
    
    # Default UTF-8 encoding (can handle binary data gracefully)
    "encoder": "utf-8",
    
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
    
    # Conservative timeouts for production
    "socket_timeout": 3.0,
    "socket_connect_timeout": 2.0,
    
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
            # Allow slightly longer timeouts for cache operations
            "socket_timeout": 5.0,
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
    
    # Balanced timeouts for staging
    "socket_timeout": 5.0,
    "socket_connect_timeout": 3.0,
    
    "INSTANCES": {
        "staging": {
            "description": "Staging Redis",
            "host": "staging-redis.example.com",
            "port": 6379,
            "password": "staging-password",
            # Remote server may need longer connection timeout
            "socket_connect_timeout": 5.0,
        },
        "debug": {
            "description": "Debug Redis (Full Access)",
            "host": "127.0.0.1",
            "port": 6379,
            "features": {
                "ALLOW_KEY_DELETE": True,  # Allow deletion for debugging
            },
            # Local debug instance can use faster timeouts
            "socket_timeout": 2.0,
            "socket_connect_timeout": 1.0,
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
    # Default timeouts
    "socket_timeout": 5.0,
    "socket_connect_timeout": 3.0,
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
    # Stricter timeouts for production
    DJ_REDIS_PANEL_SETTINGS["socket_timeout"] = 3.0
    DJ_REDIS_PANEL_SETTINGS["socket_connect_timeout"] = 2.0
else:
    DJ_REDIS_PANEL_SETTINGS["ALLOW_KEY_DELETE"] = True
    # More relaxed timeouts for development
    DJ_REDIS_PANEL_SETTINGS["socket_timeout"] = 10.0
    DJ_REDIS_PANEL_SETTINGS["socket_connect_timeout"] = 5.0
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
