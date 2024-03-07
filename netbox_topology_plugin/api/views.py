from rest_framework.routers import APIRootView
from rest_framework.viewsets import ModelViewSet
from netbox_topology_plugin.models import SavedTopology
from . import serializers


class NetBoxTopologyPluginRootView(APIRootView):
    """
    NetBoxTopology_plugin API root view
    """
    def get_view_name(self):
        return 'NetBoxTopology'


class SavedTopologyViewSet(ModelViewSet):
    queryset = SavedTopology.objects.all()
    serializer_class = serializers.SavedTopologySerializer
