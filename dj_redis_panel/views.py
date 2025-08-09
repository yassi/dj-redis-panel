from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from .redis_utils import RedisPanelUtils

# Create your views here.

def _get_page_range(current_page, total_pages):
    """
    Generate a smart page range for pagination display
    for example:
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    [1, "...", 4, 5, 6, 7, 8, 9, 10, "...", 100]
    [1, "...", 4, 5, 6, 7, 8, 9, 10, "...", 100]
    """
    if total_pages <= 10:
        return list(range(1, total_pages + 1))
    
    # For larger page counts, show pages around current page
    start = max(1, current_page - 5)
    end = min(total_pages + 1, current_page + 6)
    
    pages = list(range(start, end))
    
    # Always include first and last pages
    if 1 not in pages:
        pages = [1, "..."] + pages
    if total_pages not in pages:
        pages = pages + ["...", total_pages]
    
    return pages


@staff_member_required
def index(request):
    instances = RedisPanelUtils.get_instances()
    redis_instances = []
    for alias, config in instances.items():
        # This is the meta data that will be displayed in the index page
        instance_info = {
            "alias": alias,
            "config": config,
            "status": "disconnected",
            "info": None,
            "error": None,
        }

        instance_meta_data = RedisPanelUtils.get_instance_meta_data(alias)
        instance_info.update(instance_meta_data)

        redis_instances.append(instance_info)

    context = {
        "title": "DJ Redis Panel - Instances",
        "opts": None,
        "has_permission": True,
        "site_title": admin.site.site_title,
        "site_header": admin.site.site_header,
        "site_url": admin.site.site_url,
        "user": request.user,
        "redis_instances": redis_instances,
    }
    return render(request, "admin/dj_redis_panel/index.html", context)


@staff_member_required
def instance_overview(request, instance_alias):
    # Get configured Redis instances
    instances = RedisPanelUtils.get_instances()

    # Validate instance exists
    if instance_alias not in instances:
        raise Http404(f"Redis instance '{instance_alias}' not found")

    instance_config = instances[instance_alias]

    # Get instance metadata using the utility method
    meta_data = RedisPanelUtils.get_instance_meta_data(instance_alias)

    context = {
        "title": f"Instance Overview: {instance_alias}",
        "opts": None,
        "has_permission": True,
        "site_title": admin.site.site_title,
        "site_header": admin.site.site_header,
        "site_url": admin.site.site_url,
        "user": request.user,
        "instance_alias": instance_alias,
        "instance_config": instance_config,
        "hero_numbers": meta_data.get("hero_numbers", {}),
        "databases": meta_data.get("databases", []),
        "error_message": meta_data.get("error"),
    }
    return render(request, "admin/dj_redis_panel/instance_overview.html", context)


@staff_member_required
def key_search(request, instance_alias, db_number):
    # Get configured Redis instances
    instances = RedisPanelUtils.get_instances()

    # Validate instance exists
    if instance_alias not in instances:
        raise Http404(f"Redis instance '{instance_alias}' not found")

    instance_config = instances[instance_alias]
    search_query = request.GET.get("q", "*")
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 25))
    selected_db = int(db_number)  # Use the URL parameter instead of GET parameter
    
    # no need to support weird values for pagination, just allow our presets
    if per_page not in [10, 25, 50, 100]:
        per_page = 25

    # Check for success messages
    success_message = None
    if request.GET.get("deleted") == "1":
        success_message = "Key deleted successfully"

    try:
        try:
            page_num = int(page)
        except (ValueError, TypeError):
            page_num = 1
            
        scan_result = RedisPanelUtils.paginated_scan(
            instance_alias=instance_alias,
            db_number=selected_db,
            pattern=search_query,
            page=page_num,
            per_page=per_page
        )
        
        if scan_result["error"]:
            error_message = scan_result["error"]
            keys_data = []
            total_keys = 0
            page_obj = None
        else:
            keys_data = scan_result["keys_with_details"]
            total_keys = scan_result["total_keys"]  # Now we have accurate total counts
            error_message = None
            
    except Exception as e:
        error_message = str(e)
        keys_data = []
        total_keys = 0
        scan_result = {
            "page": 1,
            "per_page": per_page,
            "total_pages": 0,
            "has_more": False
        }

    context = {
        "title": f"{instance_alias}::DB{selected_db}::Key Search",
        "opts": None,
        "has_permission": True,
        "site_title": admin.site.site_title,
        "site_header": admin.site.site_header,
        "site_url": admin.site.site_url,
        "user": request.user,
        "instance_alias": instance_alias,
        "instance_config": instance_config,
        "search_query": search_query,
        "selected_db": selected_db,
        "keys_data": keys_data,
        "total_keys": total_keys,
        "showing_keys": len(keys_data),
        "error_message": error_message,
        "success_message": success_message,
        "per_page": per_page,
        "current_page": scan_result["page"],
        "total_pages": scan_result["total_pages"],
        "has_previous": scan_result["page"] > 1,
        "has_next": scan_result["has_more"],
        "previous_page": scan_result["page"] - 1 if scan_result["page"] > 1 else None,
        "next_page": scan_result["page"] + 1 if scan_result["has_more"] else None,
        "start_index": (scan_result["page"] - 1) * scan_result["per_page"] + 1,
        "end_index": min((scan_result["page"] - 1) * scan_result["per_page"] + len(keys_data), total_keys),
        "page_range": _get_page_range(scan_result["page"], scan_result["total_pages"]),
    }
    return render(request, "admin/dj_redis_panel/key_search.html", context)


