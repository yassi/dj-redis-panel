from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse


from .models import RedisPanelPlaceholder


@admin.register(RedisPanelPlaceholder)
class RedisPanelPlaceholderAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        # The @staff_member_required decorator on the view will handle auth
        return HttpResponseRedirect(reverse("dj_redis_panel:index"))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow staff members to "view" the Redis panel
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        # Allow staff members to view the Redis panel
        return request.user.is_staff
