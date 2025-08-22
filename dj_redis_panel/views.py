from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.utils.decorators import method_decorator
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


@method_decorator(staff_member_required, name='dispatch')
class KeyDetailView(View):
    """Class-based view for displaying and editing Redis keys"""
    
    def dispatch(self, request, instance_alias, db_number, key_name):
        """Initialize common data for both GET and POST requests"""
        self.instance_alias = instance_alias
        self.db_number = int(db_number)
        self.key_name = key_name
        self.request = request
        
        # Validate instance exists
        instances = RedisPanelUtils.get_instances()
        if instance_alias not in instances:
            raise Http404(f"Redis instance '{instance_alias}' not found")
        
        self.instance_config = instances[instance_alias]
        
        # Get feature flags
        self.allow_key_delete = RedisPanelUtils.is_feature_enabled(instance_alias, "ALLOW_KEY_DELETE")
        self.allow_key_edit = RedisPanelUtils.is_feature_enabled(instance_alias, "ALLOW_KEY_EDIT")
        self.allow_ttl_update = RedisPanelUtils.is_feature_enabled(instance_alias, "ALLOW_TTL_UPDATE")
        self.use_cursor_pagination = RedisPanelUtils.is_feature_enabled(instance_alias, "CURSOR_PAGINATED_COLLECTIONS")
        
        # Get pagination parameters
        self.per_page = self._get_per_page()
        
        return super().dispatch(request, instance_alias, db_number, key_name)
    
    def _get_per_page(self):
        """Get and validate per_page parameter"""
        try:
            per_page = int(self.request.GET.get('per_page', 50))
        except (ValueError, TypeError):
            per_page = 50
        
        if per_page not in [25, 50, 100, 200]:
            per_page = 50
        
        return per_page
    
    def _get_key_data(self):
        """Get key data with appropriate pagination"""
        if self.use_cursor_pagination:
            cursor = self.request.GET.get('cursor', '0')
            try:
                cursor = int(cursor)
                if cursor < 0:
                    cursor = 0
            except (ValueError, TypeError):
                cursor = 0
            
            return RedisPanelUtils.get_paginated_key_data(
                self.instance_alias, self.db_number, self.key_name, 
                cursor=cursor, per_page=self.per_page, pagination_threshold=100
            )
        else:
            page = self.request.GET.get('page', 1)
            try:
                page = int(page)
                if page < 1:
                    page = 1
            except (ValueError, TypeError):
                page = 1
            
            return RedisPanelUtils.get_paginated_key_data(
                self.instance_alias, self.db_number, self.key_name, 
                page=page, per_page=self.per_page, pagination_threshold=100
            )
    
    
    def _add_pagination_info_to_key_data(self, key_data):
        """Add pagination info for template compatibility after non-paginated operations"""
        if self.use_cursor_pagination:
            key_data.update({
                "is_paginated": False,
                "cursor": key_data.get("cursor", 0),
                "per_page": self.per_page,
                "has_more": False,
                "pagination_type": "cursor"
            })
        else:
            key_data.update({
                "is_paginated": False,
                "page": key_data.get("page", 1),
                "per_page": self.per_page,
                "total_pages": 0,
                "has_more": False,
                "pagination_type": "page"
            })
        return key_data
    
    def get(self, request, instance_alias, db_number, key_name):
        """Handle GET requests"""
        key_data = self._get_key_data()
        
        # Handle key not found
        if not key_data["exists"]:
            if key_data["error"]:
                error_message = key_data["error"]
            else:
                raise Http404(f"Key '{key_name}' not found in database {db_number}")
        else:
            error_message = None
        
        context = self._build_context(key_data, error_message=error_message)
        return render(request, "admin/dj_redis_panel/key_detail.html", context)
    
    def post(self, request, instance_alias, db_number, key_name):
        """Handle POST requests"""
        key_data = self._get_key_data()
        error_message = None
        success_message = None
        
        # Handle key not found
        if not key_data["exists"]:
            if key_data["error"]:
                error_message = key_data["error"]
            else:
                raise Http404(f"Key '{key_name}' not found in database {db_number}")
        
        if not error_message:
            try:
                action = request.POST.get("action")
                
                if action == "update_value":
                    success_message, error_message, key_data = self._handle_update_value(key_data)
                elif action == "update_ttl":
                    success_message, error_message, key_data = self._handle_update_ttl(key_data)
                elif action == "delete_key":
                    return self._handle_delete_key()
                elif action == "add_list_item":
                    success_message, error_message, key_data = self._handle_add_list_item()
                elif action == "add_set_member":
                    success_message, error_message, key_data = self._handle_add_set_member()
                elif action == "add_zset_member":
                    success_message, error_message, key_data = self._handle_add_zset_member()
                elif action == "add_hash_field":
                    success_message, error_message, key_data = self._handle_add_hash_field()
                elif action == "delete_list_item":
                    success_message, error_message, key_data = self._handle_delete_list_item()
                elif action == "delete_set_member":
                    success_message, error_message, key_data = self._handle_delete_set_member()
                elif action == "delete_zset_member":
                    success_message, error_message, key_data = self._handle_delete_zset_member()
                elif action == "delete_hash_field":
                    success_message, error_message, key_data = self._handle_delete_hash_field()
                elif action == "update_list_item":
                    success_message, error_message, key_data = self._handle_update_list_item()
                elif action == "update_hash_field_value":
                    success_message, error_message, key_data = self._handle_update_hash_field_value()
                elif action == "update_zset_member_score":
                    success_message, error_message, key_data = self._handle_update_zset_member_score()
                
            except Exception as e:
                error_message = str(e)
        
        context = self._build_context(key_data, error_message=error_message, success_message=success_message)
        return render(request, "admin/dj_redis_panel/key_detail.html", context)
    
    def _handle_update_value(self, key_data):
        """Handle update_value action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", key_data
        
        new_value = self.request.POST.get("new_value", "")
        
        if key_data["type"] == "string":
            redis_conn = RedisPanelUtils.get_redis_connection(self.instance_alias)
            redis_conn.select(self.db_number)
            redis_conn.set(self.key_name, new_value)
            
            # Refresh key data (use non-paginated for editing)
            key_data = RedisPanelUtils.get_key_data(self.instance_alias, self.db_number, self.key_name)
            key_data = self._add_pagination_info_to_key_data(key_data)
            
            return "Key value updated successfully", None, key_data
        else:
            return None, f"Direct editing not supported for {key_data['type']} keys", key_data
    
    def _handle_update_ttl(self, key_data):
        """Handle update_ttl action"""
        if not self.allow_ttl_update:
            return None, "TTL updates are disabled for this instance", key_data
        
        new_ttl = self.request.POST.get("new_ttl", "")
        
        try:
            redis_conn = RedisPanelUtils.get_redis_connection(self.instance_alias)
            redis_conn.select(self.db_number)
            
            if new_ttl.strip() == "" or new_ttl == "-1":
                redis_conn.persist(self.key_name)
                success_message = "TTL removed (key will not expire)"
            else:
                ttl_seconds = int(new_ttl)
                if ttl_seconds > 0:
                    redis_conn.expire(self.key_name, ttl_seconds)
                    success_message = f"TTL set to {ttl_seconds} seconds"
                else:
                    return None, "TTL must be a positive number", key_data
            
            # Refresh key data after TTL update
            key_data = RedisPanelUtils.get_key_data(self.instance_alias, self.db_number, self.key_name)
            key_data = self._add_pagination_info_to_key_data(key_data)
            
            return success_message, None, key_data
            
        except ValueError:
            return None, "TTL must be a valid number", key_data
    
    def _handle_delete_key(self):
        """Handle delete_key action"""
        if not self.allow_key_delete:
            # Return to the same page with error
            key_data = self._get_key_data()
            context = self._build_context(key_data, error_message="Key deletion is disabled for this instance")
            return render(self.request, "admin/dj_redis_panel/key_detail.html", context)
        
        redis_conn = RedisPanelUtils.get_redis_connection(self.instance_alias)
        redis_conn.select(self.db_number)
        redis_conn.delete(self.key_name)
        
        return HttpResponseRedirect(
            reverse("dj_redis_panel:key_search", args=[self.instance_alias, self.db_number]) + "?deleted=1"
        )
    
    def _handle_add_list_item(self):
        """Handle add_list_item action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        new_value = self.request.POST.get("new_value", "")
        position = self.request.POST.get("position", "end")
        
        result = RedisPanelUtils.add_list_item(self.instance_alias, self.db_number, self.key_name, new_value, position)
        
        if result["success"]:
            success_message = result.get("message", f"New item added to {'beginning' if position == 'start' else 'end'} of list")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_add_set_member(self):
        """Handle add_set_member action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        new_member = self.request.POST.get("new_member", "")
        
        result = RedisPanelUtils.add_set_member(self.instance_alias, self.db_number, self.key_name, new_member)
        
        if result["success"]:
            success_message = result.get("message", "Member added to set")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_add_zset_member(self):
        """Handle add_zset_member action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        try:
            new_score = float(self.request.POST.get("new_score", "0"))
            new_member = self.request.POST.get("new_member", "")
            
            result = RedisPanelUtils.add_zset_member(self.instance_alias, self.db_number, self.key_name, new_score, new_member)
            
            if result["success"]:
                success_message = result.get("message", "Member added to sorted set")
                key_data = self._get_key_data()
                return success_message, None, key_data
            else:
                return None, result["error"], self._get_key_data()
                
        except (ValueError, TypeError):
            return None, "Invalid score provided. Score must be a number.", self._get_key_data()
    
    def _handle_add_hash_field(self):
        """Handle add_hash_field action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        new_field = self.request.POST.get("new_field", "")
        new_value = self.request.POST.get("new_value", "")
        
        result = RedisPanelUtils.add_hash_field(self.instance_alias, self.db_number, self.key_name, new_field, new_value)
        
        if result["success"]:
            success_message = result.get("message", "Field added to hash")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_delete_list_item(self):
        """Handle delete_list_item action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        try:
            index = int(self.request.POST.get("index", -1))
            
            result = RedisPanelUtils.delete_list_item_by_index(self.instance_alias, self.db_number, self.key_name, index)
            
            if result["success"]:
                success_message = result.get("message", f"List item at index {index} deleted successfully")
                key_data = self._get_key_data()
                return success_message, None, key_data
            else:
                return None, result["error"], self._get_key_data()
                
        except (ValueError, TypeError):
            return None, "Invalid index provided", self._get_key_data()
    
    def _handle_delete_set_member(self):
        """Handle delete_set_member action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        member = self.request.POST.get("member", "")
        
        result = RedisPanelUtils.delete_set_member(self.instance_alias, self.db_number, self.key_name, member)
        
        if result["success"]:
            success_message = result.get("message", "Set member deleted successfully")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_delete_zset_member(self):
        """Handle delete_zset_member action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        member = self.request.POST.get("member", "")
        
        result = RedisPanelUtils.delete_zset_member(self.instance_alias, self.db_number, self.key_name, member)
        
        if result["success"]:
            success_message = result.get("message", "Sorted set member deleted successfully")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_delete_hash_field(self):
        """Handle delete_hash_field action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        field = self.request.POST.get("field", "")
        
        result = RedisPanelUtils.delete_hash_field(self.instance_alias, self.db_number, self.key_name, field)
        
        if result["success"]:
            success_message = result.get("message", "Hash field deleted successfully")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_update_list_item(self):
        """Handle update_list_item action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        try:
            index = int(self.request.POST.get("index", -1))
            new_value = self.request.POST.get("new_value", "")
            
            result = RedisPanelUtils.update_list_item_by_index(self.instance_alias, self.db_number, self.key_name, index, new_value)
            
            if result["success"]:
                success_message = result.get("message", f"List item at index {index} updated successfully")
                key_data = self._get_key_data()
                return success_message, None, key_data
            else:
                return None, result["error"], self._get_key_data()
                
        except (ValueError, TypeError):
            return None, "Invalid index provided", self._get_key_data()
    
    def _handle_update_hash_field_value(self):
        """Handle update_hash_field_value action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        field = self.request.POST.get("field", "")
        new_value = self.request.POST.get("new_value", "")
        
        result = RedisPanelUtils.update_hash_field_value(self.instance_alias, self.db_number, self.key_name, field, new_value)
        
        if result["success"]:
            success_message = result.get("message", f"Hash field '{field}' updated successfully")
            key_data = self._get_key_data()
            return success_message, None, key_data
        else:
            return None, result["error"], self._get_key_data()
    
    def _handle_update_zset_member_score(self):
        """Handle update_zset_member_score action"""
        if not self.allow_key_edit:
            return None, "Key editing is disabled for this instance", self._get_key_data()
        
        try:
            member = self.request.POST.get("member", "")
            new_score = float(self.request.POST.get("new_score", "0"))
            
            result = RedisPanelUtils.update_zset_member_score(self.instance_alias, self.db_number, self.key_name, member, new_score)
            
            if result["success"]:
                success_message = result.get("message", f"Score for member '{member}' updated successfully")
                key_data = self._get_key_data()
                return success_message, None, key_data
            else:
                return None, result["error"], self._get_key_data()
                
        except (ValueError, TypeError):
            return None, "Invalid score provided. Score must be a number.", self._get_key_data()
    
    def _build_context(self, key_data, error_message=None, success_message=None):
        """Build template context"""
        return {
            "opts": None,
            "has_permission": True,
            "site_title": admin.site.site_title,
            "site_header": admin.site.site_header,
            "site_url": admin.site.site_url,
            "user": self.request.user,
            "instance_alias": self.instance_alias,
            "instance_config": self.instance_config,
            "db_number": self.db_number,
            "key_data": key_data,
            "error_message": error_message,
            "success_message": success_message,
            "allow_key_delete": self.allow_key_delete,
            "allow_key_edit": self.allow_key_edit,
            "allow_ttl_update": self.allow_ttl_update,
            # Pagination context
            "per_page": self.per_page,
            "is_paginated": key_data.get("is_paginated", False),
            "showing_count": key_data.get("showing_count", 0),
            "has_more": key_data.get("has_more", False),
            "use_cursor_pagination": self.use_cursor_pagination,
            "pagination_type": key_data.get("pagination_type", "page"),
            # Page-based pagination context
            "current_page": key_data.get("page", 1),
            "total_pages": key_data.get("total_pages", 0),
            "has_previous": key_data.get("page", 1) > 1 if not self.use_cursor_pagination else False,
            "has_next": key_data.get("has_more", False),
            "previous_page": key_data.get("page", 1) - 1 if key_data.get("page", 1) > 1 and not self.use_cursor_pagination else None,
            "next_page": key_data.get("page", 1) + 1 if key_data.get("has_more", False) and not self.use_cursor_pagination else None,
            "start_index": key_data.get("start_index", 0),
            "end_index": key_data.get("end_index", 0),
            "page_range": _get_page_range(key_data.get("page", 1), key_data.get("total_pages", 0)) if not self.use_cursor_pagination else [],
            # Cursor-based pagination context
            "current_cursor": key_data.get("cursor", 0),
            "next_cursor": key_data.get("next_cursor", 0),
            "range_start": key_data.get("range_start"),
            "range_end": key_data.get("range_end"),
        }
