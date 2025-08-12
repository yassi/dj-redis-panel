# Quick Start Guide

This guide will get you up and running with Django Redis Panel in just a few minutes.

## Prerequisites

Before starting, make sure you have:

- ✅ Django Redis Panel [installed](installation.md)
- ✅ A running Redis server
- ✅ Django admin access

## Step 1: Access the Admin Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to your Django admin interface:
   ```
   http://127.0.0.1:8000/admin/
   ```

3. Log in with your admin credentials

4. Look for the **"DJ_REDIS_PANEL"** section in the admin home page

## Step 2: Explore Your Redis Instances

1. Click on **"Manage Redis keys and values"**

2. You'll see a list of your configured Redis instances with their status:
   - 🟢 **Connected**: Instance is accessible
   - 🔴 **Error**: Connection failed

3. Click on any instance to view its overview

## Step 3: Instance Overview

The instance overview page shows:

- **Connection Info**: Host, port, database number
- **Server Info**: Redis version, uptime, memory usage
- **Database Stats**: Total keys, expires, memory usage per database
- **Quick Actions**: Direct links to browse keys

![Instance Overview](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/instance_overview.png)

## Step 4: Browse Redis Keys

1. From the instance overview, click **"Browse Keys"** or navigate to the key search page

2. You'll see the key browser with:
   - **Search box**: Enter patterns like `user:*` or `session:*`
   - **Database selector**: Switch between Redis databases
   - **Pagination controls**: Navigate through results

![Key Search](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_search_page_index.png)

### Search Examples

Try these search patterns:

- `*` - Show all keys
- `user:*` - All keys starting with "user:"
- `*session*` - All keys containing "session"
- `cache:user:*` - Nested pattern matching

## Step 5: Inspect Key Details

1. Click on any key from the search results

2. The key detail page shows:
   - **Key information**: Name, type, TTL, size
   - **Value display**: Formatted based on data type
   - **Actions**: Edit, delete, update TTL (if enabled)

![Key Detail - String](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_detail_string.png)

### Data Type Examples

=== "String"
    Simple text values with edit capability
    ```
    Key: user:1:name
    Value: "John Doe"
    ```

=== "Hash"
    Field-value pairs displayed in a table
    ```
    Key: user:1:profile
    Fields:
    - name: "John Doe"
    - email: "john@example.com"
    - age: "30"
    ```

=== "List"
    Ordered list of values with pagination
    ```
    Key: user:1:notifications
    Items:
    0: "Welcome message"
    1: "New feature available"
    ```

=== "Set"
    Unique values in no particular order
    ```
    Key: user:1:tags
    Members:
    - "premium"
    - "verified"
    - "active"
    ```

## Step 6: Key Management (Optional)

If key editing is enabled in your configuration, you can:

### Edit Key Values

1. Click the **"Edit"** button on a key detail page
2. Modify the value in the text area
3. Click **"Save"** to update the key

### Update TTL (Time To Live)

1. Use the TTL controls to set expiration
2. Options include:
   - Set specific expiration time
   - Set seconds/minutes/hours from now
   - Remove expiration (make key persistent)

### Delete Keys

!!! warning "Destructive Operation"
    Key deletion is permanent and cannot be undone. Use with caution.

1. Click the **"Delete"** button
2. Confirm the deletion in the popup
3. The key will be permanently removed from Redis

## Common Workflows

### Debugging Application Issues

1. **Search for user-specific keys**:
   ```
   user:123:*
   ```

2. **Check session data**:
   ```
   session:*
   ```

3. **Inspect cache entries**:
   ```
   cache:*
   ```

### Cache Management

1. **Find all cache keys**:
   ```
   cache:*
   ```

2. **Check cache hit rates** in instance overview

3. **Clear specific cache entries** by deleting keys

### Session Debugging

1. **Find user sessions**:
   ```
   session:*
   ```

2. **Inspect session data** to debug login issues

3. **Remove problematic sessions** if needed

## Tips and Best Practices

### Search Efficiency

- Use specific patterns instead of `*` for large datasets
- Enable cursor-based pagination for better performance
- Use database selection to narrow down results

### Safety

- Always verify key contents before deletion
- Use read-only mode in production environments
- Test configuration changes in development first

### Performance

- Enable cursor pagination for large key sets
- Use specific search patterns to reduce result sets
- Monitor Redis memory usage in instance overview

## Troubleshooting

### Can't see Redis Panel in admin

- Verify `dj_redis_panel` is in `INSTALLED_APPS`
- Check that you're logged in as a staff user
- Ensure URLs are properly configured

### Connection errors

- Verify Redis server is running
- Check host, port, and credentials in configuration
- Test Redis connection outside of Django

### No keys visible

- Verify you're looking in the correct database
- Check if Redis instance actually contains data
- Try using `*` pattern to show all keys

## Next Steps

Now that you're familiar with the basics:

- [Explore all features](features.md) in detail
- [Learn about configuration options](configuration.md)
- [View screenshots](screenshots.md) of all interfaces
- [Understand Redis data types](redis-data-types.md) support
