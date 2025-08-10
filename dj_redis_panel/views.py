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
    cursor_param = request.GET.get('cursor', '0')  # Get cursor from URL parameter
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
        
        try:
            cursor_int = int(cursor_param)
        except (ValueError, TypeError):
            cursor_int = 0
        
        # Check if cursor-based pagination is enabled for this instance
        use_cursor_pagination = RedisPanelUtils.is_feature_enabled(instance_alias, "CURSOR_PAGINATED_SCAN")
        
        if use_cursor_pagination:
            scan_result = RedisPanelUtils.cursor_paginated_scan(
                instance_alias=instance_alias,
                db_number=selected_db,
                pattern=search_query,
                per_page=per_page,
                cursor=cursor_int
            )
        else:
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
        use_cursor_pagination = RedisPanelUtils.is_feature_enabled(instance_alias, "CURSOR_PAGINATED_SCAN")
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
        "use_cursor_pagination": use_cursor_pagination,
        "current_cursor": scan_result.get("current_cursor", 0),
        "next_cursor": scan_result.get("next_cursor", 0),
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

    allow_key_delete = RedisPanelUtils.is_feature_enabled(instance_alias, "ALLOW_KEY_DELETE")
    allow_key_edit = RedisPanelUtils.is_feature_enabled(instance_alias, "ALLOW_KEY_EDIT")
    allow_ttl_update = RedisPanelUtils.is_feature_enabled(instance_alias, "ALLOW_TTL_UPDATE")

    key_data = RedisPanelUtils.get_key_data(instance_alias, db_number, key_name)
    
    # Handle key not found
    if not key_data["exists"]:
        if key_data["error"]:
            error_message = key_data["error"]
        else:
            raise Http404(f"Key '{key_name}' not found in database {db_number}")
    
    try:
        # Only get Redis connection for POST operations (editing)
        redis_conn = None
        if request.method == "POST":
            redis_conn = RedisPanelUtils.get_redis_connection(instance_alias)
            redis_conn.select(db_number)

        # Handle POST request for editing
        if request.method == "POST":
            action = request.POST.get("action")

            if action == "update_value":
                if allow_key_edit:
                    new_value = request.POST.get("new_value", "")

                    if key_data["type"] == "string":
                        redis_conn.set(key_name, new_value)
                        success_message = "Key value updated successfully"
                        # Refresh key data after update
                        key_data = RedisPanelUtils.get_key_data(instance_alias, db_number, key_name)
                    else:
                        error_message = f"Direct editing not supported for {key_data['type']} keys"
                else:
                    error_message = "Key editing is disabled for this instance"

            elif action == "update_ttl":
                if allow_ttl_update:
                    new_ttl = request.POST.get("new_ttl", "")
                    try:
                        if new_ttl.strip() == "" or new_ttl == "-1":
                            redis_conn.persist(key_name)
                            success_message = "TTL removed (key will not expire)"
                        else:
                            ttl_seconds = int(new_ttl)
                            if ttl_seconds > 0:
                                redis_conn.expire(key_name, ttl_seconds)
                                success_message = f"TTL set to {ttl_seconds} seconds"
                            else:
                                error_message = "TTL must be a positive number"
                        
                        # Refresh key data after TTL update
                        if not error_message:
                            key_data = RedisPanelUtils.get_key_data(instance_alias, db_number, key_name)
                    except ValueError:
                        error_message = "TTL must be a valid number"
                else:
                    error_message = "TTL updates are disabled for this instance"

            elif action == "delete_key":
                if allow_key_delete:
                    redis_conn.delete(key_name)
                    return HttpResponseRedirect(
                        reverse(
                            "dj_redis_panel:key_search", args=[instance_alias, db_number]
                        )
                        + "?deleted=1"
                    )
                else:
                    error_message = "Key deletion is disabled for this instance"

    except Exception as e:
        error_message = str(e)

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
        "allow_key_edit": allow_key_edit,
        "allow_ttl_update": allow_ttl_update,
    }
    return render(request, "admin/dj_redis_panel/key_detail.html", context)
