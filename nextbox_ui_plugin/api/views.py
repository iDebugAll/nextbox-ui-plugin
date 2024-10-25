from rest_framework.routers import APIRootView
from rest_framework.viewsets import ModelViewSet
from nextbox_ui_plugin.models import SavedTopology
from . import serializers


class NextBoxUIPluginRootView(APIRootView):
    """
    NextBoxUI_plugin API root view
    """
    def get_view_name(self):
        return 'NextBoxUI'

