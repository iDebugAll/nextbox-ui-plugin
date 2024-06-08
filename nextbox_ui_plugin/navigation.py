from packaging import version
from django.conf import settings
NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)

if NETBOX_CURRENT_VERSION >= version.parse("4.0.0"):
    from netbox.plugins import PluginMenuItem
else:
    from extras.plugins import PluginMenuItem


menu_items = (
    PluginMenuItem(
        link='plugins:nextbox_ui_plugin:topology',
        link_text='Topology Viewer',
        buttons=()
    ),
)