@staff_member_required
def key_detail(request, instance_alias, db_number, key_name):
    """View and edit a specific Redis key"""
    instances = RedisPanelUtils.get_instances()
    if instance_alias not in instances:
        raise Http404(f"Redis instance '{instance_alias}' not found")

    instance_config = instances[instance_alias]
    error_message = None
    success_message = None
    key_data = None

    try:
        redis_conn = RedisPanelUtils.get_redis_connection(instance_alias)
        redis_conn.select(db_number)

        # Check if key exists
        if not redis_conn.exists(key_name):
            raise Http404(f"Key '{key_name}' not found in database {db_number}")

        # Get key information
        key_type = redis_conn.type(key_name)
        ttl = redis_conn.ttl(key_name)

        # Get key value based on type
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

        key_data = {
            "name": key_name,
            "type": key_type,
            "ttl": ttl if ttl > 0 else None,
            "size": key_size,
            "value": key_value,
        }

        # Handle POST request for editing
        if request.method == "POST":
            action = request.POST.get("action")

            if action == "update_value":
                new_value = request.POST.get("new_value", "")

                if key_type == "string":
                    redis_conn.set(key_name, new_value)
                    key_data["value"] = new_value
                    success_message = "Key value updated successfully"
                else:
                    error_message = f"Direct editing not supported for {key_type} keys"

            elif action == "update_ttl":
                new_ttl = request.POST.get("new_ttl", "")
                try:
                    if new_ttl.strip() == "" or new_ttl == "-1":
                        redis_conn.persist(key_name)
                        key_data["ttl"] = None
                        success_message = "TTL removed (key will not expire)"
                    else:
                        ttl_seconds = int(new_ttl)
                        if ttl_seconds > 0:
                            redis_conn.expire(key_name, ttl_seconds)
                            key_data["ttl"] = ttl_seconds
                            success_message = f"TTL set to {ttl_seconds} seconds"
                        else:
                            error_message = "TTL must be a positive number"
                except ValueError:
                    error_message = "TTL must be a valid number"

            elif action == "delete_key":
                # Check if key deletion is allowed
                panel_settings = RedisPanelUtils.get_settings()
                allow_key_delete = panel_settings.get("ALLOW_KEY_DELETE", False)
                
                if allow_key_delete:
                    redis_conn.delete(key_name)
                    return HttpResponseRedirect(
                        reverse(
                            "dj_redis_panel:key_search", args=[instance_alias, db_number]
                        )
                        + "?deleted=1"
                    )
                else:
                    error_message = "Key deletion is disabled in settings"

    except Exception as e:
        error_message = str(e)

    # Check if key deletion is allowed
    panel_settings = RedisPanelUtils.get_settings()
    allow_key_delete = panel_settings.get("ALLOW_KEY_DELETE", False)

    context = {
        "opts": None,
        "has_permission": True,
        "site_title": admin.site.site_title,
        "site_header": admin.site.site_header,
        "site_url": admin.site.site_url,
        "user": request.user,
        "instance_alias": instance_alias,
        "instance_config": instance_config,
        "db_number": db_number,
        "key_data": key_data,
        "error_message": error_message,
        "success_message": success_message,
        "allow_key_delete": allow_key_delete,
    }
    return render(request, "admin/dj_redis_panel/key_detail.html", context)
