from netbox.plugins import PluginConfig

from importlib.metadata import metadata


class NetBoxTopologyConfig(PluginConfig):
    name = metadata("netbox_topology_plugin").get('Name').replace('-', '_')
    verbose_name = "Netbox Topology Plugin"
    description = metadata("netbox_topology_plugin").get('Summary') #metadata("netbox_topology_plugin").get('Description')
    version = metadata("netbox_topology_plugin").get('Version')
    author = metadata("netbox_topology_plugin").get("Author-email")
    author_email = metadata("netbox_topology_plugin").get("Author-email")
    base_url = 'topology'
    required_settings = []
    default_settings = {}
    caching_config = {
        '*': None
    }


config = NetBoxTopologyConfig
