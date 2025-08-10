import redis
from django.conf import settings
from typing import Dict, Any


REDIS_PANEL_SETTINGS_NAME = "DJ_REDIS_PANEL_SETTINGS"


class RedisPanelUtils:
    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
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
                return redis.Redis.from_url(
                    config["url"],
                    ssl_cert_reqs=config.get("ssl_cert_reqs", None),
                    decode_responses=True,
                )
            else:
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
            
            # Scan from the provided cursor until we have enough keys for this page
            while len(page_keys) < per_page and scan_iterations < max_scan_iterations:
                current_cursor, partial_keys = redis_conn.scan(
                    cursor=current_cursor, 
                    match=pattern, 
                    count=scan_count
                )
                
                # Filter and add keys to our page
                matching_keys = [k for k in partial_keys if k]
                remaining_needed = per_page - len(page_keys)
                page_keys.extend(matching_keys[:remaining_needed])
                
                scan_iterations += 1
                
                # If cursor returned to 0, we've completed the full scan
                if current_cursor == 0:
                    break
            
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
            has_more = current_cursor != 0
            scan_complete = current_cursor == 0
            
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
            return {
                "name": key_name,
                "type": None,
                "ttl": None,
                "size": 0,
                "value": None,
                "exists": False,
                "error": str(e)
            }
