from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.shortcuts import render
from django_redis import get_redis_connection
from .redis_utils import RedisPanelUtils

# Create your views here.


@staff_member_required
def index(request):
    # Get configured Redis instances
    instances = RedisPanelUtils.get_instances()

    # Check connection status for each configured instance
    redis_instances = []
    for alias, config in instances.items():
        instance_info = {
            "alias": alias,
            "config": config,
            "status": "disconnected",
            "info": None,
            "error": None,
        }

        try:
            # Try to connect and get basic info
            redis_conn = get_redis_connection(alias)
            redis_conn.ping()  # Test connection
            info = redis_conn.info()
            instance_info.update(
                {
                    "status": "connected",
                    "info": {
                        "version": info.get("redis_version", "Unknown"),
                        "memory_used": info.get("used_memory_human", "Unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "total_keys": sum(
                            redis_conn.dbsize()
                            for db in range(16)
                            if redis_conn.select(db) or True
                        ),
                    },
                }
            )
            redis_conn.select(0)  # Reset to default DB
        except Exception as e:
            instance_info["error"] = str(e)

        redis_instances.append(instance_info)

    context = {
        "title": "Dj Redis Panel",
        "opts": None,
        "has_permission": True,
        "site_title": admin.site.site_title,
        "site_header": admin.site.site_header,
        "site_url": admin.site.site_url,
        "user": request.user,
        "redis_instances": redis_instances,
    }
    return render(request, "admin/dj_redis_panel/index.html", context)
