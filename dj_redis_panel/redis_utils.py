from django_redis import get_redis_connection
from django.conf import settings


REDIS_PANEL_SETTINGS_NAME = "DJ_REDIS_PANEL_SETTINGS"


class RedisPanelUtils:
    @classmethod
    def get_settings(cls):
        panel_settings = getattr(settings, REDIS_PANEL_SETTINGS_NAME, {})
        return panel_settings

    @classmethod
    def get_instances(cls):
        panel_settings = cls.get_settings()
        instances = panel_settings.get("INSTANCES", {})
        return instances

    @classmethod
    def get_redis_connection(cls):
        panel_settings = cls.get_settings()
        redis_connection = get_redis_connection(
            alias=panel_settings.get("REDIS_ALIAS", "default"),
        )
        return redis_connection
