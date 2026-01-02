from django.db import models


class RedisPanelPlaceholder(models.Model):
    """
    This is a fake model used to create an entry in the admin panel for the redis panel.
    When we register this app with the admin site, it is configured to simply load
    the redis panel templates.
    """

    class Meta:
        managed = False
        verbose_name = "DJ Redis Panel"
        verbose_name_plural = "DJ Redis Panel"
