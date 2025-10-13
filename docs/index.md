# Django Redis Panel

A Django Admin panel for browsing, inspecting, and managing Redis keys. No PostgreSQL/MySQL models or changes required.

![Django Redis Panel - Instance List](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_search_page_index.png)

## Overview

Django Redis Panel seamlessly integrates into your existing Django admin interface, providing a powerful tool for Redis database management without requiring any model definitions or database migrations.

## Key Features

- **Browse Redis Keys**: Search and filter Redis keys with pattern matching
- **Instance Overview**: Monitor Redis instance metrics and database statistics  
- **Key Management**: View, edit, and delete Redis keys with support for all data types
- **Feature Toggles**: Granular control over operations (delete, edit, TTL updates)
- **Pagination**: Both traditional page-based and cursor-based pagination support
- **Django Admin Integration**: Seamless integration with Django admin styling and dark mode
- **Permission Control**: Respects Django admin permissions and staff-only access
- **Multiple Instances**: Support for multiple Redis instances with different configurations

## Supported Redis Data Types

- **String**: View and edit string values
- **List**: Browse list items with pagination and edit/delete list items
- **Set**: View set members and delete
- **Hash**: Display hash fields and values in a table format. Ability to edit hash values and delete hash entries.
- **Sorted Set**: Show sorted set members with scores. Able to delete set members and edit scores.


## Requirements

- Python 3.9+
- Django 4.2+
- Redis 4.0+
- redis-py 4.0+

Note: some combinations of versions of python and django are not supported. Wherever these
combinations are not supported, dj-redis-panel is also not supported.

## License

This project is licensed under the MIT License.

## Getting Help

- 📖 [Read the full documentation](installation.md)
- 🐛 [Report issues on GitHub](https://github.com/yassi/dj-redis-panel/issues)
- 💡 [Request features](https://github.com/yassi/dj-redis-panel/issues/new)
