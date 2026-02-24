from django.urls import path
from . import views

app_name = "dj_redis_panel"

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:instance_alias>/", views.instance_overview, name="instance_overview"),
    path("<str:instance_alias>/flush/<int:db_number>/", views.flush, name="flushdb"),
    path("<str:instance_alias>/flush/all/", views.flush, {"flushall": True}, name="flushall"),
    path(
        "<str:instance_alias>/db/<int:db_number>/keys/",
        views.key_search,
        name="key_search",
    ),
    path(
        "<str:instance_alias>/db/<int:db_number>/keys/add/",
        views.key_add,
        name="key_add",
    ),
    path(
        "<str:instance_alias>/db/<int:db_number>/key/<path:key_name>",
        views.KeyDetailView.as_view(),
        name="key_detail",
    ),
]
