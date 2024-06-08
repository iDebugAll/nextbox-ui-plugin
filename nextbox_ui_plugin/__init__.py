from packaging import version
from django.conf import settings
NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)

if NETBOX_CURRENT_VERSION >= version.parse("4.0.0"):
    from netbox.plugins import PluginConfig
else:
    from extras.plugins import PluginConfig

class NextBoxUIConfig(PluginConfig):
    name = 'nextbox_ui_plugin'
    verbose_name = 'NextBox UI'
    description = 'A topology visualization plugin for Netbox powered by NextUI Toolkit.'
    version = '0.15.0'
    author = 'Igor Korotchenkov'
    author_email = 'iDebugAll@gmail.com'
    base_url = 'nextbox-ui'
    required_settings = []
    default_settings = {}
    caching_config = {
        '*': None
    }

config = NextBoxUIConfig
