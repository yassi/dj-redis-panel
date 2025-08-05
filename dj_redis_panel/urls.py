from django.urls import path
from . import views

app_name = "dj_redis_panel"

urlpatterns = [
    path("", views.index, name="index"),
]
