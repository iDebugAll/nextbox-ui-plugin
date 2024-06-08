from django.db import models
from utilities.querysets import RestrictedQuerySet
from django.conf import settings
from packaging import version

NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)

def get_user_model():
    if NETBOX_CURRENT_VERSION >= version.parse("4.0.0"):
        return 'users.User'
    else:
        return 'users.NetBoxUser'

class SavedTopology(models.Model):

    name = models.CharField(max_length=100, blank=True)
    topology = models.JSONField()
    layout_context = models.JSONField(null=True, blank=True)
    created_by = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    timestamp = models.DateTimeField()

    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return str(self.name)
