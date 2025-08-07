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
