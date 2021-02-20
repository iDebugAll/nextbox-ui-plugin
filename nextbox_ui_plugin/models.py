from django.db import models
from utilities.querysets import RestrictedQuerySet


class SavedTopology(models.Model):

    name = models.CharField(max_length=100, blank=True)
    topology = models.JSONField()
    layout_context = models.JSONField(null=True, blank=True)
    created_by = models.ForeignKey(
        to="users.AdminUser",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    timestamp = models.DateTimeField()

    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return str(self.name)
