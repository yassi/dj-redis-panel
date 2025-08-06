from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
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

        # Use the test_connection method from RedisPanelUtils
        connection_result = RedisPanelUtils.test_connection(alias)
        instance_info.update(connection_result)

        redis_instances.append(instance_info)

    context = {
        "title": "Redis Instances",
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
    error_message = None
    databases = []
    instance_info = None

    try:
        redis_conn = RedisPanelUtils.get_redis_connection(instance_alias)
        redis_conn.ping()  # Test connection

        # Get instance info
        info = redis_conn.info()
        instance_info = {
            "version": info.get("redis_version", "Unknown"),
            "memory_used": info.get("used_memory_human", "Unknown"),
            "memory_peak": info.get("used_memory_peak_human", "Unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime": info.get("uptime_in_seconds", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
        }

        # Get database overview
        for db_num in range(16):  # Redis default max databases
            try:
                redis_conn.select(db_num)
                key_count = redis_conn.dbsize()

                # Skip empty databases after DB 0
                if key_count == 0 and db_num > 0:
                    continue

                # Count keys with expiration and estimate space usage (sample approach for performance)
                expires = 0
                estimated_space_bytes = 0

                if key_count > 0:
                    # Sample keys to estimate expiration count and space usage
                    cursor, sample_keys = redis_conn.scan(count=100)
                    sample_space = 0

                    for key in sample_keys:
                        # Check expiration
                        if redis_conn.ttl(key) > 0:
                            expires += 1

                        # Estimate space usage for this key
                        try:
                            key_type = redis_conn.type(key)
                            key_size = len(key.encode("utf-8"))  # Key name size

                            if key_type == "string":
                                value = redis_conn.get(key)
                                if value:
                                    key_size += len(str(value).encode("utf-8"))
                            elif key_type == "list":
                                # Estimate list size (sample first few elements)
                                list_len = redis_conn.llen(key)
                                if list_len > 0:
                                    sample_elements = redis_conn.lrange(
                                        key, 0, min(9, list_len - 1)
                                    )
                                    avg_element_size = sum(
                                        len(str(elem).encode("utf-8"))
                                        for elem in sample_elements
                                    ) / len(sample_elements)
                                    key_size += int(avg_element_size * list_len)
                            elif key_type == "set":
                                # Estimate set size (sample members)
                                set_size = redis_conn.scard(key)
                                if set_size > 0:
                                    sample_members = list(
                                        redis_conn.sscan(key, count=10)[1]
                                    )
                                    if sample_members:
                                        avg_member_size = sum(
                                            len(str(member).encode("utf-8"))
                                            for member in sample_members
                                        ) / len(sample_members)
                                        key_size += int(avg_member_size * set_size)
                            elif key_type == "zset":
                                # Estimate sorted set size
                                zset_size = redis_conn.zcard(key)
                                if zset_size > 0:
                                    sample_members = redis_conn.zrange(
                                        key, 0, min(9, zset_size - 1), withscores=True
                                    )
                                    if sample_members:
                                        avg_member_size = sum(
                                            len(str(member).encode("utf-8")) + 8
                                            for member, score in sample_members
                                        ) / len(sample_members)  # +8 for score
                                        key_size += int(avg_member_size * zset_size)
                            elif key_type == "hash":
                                # Estimate hash size
                                hash_size = redis_conn.hlen(key)
                                if hash_size > 0:
                                    sample_fields = dict(
                                        list(
                                            redis_conn.hscan(key, count=10)[1].items()
                                        )[:10]
                                    )
                                    if sample_fields:
                                        avg_field_size = sum(
                                            len(str(k).encode("utf-8"))
                                            + len(str(v).encode("utf-8"))
                                            for k, v in sample_fields.items()
                                        ) / len(sample_fields)
                                        key_size += int(avg_field_size * hash_size)

                            sample_space += key_size
                        except Exception:
                            # If we can't estimate size for a key, use a default estimate
                            sample_space += 100  # 100 bytes default estimate

                    # Estimate total space and expires based on sample
                    if len(sample_keys) > 0:
                        expires = int(expires * (key_count / len(sample_keys)))
                        estimated_space_bytes = int(
                            sample_space * (key_count / len(sample_keys))
                        )

                databases.append(
                    {
                        "db_number": db_num,
                        "key_count": key_count,
                        "expires": expires,
                        "space_mb": round(
                            estimated_space_bytes / (1024 * 1024), 2
                        ),  # Convert to MB
                        "space_kb": round(
                            estimated_space_bytes / 1024, 1
                        ),  # Convert to KB
                        "space_bytes": estimated_space_bytes,
                        "is_default": db_num == 0,
                    }
                )

            except Exception:
                break  # Stop if database doesn't exist

        # Reset to DB 0
        redis_conn.select(0)

    except Exception as e:
        error_message = str(e)

    context = {
        "title": f"Redis Instance - {instance_alias}",
        "opts": None,
        "has_permission": True,
        "site_title": admin.site.site_title,
        "site_header": admin.site.site_header,
        "site_url": admin.site.site_url,
        "user": request.user,
        "instance_alias": instance_alias,
        "instance_config": instance_config,
        "instance_info": instance_info,
        "databases": databases,
        "error_message": error_message,
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
    selected_db = int(db_number)  # Use the URL parameter instead of GET parameter

    # Check for success messages
    success_message = None
    if request.GET.get("deleted") == "1":
        success_message = "Key deleted successfully"

    # Get connection and search keys
    keys_data = []
    total_keys = 0
    error_message = None

    try:
        redis_conn = RedisPanelUtils.get_redis_connection(instance_alias)
        redis_conn.select(selected_db)

        # Use SCAN for better performance than KEYS
        cursor = 0
        keys = []
        while True:
            cursor, partial_keys = redis_conn.scan(
                cursor=cursor, match=search_query, count=100
            )
            keys.extend(partial_keys)
            if cursor == 0:
                break
            # Limit results to prevent overwhelming the browser
            if len(keys) >= 1000:
                break

        total_keys = len(keys)

        # Get detailed information for each key
        for key in keys[:100]:  # Limit displayed keys
            try:
                # Since decode_responses=True, keys are already strings
                key_str = str(key)
                key_type = redis_conn.type(key)  # Already decoded
                ttl = redis_conn.ttl(key)

                # Get size/length based on type
                size = 0
                if key_type == "string":
                    value = redis_conn.get(key) or ""
                    size = len(str(value).encode("utf-8"))  # Get byte size
                elif key_type == "list":
                    size = redis_conn.llen(key)
                elif key_type == "set":
                    size = redis_conn.scard(key)
                elif key_type == "zset":
                    size = redis_conn.zcard(key)
                elif key_type == "hash":
                    size = redis_conn.hlen(key)

                keys_data.append(
                    {
                        "key": key_str,
                        "type": key_type,
                        "ttl": ttl if ttl > 0 else None,
                        "size": size,
                    }
                )
            except Exception:
                # Skip keys that can't be processed
                continue

    except Exception as e:
        error_message = str(e)

    context = {
        "title": f"Redis Keys - {instance_alias} DB {selected_db}",
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
                redis_conn.delete(key_name)
                return HttpResponseRedirect(
                    reverse(
                        "dj_redis_panel:key_search", args=[instance_alias, db_number]
                    )
                    + "?deleted=1"
                )

    except Exception as e:
        error_message = str(e)

    context = {
        "title": f"Redis Key - {key_name}",
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
    }
    return render(request, "admin/dj_redis_panel/key_detail.html", context)
