from django.contrib import admin
from .models import SavedTopology


@admin.register(SavedTopology)
class SavedTopologyAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "timestamp", "topology",)
