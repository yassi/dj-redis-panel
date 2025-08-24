import redis
import logging
from django.conf import settings
from typing import Dict, Any


logger = logging.getLogger(__name__)


REDIS_PANEL_SETTINGS_NAME = "DJ_REDIS_PANEL_SETTINGS"


class RedisPanelUtils:
    @classmethod
    def get_settings(cls) -> Dict[str, Any]:  # pragma: no cover
        panel_settings = getattr(settings, REDIS_PANEL_SETTINGS_NAME, {})
        return panel_settings

    @classmethod
    def get_instances(cls) -> Dict[str, Dict[str, Any]]:
        panel_settings = cls.get_settings()
        instances = panel_settings.get("INSTANCES", {})
        return instances

    @classmethod
    def is_feature_enabled(cls, instance_alias: str, feature_name: str) -> bool:
        """
        Check if a feature is enabled for a specific instance.
        
        Priority order:
        1. Instance-specific feature setting
        2. Global feature setting
        3. Default False
        """
        instances = cls.get_instances()
        panel_settings = cls.get_settings()
        
        # Check if instance exists
        if instance_alias not in instances:
            return False
        
        instance_config = instances[instance_alias]
        
        # Check instance-specific features first
        instance_features = instance_config.get("features", {})
        if feature_name in instance_features:
            return bool(instance_features[feature_name])
        
        # Fall back to global setting
        return bool(panel_settings.get(feature_name, False))

    @classmethod
    def get_redis_connection(cls, instance_alias: str) -> redis.Redis:
        """
        Create a direct Redis connection for the specified instance.
        Supports single Redis instances with future extensibility for clusters.
        """
        instances = cls.get_instances()
        if instance_alias not in instances:
            raise ValueError(
                f"Redis instance '{instance_alias}' not found in configuration"
            )

        instance_config = instances[instance_alias]

        # Handle different connection types (future: cluster, sentinel)
        connection_type = instance_config.get("type", "single")

        if connection_type == "single":
            return cls._create_single_connection(instance_config)
        # Future: elif connection_type == "cluster":
        #     return cls._create_cluster_connection(instance_config)
        else:
            raise ValueError(f"Unsupported Redis connection type: {connection_type}")

    @classmethod
    def _create_single_connection(cls, config: Dict[str, Any]) -> redis.Redis:
        """Create a connection to a single Redis instance."""
        connection_params = {
            "host": config.get("host", "127.0.0.1"),
            "port": config.get("port", 6379),
            "db": 0,  # Always connect to DB 0 initially, switch in UI
            "decode_responses": True,  # Always decode for management operations
        }

        if "url" in config:
            if config["url"].startswith("rediss://"):
                logger.debug(f"Creating Redis connection using URL with SSL enabled")
                return redis.Redis.from_url(
                    config["url"],
                    ssl_cert_reqs=config.get("ssl_cert_reqs", None),
                    decode_responses=True,
                )
            else:
                logger.debug(f"Creating Redis connection using URL with SSL disabled")
                return redis.Redis.from_url(config["url"], decode_responses=True)

        # Optional connection parameters
        if "password" in config:
            connection_params["password"] = config["password"]
        if "username" in config:
            connection_params["username"] = config["username"]
        if "ssl" in config:
            connection_params["ssl"] = config["ssl"]
        if "ssl_cert_reqs" in config:
            connection_params["ssl_cert_reqs"] = config["ssl_cert_reqs"]
        if "socket_timeout" in config:
            connection_params["socket_timeout"] = config["socket_timeout"]
        if "socket_connect_timeout" in config:
            connection_params["socket_connect_timeout"] = config[
                "socket_connect_timeout"
            ]

        logger.debug(f"Creating Redis connection with params for host: {connection_params['host']}, port: {connection_params['port']}")

        return redis.Redis(**connection_params)

    @classmethod
    def get_instance_meta_data(cls, instance_alias: str) -> Dict[str, Any]:
        """
        Ping a redis instance and return meta data about the instance.
        Includes parsed database information for the instance overview.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.ping()
            info = redis_conn.info()
            total_keys = 0
            databases = []

            # Get all databases, their key counts and other info
            for db_num in range(16):
                db_key = f"db{db_num}"
                if db_key in info:
                    db_info = info[db_key]
                    key_count = db_info.get("keys", 0)
                    total_keys += key_count
                    if key_count > 0 or db_num == 0:
                        databases.append(
                            {
                                "db_number": db_num,
                                "is_default": db_num == 0,
                                **db_info,
                            }
                        )

            hero_numbers = {
                "version": info.get("redis_version", "Unknown"),
                "memory_used": info.get("used_memory_human", "Unknown"),
                "memory_peak": info.get("used_memory_peak_human", "Unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }

            return {
                "status": "connected",
                "info": info,
                "total_keys": total_keys,
                "hero_numbers": hero_numbers,
                "databases": databases,
                "error": None,
            }
        except Exception as e:
            logger.exception(f"Error getting instance meta data for {instance_alias}", exc_info=True)
            return {
                "status": "disconnected",
                "info": None,
                "total_keys": 0,
                "hero_numbers": None,
                "databases": [],
                "error": str(e),
            }
    


    @classmethod
    def paginated_scan(
        cls, 
        instance_alias: str, 
        db_number: int, 
        pattern: str = "*", 
        page: int = 1, 
        per_page: int = 25,
        scan_count: int = 100
    ) -> Dict[str, Any]:
        """
        Perform a paginated SCAN operation on Redis keys.
        
        Scans all matching keys first, then applies pagination.
        This ensures accurate pagination information and total counts.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Scan all matching keys
            cursor = 0
            all_keys = []
            scan_iterations = 0
            max_scan_iterations = 2000  # Prevent infinite loops
            
            while scan_iterations < max_scan_iterations:
                cursor, partial_keys = redis_conn.scan(
                    cursor=cursor, match=pattern, count=scan_count
                )
                all_keys.extend(partial_keys)
                scan_iterations += 1
                
                if cursor == 0:  # Scan complete
                    break
                    
                # Safety limit to prevent memory issues with very large datasets
                if len(all_keys) >= 100000:
                    break
            
            # Sort keys for consistent pagination
            all_keys.sort()
            
            total_keys = len(all_keys)
            total_pages = (total_keys + per_page - 1) // per_page if total_keys > 0 else 1
            
            # Calculate pagination bounds
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            page_keys = all_keys[start_index:end_index]
            
            # Get detailed information for each key on this page
            keys_with_details = []
            for key in page_keys:
                try:
                    key_str = str(key)
                    key_type = redis_conn.type(key)
                    ttl = redis_conn.ttl(key)
                    
                    # Get size/length based on type
                    size = 0
                    if key_type == "string":
                        value = redis_conn.get(key) or ""
                        size = len(str(value).encode("utf-8"))
                    elif key_type == "list":
                        size = redis_conn.llen(key)
                    elif key_type == "set":
                        size = redis_conn.scard(key)
                    elif key_type == "zset":
                        size = redis_conn.zcard(key)
                    elif key_type == "hash":
                        size = redis_conn.hlen(key)
                    
                    keys_with_details.append({
                        "key": key_str,
                        "type": key_type,
                        "ttl": ttl if ttl > 0 else None,
                        "size": size,
                    })
                except Exception:
                    # Skip keys that can't be processed
                    continue
            
            return {
                "keys": [str(key) for key in page_keys],
                "keys_with_details": keys_with_details,
                "total_keys": total_keys,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_more": page < total_pages,
                "scan_complete": cursor == 0,
                "limited_scan": len(all_keys) >= 100000,
                "error": None
            }
            
        except Exception as e:
            logger.exception(f"Error in paginated scan for {instance_alias}", exc_info=True)
            return {
                "keys": [],
                "keys_with_details": [],
                "total_keys": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "has_more": False,
                "scan_complete": False,
                "limited_scan": False,
                "error": str(e)
            }
        
    @classmethod
    def cursor_paginated_scan(
        cls, 
        instance_alias: str, 
        db_number: int, 
        pattern: str = "*", 
        per_page: int = 25,
        scan_count: int = 100,
        cursor: int = 0
    ) -> Dict[str, Any]:
        """
        Perform a cursor-based paginated SCAN operation on Redis keys.

        Rather than scanning all keys and then applying pagination,
        we scan the keys in chunks of scan_count. This is much more
        efficient and should be used whenever the dataset is too
        large and paginated_scan() is too slow.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Use the provided cursor directly - no approximation needed
            current_cursor = cursor
            page_keys = []
            scan_iterations = 0
            max_scan_iterations = 20  # Limit iterations per page to prevent infinite loops
            
            # Set scan_count to per_page for better cursor pagination behavior
            # This encourages Redis to return approximately the right number of keys per iteration
            scan_count = per_page
            
            # Perform one Redis SCAN iteration for this page
            current_cursor, partial_keys = redis_conn.scan(
                cursor=current_cursor, 
                match=pattern, 
                count=scan_count
            )
            
            # Filter keys from this scan iteration
            page_keys = [k for k in partial_keys if k]
            
            # Sort keys for consistent display
            page_keys.sort()
            
            # Get detailed information for each key on this page
            keys_with_details = []
            for key in page_keys:
                try:
                    key_str = str(key)
                    key_type = redis_conn.type(key)
                    ttl = redis_conn.ttl(key)
                    
                    # Get size/length based on type
                    size = 0
                    if key_type == "string":
                        value = redis_conn.get(key) or ""
                        size = len(str(value).encode("utf-8"))
                    elif key_type == "list":
                        size = redis_conn.llen(key)
                    elif key_type == "set":
                        size = redis_conn.scard(key)
                    elif key_type == "zset":
                        size = redis_conn.zcard(key)
                    elif key_type == "hash":
                        size = redis_conn.hlen(key)
                    
                    keys_with_details.append({
                        "key": key_str,
                        "type": key_type,
                        "ttl": ttl if ttl > 0 else None,
                        "size": size,
                    })
                except Exception:
                    # Skip keys that can't be processed
                    continue
            
            # With cursor-based pagination, we don't estimate totals
            # Instead, we focus on "has_more" navigation
            scan_complete = current_cursor == 0
            
            # Don't show "next" if:
            # 1. Scan is complete, OR
            # 2. This page returned no keys (prevents showing empty pages)
            has_more = not scan_complete and len(page_keys) > 0
            
            # For compatibility with the template, we provide minimal pagination info
            # In cursor-based pagination, we don't have accurate total counts
            estimated_total = len(page_keys) if scan_complete and cursor == 0 else len(page_keys)
            if has_more:
                estimated_total = max(estimated_total, per_page)  # At least one page worth
            
            return {
                "keys": [str(key) for key in page_keys],
                "keys_with_details": keys_with_details,
                "total_keys": estimated_total,  # Not accurate for cursor-based
                "page": 1,  # Always 1 for cursor-based (for template compatibility)
                "per_page": per_page,
                "total_pages": 1,  # Not meaningful in cursor-based pagination
                "has_more": has_more,
                "scan_complete": scan_complete,
                "limited_scan": False,
                "next_cursor": current_cursor,  # The cursor for the next page
                "current_cursor": cursor,  # The cursor used for this page
                "error": None
            }
            
        except Exception as e:
            logger.exception(f"Error in cursor paginated scan for {instance_alias}", exc_info=True)
            return {
                "keys": [],
                "keys_with_details": [],
                "total_keys": 0,
                "page": 1,  # Always 1 for cursor-based (for template compatibility)
                "per_page": per_page,
                "total_pages": 0,
                "has_more": False,
                "scan_complete": False,
                "limited_scan": False,
                "next_cursor": 0,
                "current_cursor": cursor,
                "error": str(e)
            }
    
    @classmethod
    def get_key_data(cls, instance_alias: str, db_number: int, key_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Redis key.
        This method does not support pagination.       
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            if not redis_conn.exists(key_name):
                return {
                    "name": key_name,
                    "type": None,
                    "ttl": None,
                    "size": 0,
                    "value": None,
                    "exists": False,
                    "error": None
                }
            
            key_type = redis_conn.type(key_name)
            ttl = redis_conn.ttl(key_name)
            
            key_value = None
            key_size = 0
            
            if key_type == "string":
                key_value = redis_conn.get(key_name) or ""
                key_size = len(str(key_value).encode("utf-8"))
            elif key_type == "list":
                key_value = redis_conn.lrange(key_name, 0, -1)
                key_size = redis_conn.llen(key_name)
            elif key_type == "set":
                key_value = list(redis_conn.smembers(key_name))
                key_size = redis_conn.scard(key_name)
            elif key_type == "zset":
                key_value = redis_conn.zrange(key_name, 0, -1, withscores=True)
                key_size = redis_conn.zcard(key_name)
            elif key_type == "hash":
                key_value = redis_conn.hgetall(key_name)
                key_size = redis_conn.hlen(key_name)
            
            return {
                "name": key_name,
                "type": key_type,
                "ttl": ttl if ttl > 0 else None,
                "size": key_size,
                "value": key_value,
                "exists": True,
                "error": None
            }
            
        except Exception as e:
            logger.exception(f"Error getting key data for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {
                "name": key_name,
                "type": None,
                "ttl": None,
                "size": 0,
                "value": None,
                "exists": False,
                "error": str(e)
            }

    @classmethod
    def get_paginated_key_data(
        cls, 
        instance_alias: str, 
        db_number: int, 
        key_name: str, 
        page: int = None,
        cursor: int = None,
        per_page: int = 50,
        pagination_threshold: int = 100
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific Redis key with pagination support for collections.
        
        Supports both page-based and cursor-based pagination:
        - Page-based: pass page parameter (e.g. page=1, page=2, etc.)
        - Cursor-based: pass cursor parameter (e.g. cursor=0, cursor=123, etc.)
        
        If neither page nor cursor is provided, defaults to page-based pagination with page=1.
        """
        try:
            # Determine pagination type and set defaults
            if cursor is not None:
                use_cursor_pagination = True
                cursor = max(0, cursor)  # Ensure cursor is non-negative
            else:
                use_cursor_pagination = False
                page = max(1, page or 1)  # Ensure page is at least 1
            
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Handle non-existent key
            if not redis_conn.exists(key_name):
                base_response = {
                    "name": key_name,
                    "type": None,
                    "ttl": None,
                    "size": 0,
                    "value": None,
                    "exists": False,
                    "error": None,
                    "is_paginated": False,
                }
                
                if use_cursor_pagination:
                    base_response.update({
                        "cursor": cursor,
                        "next_cursor": 0,
                        "has_more": False,
                        "showing_count": 0
                    })
                else:
                    base_response.update({
                        "page": page,
                        "per_page": per_page,
                        "total_pages": 0,
                        "has_more": False
                    })
                
                return base_response
            
            key_type = redis_conn.type(key_name)
            ttl = redis_conn.ttl(key_name)
            
            # Get collection size
            key_size = 0
            if key_type == "string":
                key_value = redis_conn.get(key_name) or ""
                key_size = len(str(key_value).encode("utf-8"))
                # Strings are never paginated
                base_response = {
                    "name": key_name,
                    "type": key_type,
                    "ttl": ttl if ttl > 0 else None,
                    "size": key_size,
                    "value": key_value,
                    "exists": True,
                    "error": None,
                    "is_paginated": False,
                }
                
                if use_cursor_pagination:
                    base_response.update({
                        "cursor": cursor,
                        "next_cursor": 0,
                        "has_more": False,
                        "showing_count": len(str(key_value))
                    })
                else:
                    base_response.update({
                        "page": page,
                        "per_page": per_page,
                        "total_pages": 0,
                        "has_more": False
                    })
                
                return base_response
                
            elif key_type == "list":
                key_size = redis_conn.llen(key_name)
            elif key_type == "set":
                key_size = redis_conn.scard(key_name)
            elif key_type == "zset":
                key_size = redis_conn.zcard(key_name)
            elif key_type == "hash":
                key_size = redis_conn.hlen(key_name)
            
            # Determine if pagination is needed
            should_paginate = key_size > pagination_threshold
            
            if not should_paginate:
                # Use the original method for small collections
                original_data = cls.get_key_data(instance_alias, db_number, key_name)
                original_data.update({"is_paginated": False})
                
                if use_cursor_pagination:
                    original_data.update({
                        "cursor": cursor,
                        "next_cursor": 0,
                        "has_more": False,
                        "showing_count": key_size
                    })
                else:
                    original_data.update({
                        "page": page,
                        "per_page": per_page,
                        "total_pages": 1 if key_size > 0 else 0,
                        "has_more": False
                    })
                
                return original_data
            
            # Handle paginated collections
            key_value = None
            
            if use_cursor_pagination:
                # Cursor-based pagination
                next_cursor = 0
                has_more = False
                showing_count = 0
                
                if key_type == "list":
                    # For lists, cursor represents the start index
                    start_index = cursor
                    end_index = start_index + per_page - 1
                    key_value = redis_conn.lrange(key_name, start_index, end_index)
                    showing_count = len(key_value)
                    next_cursor = start_index + showing_count
                    has_more = next_cursor < key_size
                    
                elif key_type == "set":
                    # Use SSCAN for cursor-based set iteration
                    scan_cursor, members = redis_conn.sscan(key_name, cursor=cursor, count=per_page)
                    key_value = list(members)
                    showing_count = len(key_value)
                    next_cursor = scan_cursor
                    has_more = scan_cursor != 0
                    
                elif key_type == "zset":
                    # For sorted sets, cursor represents the start index (already sorted by score)
                    start_index = cursor
                    end_index = start_index + per_page - 1
                    key_value = redis_conn.zrange(key_name, start_index, end_index, withscores=True)
                    showing_count = len(key_value)
                    next_cursor = start_index + showing_count
                    has_more = next_cursor < key_size
                    
                elif key_type == "hash":
                    # Use HSCAN for cursor-based hash iteration
                    scan_cursor, fields = redis_conn.hscan(key_name, cursor=cursor, count=per_page)
                    key_value = fields
                    showing_count = len(key_value)
                    next_cursor = scan_cursor
                    has_more = scan_cursor != 0
                
                # Calculate range information for display
                if key_type in ["list", "zset"]:
                    # For lists and sorted sets, cursor is the actual start index
                    range_start = cursor + 1 if showing_count > 0 else 0
                    range_end = cursor + showing_count
                else:
                    # For sets and hashes using scan cursors, we can't provide exact ranges
                    range_start = None
                    range_end = None
                
                return {
                    "name": key_name,
                    "type": key_type,
                    "ttl": ttl if ttl > 0 else None,
                    "size": key_size,
                    "value": key_value,
                    "exists": True,
                    "error": None,
                    "is_paginated": True,
                    "cursor": cursor,
                    "next_cursor": next_cursor,
                    "has_more": has_more,
                    "showing_count": showing_count,
                    "start_index": cursor if key_type in ["list", "zset"] else None,
                    "range_start": range_start,
                    "range_end": range_end,
                    "pagination_type": "cursor"
                }
                
            else:
                # Page-based pagination
                total_pages = (key_size + per_page - 1) // per_page if key_size > 0 else 1
                start_index = (page - 1) * per_page
                end_index = start_index + per_page - 1  # Redis uses inclusive end indices
                
                if key_type == "list":
                    # Use LRANGE for lists
                    key_value = redis_conn.lrange(key_name, start_index, end_index)
                    
                elif key_type == "set":
                    # For sets, we need to use SSCAN for pagination
                    scan_cursor = 0
                    all_members = []
                    # Get all members first (sets don't have inherent ordering)
                    while True:
                        scan_cursor, members = redis_conn.sscan(key_name, cursor=scan_cursor, count=1000)
                        all_members.extend(members)
                        if scan_cursor == 0:
                            break
                    
                    # Sort for consistent pagination
                    all_members.sort()
                    key_value = all_members[start_index:start_index + per_page]
                    
                elif key_type == "zset":
                    # Use ZRANGE for sorted sets (already ordered by score)
                    key_value = redis_conn.zrange(key_name, start_index, end_index, withscores=True)
                    
                elif key_type == "hash":
                    # For hashes, get all fields first then paginate
                    all_fields = redis_conn.hgetall(key_name)
                    # Sort fields for consistent pagination
                    sorted_fields = sorted(all_fields.items())
                    paginated_fields = sorted_fields[start_index:start_index + per_page]
                    key_value = dict(paginated_fields)
                
                return {
                    "name": key_name,
                    "type": key_type,
                    "ttl": ttl if ttl > 0 else None,
                    "size": key_size,
                    "value": key_value,
                    "exists": True,
                    "error": None,
                    "is_paginated": True,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "has_more": page < total_pages,
                    "start_index": start_index,
                    "end_index": min(start_index + len(key_value) - 1, key_size - 1) if key_value else start_index,
                    "showing_count": len(key_value) if key_value else 0
                }
            
        except Exception as e:
            logger.exception(f"Error getting paginated key data for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            
            base_error_response = {
                "name": key_name,
                "type": None,
                "ttl": None,
                "size": 0,
                "value": None,
                "exists": False,
                "error": str(e),
                "is_paginated": False,
            }
            
            if use_cursor_pagination:
                base_error_response.update({
                    "cursor": cursor,
                    "next_cursor": 0,
                    "has_more": False,
                    "showing_count": 0
                })
            else:
                base_error_response.update({
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0,
                    "has_more": False
                })
            
            return base_error_response

    @classmethod
    def add_list_item(cls, instance_alias: str, db_number: int, key_name: str, value: str, position: str = "end") -> Dict[str, Any]:
        """
        Add a new item to a Redis list.
        
        Args:
            instance_alias: Redis instance alias
            db_number: Database number
            key_name: Name of the list key
            value: Value to add to the list
            position: Where to add the item ("start" or "end", defaults to "end")
            
        Returns:
            Dict with success status and any error information
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a list (or doesn't exist yet)
            if redis_conn.exists(key_name) and redis_conn.type(key_name) != "list":
                return {"success": False, "error": f"Key '{key_name}' exists but is not a list"}
            
            # Add the item to the list
            if position == "start":
                redis_conn.lpush(key_name, value)
            else:  # default to "end"
                redis_conn.rpush(key_name, value)
            
            return {"success": True, "error": None}
            
        except Exception as e:
            logger.exception(f"Error adding list item for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def add_set_member(cls, instance_alias: str, db_number: int, key_name: str, member: str) -> Dict[str, Any]:
        """
        Add a member to a Redis set.
        
        Args:
            instance_alias: Redis instance alias
            db_number: Database number
            key_name: Name of the set key
            member: Member to add to the set
            
        Returns:
            Dict with success status and any error information
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a set (or doesn't exist yet)
            if redis_conn.exists(key_name) and redis_conn.type(key_name) != "set":
                return {"success": False, "error": f"Key '{key_name}' exists but is not a set"}
            
            # Add the member to the set
            result = redis_conn.sadd(key_name, member)
            
            # result is 1 if member was added, 0 if it already existed
            if result == 0:
                return {"success": True, "error": None, "message": "Member already exists in set"}
            else:
                return {"success": True, "error": None, "message": "Member added to set"}
            
        except Exception as e:
            logger.exception(f"Error adding set member for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def add_zset_member(cls, instance_alias: str, db_number: int, key_name: str, score: float, member: str) -> Dict[str, Any]:
        """
        Add a member with score to a Redis sorted set.
        
        Args:
            instance_alias: Redis instance alias
            db_number: Database number
            key_name: Name of the sorted set key
            score: Score for the member
            member: Member to add to the sorted set
            
        Returns:
            Dict with success status and any error information
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a sorted set (or doesn't exist yet)
            if redis_conn.exists(key_name) and redis_conn.type(key_name) != "zset":
                return {"success": False, "error": f"Key '{key_name}' exists but is not a sorted set"}
            
            # Add the member to the sorted set
            result = redis_conn.zadd(key_name, {member: score})
            
            # result is 1 if member was added, 0 if score was updated
            if result == 0:
                return {"success": True, "error": None, "message": "Member score updated in sorted set"}
            else:
                return {"success": True, "error": None, "message": "Member added to sorted set"}
            
        except Exception as e:
            logger.exception(f"Error adding zset member for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def add_hash_field(cls, instance_alias: str, db_number: int, key_name: str, field: str, value: str) -> Dict[str, Any]:
        """
        Add a field-value pair to a Redis hash.
        
        Args:
            instance_alias: Redis instance alias
            db_number: Database number
            key_name: Name of the hash key
            field: Field name
            value: Field value
            
        Returns:
            Dict with success status and any error information
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a hash (or doesn't exist yet)
            if redis_conn.exists(key_name) and redis_conn.type(key_name) != "hash":
                return {"success": False, "error": f"Key '{key_name}' exists but is not a hash"}
            
            # Add the field to the hash
            result = redis_conn.hset(key_name, field, value)
            
            # result is 1 if field was added, 0 if it was updated
            if result == 0:
                return {"success": True, "error": None, "message": "Field updated in hash"}
            else:
                return {"success": True, "error": None, "message": "Field added to hash"}
            
        except Exception as e:
            logger.exception(f"Error adding hash field for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def delete_list_item_by_index(cls, instance_alias: str, db_number: int, key_name: str, index: int) -> Dict[str, Any]:
        """
        Delete a specific item from a Redis list at the given index.
        
        Note: This is implemented by setting the item to a unique temporary value
        and then removing it, as Redis doesn't have a direct "delete by index" command.        
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a list
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "list":
                return {"success": False, "error": f"Key '{key_name}' is not a list"}
            
            # Get list length to validate index
            list_length = redis_conn.llen(key_name)
            if index < 0 or index >= list_length:
                return {"success": False, "error": f"Index {index} is out of range (list length: {list_length})"}
            
            # Use a unique temporary value to mark the item for deletion
            import uuid
            temp_value = f"__DELETE_MARKER_{uuid.uuid4().hex}__"
            
            # Set the item to the temporary value
            redis_conn.lset(key_name, index, temp_value)
            
            # Remove the temporary value (removes first occurrence)
            redis_conn.lrem(key_name, 1, temp_value)
            
            return {"success": True, "error": None, "message": "List item deleted successfully"}
            
        except Exception as e:
            logger.exception(f"Error deleting list item for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def delete_set_member(cls, instance_alias: str, db_number: int, key_name: str, member: str) -> Dict[str, Any]:
        """
        Delete a member from a Redis set.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a set
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "set":
                return {"success": False, "error": f"Key '{key_name}' is not a set"}
            
            # Remove the member from the set
            result = redis_conn.srem(key_name, member)
            
            # result is 1 if member was removed, 0 if it didn't exist
            if result == 0:
                return {"success": False, "error": "Member does not exist in set"}
            else:
                return {"success": True, "error": None, "message": "Set member deleted successfully"}
            
        except Exception as e:
            logger.exception(f"Error deleting set member for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def delete_zset_member(cls, instance_alias: str, db_number: int, key_name: str, member: str) -> Dict[str, Any]:
        """
        Delete a member from a Redis sorted set.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a sorted set
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "zset":
                return {"success": False, "error": f"Key '{key_name}' is not a sorted set"}
            
            # Remove the member from the sorted set
            result = redis_conn.zrem(key_name, member)
            
            # result is 1 if member was removed, 0 if it didn't exist
            if result == 0:
                return {"success": False, "error": "Member does not exist in sorted set"}
            else:
                return {"success": True, "error": None, "message": "Sorted set member deleted successfully"}
            
        except Exception as e:
            logger.exception(f"Error deleting zset member for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def delete_hash_field(cls, instance_alias: str, db_number: int, key_name: str, field: str) -> Dict[str, Any]:
        """
        Delete a field from a Redis hash.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a hash
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "hash":
                return {"success": False, "error": f"Key '{key_name}' is not a hash"}
            
            # Remove the field from the hash
            result = redis_conn.hdel(key_name, field)
            
            # result is 1 if field was removed, 0 if it didn't exist
            if result == 0:
                return {"success": False, "error": "Field does not exist in hash"}
            else:
                return {"success": True, "error": None, "message": "Hash field deleted successfully"}
            
        except Exception as e:
            logger.exception(f"Error deleting hash field for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def update_list_item_by_index(cls, instance_alias: str, db_number: int, key_name: str, index: int, new_value: str) -> Dict[str, Any]:
        """
        Update a specific item in a Redis list at the given index.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a list
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "list":
                return {"success": False, "error": f"Key '{key_name}' is not a list"}
            
            # Get list length to validate index
            list_length = redis_conn.llen(key_name)
            if index < 0 or index >= list_length:
                return {"success": False, "error": f"Index {index} is out of range (list length: {list_length})"}
            
            # Update the item at the specified index
            redis_conn.lset(key_name, index, new_value)
            
            return {"success": True, "error": None, "message": "List item updated successfully"}
            
        except Exception as e:
            logger.exception(f"Error updating list item for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def update_hash_field_value(cls, instance_alias: str, db_number: int, key_name: str, field: str, new_value: str) -> Dict[str, Any]:
        """
        Update the value of an existing field in a Redis hash.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a hash
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "hash":
                return {"success": False, "error": f"Key '{key_name}' is not a hash"}
            
            # Check if field exists
            if not redis_conn.hexists(key_name, field):
                return {"success": False, "error": f"Field '{field}' does not exist in hash"}
            
            # Update the field value
            redis_conn.hset(key_name, field, new_value)
            
            return {"success": True, "error": None, "message": "Hash field value updated successfully"}
            
        except Exception as e:
            logger.exception(f"Error updating hash field value for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def update_zset_member_score(cls, instance_alias: str, db_number: int, key_name: str, member: str, new_score: float) -> Dict[str, Any]:
        """
        Update the score of an existing member in a Redis sorted set.
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key exists and is a sorted set
            if not redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' does not exist"}
            
            if redis_conn.type(key_name) != "zset":
                return {"success": False, "error": f"Key '{key_name}' is not a sorted set"}
            
            # Check if member exists
            if redis_conn.zscore(key_name, member) is None:
                return {"success": False, "error": f"Member '{member}' does not exist in sorted set"}
            
            # Update the member's score
            redis_conn.zadd(key_name, {member: new_score})
            
            return {"success": True, "error": None, "message": "Sorted set member score updated successfully"}
            
        except Exception as e:
            logger.exception(f"Error updating zset member score for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def create_key(cls, instance_alias: str, db_number: int, key_name: str, key_type: str) -> Dict[str, Any]:
        """
        Create a new empty key of the specified type.
        
        Args:
            instance_alias: Redis instance alias
            db_number: Database number
            key_name: Name of the key to create
            key_type: Type of key to create ('string', 'list', 'set', 'zset', 'hash')
            
        Returns:
            Dict with success status and any error information
        """
        try:
            redis_conn = cls.get_redis_connection(instance_alias)
            redis_conn.select(db_number)
            
            # Check if key already exists
            if redis_conn.exists(key_name):
                return {"success": False, "error": f"Key '{key_name}' already exists"}
            
            # Create empty key based on type
            if key_type == "string":
                redis_conn.set(key_name, "")
            elif key_type == "list":
                # For lists, add a clear placeholder that users can easily understand and remove
                redis_conn.lpush(key_name, "[Edit or delete this placeholder item]")
            elif key_type == "set":
                # For sets, add a clear placeholder member
                redis_conn.sadd(key_name, "[Edit or delete this placeholder member]")
            elif key_type == "zset":
                # For sorted sets, add a clear placeholder member with score 0
                redis_conn.zadd(key_name, {"[Edit or delete this placeholder member]": 0})
            elif key_type == "hash":
                # For hashes, add a clear placeholder field-value pair
                redis_conn.hset(key_name, "[placeholder_field]", "[Edit or delete this placeholder field]")
            else:
                return {"success": False, "error": f"Unsupported key type: {key_type}"}
            
            return {"success": True, "error": None, "message": f"Key '{key_name}' created successfully as {key_type}"}
            
        except Exception as e:
            logger.exception(f"Error creating key for {instance_alias} in db {db_number} for key {key_name}", exc_info=True)
            return {"success": False, "error": str(e)}
