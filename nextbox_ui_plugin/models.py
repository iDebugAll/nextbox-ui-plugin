from django.db import models
from utilities.querysets import RestrictedQuerySet


class SavedTopology(models.Model):

    topology = models.JSONField()
    user = models.ForeignKey(
        to="users.AdminUser",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    timestamp = models.DateTimeField()

    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return str(self.timestamp)
