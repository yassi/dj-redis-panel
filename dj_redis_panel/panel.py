class RedisPanel:
    id = "dj_redis_panel"
    name = "Redis Panel"
    description = "Monitor Redis connections, memory, and keys"
    icon = "database"

    def get_url_name(self):
        return "index"
